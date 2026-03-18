from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.phase9_duration_percentile_validation import (
    PHASE9B_BASELINE_CONTROL,
    Phase9ValidationWindow,
    _buy_order_diagnostics,
    _buy_trade_metrics,
    _failure_reason_breakdown,
    _find_result,
    _hash_buy_trade_set,
    _iter_trade_days,
    _load_buy_trades,
    _load_orders,
    _load_trace_counts,
    _normalize_runtime_for_phase9,
    _safe_ratio,
    _snapshot_signal_counts,
    build_phase9_validation_windows,
)
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import generate_backtest_report
from src.run_metadata import finish_run, start_run

PHASE9_REVERSAL_VALIDATION_SCOPE = "phase9b_reversal_state_validation"
PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP = "PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP"
GENE_REVERSAL_PREP_EXIT_REASON = "GENE_REVERSAL_PREP"


@dataclass(frozen=True)
class Phase9ReversalScenario:
    label: str
    rule_role: str
    target_reversal_state: str | None
    exit_reason_code: str | None
    pipeline_mode: str
    position_sizing_mode: str
    exit_control_mode: str
    notes: str


def build_phase9_reversal_candidate_label(target_state: str) -> str:
    return f"PHASE9B_REVERSAL_{str(target_state).strip().upper()}_EXIT_PREP"


def build_phase9_reversal_scenarios(config: Settings, *, target_state: str) -> list[Phase9ReversalScenario]:
    _ = config
    state_token = str(target_state).strip().upper()
    return [
        Phase9ReversalScenario(
            label=PHASE9B_BASELINE_CONTROL,
            rule_role="none",
            target_reversal_state=None,
            exit_reason_code=None,
            pipeline_mode="legacy",
            position_sizing_mode="fixed_notional",
            exit_control_mode="full_exit_control",
            notes=(
                "Validated baseline only: legacy BOF entry, FIXED_NOTIONAL_CONTROL, FULL_EXIT_CONTROL, "
                "Gene sidecar only."
            ),
        ),
        Phase9ReversalScenario(
            label=build_phase9_reversal_candidate_label(state_token),
            rule_role="reversal_state_exit_preparation",
            target_reversal_state=state_token,
            exit_reason_code=GENE_REVERSAL_PREP_EXIT_REASON,
            pipeline_mode="legacy",
            position_sizing_mode="fixed_notional",
            exit_control_mode="full_exit_control",
            notes=(
                "Single-variable candidate only: keep the validated baseline fixed and schedule a defensive "
                f"T+1 SELL when reversal_state == {state_token}."
            ),
        ),
    ]


def _scenario_scope(scenario_label: str, window_label: str) -> str:
    return f"{PHASE9_REVERSAL_VALIDATION_SCOPE}_{scenario_label.strip().lower()}_{window_label.strip().lower()}"


def _load_reversal_context_batch(store: Store, signal_date: date, codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame(columns=["code", "reversal_state", "latest_confirmed_turn_type"])
    placeholders = ", ".join(["?"] * len(codes))
    params: tuple[object, ...] = tuple(codes) + (signal_date,)
    return store.read_df(
        f"""
        SELECT code, reversal_state, latest_confirmed_turn_type
        FROM l3_stock_gene
        WHERE code IN ({placeholders}) AND calc_date = ?
        """,
        params,
    )


class ReversalStateExitHook:
    def __init__(self, *, target_state: str, exit_reason_code: str) -> None:
        self.target_state = str(target_state).strip().upper()
        self.exit_reason_code = str(exit_reason_code).strip().upper()
        self.total_position_day_count = 0
        self.matched_state_position_day_count = 0
        self.created_exit_order_count = 0
        self.pending_sell_skip_count = 0
        self.missing_state_position_day_count = 0
        self.no_execute_date_skip_count = 0
        self.created_rows: list[dict[str, object]] = []
        self.daily_rows: list[dict[str, object]] = []

    def __call__(self, trade_day: date, filled_trades, broker, store: Store):  # noqa: ARG002
        positions = list(getattr(broker, "portfolio", {}).values())
        if not positions:
            self.daily_rows.append(
                {
                    "signal_date": trade_day.isoformat(),
                    "position_day_count": 0,
                    "matched_state_position_day_count": 0,
                    "created_exit_order_count": 0,
                    "pending_sell_skip_count": 0,
                    "missing_state_position_day_count": 0,
                    "no_execute_date_skip_count": 0,
                }
            )
            return []

        codes = sorted({str(position.code) for position in positions})
        context = _load_reversal_context_batch(store, trade_day, codes)
        context_by_code = {str(row["code"]): row for row in context.to_dict(orient="records")}

        daily_total = 0
        daily_matched = 0
        daily_created = 0
        daily_pending_skip = 0
        daily_missing = 0
        daily_no_execute = 0
        created_orders = []

        for position in positions:
            daily_total += 1
            row = context_by_code.get(str(position.code), {})
            reversal_state = str(row.get("reversal_state") or "").strip().upper()
            if not reversal_state:
                daily_missing += 1
                continue
            if reversal_state != self.target_state:
                continue
            daily_matched += 1
            status, order = broker.schedule_custom_exit_order(
                str(position.code),
                trade_day,
                self.exit_reason_code,
                event_stage="GENE_REVERSAL_EXIT_PREP_CREATED",
            )
            if status == "created" and order is not None:
                daily_created += 1
                created_orders.append(order)
                self.created_rows.append(
                    {
                        "signal_date": trade_day.isoformat(),
                        "code": str(position.code),
                        "position_id": getattr(position, "position_id", None),
                        "reversal_state": reversal_state,
                        "latest_confirmed_turn_type": str(row.get("latest_confirmed_turn_type") or ""),
                        "exit_reason_code": self.exit_reason_code,
                        "order_id": str(order.order_id),
                    }
                )
            elif status == "pending_sell_exists":
                daily_pending_skip += 1
            elif status == "no_execute_date":
                daily_no_execute += 1

        self.total_position_day_count += daily_total
        self.matched_state_position_day_count += daily_matched
        self.created_exit_order_count += daily_created
        self.pending_sell_skip_count += daily_pending_skip
        self.missing_state_position_day_count += daily_missing
        self.no_execute_date_skip_count += daily_no_execute
        self.daily_rows.append(
            {
                "signal_date": trade_day.isoformat(),
                "position_day_count": int(daily_total),
                "matched_state_position_day_count": int(daily_matched),
                "created_exit_order_count": int(daily_created),
                "pending_sell_skip_count": int(daily_pending_skip),
                "missing_state_position_day_count": int(daily_missing),
                "no_execute_date_skip_count": int(daily_no_execute),
            }
        )
        return created_orders

    def build_metrics(self) -> dict[str, object]:
        return {
            "reversal_exit_total_position_day_count": int(self.total_position_day_count),
            "reversal_exit_matched_state_position_day_count": int(self.matched_state_position_day_count),
            "reversal_exit_created_count": int(self.created_exit_order_count),
            "reversal_exit_created_share_of_positions": float(
                _safe_ratio(self.created_exit_order_count, self.total_position_day_count) or 0.0
            ),
            "reversal_exit_pending_sell_skip_count": int(self.pending_sell_skip_count),
            "reversal_exit_missing_state_position_day_count": int(self.missing_state_position_day_count),
            "reversal_exit_no_execute_date_skip_count": int(self.no_execute_date_skip_count),
            "reversal_exit_target_state": self.target_state,
            "reversal_exit_reason_code": self.exit_reason_code,
            "reversal_exit_rule": f"schedule T+1 SELL when reversal_state == {self.target_state}",
        }


def _filter_window_metrics(
    exit_hook: ReversalStateExitHook | None,
    windows: list[Phase9ValidationWindow],
) -> dict[str, dict[str, object]]:
    if exit_hook is None or not exit_hook.daily_rows:
        return {}
    daily = pd.DataFrame(exit_hook.daily_rows)
    if daily.empty:
        return {}
    daily["signal_date"] = pd.to_datetime(daily["signal_date"]).dt.date
    out: dict[str, dict[str, object]] = {}
    for window in windows:
        part = daily[(daily["signal_date"] >= window.start) & (daily["signal_date"] <= window.end)].copy()
        total_position_day_count = int(part["position_day_count"].sum()) if not part.empty else 0
        matched_state_position_day_count = int(part["matched_state_position_day_count"].sum()) if not part.empty else 0
        created_exit_order_count = int(part["created_exit_order_count"].sum()) if not part.empty else 0
        pending_sell_skip_count = int(part["pending_sell_skip_count"].sum()) if not part.empty else 0
        missing_state_position_day_count = int(part["missing_state_position_day_count"].sum()) if not part.empty else 0
        no_execute_date_skip_count = int(part["no_execute_date_skip_count"].sum()) if not part.empty else 0
        out[window.label] = {
            "reversal_exit_total_position_day_count": total_position_day_count,
            "reversal_exit_matched_state_position_day_count": matched_state_position_day_count,
            "reversal_exit_created_count": created_exit_order_count,
            "reversal_exit_created_share_of_positions": float(
                _safe_ratio(created_exit_order_count, total_position_day_count) or 0.0
            ),
            "reversal_exit_pending_sell_skip_count": pending_sell_skip_count,
            "reversal_exit_missing_state_position_day_count": missing_state_position_day_count,
            "reversal_exit_no_execute_date_skip_count": no_execute_date_skip_count,
            "reversal_exit_target_state": exit_hook.target_state,
            "reversal_exit_reason_code": exit_hook.exit_reason_code,
            "reversal_exit_rule": f"schedule T+1 SELL when reversal_state == {exit_hook.target_state}",
        }
    return out


def _load_reversal_exit_orders(store: Store, start: date, end: date, exit_reason_code: str) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT order_id, signal_id, code, execute_date, status, reject_reason, position_id, exit_reason_code
        FROM l4_orders
        WHERE action = 'SELL'
          AND execute_date BETWEEN ? AND ?
          AND exit_reason_code = ?
        ORDER BY execute_date ASC, order_id ASC
        """,
        (start, end, exit_reason_code),
    )


def _load_reversal_exit_trades(store: Store, start: date, end: date, exit_reason_code: str) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT trade_id, order_id, code, execute_date, quantity, price, fee, position_id, exit_reason_code, is_partial_exit
        FROM l4_trades
        WHERE action = 'SELL'
          AND execute_date BETWEEN ? AND ?
          AND exit_reason_code = ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end, exit_reason_code),
    )


def _reversal_exit_runtime_metrics(orders: pd.DataFrame, trades: pd.DataFrame) -> dict[str, object]:
    return {
        "reversal_exit_order_count": int(len(orders)),
        "reversal_exit_filled_count": int((orders["status"] == "FILLED").sum()) if not orders.empty else 0,
        "reversal_exit_reject_count": int((orders["status"] == "REJECTED").sum()) if not orders.empty else 0,
        "reversal_exit_expire_count": int((orders["status"] == "EXPIRED").sum()) if not orders.empty else 0,
        "reversal_exit_trade_count": int(len(trades)),
        "reversal_exit_partial_trade_count": int(trades["is_partial_exit"].fillna(False).sum()) if not trades.empty else 0,
        "reversal_exit_unique_code_count": int(orders["code"].nunique()) if not orders.empty else 0,
    }


def _build_window_result_payload(
    *,
    scenario: Phase9ReversalScenario,
    window: Phase9ValidationWindow,
    metrics: dict[str, object],
    trade_days: int,
    store: Store,
    initial_cash: float,
    run_id: str,
    reversal_exit_metrics: dict[str, object] | None = None,
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
        "rule_role": scenario.rule_role,
        "target_reversal_state": scenario.target_reversal_state,
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
        "reversal_exit_metrics": None if reversal_exit_metrics is None else dict(reversal_exit_metrics),
        **_snapshot_signal_counts(store, window.start, window.end),
        **_buy_order_diagnostics(orders),
        **_buy_trade_metrics(buys, initial_cash),
    }


def build_phase9_reversal_state_validation_digest(payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "defer_with_smaller_follow_up",
            "conclusion": "Phase 9B reversal_state validation is incomplete; no truthful runtime ruling is allowed.",
        }

    results = payload.get("results")
    candidate_exit_rule = payload.get("candidate_exit_rule")
    if not isinstance(results, list):
        raise ValueError("payload.results must be a list")
    if not isinstance(candidate_exit_rule, dict):
        raise ValueError("payload.candidate_exit_rule must be a dict")

    candidate_label = next(
        (str(item.get("scenario_label") or "") for item in results if str(item.get("scenario_label") or "") != PHASE9B_BASELINE_CONTROL),
        "",
    )
    if not candidate_label:
        raise ValueError("Missing non-baseline candidate scenario in payload.results")

    baseline = _find_result(results, scenario_label=PHASE9B_BASELINE_CONTROL, window_label="full_window")
    candidate = _find_result(results, scenario_label=candidate_label, window_label="full_window")
    front_candidate = _find_result(results, scenario_label=candidate_label, window_label="front_half_window")
    back_candidate = _find_result(results, scenario_label=candidate_label, window_label="back_half_window")

    rule_metrics = candidate_exit_rule.get("metrics")
    if not isinstance(rule_metrics, dict):
        raise ValueError("payload.candidate_exit_rule.metrics must be a dict")
    candidate_reversal_metrics = candidate.get("reversal_exit_metrics")
    if not isinstance(candidate_reversal_metrics, dict):
        candidate_reversal_metrics = {}

    expected_value_delta = float(candidate.get("expected_value") or 0.0) - float(baseline.get("expected_value") or 0.0)
    profit_factor_delta = float(candidate.get("profit_factor") or 0.0) - float(baseline.get("profit_factor") or 0.0)
    max_drawdown_delta = float(candidate.get("max_drawdown") or 0.0) - float(baseline.get("max_drawdown") or 0.0)
    trade_count_delta = int(candidate.get("trade_count") or 0) - int(baseline.get("trade_count") or 0)
    buy_filled_delta = int(candidate.get("buy_filled_count") or 0) - int(baseline.get("buy_filled_count") or 0)
    signal_count_delta = int(candidate.get("signals_count") or 0) - int(baseline.get("signals_count") or 0)

    created_count = int(rule_metrics.get("reversal_exit_created_count", 0) or 0)
    matched_state_count = int(rule_metrics.get("reversal_exit_matched_state_position_day_count", 0) or 0)
    filled_exit_count = int(candidate_reversal_metrics.get("reversal_exit_filled_count", 0) or 0)
    trade_exit_count = int(candidate_reversal_metrics.get("reversal_exit_trade_count", 0) or 0)

    trace_complete = all(
        int(entry.get("trace_counts", {}).get("pas_trigger_trace_count", 0)) > 0
        and int(entry.get("trace_counts", {}).get("broker_lifecycle_trace_count", 0)) > 0
        for entry in (baseline, candidate, front_candidate, back_candidate)
    )
    window_slice_complete = all(int(entry.get("trade_days") or 0) > 0 for entry in (front_candidate, back_candidate))
    candidate_improves = expected_value_delta > 0.0 and profit_factor_delta > 0.0 and max_drawdown_delta <= 0.0
    candidate_mixed = expected_value_delta > 0.0 and (profit_factor_delta <= 0.0 or max_drawdown_delta > 0.0)

    if not trace_complete or not window_slice_complete:
        decision = "defer_with_smaller_follow_up"
        diagnosis = "validation_trace_gap"
        conclusion = "Phase 9B reversal_state validation produced replay output, but the trace is not complete enough yet."
    elif created_count <= 0 or filled_exit_count <= 0 or trade_exit_count <= 0:
        decision = "retain_sidecar_only"
        diagnosis = "rule_did_not_truthfully_touch_runtime_exits"
        conclusion = "The isolated reversal_state rule did not produce enough real defensive exits; retain reversal_state as sidecar only."
    elif candidate_improves:
        decision = "promote_reversal_state_exit_preparation"
        diagnosis = "isolated_exit_preparation_improves_baseline"
        conclusion = "The isolated reversal_state exit-preparation rule improved the validated baseline cleanly enough to earn promotion."
    elif candidate_mixed:
        decision = "defer_with_smaller_follow_up"
        diagnosis = "mixed_tradeoff_needs_smaller_follow_up"
        conclusion = "The isolated reversal_state rule changes runtime behavior, but the trade-off is mixed and needs a smaller follow-up."
    else:
        decision = "retain_sidecar_only"
        diagnosis = "isolated_rule_not_better_than_baseline"
        conclusion = "The isolated reversal_state exit-preparation rule failed to beat the validated baseline cleanly; retain reversal_state as sidecar only."

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
            "matched_state_position_day_count": matched_state_count,
            "created_exit_order_count": created_count,
            "filled_exit_order_count": filled_exit_count,
            "filled_exit_trade_count": trade_exit_count,
            "target_reversal_state": str(rule_metrics.get("reversal_exit_target_state") or ""),
            "exit_reason_code": str(rule_metrics.get("reversal_exit_reason_code") or ""),
            "rule": str(rule_metrics.get("reversal_exit_rule") or ""),
        },
        "candidate_window_summary": {
            "front_half_trade_count": front_candidate.get("trade_count"),
            "front_half_expected_value": front_candidate.get("expected_value"),
            "back_half_trade_count": back_candidate.get("trade_count"),
            "back_half_expected_value": back_candidate.get("expected_value"),
        },
        "conclusion": conclusion,
    }


def run_phase9_reversal_state_validation(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    target_state: str = "CONFIRMED_TURN_DOWN",
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, object]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    target_state_token = str(target_state).strip().upper()
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

    results: list[dict[str, object]] = []
    candidate_exit_rule_payload: dict[str, object] | None = None
    for scenario in build_phase9_reversal_scenarios(config, target_state=target_state_token):
        cfg = _normalize_runtime_for_phase9(config, initial_cash=starting_cash)
        exit_hook = None if scenario.rule_role == "none" else ReversalStateExitHook(
            target_state=str(scenario.target_reversal_state or target_state_token),
            exit_reason_code=str(scenario.exit_reason_code or GENE_REVERSAL_PREP_EXIT_REASON),
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
                exit_hook=exit_hook,
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

        window_exit_metrics = _filter_window_metrics(exit_hook, windows)
        snap_store = Store(db_file)
        try:
            for window in windows:
                metrics = (
                    {
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
                    if window.label == "full_window"
                    else generate_backtest_report(snap_store, cfg, window.start, window.end, starting_cash)
                )
                trade_days = backtest_result.trade_days if window.label == "full_window" else len(_iter_trade_days(snap_store, window.start, window.end))
                reversal_exit_metrics = None
                if scenario.exit_reason_code is not None:
                    reversal_exit_metrics = _reversal_exit_runtime_metrics(
                        _load_reversal_exit_orders(snap_store, window.start, window.end, scenario.exit_reason_code),
                        _load_reversal_exit_trades(snap_store, window.start, window.end, scenario.exit_reason_code),
                    )
                    if window.label in window_exit_metrics:
                        reversal_exit_metrics.update(window_exit_metrics[window.label])
                results.append(
                    _build_window_result_payload(
                        scenario=scenario,
                        window=window,
                        metrics=metrics,
                        trade_days=trade_days,
                        store=snap_store,
                        initial_cash=starting_cash,
                        run_id=run.run_id,
                        reversal_exit_metrics=reversal_exit_metrics,
                    )
                )
        finally:
            snap_store.close()
        if exit_hook is not None:
            candidate_exit_rule_payload = {
                "metrics": dict(exit_hook.build_metrics()),
                "daily_rows": list(exit_hook.daily_rows),
                "created_rows": list(exit_hook.created_rows),
                "window_metrics": window_exit_metrics,
            }

    if candidate_exit_rule_payload is None:
        raise RuntimeError("Phase 9B reversal_state candidate exit rule payload is missing.")
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "phase9_gene_mainline_integration_package",
        "research_question": "If reversal_state alone is connected into the validated baseline as an exit-preparation rule, does it improve the current mainline enough to justify formal promotion?",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "validation_rule": {
            "runtime_field": "reversal_state",
            "promoted_metric": "reversal_state",
            "role": "exit_preparation_only",
            "operator": "==",
            "target_state": target_state_token,
            "exit_reason_code": GENE_REVERSAL_PREP_EXIT_REASON,
            "rule": f"schedule T+1 SELL when reversal_state == {target_state_token}",
            "rule_source": "Gene reversal_state compression semantics",
            "forbidden_companions": ["duration_percentile", "wave_role", "current_wave_age_band", "context_trend_direction_before", "mirror", "conditioning", "gene_score", "gene_entry_filter", "gene_sizing_overlay"],
        },
        "windows": [{"label": window.label, "start": window.start.isoformat(), "end": window.end.isoformat()} for window in windows],
        "scenarios": [asdict(scenario) for scenario in build_phase9_reversal_scenarios(config, target_state=target_state_token)],
        "candidate_exit_rule": candidate_exit_rule_payload,
        "results": results,
    }
    payload["digest"] = build_phase9_reversal_state_validation_digest(payload)
    return payload


def write_phase9_reversal_state_validation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
