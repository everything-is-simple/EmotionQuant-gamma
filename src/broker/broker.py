from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import cast

import pandas as pd

from src.broker.matcher import Matcher
from src.broker.risk import BrokerRiskState, RiskManager
from src.config import Settings
from src.contracts import Order, Signal, Trade, build_order_id
from src.data.store import Store


@dataclass
class Position:
    code: str
    entry_date: date
    entry_price: float
    quantity: int
    current_price: float
    max_price: float
    pattern: str
    is_paper: bool = False


class Broker:
    def __init__(self, store: Store, config: Settings, initial_cash: float | None = None):
        self.store = store
        self.config = config
        self.cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
        self.portfolio: dict[str, Position] = {}
        self.pending_orders: list[Order] = []
        self.risk = RiskManager(store, config)
        self.matcher = Matcher(config)

    def _portfolio_market_value(self) -> float:
        return sum(pos.current_price * pos.quantity for pos in self.portfolio.values() if not pos.is_paper)

    def process_signals(self, signals: list[Signal]) -> list[Order]:
        orders: list[Order] = []
        rejected: list[Order] = []
        state = BrokerRiskState(
            cash=self.cash,
            portfolio_market_value=self._portfolio_market_value(),
            holdings=set(self.portfolio.keys()),
        )
        # DTT 主线优先按 final_score 排序；legacy 对照链则退回 strength。
        sorted_signals = sorted(
            signals,
            key=lambda s: float(s.final_score if s.final_score is not None else s.strength),
            reverse=True,
        )
        for signal in sorted_signals:
            decision = self.risk.assess_signal(signal, state)
            if decision.order is None:
                # 风控拒绝也写入订单表，便于后续统计机会参与率与拒绝分布。
                if decision.reject_reason is not None:
                    rejected.append(
                        Order(
                            order_id=build_order_id(signal.signal_id),
                            signal_id=signal.signal_id,
                            code=signal.code,
                            action=signal.action,
                            quantity=0,
                            execute_date=decision.execute_date or signal.signal_date,
                            pattern=signal.pattern,
                            status="REJECTED",
                            reject_reason=decision.reject_reason,
                        )
                    )
                continue
            order = decision.order
            orders.append(order)
            self.add_pending_order(order)
            # 预占现金与持仓名额，避免同日后续信号“重复花钱”。
            state.cash = max(0.0, state.cash - float(decision.reserved_cash))
            state.holdings.add(order.code)

        rows = orders + rejected
        if rows:
            self.store.bulk_upsert("l4_orders", pd.DataFrame([o.model_dump() for o in rows]))
        return orders

    def add_pending_order(self, order: Order) -> None:
        self.pending_orders.append(order)

    def get_pending_orders(self, trade_date: date) -> list[Order]:
        return [o for o in self.pending_orders if o.execute_date == trade_date and o.status == "PENDING"]

    def _mark_order_status(self, order: Order, status: str, reason: str | None = None) -> Order:
        payload = order.model_copy(update={"status": status, "reject_reason": reason})
        self.store.bulk_upsert("l4_orders", pd.DataFrame([payload.model_dump()]))
        return payload

    def _get_market_bar(self, code: str, trade_date: date) -> dict | None:
        row = self.store.read_df(
            """
            SELECT
                l2.code,
                l2.date,
                l2.adj_open,
                l1.open AS raw_open,
                l1.is_halt,
                l1.up_limit,
                l1.down_limit
            FROM l2_stock_adj_daily l2
            LEFT JOIN l1_stock_daily l1
                ON split_part(l1.ts_code, '.', 1) = l2.code AND l1.date = l2.date
            WHERE l2.code = ? AND l2.date = ?
            LIMIT 1
            """,
            (code, trade_date),
        )
        if row.empty:
            return None
        return cast(dict[str, object], row.iloc[0].to_dict())

    def _resolve_adj_close(self, code: str, trade_date: date) -> float | None:
        row = self.store.read_df(
            """
            SELECT adj_close
            FROM l2_stock_adj_daily
            WHERE code = ? AND date = ?
            LIMIT 1
            """,
            (code, trade_date),
        )
        if row.empty:
            return None
        value = float(row.iloc[0]["adj_close"] or 0.0)
        return value if value > 0 else None

    def _has_pending_sell(self, code: str) -> bool:
        return any(
            o.status == "PENDING" and o.action == "SELL" and o.code == code for o in self.pending_orders
        )

    def generate_exit_orders(self, signal_date: date) -> list[Order]:
        """
        最小退出机制（Gate 修复项）：
        - 用当日收盘价检查止损/回撤
        - 触发后挂 T+1 开盘 SELL 订单
        - 不改 v0.01 BOF 触发器，仅用于释放仓位占用
        """
        execute_date = self.store.next_trade_date(signal_date)
        if execute_date is None or not self.portfolio:
            return []

        orders: list[Order] = []
        for code, pos in list(self.portfolio.items()):
            if self._has_pending_sell(code):
                continue

            close_price = self._resolve_adj_close(code, signal_date)
            if close_price is None:
                continue

            # 每日更新持仓参考价与历史最高价，供回撤止盈/止损判断。
            pos.current_price = close_price
            pos.max_price = max(pos.max_price, close_price)
            self.portfolio[code] = pos

            stop_loss_price = pos.entry_price * (1 - self.config.stop_loss_pct)
            trailing_price = pos.max_price * (1 - self.config.trailing_stop_pct)

            exit_reason: str | None = None
            if close_price <= stop_loss_price:
                exit_reason = "STOP_LOSS"
            elif close_price <= trailing_price:
                exit_reason = "TRAILING_STOP"

            if exit_reason is None:
                continue

            signal_id = f"{code}_{signal_date.isoformat()}_{exit_reason.lower()}"
            order_id = f"EXIT_{signal_id}"
            order = Order(
                order_id=order_id,
                signal_id=signal_id,
                code=code,
                action="SELL",
                quantity=int(pos.quantity),
                execute_date=execute_date,
                pattern=pos.pattern,
                status="PENDING",
            )
            orders.append(order)
            self.add_pending_order(order)

        if orders:
            self.store.bulk_upsert("l4_orders", pd.DataFrame([o.model_dump() for o in orders]))
        return orders

    def _apply_position_trade(self, trade: Trade) -> None:
        if trade.action == "BUY":
            self.cash -= trade.price * trade.quantity + trade.fee
            self.portfolio[trade.code] = Position(
                code=trade.code,
                entry_date=trade.execute_date,
                entry_price=trade.price,
                quantity=trade.quantity,
                current_price=trade.price,
                max_price=trade.price,
                pattern=trade.pattern,
                is_paper=trade.is_paper,
            )
            return

        # v0.01 SELL 简化：默认全平，后续可扩展部分减仓。
        pos = self.portfolio.get(trade.code)
        if pos is None:
            return
        qty = min(pos.quantity, trade.quantity)
        self.cash += trade.price * qty - trade.fee
        remain = pos.quantity - qty
        if remain <= 0:
            self.portfolio.pop(trade.code, None)
        else:
            pos.quantity = remain
            pos.current_price = trade.price
            pos.max_price = max(pos.max_price, trade.price)
            self.portfolio[trade.code] = pos

    def execute_pending_orders(self, trade_date: date) -> list[Trade]:
        trades: list[Trade] = []
        updated_pending: list[Order] = []
        for order in self.pending_orders:
            if order.status != "PENDING":
                updated_pending.append(order)
                continue
            # 非当日订单继续保留；过期策略由 _expire_orders 处理。
            if order.execute_date != trade_date:
                updated_pending.append(order)
                continue

            bar = self._get_market_bar(order.code, trade_date)
            trade, reject_reason = self.matcher.execute(order, bar or {}, trade_date)
            if trade is None:
                self._mark_order_status(order, "REJECTED", reject_reason)
                continue

            if trade.action == "BUY":
                # 开盘跳空可能导致实成交成本高于前一日预估，需在成交前二次现金校验。
                buy_cost = float(trade.price) * int(trade.quantity) + float(trade.fee)
                if buy_cost > self.cash + 1e-6:
                    self._mark_order_status(order, "REJECTED", "INSUFFICIENT_CASH_AT_EXECUTION")
                    continue

            self._mark_order_status(order, "FILLED")
            trades.append(trade)
            self._apply_position_trade(trade)

        self.pending_orders = updated_pending
        if trades:
            self.store.bulk_upsert("l4_trades", pd.DataFrame([t.model_dump() for t in trades]))
        return trades

    def expire_orders(self, today: date) -> int:
        """
        订单过期处理：
        execute_date 之后超过 max_pending_trade_days 仍未成交，则标记 EXPIRED。
        """
        expired = 0
        updated_pending: list[Order] = []
        for order in self.pending_orders:
            if order.status != "PENDING":
                continue
            # 使用交易日历推进差值，避免自然日周末误差。
            cursor: date | None = order.execute_date
            days = 0
            while cursor is not None and cursor < today:
                cursor = self.store.next_trade_date(cursor)
                days += 1
                if days > self.config.max_pending_trade_days:
                    break
            if days > self.config.max_pending_trade_days:
                self._mark_order_status(order, "EXPIRED", "ORDER_TIMEOUT")
                expired += 1
                continue
            updated_pending.append(order)
        self.pending_orders = updated_pending
        return expired

