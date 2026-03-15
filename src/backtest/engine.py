from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.broker.broker import Broker
from src.config import Settings
from src.contracts import Order, Signal, Trade, build_force_close_order_id, build_trade_id, resolve_order_origin
from src.data.store import Store
from src.logging_utils import logger
from src.report.reporter import generate_backtest_report
from src.selector.selector import select_candidates
from src.strategy.strategy import generate_signals

SignalFilterHook = Callable[[list[Signal], date, list[Trade], Broker, Store], list[Signal]]


@dataclass(frozen=True)
class BacktestResult:
    start: date
    end: date
    trade_days: int
    win_rate: float
    avg_win: float
    avg_loss: float
    expected_value: float
    profit_factor: float
    max_drawdown: float
    trade_count: int
    reject_rate: float
    missing_rate: float
    exposure_rate: float
    opportunity_count: float
    filled_count: float
    skip_cash_count: float
    skip_maxpos_count: float
    participation_rate: float
    environment_breakdown: dict[str, dict[str, Any]]
    signal_filter_metrics: dict[str, Any] | None = None


def _iter_trade_days(store: Store, start: date, end: date) -> list[date]:
    days = store.read_df(
        """
        SELECT date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE
          AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if days.empty:
        return []
    return [d.date() if isinstance(d, pd.Timestamp) else d for d in days["date"].tolist()]


def _resolve_close_price(store: Store, code: str, trade_date: date) -> float | None:
    row = store.read_df(
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


def _force_close_all(store: Store, broker: Broker, trade_date: date) -> int:
    """Force-close any remaining positions on the final bar for pairing completeness."""
    if not broker.portfolio:
        return 0

    orders: list[Order] = []
    trades: list[Trade] = []
    lifecycle_rows: list[dict[str, object]] = []
    for code, pos in list(broker.portfolio.items()):
        close_price = _resolve_close_price(store, code, trade_date)
        if close_price is None:
            logger.warning(f"force_close skipped: {code} has no close price on {trade_date}")
            continue

        slip = broker.config.slippage_bps / 10000.0
        sell_price = close_price * (1 - slip)
        fee = broker.matcher._calculate_fee(sell_price * pos.remaining_quantity, "SELL")

        order_id = build_force_close_order_id(code, trade_date)
        order = Order(
            order_id=order_id,
            signal_id=order_id,
            code=code,
            action="SELL",
            quantity=int(pos.remaining_quantity),
            execute_date=trade_date,
            pattern=pos.pattern,
            is_paper=pos.is_paper,
            status="FILLED",
            position_id=pos.position_id,
            exit_reason_code="FORCE_CLOSE",
            is_partial_exit=False,
            remaining_qty_before=int(pos.remaining_quantity),
            target_qty_after=0,
        )
        trade = Trade(
            trade_id=build_trade_id(order_id),
            order_id=order_id,
            code=code,
            execute_date=trade_date,
            action="SELL",
            price=sell_price,
            quantity=int(pos.remaining_quantity),
            fee=fee,
            pattern=pos.pattern,
            is_paper=pos.is_paper,
            position_id=pos.position_id,
            exit_reason_code="FORCE_CLOSE",
            is_partial_exit=False,
            remaining_qty_after=0,
        )
        orders.append(order)
        trades.append(trade)
        lifecycle_rows.append(
            {
                "run_id": broker.run_id,
                "order_id": order.order_id,
                "event_stage": "FORCE_CLOSE_FILLED",
                "signal_id": order.signal_id,
                "trade_id": trade.trade_id,
                "code": order.code,
                "action": order.action,
                "pattern": order.pattern,
                "event_date": trade_date,
                "execute_date": order.execute_date,
                "order_status": order.status,
                "reason_code": "FORCE_CLOSE",
                "origin": resolve_order_origin(order.order_id, order.signal_id),
                "quantity": int(order.quantity),
                "price": float(trade.price),
                "is_paper": order.is_paper,
                "position_id": order.position_id,
                "exit_plan_id": order.exit_plan_id,
                "exit_leg_id": order.exit_leg_id,
                "exit_leg_seq": order.exit_leg_seq,
                "exit_leg_count": order.exit_leg_count,
                "exit_reason_code": order.exit_reason_code,
                "is_partial_exit": bool(order.is_partial_exit),
                "remaining_qty_before": order.remaining_qty_before,
                "remaining_qty_after": trade.remaining_qty_after,
            }
        )

    if not orders:
        return 0

    store.bulk_upsert("l4_orders", pd.DataFrame([o.model_dump() for o in orders]))
    store.bulk_upsert("l4_trades", pd.DataFrame([t.model_dump() for t in trades]))
    broker.record_lifecycle_events(lifecycle_rows)

    for trade in trades:
        broker._apply_position_trade(trade)

    return len(trades)


def run_backtest(
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    patterns: list[str] | None = None,
    initial_cash: float | None = None,
    run_id: str | None = None,
    signal_filter: SignalFilterHook | None = None,
) -> BacktestResult:
    """Run the minimal BOF backtest loop with an optional pre-broker signal filter."""
    cfg = config.model_copy(deep=True)
    if patterns:
        cfg.pas_patterns = ",".join(patterns)
    starting_cash = float(initial_cash if initial_cash is not None else cfg.backtest_initial_cash)

    store = Store(db_path)
    broker = Broker(store, cfg, initial_cash=starting_cash, run_id=run_id)

    try:
        trade_days = _iter_trade_days(store, start, end)
        if not trade_days:
            raise RuntimeError("No trade days available in l1_trade_calendar for given range.")

        for trade_day in trade_days:
            filled_trades = broker.execute_pending_orders(trade_day)
            broker.expire_orders(trade_day)
            broker.generate_exit_orders(trade_day)

            candidates = select_candidates(store, trade_day, cfg, run_id=run_id)
            signals = generate_signals(store, candidates, trade_day, cfg, run_id=run_id)
            if signal_filter is not None:
                filtered_signals = signal_filter(signals, trade_day, filled_trades, broker, store)
                signals = list(filtered_signals) if filtered_signals is not None else []
            broker.process_signals(signals)

        force_closed = _force_close_all(store, broker, trade_days[-1])
        if force_closed > 0:
            logger.info(f"force_close completed: {force_closed} positions on {trade_days[-1]}")

        metrics = generate_backtest_report(store, cfg, start, end, starting_cash)
        signal_filter_metrics: dict[str, Any] | None = None
        if signal_filter is not None:
            build_metrics = getattr(signal_filter, "build_metrics", None)
            if callable(build_metrics):
                payload = build_metrics()
                if isinstance(payload, dict):
                    signal_filter_metrics = payload

        return BacktestResult(
            start=start,
            end=end,
            trade_days=len(trade_days),
            win_rate=float(metrics["win_rate"]),
            avg_win=float(metrics["avg_win"]),
            avg_loss=float(metrics["avg_loss"]),
            expected_value=float(metrics["expected_value"]),
            profit_factor=float(metrics["profit_factor"]),
            max_drawdown=float(metrics["max_drawdown"]),
            trade_count=int(metrics["trade_count"]),
            reject_rate=float(metrics["reject_rate"]),
            missing_rate=float(metrics["missing_rate"]),
            exposure_rate=float(metrics["exposure_rate"]),
            opportunity_count=float(metrics["opportunity_count"]),
            filled_count=float(metrics["filled_count"]),
            skip_cash_count=float(metrics["skip_cash_count"]),
            skip_maxpos_count=float(metrics["skip_maxpos_count"]),
            participation_rate=float(metrics["participation_rate"]),
            environment_breakdown=dict(metrics["environment_breakdown"]),
            signal_filter_metrics=signal_filter_metrics,
        )
    finally:
        store.close()
