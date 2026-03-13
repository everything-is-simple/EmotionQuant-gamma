from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from src.backtest.normandy_bof_quality import (
    NORMANDY_BOF_QUALITY_DTT_VARIANT,
    run_normandy_bof_quality_matrix,
)
from src.broker.matcher import Matcher
from src.config import Settings
from src.contracts import Order, build_exit_order_id, build_exit_signal_id


NORMANDY_BOF_CONTROL_EXIT_DTT_VARIANT = NORMANDY_BOF_QUALITY_DTT_VARIANT
NORMANDY_BOF_CONTROL_EXIT_SCOPE = "normandy_bof_control_exit"


@dataclass(frozen=True)
class NormandyBofExitVariant:
    label: str
    stop_loss_pct: float
    trailing_stop_pct: float
    notes: str
    trailing_activation_delay_trade_days: int | None = None
    trailing_activation_profit_pct: float | None = None
    trailing_loosen_profit_pct: float | None = None
    trailing_stop_pct_after_loosen: float | None = None


def build_normandy_bof_control_exit_variants(_config: Settings | None = None) -> list[NormandyBofExitVariant]:
    return [
        NormandyBofExitVariant(
            label="TIGHT_EXIT",
            stop_loss_pct=0.03,
            trailing_stop_pct=0.05,
            notes="Tighter risk guardrail; answers whether baseline edge is being given back too late.",
        ),
        NormandyBofExitVariant(
            label="LOOSE_EXIT",
            stop_loss_pct=0.08,
            trailing_stop_pct=0.12,
            notes="Looser leash; answers whether current baseline is getting shaken out too early.",
        ),
        NormandyBofExitVariant(
            label="STOP_ONLY",
            stop_loss_pct=0.05,
            trailing_stop_pct=1.00,
            notes="Disable trailing-stop pressure while keeping the current hard stop distance.",
        ),
        NormandyBofExitVariant(
            label="TRAIL_ONLY",
            stop_loss_pct=1.00,
            trailing_stop_pct=0.08,
            notes="Disable fixed stop-loss and keep only the current trailing-stop behavior.",
        ),
    ]


def resolve_normandy_bof_control_exit_variants(
    requested_labels: list[str] | None = None,
) -> list[NormandyBofExitVariant]:
    variants = build_normandy_bof_control_exit_variants()
    if not requested_labels:
        return variants

    requested = {str(label).strip().upper() for label in requested_labels if str(label).strip()}
    if not requested:
        return variants

    known = {variant.label for variant in variants}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(f"Unknown Normandy BOF exit variants: {', '.join(unknown)}")
    return [variant for variant in variants if variant.label in requested]


def _normalize_scalar(value: object) -> object:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    if isinstance(value, int):
        return int(value)
    return value


def _normalize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        clean = {key: _normalize_scalar(value) for key, value in row.items()}
        normalized.append(clean)
    return normalized


def _to_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text)


def _finite_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        cast = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(cast):
        return None
    return cast


BASELINE_PAIRED_TRADES_QUERY = """
WITH buyfills AS (
    SELECT
        signal_id,
        code,
        execute_date AS entry_date,
        quantity AS entry_qty,
        price AS entry_price
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND event_stage = 'MATCH_FILLED'
      AND action = 'BUY'
),
entries AS (
    SELECT
        pt.signal_id,
        pt.signal_date,
        pt.code,
        ROW_NUMBER() OVER (PARTITION BY pt.code ORDER BY pt.signal_date, pt.signal_id) AS entry_seq
    FROM pas_trigger_trace_exp pt
    JOIN buyfills b
      ON pt.signal_id = b.signal_id
     AND pt.code = b.code
    WHERE pt.run_id = ?
      AND pt.detected = TRUE
      AND pt.selected_pattern = pt.detector
),
exit_orders AS (
    SELECT order_id, reason_code AS planned_exit_reason
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND action = 'SELL'
      AND event_stage = 'EXIT_ORDER_CREATED'
),
exits AS (
    SELECT
        order_id,
        code,
        execute_date AS exit_date,
        quantity AS exit_qty,
        price AS exit_price,
        event_stage AS exit_stage,
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY execute_date, COALESCE(trade_id, order_id)) AS exit_seq
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND action = 'SELL'
      AND event_stage IN ('MATCH_FILLED', 'FORCE_CLOSE_FILLED')
),
paired AS (
    SELECT
        e.signal_id,
        e.signal_date,
        e.code,
        b.entry_date,
        b.entry_qty,
        b.entry_price,
        x.order_id AS exit_order_id,
        x.exit_date,
        x.exit_qty,
        x.exit_price,
        x.exit_stage,
        CASE
            WHEN x.exit_stage = 'FORCE_CLOSE_FILLED' THEN 'FORCE_CLOSE'
            ELSE COALESCE(eo.planned_exit_reason, 'UNKNOWN')
        END AS exit_reason
    FROM entries e
    JOIN buyfills b
      ON e.signal_id = b.signal_id
     AND e.code = b.code
    JOIN exits x
      ON e.code = x.code
     AND e.entry_seq = x.exit_seq
     AND b.entry_qty = x.exit_qty
    LEFT JOIN exit_orders eo
      ON eo.order_id = x.order_id
)
SELECT
    signal_id,
    signal_date,
    code,
    entry_date,
    entry_qty,
    entry_price,
    exit_order_id,
    exit_date,
    exit_qty,
    exit_price,
    exit_stage,
    exit_reason
FROM paired
ORDER BY entry_date ASC, code ASC, signal_id ASC
"""


MARKET_BAR_SELECT_PREFIX = """
SELECT
    l2.code,
    l2.date,
    l2.adj_open,
    l2.adj_close,
    l1.open AS raw_open,
    l1.is_halt,
    l1.up_limit,
    l1.down_limit
FROM l2_stock_adj_daily l2
LEFT JOIN l1_stock_daily l1
    ON split_part(l1.ts_code, '.', 1) = l2.code AND l1.date = l2.date
WHERE l2.code IN ({placeholders})
  AND l2.date BETWEEN ? AND ?
ORDER BY l2.code ASC, l2.date ASC
"""


def _query_dicts(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    params: list[object] | tuple[object, ...],
) -> list[dict[str, object]]:
    cursor = connection.execute(query, params)
    columns = [str(item[0]) for item in (cursor.description or ())]
    rows: list[dict[str, object]] = []
    for values in cursor.fetchall():
        row = {columns[index]: values[index] for index in range(len(columns))}
        rows.append(row)
    return rows


def _load_trade_calendar(
    connection: duckdb.DuckDBPyConnection,
    start: date,
    end: date,
) -> tuple[list[date], dict[date, date | None], dict[date, int]]:
    rows = _query_dicts(
        connection,
        """
        SELECT
            date,
            LEAD(date) OVER (ORDER BY date) AS next_trade_date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE
          AND date BETWEEN ? AND ?
        ORDER BY date ASC
        """,
        [start, end],
    )
    trade_days: list[date] = []
    next_trade_day: dict[date, date | None] = {}
    for row in rows:
        trade_date = _to_date(row.get("date"))
        if trade_date is None:
            continue
        trade_days.append(trade_date)
        next_trade_day[trade_date] = _to_date(row.get("next_trade_date"))
    trade_day_index = {trade_date: index for index, trade_date in enumerate(trade_days)}
    return trade_days, next_trade_day, trade_day_index


def _load_market_bars(
    connection: duckdb.DuckDBPyConnection,
    codes: list[str],
    start: date,
    end: date,
) -> dict[str, dict[date, dict[str, object]]]:
    if not codes:
        return {}
    placeholders = ", ".join("?" for _ in codes)
    query = MARKET_BAR_SELECT_PREFIX.format(placeholders=placeholders)
    params: list[object] = [*codes, start, end]
    rows = _query_dicts(connection, query, params)
    bars: dict[str, dict[date, dict[str, object]]] = {}
    for row in rows:
        code = str(row.get("code") or "")
        trade_date = _to_date(row.get("date"))
        if not code or trade_date is None:
            continue
        bars.setdefault(code, {})[trade_date] = {
            "adj_open": _finite_or_none(row.get("adj_open")) or 0.0,
            "adj_close": _finite_or_none(row.get("adj_close")) or 0.0,
            "raw_open": _finite_or_none(row.get("raw_open")) or 0.0,
            "is_halt": bool(row.get("is_halt") or False),
            "up_limit": _finite_or_none(row.get("up_limit")),
            "down_limit": _finite_or_none(row.get("down_limit")),
        }
    return bars


def _count_trade_days_between(start: date, end: date, trade_day_index: dict[date, int]) -> int | None:
    if start not in trade_day_index or end not in trade_day_index:
        return None
    return max(int(trade_day_index[end] - trade_day_index[start]), 0)


def _calculate_trade_pnl(
    matcher: Matcher,
    *,
    entry_price: float,
    exit_price: float,
    quantity: int,
) -> tuple[float, float, float, float]:
    buy_fee = matcher._calculate_fee(entry_price * quantity, "BUY")
    sell_fee = matcher._calculate_fee(exit_price * quantity, "SELL")
    pnl = (exit_price - entry_price) * quantity - buy_fee - sell_fee
    notional = entry_price * quantity
    pnl_pct = 0.0 if notional <= 0 else float(pnl / notional)
    return float(pnl), float(pnl_pct), float(buy_fee), float(sell_fee)


def _build_realized_control_rows(
    paired_rows: list[dict[str, object]],
    matcher: Matcher,
    trade_day_index: dict[date, int],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in paired_rows:
        entry_date = _to_date(item.get("entry_date"))
        exit_date = _to_date(item.get("exit_date"))
        entry_price = _finite_or_none(item.get("entry_price"))
        exit_price = _finite_or_none(item.get("exit_price"))
        quantity = int(item.get("entry_qty") or 0)
        if entry_date is None or exit_date is None or entry_price is None or exit_price is None or quantity <= 0:
            continue
        pnl, pnl_pct, buy_fee, sell_fee = _calculate_trade_pnl(
            matcher,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
        )
        rows.append(
            {
                "signal_id": str(item.get("signal_id") or ""),
                "code": str(item.get("code") or ""),
                "entry_date": entry_date.isoformat(),
                "exit_date": exit_date.isoformat(),
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "quantity": quantity,
                "exit_reason": str(item.get("exit_reason") or "UNKNOWN"),
                "exit_stage": str(item.get("exit_stage") or "UNKNOWN"),
                "hold_trade_days": _count_trade_days_between(entry_date, exit_date, trade_day_index),
                "buy_fee": buy_fee,
                "sell_fee": sell_fee,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "failed_exit_attempts_total": 0,
                "failed_exit_reasons": {},
            }
        )
    return rows


def _simulate_counterfactual_exit(
    *,
    entry: dict[str, object],
    bars_by_date: dict[date, dict[str, object]],
    trade_days: list[date],
    next_trade_day: dict[date, date | None],
    trade_day_index: dict[date, int],
    matcher: Matcher,
    variant: NormandyBofExitVariant,
    end: date,
) -> dict[str, object]:
    signal_id = str(entry.get("signal_id") or "")
    code = str(entry.get("code") or "")
    entry_date = _to_date(entry.get("entry_date"))
    entry_price = _finite_or_none(entry.get("entry_price"))
    quantity = int(entry.get("quantity") or 0)
    if entry_date is None or entry_price is None or quantity <= 0:
        raise ValueError("Counterfactual exit entry is missing required fields")

    max_price = float(entry_price)
    pending_execute_date: date | None = None
    pending_reason: str | None = None
    failed_attempts: list[dict[str, object]] = []

    active_trade_days = [trade_day for trade_day in trade_days if trade_day >= entry_date and trade_day <= end]
    for trade_day in active_trade_days:
        bar = bars_by_date.get(trade_day, {})

        if pending_execute_date == trade_day and pending_reason is not None:
            order = Order(
                order_id=build_exit_order_id(code, trade_day, pending_reason),
                signal_id=build_exit_signal_id(code, trade_day, pending_reason),
                code=code,
                action="SELL",
                quantity=quantity,
                execute_date=trade_day,
                pattern="bof",
                status="PENDING",
            )
            trade, reject_reason = matcher.execute(order, bar, trade_day)
            if trade is not None:
                pnl, pnl_pct, buy_fee, sell_fee = _calculate_trade_pnl(
                    matcher,
                    entry_price=entry_price,
                    exit_price=float(trade.price),
                    quantity=quantity,
                )
                reject_breakdown: dict[str, int] = {}
                for attempt in failed_attempts:
                    reason = str(attempt.get("reject_reason") or "UNKNOWN")
                    reject_breakdown[reason] = reject_breakdown.get(reason, 0) + 1
                return {
                    "signal_id": signal_id,
                    "code": code,
                    "entry_date": entry_date.isoformat(),
                    "exit_date": trade_day.isoformat(),
                    "entry_price": float(entry_price),
                    "exit_price": float(trade.price),
                    "quantity": quantity,
                    "exit_reason": pending_reason,
                    "exit_stage": "MATCH_FILLED",
                    "hold_trade_days": _count_trade_days_between(entry_date, trade_day, trade_day_index),
                    "buy_fee": buy_fee,
                    "sell_fee": sell_fee,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "failed_exit_attempts_total": len(failed_attempts),
                    "failed_exit_reasons": reject_breakdown,
                }
            if reject_reason is not None:
                failed_attempts.append(
                    {
                        "execute_date": trade_day.isoformat(),
                        "planned_exit_reason": pending_reason,
                        "reject_reason": reject_reason,
                    }
                )
            pending_execute_date = None
            pending_reason = None

        close_price = _finite_or_none(bar.get("adj_close"))
        if close_price is None or close_price <= 0:
            continue

        max_price = max(max_price, float(close_price))
        if trade_day == end:
            break
        if pending_execute_date is not None:
            continue

        stop_loss_price = float(entry_price) * (1.0 - float(variant.stop_loss_pct))
        hold_trade_days = _count_trade_days_between(entry_date, trade_day, trade_day_index)
        delay_gate_ready = (
            variant.trailing_activation_delay_trade_days is None
            or (hold_trade_days is not None and hold_trade_days >= int(variant.trailing_activation_delay_trade_days))
        )
        profit_gate_ready = (
            variant.trailing_activation_profit_pct is None
            or max_price >= float(entry_price) * (1.0 + float(variant.trailing_activation_profit_pct))
        )
        trailing_gate_ready = bool(delay_gate_ready and profit_gate_ready)
        active_trailing_stop_pct = float(variant.trailing_stop_pct)
        loosen_gate_ready = (
            variant.trailing_loosen_profit_pct is not None
            and variant.trailing_stop_pct_after_loosen is not None
            and max_price >= float(entry_price) * (1.0 + float(variant.trailing_loosen_profit_pct))
        )
        if loosen_gate_ready:
            active_trailing_stop_pct = float(variant.trailing_stop_pct_after_loosen)
        trailing_price = float(max_price) * (1.0 - active_trailing_stop_pct)
        trigger_reason: str | None = None
        if float(close_price) <= stop_loss_price:
            trigger_reason = "STOP_LOSS"
        elif trailing_gate_ready and float(close_price) <= trailing_price:
            trigger_reason = "TRAILING_STOP"
        if trigger_reason is None:
            continue

        next_day = next_trade_day.get(trade_day)
        if next_day is None or next_day > end:
            continue
        pending_execute_date = next_day
        pending_reason = trigger_reason

    final_bar = bars_by_date.get(end, {})
    final_close = _finite_or_none(final_bar.get("adj_close"))
    if final_close is None or final_close <= 0:
        reject_breakdown: dict[str, int] = {}
        for attempt in failed_attempts:
            reason = str(attempt.get("reject_reason") or "UNKNOWN")
            reject_breakdown[reason] = reject_breakdown.get(reason, 0) + 1
        return {
            "signal_id": signal_id,
            "code": code,
            "entry_date": entry_date.isoformat(),
            "exit_date": None,
            "entry_price": float(entry_price),
            "exit_price": None,
            "quantity": quantity,
            "exit_reason": "MISSING_FORCE_CLOSE",
            "exit_stage": "FORCE_CLOSE_SKIPPED",
            "hold_trade_days": None,
            "buy_fee": matcher._calculate_fee(float(entry_price) * quantity, "BUY"),
            "sell_fee": None,
            "pnl": None,
            "pnl_pct": None,
            "failed_exit_attempts_total": len(failed_attempts),
            "failed_exit_reasons": reject_breakdown,
        }

    slip = matcher.config.slippage_bps / 10000.0
    exit_price = float(final_close) * (1.0 - slip)
    pnl, pnl_pct, buy_fee, sell_fee = _calculate_trade_pnl(
        matcher,
        entry_price=float(entry_price),
        exit_price=exit_price,
        quantity=quantity,
    )
    reject_breakdown = {}
    for attempt in failed_attempts:
        reason = str(attempt.get("reject_reason") or "UNKNOWN")
        reject_breakdown[reason] = reject_breakdown.get(reason, 0) + 1
    return {
        "signal_id": signal_id,
        "code": code,
        "entry_date": entry_date.isoformat(),
        "exit_date": end.isoformat(),
        "entry_price": float(entry_price),
        "exit_price": exit_price,
        "quantity": quantity,
        "exit_reason": "FORCE_CLOSE",
        "exit_stage": "FORCE_CLOSE_FILLED",
        "hold_trade_days": _count_trade_days_between(entry_date, end, trade_day_index),
        "buy_fee": buy_fee,
        "sell_fee": sell_fee,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "failed_exit_attempts_total": len(failed_attempts),
        "failed_exit_reasons": reject_breakdown,
    }


def _summarize_exit_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    frame = pd.DataFrame(rows)
    valid = frame.dropna(subset=["pnl_pct", "pnl"]).copy()
    if valid.empty:
        return {
            "trade_count": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "expected_value": 0.0,
            "profit_factor": 0.0,
            "median_pnl_pct": 0.0,
            "total_pnl": 0.0,
            "avg_hold_trade_days": None,
            "trade_sequence_max_drawdown": None,
            "exit_reason_breakdown": {},
            "failed_exit_attempts_total": 0,
        }

    wins = valid[valid["pnl_pct"] > 0]
    losses = valid[valid["pnl_pct"] <= 0]
    trade_count = int(len(valid))
    avg_win = 0.0 if wins.empty else float(wins["pnl_pct"].mean())
    avg_loss = 0.0 if losses.empty else float(abs(losses["pnl_pct"].mean()))
    win_rate = float(len(wins) / trade_count) if trade_count > 0 else 0.0
    expected_value = float(win_rate * avg_win - (1.0 - win_rate) * avg_loss)
    profit_factor = 0.0 if avg_loss <= 0 else float(avg_win / avg_loss)

    curve = valid.sort_values(["exit_date", "code", "signal_id"], na_position="last")["pnl"].cumsum()
    running_peak = curve.cummax()
    drawdown = (running_peak - curve) / running_peak.replace(0, pd.NA)
    drawdown = drawdown.fillna(0.0)

    exit_reason_breakdown = (
        valid["exit_reason"].fillna("UNKNOWN").astype(str).value_counts().sort_index().to_dict()
    )
    return {
        "trade_count": trade_count,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expected_value": expected_value,
        "profit_factor": profit_factor,
        "median_pnl_pct": float(valid["pnl_pct"].median()),
        "total_pnl": float(valid["pnl"].sum()),
        "avg_hold_trade_days": None
        if valid["hold_trade_days"].dropna().empty
        else float(valid["hold_trade_days"].dropna().mean()),
        "trade_sequence_max_drawdown": float(drawdown.max()),
        "exit_reason_breakdown": {str(key): int(value) for key, value in exit_reason_breakdown.items()},
        "failed_exit_attempts_total": int(valid["failed_exit_attempts_total"].fillna(0).sum()),
    }


def _build_counterfactual_comparison(
    rows: list[dict[str, object]],
    control_lookup: dict[str, dict[str, object]],
    trade_day_index: dict[date, int],
) -> dict[str, object]:
    comparisons: list[dict[str, object]] = []
    for row in rows:
        signal_id = str(row.get("signal_id") or "")
        control = control_lookup.get(signal_id)
        if control is None:
            continue
        control_pnl = _finite_or_none(control.get("pnl"))
        candidate_pnl = _finite_or_none(row.get("pnl"))
        if control_pnl is None or candidate_pnl is None:
            continue
        control_exit_date = _to_date(control.get("exit_date"))
        candidate_exit_date = _to_date(row.get("exit_date"))
        control_idx = None if control_exit_date is None else trade_day_index.get(control_exit_date)
        candidate_idx = None if candidate_exit_date is None else trade_day_index.get(candidate_exit_date)
        comparisons.append(
            {
                "signal_id": signal_id,
                "code": str(row.get("code") or control.get("code") or ""),
                "entry_date": str(row.get("entry_date") or control.get("entry_date") or ""),
                "control_exit_date": None if control_exit_date is None else control_exit_date.isoformat(),
                "candidate_exit_date": None if candidate_exit_date is None else candidate_exit_date.isoformat(),
                "control_exit_reason": str(control.get("exit_reason") or "UNKNOWN"),
                "candidate_exit_reason": str(row.get("exit_reason") or "UNKNOWN"),
                "control_pnl": float(control_pnl),
                "candidate_pnl": float(candidate_pnl),
                "pnl_delta_vs_control": float(candidate_pnl - control_pnl),
                "control_pnl_pct": _finite_or_none(control.get("pnl_pct")),
                "candidate_pnl_pct": _finite_or_none(row.get("pnl_pct")),
                "exit_date_changed": control_exit_date != candidate_exit_date,
                "exit_reason_changed": str(control.get("exit_reason") or "UNKNOWN") != str(row.get("exit_reason") or "UNKNOWN"),
                "exit_timing_delta_trade_days": None
                if control_idx is None or candidate_idx is None
                else int(candidate_idx - control_idx),
            }
        )

    improved = sorted(
        (item for item in comparisons if float(item["pnl_delta_vs_control"]) > 0),
        key=lambda item: float(item["pnl_delta_vs_control"]),
        reverse=True,
    )
    worsened = sorted(
        (item for item in comparisons if float(item["pnl_delta_vs_control"]) < 0),
        key=lambda item: float(item["pnl_delta_vs_control"]),
    )
    total_delta = float(sum(float(item["pnl_delta_vs_control"]) for item in comparisons))
    return {
        "changed_exit_count_vs_control": int(sum(1 for item in comparisons if item["exit_date_changed"] or item["exit_reason_changed"])),
        "improved_trade_count_vs_control": int(len(improved)),
        "worsened_trade_count_vs_control": int(len(worsened)),
        "later_exit_count_vs_control": int(
            sum(1 for item in comparisons if item["exit_timing_delta_trade_days"] is not None and int(item["exit_timing_delta_trade_days"]) > 0)
        ),
        "earlier_exit_count_vs_control": int(
            sum(1 for item in comparisons if item["exit_timing_delta_trade_days"] is not None and int(item["exit_timing_delta_trade_days"]) < 0)
        ),
        "total_pnl_delta_vs_control": total_delta,
        "avg_pnl_delta_vs_control": 0.0 if not comparisons else float(total_delta / len(comparisons)),
        "top_improved_examples": _normalize_rows(improved[:5]),
        "top_worsened_examples": _normalize_rows(worsened[:5]),
    }


def _build_result_payload(
    *,
    label: str,
    kind: str,
    notes: str,
    rows: list[dict[str, object]],
    control_lookup: dict[str, dict[str, object]] | None,
    trade_day_index: dict[date, int],
    stop_loss_pct: float | None = None,
    trailing_stop_pct: float | None = None,
    trailing_activation_delay_trade_days: int | None = None,
    trailing_activation_profit_pct: float | None = None,
    trailing_loosen_profit_pct: float | None = None,
    trailing_stop_pct_after_loosen: float | None = None,
) -> dict[str, object]:
    summary = _summarize_exit_rows(rows)
    payload: dict[str, object] = {
        "label": label,
        "kind": kind,
        "notes": notes,
        "stop_loss_pct": stop_loss_pct,
        "trailing_stop_pct": trailing_stop_pct,
        "trailing_activation_delay_trade_days": trailing_activation_delay_trade_days,
        "trailing_activation_profit_pct": trailing_activation_profit_pct,
        "trailing_loosen_profit_pct": trailing_loosen_profit_pct,
        "trailing_stop_pct_after_loosen": trailing_stop_pct_after_loosen,
        **summary,
        "sample_rows": _normalize_rows(rows[:5]),
    }
    if control_lookup is not None:
        payload["comparison_vs_control"] = _build_counterfactual_comparison(rows, control_lookup, trade_day_index)
    return payload


def run_normandy_bof_control_exit_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str = NORMANDY_BOF_CONTROL_EXIT_DTT_VARIANT,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    dtt_top_n: int | None = None,
    max_positions: int | None = None,
    exit_variant_labels: list[str] | None = None,
) -> dict[str, object]:
    baseline_payload = run_normandy_bof_quality_matrix(
        db_path=db_path,
        config=config,
        start=start,
        end=end,
        dtt_variant=dtt_variant,
        initial_cash=initial_cash,
        rebuild_l3=rebuild_l3,
        working_db_path=working_db_path,
        artifact_root=artifact_root,
        dtt_top_n=dtt_top_n,
        max_positions=max_positions,
        scenario_labels=["BOF_CONTROL"],
    )
    control_result = next(
        item for item in baseline_payload.get("results", []) if isinstance(item, dict) and str(item.get("label") or "") == "BOF_CONTROL"
    )
    control_run_id = str(control_result.get("run_id") or "").strip()
    if not control_run_id:
        raise ValueError("BOF_CONTROL baseline run is missing run_id")

    baseline_db_path = Path(str(baseline_payload.get("db_path") or db_path)).expanduser().resolve()
    variants = resolve_normandy_bof_control_exit_variants(exit_variant_labels)
    matcher = Matcher(config)

    connection = duckdb.connect(str(baseline_db_path), read_only=True)
    try:
        paired_rows = _query_dicts(
            connection,
            BASELINE_PAIRED_TRADES_QUERY,
            [control_run_id, control_run_id, control_run_id, control_run_id],
        )
        if not paired_rows:
            return {
                "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "matrix_status": "empty_control_trade_set",
                "research_parent": "BOF_CONTROL",
                "research_question": "How much edge is BOF_CONTROL losing under the current exit semantics?",
                "source_db_path": str(Path(db_path).expanduser().resolve()),
                "db_path": str(baseline_db_path),
                "artifact_root": str(baseline_payload.get("artifact_root") or ""),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "dtt_variant": dtt_variant,
                "baseline_matrix_summary_run_id": baseline_payload.get("summary_run_id"),
                "baseline_run_id": control_run_id,
                "results": [],
            }

        calendar_start = min(_to_date(row.get("entry_date")) for row in paired_rows if _to_date(row.get("entry_date")) is not None)
        trade_days, next_trade_day, trade_day_index = _load_trade_calendar(connection, calendar_start, end)
        codes = sorted({str(row.get("code") or "") for row in paired_rows if str(row.get("code") or "")})
        market_bars = _load_market_bars(connection, codes, calendar_start, end)
    finally:
        connection.close()

    actual_rows = _build_realized_control_rows(paired_rows, matcher, trade_day_index)
    control_lookup = {str(row.get("signal_id") or ""): row for row in actual_rows}

    results = [
        _build_result_payload(
            label="CONTROL_REALIZED",
            kind="control_realized",
            notes="Observed BOF_CONTROL path under the current broker-frozen exit semantics.",
            rows=actual_rows,
            control_lookup=None,
            trade_day_index=trade_day_index,
            stop_loss_pct=float(config.stop_loss_pct),
            trailing_stop_pct=float(config.trailing_stop_pct),
            trailing_activation_delay_trade_days=None,
            trailing_activation_profit_pct=None,
        )
    ]

    for variant in variants:
        variant_rows = [
            _simulate_counterfactual_exit(
                entry=control_row,
                bars_by_date=market_bars.get(str(control_row.get("code") or ""), {}),
                trade_days=trade_days,
                next_trade_day=next_trade_day,
                trade_day_index=trade_day_index,
                matcher=matcher,
                variant=variant,
                end=end,
            )
            for control_row in actual_rows
        ]
        results.append(
            _build_result_payload(
                label=variant.label,
                kind="counterfactual_exit_variant",
                notes=variant.notes,
                rows=variant_rows,
                control_lookup=control_lookup,
                trade_day_index=trade_day_index,
                stop_loss_pct=float(variant.stop_loss_pct),
                trailing_stop_pct=float(variant.trailing_stop_pct),
                trailing_activation_delay_trade_days=variant.trailing_activation_delay_trade_days,
                trailing_activation_profit_pct=variant.trailing_activation_profit_pct,
                trailing_loosen_profit_pct=variant.trailing_loosen_profit_pct,
                trailing_stop_pct_after_loosen=variant.trailing_stop_pct_after_loosen,
            )
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "BOF_CONTROL",
        "research_question": "On the same BOF_CONTROL entry set, how much edge is being lost by the current exit semantics?",
        "source_db_path": str(Path(db_path).expanduser().resolve()),
        "db_path": str(baseline_db_path),
        "artifact_root": str(baseline_payload.get("artifact_root") or ""),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "baseline_matrix_summary_run_id": baseline_payload.get("summary_run_id"),
        "baseline_run_id": control_run_id,
        "execution_mode": baseline_payload.get("execution_mode"),
        "baseline_trade_count": int(len(actual_rows)),
        "baseline_codes_count": int(len(codes)),
        "exit_variants": [asdict(variant) for variant in variants],
        "results": results,
    }


def build_normandy_bof_control_exit_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_summary_run_id": matrix_payload.get("summary_run_id") or matrix_payload.get("baseline_matrix_summary_run_id"),
            "matrix_status": matrix_status,
            "decision": "rerun_bof_control_exit_matrix",
            "conclusion": "BOF_CONTROL exit matrix 尚未完成，当前不能裁决 baseline lane 的 exit damage。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (item for item in results if isinstance(item, dict) and str(item.get("label") or "") == "CONTROL_REALIZED"),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include CONTROL_REALIZED")

    candidates = [
        item
        for item in results
        if isinstance(item, dict) and str(item.get("kind") or "") == "counterfactual_exit_variant"
    ]
    if not candidates:
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_summary_run_id": matrix_payload.get("summary_run_id") or matrix_payload.get("baseline_matrix_summary_run_id"),
            "matrix_status": matrix_status,
            "decision": "no_counterfactual_variants",
            "conclusion": "当前没有可比的 counterfactual exit 变体，baseline lane 还不能给出 N2 诊断结论。",
        }

    def _rank_key(item: dict[str, object]) -> tuple[float, float, float]:
        comparison = item.get("comparison_vs_control")
        total_delta = 0.0 if not isinstance(comparison, dict) else float(comparison.get("total_pnl_delta_vs_control") or 0.0)
        expected_value = float(item.get("expected_value") or 0.0)
        profit_factor = float(item.get("profit_factor") or 0.0)
        return total_delta, expected_value, profit_factor

    best = sorted(candidates, key=_rank_key, reverse=True)[0]
    best_comparison = best.get("comparison_vs_control")
    if not isinstance(best_comparison, dict):
        best_comparison = {}

    control_ev = float(control.get("expected_value") or 0.0)
    best_ev = float(best.get("expected_value") or 0.0)
    ev_delta = best_ev - control_ev
    total_pnl_delta = float(best_comparison.get("total_pnl_delta_vs_control") or 0.0)
    improved_count = int(best_comparison.get("improved_trade_count_vs_control") or 0)
    worsened_count = int(best_comparison.get("worsened_trade_count_vs_control") or 0)

    if total_pnl_delta > 0 and ev_delta >= 0.002 and improved_count > worsened_count:
        diagnosis = "exit_damage_material"
        decision = "prioritize_exit_semantics_follow_up"
        conclusion = (
            f"最佳 counterfactual 变体 `{best.get('label')}` 相对 CONTROL_REALIZED 录得正向净增益，"
            "说明 baseline lane 当前存在不可忽略的 exit damage。"
        )
    elif total_pnl_delta <= 0 and ev_delta <= 0.0005:
        diagnosis = "exit_damage_limited"
        decision = "keep_entry_quality_as_primary_bottleneck"
        conclusion = (
            f"最佳 counterfactual 变体 `{best.get('label')}` 也未明显优于 CONTROL_REALIZED，"
            "说明 BOF_CONTROL 当前的主要问题不在 exit。"
        )
    else:
        diagnosis = "exit_damage_mixed"
        decision = "keep_baseline_lane_open_but_do_not_rewrite_priority_yet"
        conclusion = (
            f"最佳 counterfactual 变体 `{best.get('label')}` 只给出混合信号，"
            "当前可以确认 exit 不是完全无关，但也还不足以单独改写主队列优先级。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id") or matrix_payload.get("baseline_matrix_summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "control_label": "CONTROL_REALIZED",
        "best_counterfactual_label": best.get("label"),
        "diagnosis": diagnosis,
        "decision": decision,
        "control_summary": {
            "trade_count": int(control.get("trade_count") or 0),
            "expected_value": control.get("expected_value"),
            "profit_factor": control.get("profit_factor"),
            "total_pnl": control.get("total_pnl"),
            "exit_reason_breakdown": control.get("exit_reason_breakdown"),
        },
        "best_counterfactual_summary": {
            "label": best.get("label"),
            "expected_value": best.get("expected_value"),
            "profit_factor": best.get("profit_factor"),
            "total_pnl": best.get("total_pnl"),
            "stop_loss_pct": best.get("stop_loss_pct"),
            "trailing_stop_pct": best.get("trailing_stop_pct"),
            "comparison_vs_control": best_comparison,
        },
        "expected_value_delta_vs_control": ev_delta,
        "conclusion": conclusion,
        "next_actions": [
            "把 BOF_CONTROL 的 baseline lane 结论写成 formal N2 record。",
            "若 exit_damage_material 成立，再决定是否优先改 exit semantics。",
            "保持 N2 promotion lane 继续锁住，不把 baseline diagnosis 误读成 branch promotion。",
        ],
    }


def read_normandy_bof_control_exit_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_bof_control_exit_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
