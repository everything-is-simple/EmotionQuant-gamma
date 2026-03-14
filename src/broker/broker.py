from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import cast

import pandas as pd

from src.broker.matcher import Matcher
from src.broker.risk import BrokerRiskState, RiskManager
from src.config import Settings
from src.contracts import (
    Order,
    Signal,
    Trade,
    build_exit_leg_id,
    build_exit_order_id,
    build_exit_plan_id,
    build_exit_signal_id,
    build_order_id,
    resolve_order_origin,
)
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
    position_id: str | None = None
    entry_signal_id: str | None = None
    entry_order_id: str | None = None
    entry_trade_id: str | None = None
    initial_quantity: int | None = None
    exit_leg_filled_count: int = 0
    last_exit_date: date | None = None
    last_exit_reason: str | None = None
    state: str = "OPEN"
    active_exit_plan_id: str | None = None
    active_exit_leg_count: int = 0

    def __post_init__(self) -> None:
        if self.initial_quantity is None:
            self.initial_quantity = int(self.quantity)

    @property
    def remaining_quantity(self) -> int:
        # `quantity` 仍是当前持仓的兼容存储位；P6 起显式暴露 remaining_quantity 语义。
        return int(self.quantity)

    @remaining_quantity.setter
    def remaining_quantity(self, value: int) -> None:
        self.quantity = int(value)


class Broker:
    def __init__(
        self,
        store: Store,
        config: Settings,
        initial_cash: float | None = None,
        run_id: str | None = None,
    ):
        self.store = store
        self.config = config
        self.run_id = (run_id or "").strip()
        self.cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
        self.portfolio: dict[str, Position] = {}
        self.pending_orders: list[Order] = []
        self.risk = RiskManager(store, config)
        self.matcher = Matcher(config)

    def _portfolio_market_value(self) -> float:
        return sum(pos.current_price * pos.remaining_quantity for pos in self.portfolio.values() if not pos.is_paper)

    def record_lifecycle_events(self, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        self.store.bulk_upsert("broker_order_lifecycle_trace_exp", pd.DataFrame(rows))

    @staticmethod
    def _resolve_decision_bucket(decision) -> str:
        if decision.order is not None:
            return "ACCEPTED"
        # Phase 3 需要把“容量不足导致的拒绝”单独拎出来，
        # 这样 evidence 才能区分是真 regime 缩容，还是撮合/数据路径失败。
        if decision.reject_reason in {"MAX_POSITIONS_REACHED", "INSUFFICIENT_CASH", "SIZE_BELOW_MIN_LOT"}:
            return "BROKER_CAPACITY_REJECT"
        return str(decision.reject_reason or "UNKNOWN")

    def _record_lifecycle_event(
        self,
        order: Order,
        event_stage: str,
        event_date: date,
        reason_code: str | None = None,
        trade: Trade | None = None,
        price: float | None = None,
    ) -> None:
        self.record_lifecycle_events(
            [
                {
                    "run_id": self.run_id,
                    "order_id": order.order_id,
                    "event_stage": event_stage,
                    "signal_id": order.signal_id,
                    "trade_id": None if trade is None else trade.trade_id,
                    "code": order.code,
                    "action": order.action,
                    "pattern": order.pattern,
                    "event_date": event_date,
                    "execute_date": order.execute_date,
                    "order_status": order.status,
                    "reason_code": reason_code,
                    "origin": resolve_order_origin(order.order_id, order.signal_id),
                    "quantity": int(order.quantity),
                    "price": price,
                    "is_paper": order.is_paper,
                    "position_id": order.position_id,
                    "exit_plan_id": order.exit_plan_id,
                    "exit_leg_id": order.exit_leg_id,
                    "exit_leg_seq": order.exit_leg_seq,
                    "exit_leg_count": order.exit_leg_count,
                    "exit_reason_code": order.exit_reason_code,
                    "is_partial_exit": bool(order.is_partial_exit),
                    "remaining_qty_before": order.remaining_qty_before,
                    "remaining_qty_after": None if trade is None else trade.remaining_qty_after,
                }
            ]
        )

    def _record_mss_overlay_trace(
        self,
        signal: Signal,
        decision,
        state: BrokerRiskState,
    ) -> None:
        # MSS overlay trace 是 Broker 侧的“执行解释真相源”：
        # 同一笔 signal 在评估时看到了什么市场状态、有效容量是多少、最终为何接收/拒绝。
        overlay = decision.overlay
        if overlay is None:
            return
        self.store.bulk_upsert(
            "mss_risk_overlay_trace_exp",
            pd.DataFrame(
                [
                    {
                        "run_id": self.run_id,
                        "signal_id": signal.signal_id,
                        "signal_date": signal.signal_date,
                        "code": signal.code,
                        "pattern": signal.pattern,
                        "variant": signal.variant or self.config.dtt_variant,
                        "signal_mss_score": signal.mss_score,
                        "ranker_mss_score": signal.mss_score,
                        # signal_mss_score/ranker_mss_score 继续只代表排序侧附着分；
                        # 真正控制容量的是下面的 phase/risk_regime/overlay 字段。
                        "overlay_enabled": bool(overlay.overlay_enabled),
                        "overlay_state": overlay.state,
                        "coverage_flag": overlay.coverage_flag,
                        "overlay_reason": overlay.overlay_reason,
                        "market_signal": overlay.signal,
                        "market_score": float(overlay.score),
                        "phase": overlay.phase,
                        "phase_trend": overlay.phase_trend,
                        "phase_days": overlay.phase_days,
                        "position_advice": overlay.position_advice,
                        "risk_regime": overlay.risk_regime,
                        "trend_quality": overlay.trend_quality,
                        "regime_source": overlay.regime_source,
                        "market_coefficient_raw": overlay.market_coefficient_raw,
                        "profit_effect_raw": overlay.profit_effect_raw,
                        "loss_effect_raw": overlay.loss_effect_raw,
                        "continuity_raw": overlay.continuity_raw,
                        "extreme_raw": overlay.extreme_raw,
                        "volatility_raw": overlay.volatility_raw,
                        "market_coefficient": overlay.market_coefficient,
                        "profit_effect": overlay.profit_effect,
                        "loss_effect": overlay.loss_effect,
                        "continuity": overlay.continuity,
                        "extreme": overlay.extreme,
                        "volatility": overlay.volatility,
                        "base_max_positions": int(self.config.max_positions),
                        "base_risk_per_trade_pct": float(self.config.risk_per_trade_pct),
                        "base_max_position_pct": float(self.config.max_position_pct),
                        "max_positions_mult": float(overlay.max_positions_mult),
                        "risk_per_trade_mult": float(overlay.risk_per_trade_mult),
                        "max_position_mult": float(overlay.max_position_mult),
                        "target_max_positions": int(overlay.target_max_positions),
                        "effective_max_positions": int(overlay.max_positions),
                        "max_positions_mode": overlay.max_positions_mode,
                        "max_positions_buffer_slots": int(overlay.max_positions_buffer_slots),
                        "effective_risk_per_trade_pct": float(overlay.risk_per_trade_pct),
                        "effective_max_position_pct": float(overlay.max_position_pct),
                        "holdings_before": int(len(state.holdings)),
                        "available_cash": float(state.cash),
                        "portfolio_market_value": float(state.portfolio_market_value),
                        "decision_status": "ACCEPTED" if decision.order is not None else "REJECTED",
                        "decision_bucket": self._resolve_decision_bucket(decision),
                        "decision_reason": decision.reject_reason,
                        "reserved_cash": float(decision.reserved_cash),
                    }
                ]
            ),
        )

    def process_signals(self, signals: list[Signal]) -> list[Order]:
        """
        信号批量处理（Phase 0 核心）：
        
        流程：
        1. 按 final_score 降序排序（DTT 主线）或 strength（legacy）
        2. 逐个信号调用 RiskManager.assess_signal
        3. 通过的信号生成 Order，预占现金与持仓名额
        4. 拒绝的信号记录 REJECTED 订单与 lifecycle trace
        5. 所有订单（通过+拒绝）写入 l4_orders
        6. MSS overlay trace 写入 mss_risk_overlay_trace_exp
        
        关键约束：
        - 同日信号按分数顺序消费现金与仓位，避免"重复花钱"
        - 拒绝订单也入库，便于统计机会参与率
        """
        orders: list[Order] = []
        rejected: list[Order] = []
        state = BrokerRiskState(
            cash=self.cash,
            portfolio_market_value=self._portfolio_market_value(),
            holdings=set(self.portfolio.keys()),
            batch_start_holdings_count=len(self.portfolio),
        )
        # DTT 主线优先按 final_score 排序；legacy 对照链则退回 strength。
        sorted_signals = sorted(
            signals,
            key=lambda s: float(s.final_score if s.final_score is not None else s.strength),
            reverse=True,
        )
        for signal in sorted_signals:
            # 每条 signal 都基于“当前批次内已经预占过的现金/仓位”来评估，
            # 这样才能真实复现同日竞争带来的顺序效应。
            state_before = BrokerRiskState(
                cash=float(state.cash),
                portfolio_market_value=float(state.portfolio_market_value),
                holdings=set(state.holdings),
                batch_start_holdings_count=state.batch_start_holdings_count,
            )
            decision = self.risk.assess_signal(signal, state)
            self._record_mss_overlay_trace(signal, decision, state_before)
            if decision.order is None:
                # 风控拒绝也写入订单表，便于后续统计机会参与率与拒绝分布。
                if decision.reject_reason is not None:
                    rejected_order = Order(
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
                    rejected.append(rejected_order)
                    self._record_lifecycle_event(
                        rejected_order,
                        event_stage="RISK_REJECTED",
                        event_date=signal.signal_date,
                        reason_code=decision.reject_reason,
                    )
                continue
            order = decision.order
            orders.append(order)
            self.add_pending_order(order)
            self._record_lifecycle_event(
                order,
                event_stage="RISK_ACCEPTED",
                event_date=signal.signal_date,
                reason_code="ACCEPTED",
            )
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

    def _has_pending_sell(self, position: Position) -> bool:
        return any(
            o.status == "PENDING"
            and o.action == "SELL"
            and (
                (position.position_id is not None and o.position_id == position.position_id)
                or (o.position_id is None and o.code == position.code)
            )
            for o in self.pending_orders
        )

    def _resolve_partial_exit_quantity(self, remaining_qty: int) -> int | None:
        ratio = float(self.config.partial_exit_scale_out_ratio)
        ratio = min(max(ratio, 0.0), 1.0)
        target_qty = int(remaining_qty * ratio)
        partial_qty = (target_qty // 100) * 100
        if partial_qty <= 0:
            return None
        remaining_after = remaining_qty - partial_qty
        if remaining_after < 100:
            return None
        return partial_qty

    def _build_exit_order(self, position: Position, signal_date: date, execute_date: date, exit_reason: str) -> Order:
        remaining_before = int(position.remaining_quantity)
        control_mode = self.config.exit_control_mode_normalized
        exit_plan_id: str | None = None
        exit_leg_id: str | None = None
        exit_leg_seq: int | None = None
        exit_leg_count: int | None = None
        is_partial_exit = False
        quantity = remaining_before
        target_qty_after = 0

        if (
            exit_reason == "TRAILING_STOP"
            and control_mode == "naive_trail_scale_out_50_50_control"
            and position.exit_leg_filled_count == 0
        ):
            partial_qty = self._resolve_partial_exit_quantity(remaining_before)
            if partial_qty is not None:
                quantity = partial_qty
                target_qty_after = remaining_before - partial_qty
                exit_plan_id = position.active_exit_plan_id or build_exit_plan_id(
                    position.position_id or position.code,
                    signal_date,
                    exit_reason,
                )
                exit_leg_seq = 1
                exit_leg_count = 2
                is_partial_exit = True
        elif (
            exit_reason == "TRAILING_STOP"
            and control_mode == "naive_trail_scale_out_50_50_control"
            and position.exit_leg_filled_count > 0
            and position.active_exit_plan_id is not None
        ):
            exit_plan_id = position.active_exit_plan_id
            exit_leg_seq = position.exit_leg_filled_count + 1
            exit_leg_count = max(int(position.active_exit_leg_count), int(exit_leg_seq))
            is_partial_exit = True
        if exit_plan_id is not None and exit_leg_seq is not None:
            exit_leg_id = build_exit_leg_id(exit_plan_id, exit_leg_seq)

        order_id = build_exit_order_id(
            position.code,
            signal_date,
            exit_reason,
            exit_plan_id=exit_plan_id,
            exit_leg_seq=exit_leg_seq,
        )
        return Order(
            order_id=order_id,
            signal_id=build_exit_signal_id(position.code, signal_date, exit_reason),
            code=position.code,
            action="SELL",
            quantity=int(quantity),
            execute_date=execute_date,
            pattern=position.pattern,
            status="PENDING",
            position_id=position.position_id,
            exit_plan_id=exit_plan_id,
            exit_leg_id=exit_leg_id,
            exit_leg_seq=exit_leg_seq,
            exit_leg_count=exit_leg_count,
            exit_reason_code=exit_reason,
            is_partial_exit=is_partial_exit,
            remaining_qty_before=remaining_before,
            target_qty_after=target_qty_after,
        )

    def _mark_position_exit_pending(self, order: Order) -> None:
        if order.action != "SELL":
            return
        position = self.portfolio.get(order.code)
        if position is None:
            return
        if position.position_id is not None and order.position_id != position.position_id:
            return
        if order.is_partial_exit and (order.target_qty_after or 0) > 0:
            position.state = "PARTIAL_EXIT_PENDING"
            position.active_exit_plan_id = order.exit_plan_id
            position.active_exit_leg_count = int(order.exit_leg_count or 0)
        else:
            position.state = "FULL_EXIT_PENDING"
        self.portfolio[order.code] = position

    def _restore_position_after_sell_cancel(self, order: Order) -> None:
        if order.action != "SELL":
            return
        position = self.portfolio.get(order.code)
        if position is None:
            return
        if position.position_id is not None and order.position_id != position.position_id:
            return
        if int(position.remaining_quantity) < int(position.initial_quantity or position.remaining_quantity):
            position.state = "OPEN_REDUCED"
        else:
            position.state = "OPEN"
        if position.exit_leg_filled_count <= 0:
            position.active_exit_plan_id = None
            position.active_exit_leg_count = 0
        self.portfolio[order.code] = position

    def _bind_trade_identity(self, order: Order, trade: Trade) -> Trade:
        if order.action == "BUY":
            position_id = order.position_id or order.order_id
            return trade.model_copy(
                update={
                    "position_id": position_id,
                    "remaining_qty_after": int(order.quantity),
                }
            )

        position = self.portfolio.get(order.code)
        remaining_after = None
        if position is not None and (order.position_id is None or position.position_id == order.position_id):
            remaining_after = max(0, int(position.remaining_quantity) - int(trade.quantity))
        return trade.model_copy(
            update={
                "position_id": order.position_id,
                "exit_plan_id": order.exit_plan_id,
                "exit_leg_id": order.exit_leg_id,
                "exit_leg_seq": order.exit_leg_seq,
                "exit_reason_code": order.exit_reason_code,
                "is_partial_exit": bool(order.is_partial_exit),
                "remaining_qty_after": remaining_after,
            }
        )

    def _pending_trade_days_elapsed(self, execute_date: date, today: date) -> int:
        """
        统计 execute_date 之后、截至 today 已推进的交易日数。

        约定：
        - execute_date 当天不计入“挂单已等待天数”
        - `MAX_PENDING_TRADE_DAYS=1` 表示下一交易日仍未成交即过期
        """
        if today <= execute_date:
            return 0

        days = 0
        cursor = execute_date
        while True:
            cursor = self.store.next_trade_date(cursor)
            if cursor is None or cursor > today:
                break
            days += 1
        return days

    def generate_exit_orders(self, signal_date: date) -> list[Order]:
        """
        最小退出机制（Gate 修复项）：
        
        触发条件：
        - STOP_LOSS: 当日收盘价 <= 入场价 * (1 - stop_loss_pct)
        - TRAILING_STOP: 当日收盘价 <= 历史最高价 * (1 - trailing_stop_pct)
        
        执行语义：
        - 用当日收盘价检查止损/回撤
        - 触发后挂 T+1 开盘 SELL 订单
        - 不改 v0.01 BOF 触发器，仅用于释放仓位占用
        
        约束：
        - 同一股票已有挂单 SELL 时跳过（避免重复挂单）
        - 每日更新持仓 current_price 与 max_price
        """
        execute_date = self.store.next_trade_date(signal_date)
        if execute_date is None or not self.portfolio:
            return []

        orders: list[Order] = []
        for code, pos in list(self.portfolio.items()):
            if self._has_pending_sell(pos):
                continue

            close_price = self._resolve_adj_close(code, signal_date)
            if close_price is None:
                continue

            # 每日更新持仓参考价与历史最高价，供回撤止盈/止损判断。
            pos.current_price = close_price
            pos.max_price = max(pos.max_price, close_price)
            self.portfolio[code] = pos

            # 退出逻辑仍然只看 Broker 自己维护的持仓状态：
            # - entry_price 给 stop loss 用
            # - max_price 给 trailing stop 用
            # PAS sidecar 虽然会产 stop_ref/target_ref，但当前执行内核先不强依赖形态参考价，
            # 这样 Broker 还能保持统一、稳定、容易回放的退出语义。
            stop_loss_price = pos.entry_price * (1 - self.config.stop_loss_pct)
            trailing_price = pos.max_price * (1 - self.config.trailing_stop_pct)

            exit_reason: str | None = None
            if close_price <= stop_loss_price:
                exit_reason = "STOP_LOSS"
            elif close_price <= trailing_price:
                exit_reason = "TRAILING_STOP"

            if exit_reason is None:
                continue

            order = self._build_exit_order(pos, signal_date, execute_date, exit_reason)
            orders.append(order)
            self.add_pending_order(order)
            self._mark_position_exit_pending(order)
            self._record_lifecycle_event(
                order,
                event_stage="EXIT_ORDER_CREATED",
                event_date=signal_date,
                reason_code=exit_reason,
            )

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
                position_id=trade.position_id or trade.order_id,
                entry_signal_id=trade.order_id,
                entry_order_id=trade.order_id,
                entry_trade_id=trade.trade_id,
                initial_quantity=trade.quantity,
                state="OPEN",
            )
            return

        pos = self.portfolio.get(trade.code)
        if pos is None:
            return
        if pos.position_id is not None and trade.position_id != pos.position_id:
            return
        qty = min(pos.remaining_quantity, trade.quantity)
        self.cash += trade.price * qty - trade.fee
        remain = pos.remaining_quantity - qty
        pos.exit_leg_filled_count += 1
        pos.last_exit_date = trade.execute_date
        pos.last_exit_reason = trade.exit_reason_code
        if remain <= 0:
            self.portfolio.pop(trade.code, None)
        else:
            pos.remaining_quantity = remain
            pos.current_price = trade.price
            pos.max_price = max(pos.max_price, trade.price)
            pos.state = "OPEN_REDUCED"
            self.portfolio[trade.code] = pos

    def execute_pending_orders(self, trade_date: date) -> list[Trade]:
        """
        挂单撮合执行（Phase 0 核心）：
        
        流程：
        1. 遍历所有 PENDING 订单
        2. 非当日订单保留，等待后续交易日
        3. 当日订单调用 Matcher.execute 撮合
        4. 撮合失败标记 REJECTED，记录 lifecycle trace
        5. 撮合成功前二次现金校验（防开盘跳空超预算）
        6. 通过后标记 FILLED，更新持仓与现金
        7. 所有成交写入 l4_trades
        
        关键约束：
        - BUY 订单成交前必须二次现金校验
        - 撮合拒绝原因包括：停牌、涨跌停、无行情
        """
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
            # 撮合只依赖 execute_date 当天的市场条，严格保持 T+1 Open 语义。
            trade, reject_reason = self.matcher.execute(order, bar or {}, trade_date)
            if trade is None:
                rejected = self._mark_order_status(order, "REJECTED", reject_reason)
                self._restore_position_after_sell_cancel(rejected)
                self._record_lifecycle_event(
                    rejected,
                    event_stage="MATCH_REJECTED",
                    event_date=trade_date,
                    reason_code=reject_reason,
                )
                continue

            if trade.action == "BUY":
                # 开盘跳空可能导致实成交成本高于前一日预估，需在成交前二次现金校验。
                buy_cost = float(trade.price) * int(trade.quantity) + float(trade.fee)
                if buy_cost > self.cash + 1e-6:
                    rejected = self._mark_order_status(order, "REJECTED", "INSUFFICIENT_CASH_AT_EXECUTION")
                    self._record_lifecycle_event(
                        rejected,
                        event_stage="MATCH_REJECTED",
                        event_date=trade_date,
                        reason_code="INSUFFICIENT_CASH_AT_EXECUTION",
                    )
                    continue

            if order.action == "BUY":
                order = order.model_copy(update={"position_id": order.position_id or order.order_id})
            trade = self._bind_trade_identity(order, trade)
            filled = self._mark_order_status(order, "FILLED")
            self._record_lifecycle_event(
                filled,
                event_stage="MATCH_FILLED",
                event_date=trade_date,
                reason_code="FILLED",
                trade=trade,
                price=float(trade.price),
                )
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
        max_pending_trade_days = max(0, int(self.config.max_pending_trade_days))
        for order in self.pending_orders:
            if order.status != "PENDING":
                continue
            elapsed_trade_days = self._pending_trade_days_elapsed(order.execute_date, today)
            if elapsed_trade_days >= max_pending_trade_days:
                expired_order = self._mark_order_status(order, "EXPIRED", "ORDER_TIMEOUT")
                self._restore_position_after_sell_cancel(expired_order)
                self._record_lifecycle_event(
                    expired_order,
                    event_stage="ORDER_EXPIRED",
                    event_date=today,
                    reason_code="ORDER_TIMEOUT",
                )
                expired += 1
                continue
            updated_pending.append(order)
        self.pending_orders = updated_pending
        return expired
