from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import generate_backtest_report
from src.run_metadata import finish_run, start_run

PHASE9_DURATION_VALIDATION_SCOPE = "phase9b_duration_percentile_validation"
PHASE9B_BASELINE_CONTROL = "PHASE9B_BASELINE_CONTROL"
PHASE9B_DURATION_P95_NEGATIVE_FILTER = "PHASE9B_DURATION_P95_NEGATIVE_FILTER"


@dataclass(frozen=True)
class Phase9DurationScenario:
    label: str
    filter_role: str
    duration_percentile_threshold: float | None
    pipeline_mode: str
    position_sizing_mode: str
    exit_control_mode: str
    notes: str


@dataclass(frozen=True)
class Phase9ValidationWindow:
    label: str
    start: date
    end: date


def build_phase9_duration_candidate_label(threshold: float) -> str:
    normalized = float(threshold)
    if normalized.is_integer():
        threshold_token = str(int(normalized))
    else:
        threshold_token = str(normalized).replace(".", "_")
    return f"PHASE9B_DURATION_P{threshold_token}_NEGATIVE_FILTER"


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _iter_trade_days(store: Store, start: date, end: date) -> list[date]:
    rows = store.read_df(
        """
        SELECT date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE
          AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if rows.empty:
        return []
    return [item.date() if isinstance(item, pd.Timestamp) else item for item in rows["date"].tolist()]


def build_phase9_validation_windows(
    store: Store,
    *,
    start: date,
    end: date,
) -> list[Phase9ValidationWindow]:
    trade_days = _iter_trade_days(store, start, end)
    if not trade_days:
        raise RuntimeError("No trade days available for Phase 9B validation window.")
    if len(trade_days) < 2:
        return [Phase9ValidationWindow(label="full_window", start=start, end=end)]

    midpoint = len(trade_days) // 2
    front_end = trade_days[max(midpoint - 1, 0)]
    back_start = trade_days[midpoint]
    windows = [Phase9ValidationWindow(label="full_window", start=start, end=end)]
    if front_end >= start:
        windows.append(Phase9ValidationWindow(label="front_half_window", start=start, end=front_end))
    if back_start <= end:
        windows.append(Phase9ValidationWindow(label="back_half_window", start=back_start, end=end))
    return windows


def _resolve_fixed_notional_amount(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> float:
    amount = float(config.fixed_notional_amount)
    if amount > 0:
        return amount
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    return starting_cash * float(config.max_position_pct)


def build_phase9_duration_scenarios(
    config: Settings,
    *,
    threshold: float,
    initial_cash: float | None = None,
) -> list[Phase9DurationScenario]:
    _ = _resolve_fixed_notional_amount(config, initial_cash=initial_cash)
    baseline_note = (
        "Validated baseline only: legacy BOF entry, FIXED_NOTIONAL_CONTROL, FULL_EXIT_CONTROL, "
        "Gene sidecar only."
    )
    candidate_note = (
        "Single-variable candidate only: keep the validated baseline fixed and block entry when "
        f"current_wave_duration_percentile >= {threshold:.1f}."
    )
    return [
        Phase9DurationScenario(
            label=PHASE9B_BASELINE_CONTROL,
            filter_role="none",
            duration_percentile_threshold=None,
            pipeline_mode="legacy",
            position_sizing_mode="fixed_notional",
            exit_control_mode="full_exit_control",
            notes=baseline_note,
        ),
        Phase9DurationScenario(
            label=build_phase9_duration_candidate_label(threshold),
            filter_role="duration_percentile_negative_filter",
            duration_percentile_threshold=float(threshold),
            pipeline_mode="legacy",
            position_sizing_mode="fixed_notional",
            exit_control_mode="full_exit_control",
            notes=candidate_note,
        ),
    ]


def _normalize_runtime_for_phase9(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.history_start = date(2020, 1, 1)
    cfg.pipeline_mode = "legacy"
    cfg.enable_dtt_mode = False
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.enable_gene_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = "fixed_notional"
    cfg.fixed_notional_amount = _resolve_fixed_notional_amount(cfg, initial_cash=initial_cash)
    cfg.exit_control_mode = "full_exit_control"
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _scenario_scope(scenario_label: str, window_label: str) -> str:
    return f"{PHASE9_DURATION_VALIDATION_SCOPE}_{scenario_label.strip().lower()}_{window_label.strip().lower()}"


def _load_duration_context_batch(store: Store, signal_date: date, codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame(columns=["code", "current_wave_duration_percentile", "current_wave_duration_p95"])
    placeholders = ", ".join(["?"] * len(codes))
    params: tuple[object, ...] = tuple(codes) + (signal_date,)
    return store.read_df(
        f"""
        SELECT
            code,
            current_wave_duration_percentile,
            current_wave_duration_p95
        FROM l3_stock_gene
        WHERE code IN ({placeholders})
          AND calc_date = ?
        """,
        params,
    )


class DurationPercentileNegativeSignalFilter:
    def __init__(self, *, threshold: float) -> None:
        self.threshold = float(threshold)
        self.total_signal_count = 0
        self.allowed_signal_count = 0
        self.blocked_signal_count = 0
        self.missing_percentile_signal_count = 0
        self.blocked_rows: list[dict[str, object]] = []
        self.daily_rows: list[dict[str, object]] = []

    def __call__(self, signals, trade_day: date, filled_trades, broker, store: Store):
        daily_total = len(signals)
        if not signals:
            self.daily_rows.append(
                {
                    "signal_date": trade_day.isoformat(),
                    "total_signal_count": 0,
                    "allowed_signal_count": 0,
                    "blocked_signal_count": 0,
                    "missing_percentile_signal_count": 0,
                }
            )
            return []

        codes = sorted({str(signal.code) for signal in signals})
        context = _load_duration_context_batch(store, trade_day, codes)
        context_by_code = {str(row["code"]): row for row in context.to_dict(orient="records")}

        kept = []
        daily_blocked = 0
        daily_missing = 0
        for signal in signals:
            row = context_by_code.get(str(signal.code), {})
            duration_percentile = _optional_float(row.get("current_wave_duration_percentile"))
            if duration_percentile is None:
                daily_missing += 1
                kept.append(signal)
                continue
            if duration_percentile >= self.threshold:
                daily_blocked += 1
                self.blocked_rows.append(
                    {
                        "signal_id": str(signal.signal_id),
                        "signal_date": trade_day.isoformat(),
                        "code": str(signal.code),
                        "pattern": str(signal.pattern),
                        "block_reason": f"DURATION_PERCENTILE_GTE_{self.threshold:g}",
                        "current_wave_duration_percentile": float(duration_percentile),
                        "current_wave_duration_p95": _optional_float(row.get("current_wave_duration_p95")),
                        "duration_percentile_threshold": float(self.threshold),
                    }
                )
                continue
            kept.append(signal)

        daily_allowed = len(kept)
        self.total_signal_count += daily_total
        self.allowed_signal_count += daily_allowed
        self.blocked_signal_count += daily_blocked
        self.missing_percentile_signal_count += daily_missing
        self.daily_rows.append(
            {
                "signal_date": trade_day.isoformat(),
                "total_signal_count": int(daily_total),
                "allowed_signal_count": int(daily_allowed),
                "blocked_signal_count": int(daily_blocked),
                "missing_percentile_signal_count": int(daily_missing),
            }
        )
        return kept

    def build_metrics(self) -> dict[str, object]:
        return {
            "duration_filter_total_signal_count": int(self.total_signal_count),
            "duration_filter_allowed_signal_count": int(self.allowed_signal_count),
            "duration_filter_blocked_signal_count": int(self.blocked_signal_count),
            "duration_filter_blocked_signal_share": float(
                _safe_ratio(self.blocked_signal_count, self.total_signal_count) or 0.0
            ),
            "duration_filter_missing_percentile_signal_count": int(self.missing_percentile_signal_count),
            "duration_filter_threshold": float(self.threshold),
            "duration_filter_rule": f"block when current_wave_duration_percentile >= {self.threshold:g}",
        }


def _filter_window_metrics(
    signal_filter: DurationPercentileNegativeSignalFilter | None,
    windows: list[Phase9ValidationWindow],
) -> dict[str, dict[str, object]]:
    if signal_filter is None or not signal_filter.daily_rows:
        return {}
    daily = pd.DataFrame(signal_filter.daily_rows)
    if daily.empty:
        return {}
    daily["signal_date"] = pd.to_datetime(daily["signal_date"]).dt.date
    out: dict[str, dict[str, object]] = {}
    for window in windows:
        part = daily[(daily["signal_date"] >= window.start) & (daily["signal_date"] <= window.end)].copy()
        total_signal_count = int(part["total_signal_count"].sum()) if not part.empty else 0
        blocked_signal_count = int(part["blocked_signal_count"].sum()) if not part.empty else 0
        allowed_signal_count = int(part["allowed_signal_count"].sum()) if not part.empty else 0
        missing_percentile_signal_count = int(part["missing_percentile_signal_count"].sum()) if not part.empty else 0
        out[window.label] = {
            "duration_filter_total_signal_count": total_signal_count,
            "duration_filter_allowed_signal_count": allowed_signal_count,
            "duration_filter_blocked_signal_count": blocked_signal_count,
            "duration_filter_blocked_signal_share": float(_safe_ratio(blocked_signal_count, total_signal_count) or 0.0),
            "duration_filter_missing_percentile_signal_count": missing_percentile_signal_count,
            "duration_filter_threshold": float(signal_filter.threshold),
            "duration_filter_rule": f"block when current_wave_duration_percentile >= {signal_filter.threshold:g}",
        }
    return out


def _query_rows(store: Store, query: str, params: tuple[object, ...]) -> pd.DataFrame:
    return store.read_df(query, params)


def _load_signals(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT signal_id, signal_date, code, pattern, action, strength, reason_code
        FROM l3_signals
        WHERE signal_date BETWEEN ? AND ?
        ORDER BY signal_date ASC, signal_id ASC
        """,
        (start, end),
    )


def _load_orders(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT order_id, signal_id, code, action, execute_date, status, reject_reason
        FROM l4_orders
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, order_id ASC
        """,
        (start, end),
    )


def _load_buy_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT trade_id, order_id, code, execute_date, price, quantity, fee
        FROM l4_trades
        WHERE action = 'BUY'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )


def _load_trace_counts(store: Store, run_id: str) -> dict[str, int]:
    return {
        "selector_candidate_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM selector_candidate_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "pas_trigger_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM pas_trigger_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "broker_lifecycle_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM broker_order_lifecycle_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "rank_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM l3_signal_rank_exp WHERE run_id = ?", (run_id,)) or 0
        ),
    }


def _failure_reason_breakdown(orders: pd.DataFrame) -> dict[str, int]:
    if orders.empty:
        return {}
    failed = orders[orders["status"].isin(["REJECTED", "EXPIRED"])].copy()
    if failed.empty:
        return {}
    failed["reason_key"] = failed["reject_reason"].fillna(failed["status"]).replace("", "UNKNOWN")
    grouped = failed.groupby("reason_key").size().sort_values(ascending=False)
    return {str(key): int(value) for key, value in grouped.items()}


def _buy_order_diagnostics(orders: pd.DataFrame) -> dict[str, float | int]:
    if orders.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "buy_reject_rate": 0.0,
        }
    buys = orders[orders["action"] == "BUY"].copy()
    if buys.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "buy_reject_rate": 0.0,
        }
    buy_order_count = int(len(buys))
    buy_filled_count = int((buys["status"] == "FILLED").sum())
    buy_reject_count = int((buys["status"] == "REJECTED").sum())
    return {
        "buy_order_count": buy_order_count,
        "buy_filled_count": buy_filled_count,
        "buy_reject_count": buy_reject_count,
        "buy_reject_rate": 0.0 if buy_order_count <= 0 else float(buy_reject_count / buy_order_count),
    }


def _buy_trade_metrics(buys: pd.DataFrame, initial_cash: float) -> dict[str, float | int | None]:
    if buys.empty:
        return {
            "buy_trade_count": 0,
            "avg_entry_quantity": None,
            "avg_entry_notional": None,
            "max_entry_notional_pct_initial_cash": None,
        }
    metrics = buys.copy()
    metrics["entry_notional"] = pd.to_numeric(metrics["price"], errors="coerce").fillna(0.0) * pd.to_numeric(
        metrics["quantity"], errors="coerce"
    ).fillna(0)
    max_entry_notional = float(metrics["entry_notional"].max())
    return {
        "buy_trade_count": int(len(metrics)),
        "avg_entry_quantity": float(pd.to_numeric(metrics["quantity"], errors="coerce").mean()),
        "avg_entry_notional": float(metrics["entry_notional"].mean()),
        "max_entry_notional_pct_initial_cash": 0.0
        if initial_cash <= 0
        else float(max_entry_notional / initial_cash),
    }


def _snapshot_signal_counts(store: Store, start: date, end: date) -> dict[str, int]:
    return {
        "signals_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        )
    }


def _hash_buy_trade_set(buys: pd.DataFrame) -> str:
    if buys.empty:
        return sha256(b"[]").hexdigest()
    payload = buys.loc[:, ["execute_date", "code", "quantity", "price"]].copy()
    payload["execute_date"] = payload["execute_date"].astype(str)
    body = json.dumps(payload.to_dict(orient="records"), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return sha256(body).hexdigest()


def _build_window_result_payload(
    *,
    scenario: Phase9DurationScenario,
    window: Phase9ValidationWindow,
    metrics: dict[str, object],
    trade_days: int,
    store: Store,
    initial_cash: float,
    run_id: str,
    duration_filter_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    orders = _load_orders(store, window.start, window.end)
    buys = _load_buy_trades(store, window.start, window.end)
    return {
        "scenario_label": scenario.label,
        "window_label": window.label,
        "window_start": window.start.isoformat(),
        "window_end": window.end.isoformat(),
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": scenario.pipeline_mode,
        "filter_role": scenario.filter_role,
        "duration_percentile_threshold": scenario.duration_percentile_threshold,
        "position_sizing_mode": scenario.position_sizing_mode,
        "exit_control_mode": scenario.exit_control_mode,
        "trade_days": int(trade_days),
        "trade_count": int(float(metrics["trade_count"])),
        "win_rate": float(metrics["win_rate"]),
        "avg_win": float(metrics["avg_win"]),
        "avg_loss": float(metrics["avg_loss"]),
        "expected_value": float(metrics["expected_value"]),
        "profit_factor": float(metrics["profit_factor"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "reject_rate": float(metrics["reject_rate"]),
        "missing_rate": float(metrics["missing_rate"]),
        "exposure_rate": float(metrics["exposure_rate"]),
        "opportunity_count": float(metrics["opportunity_count"]),
        "filled_count": float(metrics["filled_count"]),
        "skip_cash_count": float(metrics["skip_cash_count"]),
        "skip_maxpos_count": float(metrics["skip_maxpos_count"]),
        "participation_rate": float(metrics["participation_rate"]),
        "environment_breakdown": dict(metrics["environment_breakdown"]),
        "buy_trade_signature": _hash_buy_trade_set(buys),
        "trace_counts": _load_trace_counts(store, run_id),
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
        "duration_filter_metrics": None if duration_filter_metrics is None else dict(duration_filter_metrics),
        **_snapshot_signal_counts(store, window.start, window.end),
        **_buy_order_diagnostics(orders),
        **_buy_trade_metrics(buys, initial_cash),
    }


def _load_runtime_snapshot(store: Store, start: date, end: date) -> dict[str, pd.DataFrame]:
    return {
        "signals": _load_signals(store, start, end),
        "orders": _load_orders(store, start, end),
    }


def build_blocked_signal_truth(
    *,
    blocked_rows: list[dict[str, object]],
    baseline_signals: pd.DataFrame,
    baseline_orders: pd.DataFrame,
) -> dict[str, object]:
    if not blocked_rows:
        return {
            "blocked_signal_count": 0,
            "blocked_signals_present_in_baseline_signal_count": 0,
            "blocked_signals_missing_from_baseline_signal_count": 0,
            "blocked_signals_with_baseline_buy_order_count": 0,
            "blocked_signals_with_baseline_buy_fill_count": 0,
            "blocked_signals_with_baseline_buy_reject_count": 0,
            "blocked_signals_with_baseline_buy_expire_count": 0,
            "blocked_signals_with_no_baseline_buy_order_count": 0,
            "blocked_signals_share_of_baseline_buy_fills": 0.0,
            "blocked_signal_examples": [],
        }

    blocked = pd.DataFrame(blocked_rows).drop_duplicates(subset=["signal_id"]).copy()
    signal_ref = (
        baseline_signals.loc[:, ["signal_id", "signal_date", "code", "pattern"]]
        .drop_duplicates(subset=["signal_id"])
        .copy()
    )
    signal_join = blocked.merge(signal_ref, on="signal_id", how="left", indicator=True, suffixes=("", "_baseline"))
    present_in_baseline = signal_join[signal_join["_merge"] == "both"].copy()
    missing_from_baseline = signal_join[signal_join["_merge"] != "both"].copy()

    baseline_buy_orders = baseline_orders[baseline_orders["action"] == "BUY"].copy()
    order_join = blocked.merge(
        baseline_buy_orders.loc[:, ["signal_id", "status"]].drop_duplicates(),
        on="signal_id",
        how="left",
    )
    with_buy_order = order_join[order_join["status"].notna()].copy()
    with_buy_fill = order_join[order_join["status"] == "FILLED"].copy()
    with_buy_reject = order_join[order_join["status"] == "REJECTED"].copy()
    with_buy_expire = order_join[order_join["status"] == "EXPIRED"].copy()
    without_buy_order = order_join[order_join["status"].isna()].copy()

    baseline_buy_fill_count = int(
        len(baseline_buy_orders[baseline_buy_orders["status"] == "FILLED"].drop_duplicates(subset=["signal_id"]))
    )
    blocked_examples = blocked.sort_values(["signal_date", "signal_id"]).head(20)

    return {
        "blocked_signal_count": int(len(blocked)),
        "blocked_signals_present_in_baseline_signal_count": int(len(present_in_baseline)),
        "blocked_signals_missing_from_baseline_signal_count": int(len(missing_from_baseline)),
        "blocked_signals_with_baseline_buy_order_count": int(len(with_buy_order.drop_duplicates(subset=["signal_id"]))),
        "blocked_signals_with_baseline_buy_fill_count": int(len(with_buy_fill.drop_duplicates(subset=["signal_id"]))),
        "blocked_signals_with_baseline_buy_reject_count": int(len(with_buy_reject.drop_duplicates(subset=["signal_id"]))),
        "blocked_signals_with_baseline_buy_expire_count": int(len(with_buy_expire.drop_duplicates(subset=["signal_id"]))),
        "blocked_signals_with_no_baseline_buy_order_count": int(len(without_buy_order.drop_duplicates(subset=["signal_id"]))),
        "blocked_signals_share_of_baseline_buy_fills": float(
            _safe_ratio(len(with_buy_fill.drop_duplicates(subset=["signal_id"])), baseline_buy_fill_count) or 0.0
        ),
        "blocked_signal_examples": blocked_examples.to_dict(orient="records"),
    }


def _find_result(
    results: list[dict[str, object]],
    *,
    scenario_label: str,
    window_label: str,
) -> dict[str, object]:
    for item in results:
        if (
            str(item.get("scenario_label") or "") == scenario_label
            and str(item.get("window_label") or "") == window_label
        ):
            return item
    raise ValueError(f"Missing result for scenario={scenario_label}, window={window_label}")


def build_phase9_duration_validation_digest(payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "defer_with_smaller_follow_up",
            "conclusion": "Phase 9B validation is incomplete; no truthful runtime ruling is allowed.",
        }

    results = payload.get("results")
    candidate_filter = payload.get("candidate_filter")
    blocked_signal_truth = payload.get("blocked_signal_truth")
    if not isinstance(results, list):
        raise ValueError("payload.results must be a list")
    if not isinstance(candidate_filter, dict):
        raise ValueError("payload.candidate_filter must be a dict")
    if not isinstance(blocked_signal_truth, dict):
        raise ValueError("payload.blocked_signal_truth must be a dict")

    candidate_labels = [
        str(item.get("scenario_label") or "")
        for item in results
        if str(item.get("scenario_label") or "") != PHASE9B_BASELINE_CONTROL
    ]
    candidate_label = candidate_labels[0] if candidate_labels else ""
    if not candidate_label:
        raise ValueError("Missing non-baseline candidate scenario in payload.results")

    baseline = _find_result(results, scenario_label=PHASE9B_BASELINE_CONTROL, window_label="full_window")
    candidate = _find_result(results, scenario_label=candidate_label, window_label="full_window")
    front_candidate = _find_result(
        results,
        scenario_label=candidate_label,
        window_label="front_half_window",
    )
    back_candidate = _find_result(
        results,
        scenario_label=candidate_label,
        window_label="back_half_window",
    )

    filter_metrics = candidate_filter.get("metrics")
    if not isinstance(filter_metrics, dict):
        raise ValueError("payload.candidate_filter.metrics must be a dict")

    expected_value_delta = float(candidate.get("expected_value") or 0.0) - float(baseline.get("expected_value") or 0.0)
    profit_factor_delta = float(candidate.get("profit_factor") or 0.0) - float(baseline.get("profit_factor") or 0.0)
    max_drawdown_delta = float(candidate.get("max_drawdown") or 0.0) - float(baseline.get("max_drawdown") or 0.0)
    trade_count_delta = int(candidate.get("trade_count") or 0) - int(baseline.get("trade_count") or 0)
    buy_filled_delta = int(candidate.get("buy_filled_count") or 0) - int(baseline.get("buy_filled_count") or 0)
    signal_count_delta = int(candidate.get("signals_count") or 0) - int(baseline.get("signals_count") or 0)

    blocked_signal_count = int(filter_metrics.get("duration_filter_blocked_signal_count", 0) or 0)
    blocked_signal_share = float(filter_metrics.get("duration_filter_blocked_signal_share", 0.0) or 0.0)
    blocked_fill_count = int(blocked_signal_truth.get("blocked_signals_with_baseline_buy_fill_count", 0) or 0)
    baseline_signal_alignment = int(
        blocked_signal_truth.get("blocked_signals_present_in_baseline_signal_count", 0) or 0
    ) == blocked_signal_count
    signal_count_aligned = int(filter_metrics.get("duration_filter_total_signal_count", 0) or 0) == int(
        candidate.get("signals_count") or 0
    )
    trace_complete = all(
        int(entry.get("trace_counts", {}).get("pas_trigger_trace_count", 0)) > 0
        and int(entry.get("trace_counts", {}).get("broker_lifecycle_trace_count", 0)) > 0
        for entry in (baseline, candidate, front_candidate, back_candidate)
    )
    window_slice_complete = all(int(entry.get("trade_days") or 0) > 0 for entry in (front_candidate, back_candidate))

    candidate_improves = expected_value_delta > 0.0 and profit_factor_delta > 0.0 and max_drawdown_delta <= 0.0
    candidate_mixed = expected_value_delta > 0.0 and (profit_factor_delta <= 0.0 or max_drawdown_delta > 0.0)

    if not trace_complete or not window_slice_complete or not signal_count_aligned or not baseline_signal_alignment:
        decision = "defer_with_smaller_follow_up"
        diagnosis = "validation_trace_gap"
        conclusion = (
            "Phase 9B produced some replay output, but the isolated rule is not yet trace-complete enough to support "
            "a truthful promotion or rejection call."
        )
    elif blocked_signal_count <= 0 or blocked_fill_count <= 0:
        decision = "retain_sidecar_only"
        diagnosis = "rule_did_not_truthfully_touch_runtime_entries"
        conclusion = (
            "The isolated rule did not remove enough baseline-filled entries to justify runtime promotion; "
            "retain duration_percentile as sidecar only."
        )
    elif candidate_improves:
        decision = "promote_duration_percentile_negative_filter"
        diagnosis = "isolated_negative_filter_improves_baseline"
        conclusion = (
            "The isolated duration_percentile negative filter improved the validated baseline on the full window "
            "without worsening drawdown, so it earns promotion to the next formal Phase 9 package step."
        )
    elif candidate_mixed:
        decision = "defer_with_smaller_follow_up"
        diagnosis = "mixed_tradeoff_needs_smaller_follow_up"
        conclusion = (
            "The isolated duration_percentile rule changes runtime behavior, but the trade-off is mixed; "
            "do not promote yet and open a smaller follow-up if needed."
        )
    else:
        decision = "retain_sidecar_only"
        diagnosis = "isolated_rule_not_better_than_baseline"
        conclusion = (
            "The isolated duration_percentile negative filter failed to beat the validated baseline cleanly; "
            "retain Gene as sidecar only."
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "diagnosis": diagnosis,
        "decision": decision,
        "full_window_comparison": {
            "expected_value_delta_candidate_minus_baseline": expected_value_delta,
            "profit_factor_delta_candidate_minus_baseline": profit_factor_delta,
            "max_drawdown_delta_candidate_minus_baseline": max_drawdown_delta,
            "trade_count_delta_candidate_minus_baseline": trade_count_delta,
            "buy_filled_count_delta_candidate_minus_baseline": buy_filled_delta,
            "signal_count_delta_candidate_minus_baseline": signal_count_delta,
        },
        "isolated_rule_summary": {
            "blocked_signal_count": blocked_signal_count,
            "blocked_signal_share": blocked_signal_share,
            "blocked_signals_with_baseline_buy_fill_count": blocked_fill_count,
            "blocked_signals_share_of_baseline_buy_fills": float(
                blocked_signal_truth.get("blocked_signals_share_of_baseline_buy_fills", 0.0) or 0.0
            ),
            "rule": str(filter_metrics.get("duration_filter_rule") or ""),
        },
        "candidate_window_summary": {
            "front_half_trade_count": front_candidate.get("trade_count"),
            "front_half_expected_value": front_candidate.get("expected_value"),
            "back_half_trade_count": back_candidate.get("trade_count"),
            "back_half_expected_value": back_candidate.get("expected_value"),
        },
        "conclusion": conclusion,
    }


def run_phase9_duration_percentile_validation(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    threshold: float = 95.0,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, object]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    source_db = Path(db_path).expanduser().resolve()
    db_file = prepare_working_db(source_db, working_db_path) if working_db_path is not None else source_db
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    artifact_root_path.mkdir(parents=True, exist_ok=True)

    if rebuild_l3:
        build_store = Store(db_file)
        try:
            build_layers(build_store, config, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    window_store = Store(db_file)
    try:
        windows = build_phase9_validation_windows(window_store, start=start, end=end)
    finally:
        window_store.close()

    scenarios = build_phase9_duration_scenarios(config, threshold=threshold, initial_cash=starting_cash)
    results: list[dict[str, object]] = []
    scenario_snapshots: dict[str, dict[str, pd.DataFrame]] = {}
    candidate_filter_payload: dict[str, object] | None = None

    for scenario in scenarios:
        cfg = _normalize_runtime_for_phase9(config, initial_cash=starting_cash)
        signal_filter = (
            None
            if scenario.filter_role == "none"
            else DurationPercentileNegativeSignalFilter(threshold=float(scenario.duration_percentile_threshold or threshold))
        )
        full_window = windows[0]

        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope=_scenario_scope(scenario.label, full_window.label),
            modules=["backtest", "selector", "strategy", "broker", "report"],
            config=cfg,
            runtime_env="script",
            artifact_root=str(artifact_root_path),
            start=full_window.start,
            end=full_window.end,
        )
        meta_store.close()

        clear_store = Store(db_file)
        try:
            clear_runtime_tables(clear_store, run_id=run.run_id)
        finally:
            clear_store.close()

        try:
            backtest_result = run_backtest(
                db_path=db_file,
                config=cfg,
                start=full_window.start,
                end=full_window.end,
                patterns=["bof"],
                initial_cash=starting_cash,
                run_id=run.run_id,
                signal_filter=signal_filter,
            )
            finish_store = Store(db_file)
            try:
                finish_run(finish_store, run.run_id, "SUCCESS")
            finally:
                finish_store.close()
        except Exception as exc:
            finish_store = Store(db_file)
            try:
                finish_run(finish_store, run.run_id, "FAILED", str(exc))
            finally:
                finish_store.close()
            raise

        filter_window_metrics = _filter_window_metrics(signal_filter, windows)
        snap_store = Store(db_file)
        try:
            scenario_snapshots[scenario.label] = _load_runtime_snapshot(snap_store, full_window.start, full_window.end)
            for window in windows:
                if window.label == "full_window":
                    metrics = {
                        "trade_count": backtest_result.trade_count,
                        "win_rate": backtest_result.win_rate,
                        "avg_win": backtest_result.avg_win,
                        "avg_loss": backtest_result.avg_loss,
                        "expected_value": backtest_result.expected_value,
                        "profit_factor": backtest_result.profit_factor,
                        "max_drawdown": backtest_result.max_drawdown,
                        "reject_rate": backtest_result.reject_rate,
                        "missing_rate": backtest_result.missing_rate,
                        "exposure_rate": backtest_result.exposure_rate,
                        "opportunity_count": backtest_result.opportunity_count,
                        "filled_count": backtest_result.filled_count,
                        "skip_cash_count": backtest_result.skip_cash_count,
                        "skip_maxpos_count": backtest_result.skip_maxpos_count,
                        "participation_rate": backtest_result.participation_rate,
                        "environment_breakdown": backtest_result.environment_breakdown,
                    }
                    trade_days = backtest_result.trade_days
                else:
                    metrics = generate_backtest_report(
                        snap_store,
                        cfg,
                        window.start,
                        window.end,
                        starting_cash,
                    )
                    trade_days = len(_iter_trade_days(snap_store, window.start, window.end))

                results.append(
                    _build_window_result_payload(
                        scenario=scenario,
                        window=window,
                        metrics=metrics,
                        trade_days=trade_days,
                        store=snap_store,
                        initial_cash=starting_cash,
                        run_id=run.run_id,
                        duration_filter_metrics=filter_window_metrics.get(window.label),
                    )
                )
        finally:
            snap_store.close()

        if signal_filter is not None:
            candidate_filter_payload = {
                "metrics": dict(signal_filter.build_metrics()),
                "daily_rows": list(signal_filter.daily_rows),
                "blocked_rows": list(signal_filter.blocked_rows),
                "window_metrics": filter_window_metrics,
            }

    if candidate_filter_payload is None:
        raise RuntimeError("Phase 9B candidate filter payload is missing.")

    baseline_snapshot = scenario_snapshots[PHASE9B_BASELINE_CONTROL]
    blocked_signal_truth = build_blocked_signal_truth(
        blocked_rows=list(candidate_filter_payload["blocked_rows"]),
        baseline_signals=baseline_snapshot["signals"],
        baseline_orders=baseline_snapshot["orders"],
    )

    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "phase9_gene_mainline_integration_package",
        "research_question": (
            "If duration_percentile alone is connected into the validated baseline as a negative filter, "
            "does it improve the current mainline enough to justify formal promotion?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "validation_rule": {
            "runtime_field": "current_wave_duration_percentile",
            "promoted_metric": "duration_percentile",
            "role": "negative_filter_only",
            "operator": ">=",
            "threshold": float(threshold),
            "rule": f"block when current_wave_duration_percentile >= {threshold:g}",
            "rule_source": "G2 duration percentile location semantics",
            "forbidden_companions": [
                "current_wave_age_band",
                "wave_role",
                "reversal_state",
                "context_trend_direction_before",
                "mirror",
                "conditioning",
                "gene_score",
                "gene_sizing_overlay",
                "gene_exit_modulation",
            ],
        },
        "windows": [
            {
                "label": window.label,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
            }
            for window in windows
        ],
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "candidate_filter": candidate_filter_payload,
        "blocked_signal_truth": blocked_signal_truth,
        "results": results,
    }
    payload["digest"] = build_phase9_duration_validation_digest(payload)
    return payload


def read_phase9_duration_validation_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_phase9_duration_validation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
