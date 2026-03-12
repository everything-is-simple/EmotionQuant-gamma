from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from src.backtest import normandy_volman_alpha as volman_helpers
from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import BacktestResult, _force_close_all, _iter_trade_days
from src.backtest.pas_ablation import (
    compute_diff_days,
    compute_trace_coverage,
    summarize_environment_bucket,
    summarize_introduced_rows,
    summarize_selected_pattern_distribution,
)
from src.broker.broker import Broker
from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import generate_backtest_report
from src.run_metadata import finish_run, start_run
from src.selector.selector import select_candidates
from src.strategy.pas_bof import BofDetector
from src.strategy.ranker import build_dtt_score_frame, finalize_dtt_rank_frame, materialize_ranked_signals
from src.strategy.strategy import _build_pas_trace_row, _enrich_selected_trace_payload


NORMANDY_BOF_QUALITY_DTT_VARIANT = "v0_01_dtt_pattern_only"
NORMANDY_BOF_QUALITY_MIN_TRADES = 20
NORMANDY_BOF_QUALITY_MIN_PARTICIPATION = 0.05
NORMANDY_BOF_QUALITY_MIN_IMPROVEMENT_DIMENSIONS = 2
NORMANDY_BOF_STABILITY_MAX_DOMINANT_BUCKET_SHARE = 0.85
NORMANDY_BOF_STABILITY_MAX_SELECTED_TO_FILL_RATIO = 4.0
NORMANDY_BOF_STABILITY_MIN_TRADE_SHARE_VS_CONTROL = 0.20


@dataclass(frozen=True)
class NormandyBofQualityScenario:
    label: str
    family: str
    signal_pattern: str
    control: bool
    requires_keylevel: bool
    requires_pinbar: bool
    notes: str


@dataclass
class NormandyBofQualityRunArtifacts:
    scenario: NormandyBofQualityScenario
    run_id: str
    trade_days: int
    trade_count: int
    win_rate: float | None
    avg_win: float | None
    avg_loss: float | None
    expected_value: float | None
    profit_factor: float | None
    max_drawdown: float | None
    reject_rate: float | None
    missing_rate: float | None
    exposure_rate: float | None
    opportunity_count: float | None
    filled_count: float | None
    skip_cash_count: float | None
    skip_maxpos_count: float | None
    participation_rate: float | None
    signals_count: int
    ranked_signals_count: int
    trades_count: int
    environment_breakdown: dict[str, dict[str, float | None]]
    selected_rank_frame: pd.DataFrame
    buy_execution_frame: pd.DataFrame
    detected_trace_frame: pd.DataFrame
    selected_trace_frame: pd.DataFrame


def build_normandy_bof_quality_scenarios(_config: Settings | None = None) -> list[NormandyBofQualityScenario]:
    return [
        NormandyBofQualityScenario(
            label="BOF_CONTROL",
            family="BOF_CONTROL",
            signal_pattern="bof",
            control=True,
            requires_keylevel=False,
            requires_pinbar=False,
            notes="Current validated BOF baseline; fixed control for Normandy BOF quality route.",
        ),
        NormandyBofQualityScenario(
            label="BOF_KEYLEVEL_STRICT",
            family="BOF_QUALITY",
            signal_pattern="bof",
            control=False,
            requires_keylevel=True,
            requires_pinbar=False,
            notes="Retain only BOF samples with stronger reclaim / invalidation clarity at the key level.",
        ),
        NormandyBofQualityScenario(
            label="BOF_PINBAR_EXPRESSION",
            family="BOF_QUALITY",
            signal_pattern="bof",
            control=False,
            requires_keylevel=False,
            requires_pinbar=True,
            notes="Retain only BOF samples with stronger rejection-bar / pinbar expression.",
        ),
        NormandyBofQualityScenario(
            label="BOF_KEYLEVEL_PINBAR",
            family="BOF_QUALITY",
            signal_pattern="bof",
            control=False,
            requires_keylevel=True,
            requires_pinbar=True,
            notes="Intersection branch: strong key level reclaim plus strong pinbar expression.",
        ),
    ]


def resolve_normandy_bof_quality_scenarios(
    config: Settings | None = None,
    scenario_labels: list[str] | None = None,
) -> list[NormandyBofQualityScenario]:
    scenarios = build_normandy_bof_quality_scenarios(config)
    if not scenario_labels:
        return scenarios

    requested = {str(label).strip().upper() for label in scenario_labels if str(label).strip()}
    if not requested:
        return scenarios
    requested.add("BOF_CONTROL")

    known = {scenario.label for scenario in scenarios}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(f"Unknown Normandy BOF quality scenarios: {', '.join(unknown)}")

    return [scenario for scenario in scenarios if scenario.label in requested]


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


def _float_or_zero(value: object) -> float:
    cast = _finite_or_none(value)
    return 0.0 if cast is None else float(cast)


def _bool_from_payload(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) <= 1e-9:
        return 0.0
    return float(numerator / denominator)


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_normandy_bof_branch_context(payload: dict[str, object]) -> dict[str, object]:
    lower_bound = _float_or_zero(payload.get("lower_bound"))
    today_low = _float_or_zero(payload.get("today_low"))
    today_open = _float_or_zero(payload.get("today_open"))
    today_close = _float_or_zero(payload.get("today_close"))
    today_high = _float_or_zero(payload.get("today_high"))
    risk_reward_ref = _float_or_zero(payload.get("risk_reward_ref"))
    entry_ref = _float_or_zero(payload.get("entry_ref"))
    stop_ref = _float_or_zero(payload.get("stop_ref"))
    pattern_quality_score = _float_or_zero(payload.get("pattern_quality_score"))
    close_pos = _float_or_zero(payload.get("close_pos"))
    body_ratio = _float_or_zero(payload.get("body_ratio"))

    candle_range = max(today_high - today_low, 0.0)
    lower_shadow = max(min(today_open, today_close) - today_low, 0.0)
    upper_shadow = max(today_high - max(today_open, today_close), 0.0)
    lower_shadow_ratio = _safe_ratio(lower_shadow, candle_range)
    upper_shadow_ratio = _safe_ratio(upper_shadow, candle_range)
    false_break_depth_pct = _safe_ratio(max(lower_bound - today_low, 0.0), lower_bound)
    reclaim_pct = _safe_ratio(max(today_close - lower_bound, 0.0), lower_bound)
    reclaim_efficiency = _safe_ratio(max(today_close - lower_bound, 0.0), max(lower_bound - today_low, 1e-9))
    stop_distance_pct = _safe_ratio(max(entry_ref - stop_ref, 0.0), max(entry_ref, 1e-9))

    keylevel_proxy_score = 100.0 * (
        0.25 * _clip(reclaim_pct / 0.015)
        + 0.25 * _clip(reclaim_efficiency / 0.60)
        + 0.20 * _clip(risk_reward_ref / 1.80)
        + 0.15 * _clip(1.0 - stop_distance_pct / 0.06)
        + 0.15 * _clip(pattern_quality_score / 100.0)
    )
    pinbar_proxy_score = 100.0 * (
        0.40 * _clip(lower_shadow_ratio / 0.55)
        + 0.25 * _clip(close_pos / 0.80)
        + 0.20 * _clip(1.0 - upper_shadow_ratio / 0.30)
        + 0.15 * _clip(1.0 - body_ratio / 0.45)
    )

    keylevel_strict = (
        str(payload.get("reference_status") or "") == "OK"
        and str(payload.get("quality_status") or "") == "OK"
        and str(payload.get("failure_handling_tag") or "") == "BOF_NO_FOLLOW_THROUGH"
        and keylevel_proxy_score >= 65.0
        and reclaim_pct >= 0.008
        and risk_reward_ref >= 1.5
        and stop_distance_pct <= 0.06
    )
    pinbar_expression = (
        pinbar_proxy_score >= 68.0
        and lower_shadow_ratio >= 0.40
        and close_pos >= 0.70
        and upper_shadow_ratio <= 0.25
        and body_ratio <= 0.40
    )

    return {
        "base_bof_triggered": _bool_from_payload(payload.get("triggered")),
        "bof_false_break_depth_pct": round(false_break_depth_pct, 6),
        "bof_reclaim_pct": round(reclaim_pct, 6),
        "bof_reclaim_efficiency": round(reclaim_efficiency, 6),
        "bof_stop_distance_pct": round(stop_distance_pct, 6),
        "bof_lower_shadow_ratio": round(lower_shadow_ratio, 6),
        "bof_upper_shadow_ratio": round(upper_shadow_ratio, 6),
        "bof_keylevel_proxy_score": round(keylevel_proxy_score, 6),
        "bof_pinbar_proxy_score": round(pinbar_proxy_score, 6),
        "bof_keylevel_strict": bool(keylevel_strict),
        "bof_pinbar_expression": bool(pinbar_expression),
        "bof_keylevel_pinbar": bool(keylevel_strict and pinbar_expression),
    }


def _evaluate_normandy_bof_branch(
    payload: dict[str, object],
    scenario: NormandyBofQualityScenario,
) -> tuple[bool, str | None]:
    if not _bool_from_payload(payload.get("triggered")):
        return False, None
    if scenario.control:
        return True, None

    keylevel_ok = _bool_from_payload(payload.get("bof_keylevel_strict"))
    pinbar_ok = _bool_from_payload(payload.get("bof_pinbar_expression"))

    if scenario.requires_keylevel and scenario.requires_pinbar:
        if keylevel_ok and pinbar_ok:
            return True, None
        if not keylevel_ok and not pinbar_ok:
            return False, "KEYLEVEL_AND_PINBAR_PROXY_REJECTED"
        return False, "KEYLEVEL_PROXY_REJECTED" if not keylevel_ok else "PINBAR_PROXY_REJECTED"
    if scenario.requires_keylevel:
        return (True, None) if keylevel_ok else (False, "KEYLEVEL_PROXY_REJECTED")
    if scenario.requires_pinbar:
        return (True, None) if pinbar_ok else (False, "PINBAR_PROXY_REJECTED")
    return True, None


def _build_execution_mode(
    config: Settings,
    *,
    dtt_variant: str,
    dtt_top_n: int | None,
    max_positions: int | None,
) -> dict[str, object]:
    return {
        "pipeline_mode": "dtt",
        "enable_mss_gate": False,
        "enable_irs_filter": False,
        "dtt_variant": dtt_variant,
        "dtt_top_n": int(dtt_top_n if dtt_top_n is not None else config.dtt_top_n),
        "max_positions": int(max_positions if max_positions is not None else config.max_positions),
        "pas_quality_enabled": True,
        "pas_reference_enabled": True,
        "control_label": "BOF_CONTROL",
    }


def _read_selected_trace_frame(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            signal_date,
            code,
            detector AS pattern,
            signal_id,
            pattern_quality_score,
            entry_ref,
            stop_ref,
            target_ref,
            risk_reward_ref,
            failure_handling_tag,
            quality_status,
            reference_status,
            trace_payload_json,
            pattern_context_json
        FROM pas_trigger_trace_exp
        WHERE run_id = ?
          AND detected = TRUE
          AND selected_pattern = detector
        ORDER BY signal_date ASC, code ASC, detector ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(volman_helpers._to_iso)
    return frame


def _generate_normandy_bof_quality_signals(
    store: Store,
    candidates: list[StockCandidate],
    asof_date: date,
    scenario: NormandyBofQualityScenario,
    config: Settings,
    run_id: str | None = None,
) -> list[Signal]:
    if not candidates:
        return []

    detector = BofDetector(config)
    history_days_required = max(int(getattr(detector, "required_window", config.pas_lookback_days)), 1)
    histories = volman_helpers._load_candidate_histories_batch(
        store,
        [candidate.code for candidate in candidates],
        asof_date,
        max(config.pas_lookback_days, history_days_required),
    )
    history_by_code = {
        str(code): frame.reset_index(drop=True)
        for code, frame in histories.groupby("code", sort=False)
    }

    raw_signals: list[Signal] = []
    trace_rows: list[dict[str, object]] = []
    run_token = (run_id or "").strip()
    for index, candidate in enumerate(candidates, start=1):
        history = history_by_code.get(candidate.code)
        if history is None:
            history = pd.DataFrame(columns=volman_helpers.NORMANDY_VOLMAN_HISTORY_COLUMNS)

        signal, trace_payload = detector.evaluate(candidate.code, asof_date, history)
        payload = _enrich_selected_trace_payload(dict(trace_payload), config, scenario.label)
        payload.update(compute_normandy_bof_branch_context(payload))
        payload["base_bof_signal_pattern"] = "bof"

        branch_passed, branch_reject_reason = _evaluate_normandy_bof_branch(payload, scenario)
        payload["branch_filter_passed"] = branch_passed
        payload["branch_filter_reason"] = branch_reject_reason
        payload["normandy_bof_branch_label"] = scenario.label
        payload["pattern"] = scenario.signal_pattern
        payload["pattern_group"] = scenario.family
        payload["registry_run_label"] = scenario.label

        scenario_signal: Signal | None = signal
        if scenario_signal is not None and branch_passed and scenario.signal_pattern != "bof":
            scenario_signal = scenario_signal.model_copy(
                update={
                    "signal_id": scenario_signal.signal_id.replace(scenario_signal.pattern, scenario.signal_pattern),
                    "pattern": scenario.signal_pattern,
                    "reason_code": f"PAS_{scenario.signal_pattern.upper()}",
                }
            )

        if scenario_signal is None or not branch_passed:
            payload["triggered"] = False
            payload["selected_pattern"] = None
            if branch_reject_reason is not None:
                payload["skip_reason"] = branch_reject_reason
                payload["detect_reason"] = branch_reject_reason
        else:
            payload["triggered"] = True
            payload["selected_pattern"] = scenario.signal_pattern
            payload["signal_id"] = scenario_signal.signal_id
            payload["reason_code"] = scenario_signal.reason_code

        trace_rows.append(
            _build_pas_trace_row(
                run_id=run_token,
                asof_date=asof_date,
                code=candidate.code,
                detector_name=scenario.signal_pattern,
                candidate_rank=int(candidate.candidate_rank or index),
                active_detector_count=1,
                combination_mode="ANY",
                min_history_days=history_days_required,
                history_days=int(len(history)),
                trace_payload=payload,
            )
        )

        if scenario_signal is not None and branch_passed:
            raw_signals.append(scenario_signal)

    if run_token and trace_rows:
        store.bulk_upsert("pas_trigger_trace_exp", pd.DataFrame(trace_rows))

    if not raw_signals:
        return []

    if not config.use_dtt_pipeline:
        store.bulk_upsert("l3_signals", pd.DataFrame([signal.to_formal_signal_row() for signal in raw_signals]))
        return raw_signals

    score_frame = build_dtt_score_frame(
        store=store,
        signals=raw_signals,
        candidates=candidates,
        asof_date=asof_date,
        run_id=run_token,
        config=config,
    )
    rank_frame = finalize_dtt_rank_frame(score_frame, config.dtt_top_n)
    if not rank_frame.empty:
        store.bulk_upsert("l3_signal_rank_exp", rank_frame)
    selected = materialize_ranked_signals(raw_signals, rank_frame)
    if selected:
        store.bulk_upsert("l3_signals", pd.DataFrame([signal.to_formal_signal_row() for signal in selected]))
    return selected


def _run_normandy_bof_quality_backtest(
    *,
    db_path: str | Path,
    config: Settings,
    scenario: NormandyBofQualityScenario,
    start: date,
    end: date,
    initial_cash: float | None,
    run_id: str,
) -> BacktestResult:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    store = Store(db_path)
    broker = Broker(store, config, initial_cash=starting_cash, run_id=run_id)

    try:
        trade_days = _iter_trade_days(store, start, end)
        if not trade_days:
            raise RuntimeError("No trade days available in l1_trade_calendar for given range.")

        for trade_day in trade_days:
            broker.execute_pending_orders(trade_day)
            broker.expire_orders(trade_day)
            broker.generate_exit_orders(trade_day)

            candidates = select_candidates(store, trade_day, config, run_id=run_id)
            signals = _generate_normandy_bof_quality_signals(
                store=store,
                candidates=candidates,
                asof_date=trade_day,
                scenario=scenario,
                config=config,
                run_id=run_id,
            )
            broker.process_signals(signals)

        _force_close_all(store, broker, trade_days[-1])
        metrics = generate_backtest_report(store, config, start, end, starting_cash)
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
        )
    finally:
        store.close()


def _build_scenario_config(
    base: Settings,
    *,
    dtt_variant: str,
    dtt_top_n: int | None,
    max_positions: int | None,
) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = dtt_variant
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.pas_quality_enabled = True
    cfg.pas_reference_enabled = True
    if dtt_top_n is not None:
        cfg.dtt_top_n = max(1, int(dtt_top_n))
    if max_positions is not None:
        cfg.max_positions = max(1, int(max_positions))
    return cfg


def _run_normandy_bof_quality_scenario(
    *,
    db_file: Path,
    base_config: Settings,
    scenario: NormandyBofQualityScenario,
    dtt_variant: str,
    start: date,
    end: date,
    initial_cash: float | None,
    artifact_root: Path,
    dtt_top_n: int | None,
    max_positions: int | None,
) -> NormandyBofQualityRunArtifacts:
    cfg = _build_scenario_config(
        base_config,
        dtt_variant=dtt_variant,
        dtt_top_n=dtt_top_n,
        max_positions=max_positions,
    )
    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="normandy_bof_quality",
        modules=["backtest", "selector", "strategy", "broker", "report"],
        config=cfg,
        runtime_env="script",
        artifact_root=str(artifact_root),
        start=start,
        end=end,
    )
    meta_store.close()

    clear_store = Store(db_file)
    try:
        clear_runtime_tables(clear_store, run_id=run.run_id)
    finally:
        clear_store.close()

    try:
        result = _run_normandy_bof_quality_backtest(
            db_path=db_file,
            config=cfg,
            scenario=scenario,
            start=start,
            end=end,
            initial_cash=initial_cash,
            run_id=run.run_id,
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

    snapshot_store = Store(db_file)
    try:
        signals_count, ranked_signals_count, trades_count = volman_helpers._snapshot_runtime_metrics(
            snapshot_store, start, end
        )
        selected_rank_frame = volman_helpers._read_selected_rank_frame(snapshot_store, run.run_id)
        buy_execution_frame = volman_helpers._read_buy_execution_frame(snapshot_store, start, end)
        detected_trace_frame = volman_helpers._read_detected_trace_frame(snapshot_store, run.run_id)
        selected_trace_frame = _read_selected_trace_frame(snapshot_store, run.run_id)
    finally:
        snapshot_store.close()

    return NormandyBofQualityRunArtifacts(
        scenario=scenario,
        run_id=run.run_id,
        trade_days=result.trade_days,
        trade_count=result.trade_count,
        win_rate=_finite_or_none(result.win_rate),
        avg_win=_finite_or_none(result.avg_win),
        avg_loss=_finite_or_none(result.avg_loss),
        expected_value=_finite_or_none(result.expected_value),
        profit_factor=_finite_or_none(result.profit_factor),
        max_drawdown=_finite_or_none(result.max_drawdown),
        reject_rate=_finite_or_none(result.reject_rate),
        missing_rate=_finite_or_none(result.missing_rate),
        exposure_rate=_finite_or_none(result.exposure_rate),
        opportunity_count=_finite_or_none(result.opportunity_count),
        filled_count=_finite_or_none(result.filled_count),
        skip_cash_count=_finite_or_none(result.skip_cash_count),
        skip_maxpos_count=_finite_or_none(result.skip_maxpos_count),
        participation_rate=_finite_or_none(result.participation_rate),
        signals_count=signals_count,
        ranked_signals_count=ranked_signals_count,
        trades_count=trades_count,
        environment_breakdown=volman_helpers._normalize_environment_breakdown(result.environment_breakdown),
        selected_rank_frame=selected_rank_frame,
        buy_execution_frame=buy_execution_frame,
        detected_trace_frame=detected_trace_frame,
        selected_trace_frame=selected_trace_frame,
    )


def _serialize_scenario_result(
    result: NormandyBofQualityRunArtifacts,
    *,
    bof_control: NormandyBofQualityRunArtifacts,
) -> dict[str, object]:
    overlap_rate = 1.0 if result.scenario.control else volman_helpers._compute_buy_overlap_rate(
        bof_control.buy_execution_frame,
        result.buy_execution_frame,
    )
    incremental_buy_trades = 0 if result.scenario.control else volman_helpers._count_incremental_buy_trades(
        bof_control.buy_execution_frame,
        result.buy_execution_frame,
    )
    return {
        "label": result.scenario.label,
        "family": result.scenario.family,
        "signal_pattern": result.scenario.signal_pattern,
        "control": result.scenario.control,
        "run_id": result.run_id,
        "trade_days": result.trade_days,
        "trade_count": result.trade_count,
        "win_rate": result.win_rate,
        "avg_win": result.avg_win,
        "avg_loss": result.avg_loss,
        "expected_value": result.expected_value,
        "profit_factor": result.profit_factor,
        "max_drawdown": result.max_drawdown,
        "reject_rate": result.reject_rate,
        "missing_rate": result.missing_rate,
        "exposure_rate": result.exposure_rate,
        "opportunity_count": result.opportunity_count,
        "filled_count": result.filled_count,
        "skip_cash_count": result.skip_cash_count,
        "skip_maxpos_count": result.skip_maxpos_count,
        "participation_rate": result.participation_rate,
        "signals_count": result.signals_count,
        "ranked_signals_count": result.ranked_signals_count,
        "trades_count": result.trades_count,
        "selected_pattern_distribution": summarize_selected_pattern_distribution(result.selected_trace_frame),
        "reference_trace_coverage": _finite_or_none(compute_trace_coverage(result.selected_trace_frame, "entry_ref")),
        "rank_diff_days_vs_bof_control": compute_diff_days(
            bof_control.selected_rank_frame,
            result.selected_rank_frame,
            date_col="signal_date",
            key_cols=("signal_id", "final_rank"),
        ),
        "execution_diff_days_vs_bof_control": compute_diff_days(
            bof_control.buy_execution_frame,
            result.buy_execution_frame,
            date_col="execute_date",
            key_cols=("signal_id", "quantity"),
        ),
        "introduced_selected_signals_vs_bof_control": summarize_introduced_rows(
            bof_control.selected_rank_frame,
            result.selected_rank_frame,
            date_col="signal_date",
            columns=("code", "signal_id", "final_rank"),
        ),
        "introduced_buy_trades_vs_bof_control": summarize_introduced_rows(
            bof_control.buy_execution_frame,
            result.buy_execution_frame,
            date_col="execute_date",
            columns=("code", "signal_id", "pattern", "quantity"),
        ),
        "overlap_rate_vs_bof_control": _finite_or_none(overlap_rate),
        "incremental_buy_trades_vs_bof_control": int(incremental_buy_trades),
        "best_environment_bucket": summarize_environment_bucket(result.environment_breakdown),
        "environment_breakdown": result.environment_breakdown,
    }


def run_normandy_bof_quality_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str = NORMANDY_BOF_QUALITY_DTT_VARIANT,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    dtt_top_n: int | None = None,
    max_positions: int | None = None,
    scenario_labels: list[str] | None = None,
) -> dict[str, object]:
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

    active_scenarios = resolve_normandy_bof_quality_scenarios(config, scenario_labels)
    runs = [
        _run_normandy_bof_quality_scenario(
            db_file=db_file,
            base_config=config,
            scenario=scenario,
            dtt_variant=dtt_variant,
            start=start,
            end=end,
            initial_cash=initial_cash,
            artifact_root=artifact_root_path,
            dtt_top_n=dtt_top_n,
            max_positions=max_positions,
        )
        for scenario in active_scenarios
    ]
    bof_control = next(result for result in runs if result.scenario.label == "BOF_CONTROL")
    serialized_results = [
        _serialize_scenario_result(result, bof_control=bof_control)
        for result in runs
    ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "BOF",
        "research_question": "Does the BOF family contain a stricter key-level / pinbar branch worth promoting under the same Broker semantics?",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "execution_mode": _build_execution_mode(
            config,
            dtt_variant=dtt_variant,
            dtt_top_n=dtt_top_n,
            max_positions=max_positions,
        ),
        "scenarios": [
            {
                "label": scenario.label,
                "family": scenario.family,
                "signal_pattern": scenario.signal_pattern,
                "control": scenario.control,
                "requires_keylevel": scenario.requires_keylevel,
                "requires_pinbar": scenario.requires_pinbar,
            }
            for scenario in active_scenarios
        ],
        "matrix_summary": volman_helpers._build_matrix_summary(serialized_results),
        "results": serialized_results,
    }


def _sample_density_ok(trade_count: int, participation_rate: float | None) -> bool:
    return trade_count >= NORMANDY_BOF_QUALITY_MIN_TRADES or (
        participation_rate is not None and participation_rate >= NORMANDY_BOF_QUALITY_MIN_PARTICIPATION
    )


def _sort_scorecard_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda item: (
            1 if bool(item.get("retained_branch_candidate")) else 0,
            int(item.get("improvement_count") or 0),
            -999.0 if item.get("expected_value") is None else float(item["expected_value"]),
            -999.0 if item.get("profit_factor") is None else float(item["profit_factor"]),
            -999.0 if item.get("max_drawdown") is None else -float(item["max_drawdown"]),
            -1.0 if item.get("participation_rate") is None else float(item["participation_rate"]),
            int(item.get("trade_count") or 0),
        ),
        reverse=True,
    )


def build_normandy_bof_quality_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
            "matrix_path": matrix_payload.get("matrix_path"),
            "start": matrix_payload.get("start"),
            "end": matrix_payload.get("end"),
            "dtt_variant": matrix_payload.get("dtt_variant"),
            "matrix_status": matrix_status,
            "control_label": "BOF_CONTROL",
            "retained_branch": None,
            "retained_branches": [],
            "family_verdict": "matrix_not_completed",
            "decision": "rerun_bof_quality_matrix",
            "scorecard": [],
            "conclusion": "BOF quality matrix 尚未完成，当前不能裁决 key-level / pinbar branches。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (item for item in results if isinstance(item, dict) and str(item.get("label") or "") == "BOF_CONTROL"),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include BOF_CONTROL baseline")

    control_ev = _finite_or_none(control.get("expected_value"))
    control_pf = _finite_or_none(control.get("profit_factor"))
    control_mdd = _finite_or_none(control.get("max_drawdown"))

    scorecard: list[dict[str, object]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "")
        trade_count = int(item.get("trade_count") or 0)
        ev = _finite_or_none(item.get("expected_value"))
        pf = _finite_or_none(item.get("profit_factor"))
        mdd = _finite_or_none(item.get("max_drawdown"))
        participation = _finite_or_none(item.get("participation_rate"))
        positive_edge_ok = ev is not None and ev > 0 and pf is not None and pf >= 1.0
        sample_density_ok = _sample_density_ok(trade_count, participation)
        ev_improves_control = ev is not None and control_ev is not None and ev >= control_ev
        pf_improves_control = pf is not None and control_pf is not None and pf >= control_pf
        mdd_improves_control = mdd is not None and control_mdd is not None and mdd <= control_mdd
        improvement_count = sum(
            1 for flag in (ev_improves_control, pf_improves_control, mdd_improves_control) if flag
        )
        retained_branch_candidate = (
            label != "BOF_CONTROL"
            and positive_edge_ok
            and sample_density_ok
            and improvement_count >= NORMANDY_BOF_QUALITY_MIN_IMPROVEMENT_DIMENSIONS
            and (ev_improves_control or pf_improves_control)
        )
        scorecard.append(
            {
                "label": label,
                "family": item.get("family"),
                "signal_pattern": item.get("signal_pattern"),
                "trade_count": trade_count,
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "overlap_rate_vs_bof_control": _finite_or_none(item.get("overlap_rate_vs_bof_control")),
                "incremental_buy_trades_vs_bof_control": int(item.get("incremental_buy_trades_vs_bof_control") or 0),
                "expected_value_delta_vs_bof_control": None if ev is None or control_ev is None else ev - control_ev,
                "profit_factor_delta_vs_bof_control": None if pf is None or control_pf is None else pf - control_pf,
                "max_drawdown_delta_vs_bof_control": None if mdd is None or control_mdd is None else mdd - control_mdd,
                "positive_edge_ok": positive_edge_ok,
                "sample_density_ok": sample_density_ok,
                "ev_improves_control": ev_improves_control,
                "pf_improves_control": pf_improves_control,
                "mdd_improves_control": mdd_improves_control,
                "improvement_count": improvement_count,
                "retained_branch_candidate": retained_branch_candidate,
                "best_environment_bucket": item.get("best_environment_bucket"),
            }
        )

    scorecard = _sort_scorecard_rows(scorecard)
    retained_rows = [row for row in scorecard if bool(row.get("retained_branch_candidate"))]
    retained_branch = retained_rows[0]["label"] if retained_rows else None

    if retained_branch is not None:
        conclusion = (
            f"{retained_branch} 当前在同一套 Broker 语义下同时满足正向 edge、样本密度和至少两项 control 改进；"
            "允许进入 N1.12 stability or no-go。"
        )
        family_verdict = "retained_branch_selected"
        decision = "advance_retained_branch_to_n1_12"
    else:
        conclusion = (
            "当前 BOF key-level / pinbar quality branches 还没有哪一支在同一套 Broker 下稳定优于 BOF_CONTROL；"
            "暂时保持 BOF_CONTROL 为唯一 baseline。"
        )
        family_verdict = "quality_family_no_better_branch"
        decision = "keep_bof_control_baseline_only"

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "start": matrix_payload.get("start"),
        "end": matrix_payload.get("end"),
        "dtt_variant": matrix_payload.get("dtt_variant"),
        "matrix_status": matrix_status,
        "control_label": "BOF_CONTROL",
        "candidate_rule": {
            "expected_value_must_be_positive": True,
            "profit_factor_floor": 1.0,
            "min_trade_count": NORMANDY_BOF_QUALITY_MIN_TRADES,
            "min_participation_rate": NORMANDY_BOF_QUALITY_MIN_PARTICIPATION,
            "min_improvement_dimensions": NORMANDY_BOF_QUALITY_MIN_IMPROVEMENT_DIMENSIONS,
        },
        "scorecard": scorecard,
        "retained_branch": retained_branch,
        "retained_branches": [str(row["label"]) for row in retained_rows],
        "family_verdict": family_verdict,
        "decision": decision,
        "conclusion": conclusion,
    }


def _normalize_scalar(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds") + "Z"
    if isinstance(value, date):
        return value.isoformat()
    return value


def _query_dicts(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    params: list[object] | tuple[object, ...],
) -> list[dict[str, object]]:
    cursor = connection.execute(query, params)
    columns = [str(item[0]) for item in (cursor.description or ())]
    rows: list[dict[str, object]] = []
    for values in cursor.fetchall():
        row = {columns[index]: _normalize_scalar(values[index]) for index in range(len(columns))}
        rows.append(row)
    return rows


def _normalize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        clean: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, float):
                clean[key] = float(value)
            elif isinstance(value, int):
                clean[key] = int(value)
            else:
                clean[key] = value
        normalized.append(clean)
    return normalized


def _resolve_retained_branch_label(digest_payload: dict[str, object]) -> str | None:
    label = str(digest_payload.get("retained_branch") or "").strip()
    return label or None


def _find_result(payload: dict[str, object], label: str) -> dict[str, object]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise KeyError(f"Payload missing results for {label}")
    for item in results:
        if isinstance(item, dict) and str(item.get("label") or "") == label:
            return item
    raise KeyError(f"Unable to find result for {label}")


def _maybe_open_snapshot_db(
    db_path: str | Path | None,
) -> tuple[duckdb.DuckDBPyConnection | None, Path | None]:
    if db_path is None:
        return None, None
    resolved = Path(db_path).expanduser().resolve()
    if not resolved.exists():
        return None, resolved
    return duckdb.connect(str(resolved), read_only=True), resolved


BOF_QUALITY_PAIRED_TRACE_CTE = """
WITH entries AS (
    SELECT
        signal_id,
        signal_date,
        code,
        CAST(pattern_strength AS DOUBLE) AS pattern_strength,
        CAST(pattern_quality_score AS DOUBLE) AS pattern_quality_score,
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY signal_date, signal_id) AS entry_seq
    FROM pas_trigger_trace_exp
    WHERE run_id = ?
      AND detected = TRUE
      AND selected_pattern = detector
),
buyfills AS (
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
exits AS (
    SELECT
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
        e.pattern_strength,
        e.pattern_quality_score,
        b.entry_date,
        b.entry_qty,
        b.entry_price,
        x.exit_date,
        x.exit_qty,
        x.exit_price,
        x.exit_stage,
        (x.exit_price - b.entry_price) / NULLIF(b.entry_price, 0) AS gross_return
    FROM entries e
    JOIN buyfills b
      ON e.signal_id = b.signal_id
     AND e.code = b.code
    JOIN exits x
      ON e.code = x.code
     AND e.entry_seq = x.exit_seq
     AND b.entry_qty = x.exit_qty
)
"""


PAIRING_DIAGNOSTICS_QUERY = (
    BOF_QUALITY_PAIRED_TRACE_CTE
    + """
SELECT
    (SELECT COUNT(*) FROM entries) AS selected_entry_count,
    (SELECT COUNT(*) FROM buyfills) AS buy_fill_count,
    (SELECT COUNT(*) FROM exits) AS exit_fill_count,
    COUNT(*) AS paired_trade_count
FROM paired
"""
)


SIGNAL_YEAR_SLICES_QUERY = (
    BOF_QUALITY_PAIRED_TRACE_CTE
    + """
SELECT
    CAST(EXTRACT(YEAR FROM signal_date) AS INTEGER) AS signal_year,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength,
    AVG(pattern_quality_score) AS avg_quality_score
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


QUARTER_ACTIVITY_QUERY = """
SELECT
    CONCAT(
        CAST(EXTRACT(YEAR FROM signal_date) AS INTEGER),
        '-Q',
        CAST(EXTRACT(QUARTER FROM signal_date) AS INTEGER)
    ) AS signal_quarter,
    COUNT(*) AS selected_count,
    AVG(CAST(pattern_strength AS DOUBLE)) AS avg_strength,
    AVG(CAST(pattern_quality_score AS DOUBLE)) AS avg_quality_score,
    AVG(CAST(risk_reward_ref AS DOUBLE)) AS avg_risk_reward_ref
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
GROUP BY 1
ORDER BY MIN(signal_date)
"""


SELECTED_TRACE_SUMMARY_QUERY = """
SELECT
    COUNT(*) AS selected_count,
    AVG(CAST(pattern_quality_score AS DOUBLE)) AS avg_pattern_quality_score,
    AVG(CAST(risk_reward_ref AS DOUBLE)) AS avg_risk_reward_ref,
    AVG(CAST(close_pos AS DOUBLE)) AS avg_close_pos,
    AVG(CAST(json_extract_string(pattern_context_json, '$.bof_reclaim_pct') AS DOUBLE)) AS avg_reclaim_pct,
    AVG(CAST(json_extract_string(pattern_context_json, '$.bof_keylevel_proxy_score') AS DOUBLE)) AS avg_keylevel_proxy_score,
    AVG(CAST(json_extract_string(pattern_context_json, '$.bof_pinbar_proxy_score') AS DOUBLE)) AS avg_pinbar_proxy_score,
    AVG(
        CASE
            WHEN LOWER(json_extract_string(pattern_context_json, '$.bof_keylevel_strict')) = 'true'
            THEN 1.0
            ELSE 0.0
        END
    ) AS keylevel_pass_ratio,
    AVG(
        CASE
            WHEN LOWER(json_extract_string(pattern_context_json, '$.bof_pinbar_expression')) = 'true'
            THEN 1.0
            ELSE 0.0
        END
    ) AS pinbar_pass_ratio
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
"""


NEGATIVE_EXAMPLES_QUERY = (
    BOF_QUALITY_PAIRED_TRACE_CTE
    + """
SELECT
    signal_date,
    code,
    entry_date,
    exit_date,
    gross_return,
    pattern_strength,
    pattern_quality_score
FROM paired
WHERE gross_return < 0
ORDER BY gross_return ASC, signal_date ASC
LIMIT 6
"""
)


POSITIVE_EXAMPLES_QUERY = (
    BOF_QUALITY_PAIRED_TRACE_CTE
    + """
SELECT
    signal_date,
    code,
    entry_date,
    exit_date,
    gross_return,
    pattern_strength,
    pattern_quality_score
FROM paired
WHERE gross_return > 0
ORDER BY gross_return DESC, signal_date ASC
LIMIT 6
"""
)


def collect_normandy_bof_quality_stability_snapshot(
    matrix_payload: dict[str, object],
    digest_payload: dict[str, object],
    db_path: str | Path | None,
) -> dict[str, object]:
    retained_branch_label = _resolve_retained_branch_label(digest_payload)
    if retained_branch_label is None:
        return {
            "snapshot_status": "skipped_no_retained_branch",
            "snapshot_db_path": str(Path(db_path).expanduser().resolve()) if db_path is not None else None,
            "retained_branch_label": None,
            "retained_branch_run_id": None,
            "pairing_diagnostics": {},
            "signal_year_slices": [],
            "quarter_activity": [],
            "selected_trace_summary": {},
            "positive_examples": [],
            "negative_examples": [],
        }

    retained_result = _find_result(matrix_payload, retained_branch_label)
    run_id = str(retained_result.get("run_id") or "").strip()
    if not run_id:
        raise KeyError(f"{retained_branch_label} result missing run_id")

    connection, resolved_path = _maybe_open_snapshot_db(db_path)
    if connection is None:
        return {
            "snapshot_status": "missing",
            "snapshot_db_path": str(resolved_path) if resolved_path is not None else None,
            "retained_branch_label": retained_branch_label,
            "retained_branch_run_id": run_id,
            "pairing_diagnostics": {},
            "signal_year_slices": [],
            "quarter_activity": [],
            "selected_trace_summary": {},
            "positive_examples": [],
            "negative_examples": [],
        }

    try:
        params = [run_id, run_id, run_id]
        pairing = _query_dicts(connection, PAIRING_DIAGNOSTICS_QUERY, params)
        signal_year_slices = _query_dicts(connection, SIGNAL_YEAR_SLICES_QUERY, params)
        quarter_activity = _query_dicts(connection, QUARTER_ACTIVITY_QUERY, [run_id])
        selected_trace_summary = _query_dicts(connection, SELECTED_TRACE_SUMMARY_QUERY, [run_id])
        positive_examples = _query_dicts(connection, POSITIVE_EXAMPLES_QUERY, params)
        negative_examples = _query_dicts(connection, NEGATIVE_EXAMPLES_QUERY, params)
    finally:
        connection.close()

    return {
        "snapshot_status": "available",
        "snapshot_db_path": str(resolved_path),
        "retained_branch_label": retained_branch_label,
        "retained_branch_run_id": run_id,
        "pairing_diagnostics": pairing[0] if pairing else {},
        "signal_year_slices": _normalize_rows(signal_year_slices),
        "quarter_activity": _normalize_rows(quarter_activity),
        "selected_trace_summary": selected_trace_summary[0] if selected_trace_summary else {},
        "positive_examples": _normalize_rows(positive_examples),
        "negative_examples": _normalize_rows(negative_examples),
    }


def _dominant_environment_share(result: dict[str, object]) -> float | None:
    breakdown = result.get("environment_breakdown")
    if not isinstance(breakdown, dict):
        return None
    counts: list[float] = []
    for metrics in breakdown.values():
        if not isinstance(metrics, dict):
            continue
        trade_count = _finite_or_none(metrics.get("trade_count"))
        if trade_count is not None:
            counts.append(trade_count)
    if not counts:
        return None
    total = sum(counts)
    if total <= 0:
        return None
    return max(counts) / total


def build_normandy_bof_quality_stability_report(
    matrix_payload: dict[str, object],
    digest_payload: dict[str, object],
    snapshot_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = snapshot_payload or {}
    retained_branch_label = _resolve_retained_branch_label(digest_payload)
    bof_result = _find_result(matrix_payload, "BOF_CONTROL")
    retained_result = _find_result(matrix_payload, retained_branch_label) if retained_branch_label else None

    signal_year_slices = [
        row for row in snapshot.get("signal_year_slices", []) if isinstance(row, dict)
    ]
    quarter_activity = [
        row for row in snapshot.get("quarter_activity", []) if isinstance(row, dict)
    ]
    positive_examples = [
        row for row in snapshot.get("positive_examples", []) if isinstance(row, dict)
    ]
    negative_examples = [
        row for row in snapshot.get("negative_examples", []) if isinstance(row, dict)
    ]
    pairing_diagnostics = snapshot.get("pairing_diagnostics", {})
    if not isinstance(pairing_diagnostics, dict):
        pairing_diagnostics = {}
    selected_trace_summary = snapshot.get("selected_trace_summary", {})
    if not isinstance(selected_trace_summary, dict):
        selected_trace_summary = {}

    meaningful_negative_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if int(row.get("trade_count") or 0) >= 2
        and _finite_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) < 0
    ]
    meaningful_positive_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if int(row.get("trade_count") or 0) >= 2
        and _finite_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) > 0
    ]

    snapshot_status = str(snapshot.get("snapshot_status") or "missing")
    if retained_branch_label is None or retained_result is None:
        stability_status = "branch_no_go"
        decision = "keep_bof_control_as_sole_baseline"
        conclusion = "N1.11 没有 retained branch，因此 N1.12 不打开；继续保持 BOF_CONTROL 为唯一 baseline。"
        stability_flags = ["no_retained_branch"]
        next_actions = [
            "关闭当前 BOF quality family 的继续扩张。",
            "保持 BOF_CONTROL 为 Normandy 唯一 baseline。",
        ]
    elif snapshot_status != "available":
        stability_status = "snapshot_missing"
        decision = "snapshot_recovery_needed"
        conclusion = "BOF retained branch stability follow-up 缺少快照库，当前不能完成 N1.12 formal readout。"
        stability_flags = ["snapshot_missing"]
        next_actions = [
            "恢复对应 working DB / trace 快照。",
            "重跑 retained branch 的 N1.12 stability report。",
        ]
    else:
        trade_count = int(retained_result.get("trade_count") or 0)
        participation_rate = _finite_or_none(retained_result.get("participation_rate"))
        sample_density_ok = _sample_density_ok(trade_count, participation_rate)
        dominant_environment_share = _dominant_environment_share(retained_result)
        overlap_rate = _finite_or_none(retained_result.get("overlap_rate_vs_bof_control"))
        control_trade_count = max(int(bof_result.get("trade_count") or 0), 1)
        trade_share_vs_control = trade_count / control_trade_count
        selected_count = int(pairing_diagnostics.get("selected_entry_count") or 0)
        paired_trade_count = int(pairing_diagnostics.get("paired_trade_count") or 0)
        selected_to_fill_ratio = (
            None if paired_trade_count <= 0 else float(selected_count) / float(paired_trade_count)
        )

        stability_flags: list[str] = []
        if not sample_density_ok:
            stability_flags.append("sample_still_small")
        if meaningful_negative_years:
            stability_flags.append("negative_signal_year_slices")
        if (
            dominant_environment_share is not None
            and dominant_environment_share >= NORMANDY_BOF_STABILITY_MAX_DOMINANT_BUCKET_SHARE
        ):
            stability_flags.append("single_bucket_dependency")
        if (
            selected_to_fill_ratio is not None
            and selected_to_fill_ratio >= NORMANDY_BOF_STABILITY_MAX_SELECTED_TO_FILL_RATIO
        ):
            stability_flags.append("selected_executed_gap_too_wide")
        if (
            overlap_rate is not None
            and overlap_rate >= 0.95
            and trade_share_vs_control < NORMANDY_BOF_STABILITY_MIN_TRADE_SHARE_VS_CONTROL
        ):
            stability_flags.append("tiny_subset_only")

        if stability_flags:
            stability_status = "branch_no_go"
            decision = "branch_no_go_keep_bof_control"
            conclusion = (
                f"{retained_branch_label} 虽然在 N1.11 中成为 retained branch，"
                "但当前稳定性 / 纯度审计仍未通过，暂不允许进入 N2。"
            )
            next_actions = [
                "结束当前 retained branch 的继续推进。",
                "保持 BOF_CONTROL 为唯一 baseline。",
                "除非后续重新定义 branch contract，否则当前不打开 N2。",
            ]
        else:
            stability_status = "eligible_for_n2_exit_decomposition"
            decision = "open_n2_for_bof_control_vs_retained_branch"
            conclusion = (
                f"{retained_branch_label} 当前已通过跨年、环境桶、selected/executed gap 与 purity 审核；"
                "可以进入 N2 / controlled exit decomposition。"
            )
            next_actions = [
                f"打开 N2 / BOF_CONTROL vs {retained_branch_label}。",
                "继续保持 Broker 出场语义冻结，只审 entry-vs-exit 责任分配。",
            ]

    candidate_summary = (
        {
            "trade_count": int(retained_result.get("trade_count") or 0),
            "expected_value": _finite_or_none(retained_result.get("expected_value")),
            "profit_factor": _finite_or_none(retained_result.get("profit_factor")),
            "max_drawdown": _finite_or_none(retained_result.get("max_drawdown")),
            "participation_rate": _finite_or_none(retained_result.get("participation_rate")),
            "overlap_rate_vs_bof_control": _finite_or_none(retained_result.get("overlap_rate_vs_bof_control")),
            "incremental_buy_trades_vs_bof_control": int(retained_result.get("incremental_buy_trades_vs_bof_control") or 0),
        }
        if retained_result is not None
        else {}
    )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "quality_digest_summary_run_id": digest_payload.get("summary_run_id"),
        "quality_digest_path": digest_payload.get("digest_path") or digest_payload.get("matrix_path"),
        "snapshot_status": snapshot_status,
        "snapshot_db_path": snapshot.get("snapshot_db_path"),
        "retained_branch_label": retained_branch_label,
        "retained_branch_run_id": snapshot.get("retained_branch_run_id") or (None if retained_result is None else retained_result.get("run_id")),
        "control_label": "BOF_CONTROL",
        "candidate_summary": candidate_summary,
        "control_summary": {
            "trade_count": int(bof_result.get("trade_count") or 0),
            "expected_value": _finite_or_none(bof_result.get("expected_value")),
            "profit_factor": _finite_or_none(bof_result.get("profit_factor")),
            "max_drawdown": _finite_or_none(bof_result.get("max_drawdown")),
            "participation_rate": _finite_or_none(bof_result.get("participation_rate")),
        },
        "pairing_diagnostics": pairing_diagnostics,
        "selected_trace_summary": selected_trace_summary,
        "signal_year_slices": signal_year_slices,
        "quarter_activity": quarter_activity,
        "positive_examples": positive_examples,
        "negative_examples": negative_examples,
        "meaningful_negative_signal_years": meaningful_negative_years,
        "meaningful_positive_signal_years": meaningful_positive_years,
        "dominant_environment_share": None if retained_result is None else _dominant_environment_share(retained_result),
        "best_environment_bucket": None if retained_result is None else retained_result.get("best_environment_bucket"),
        "trade_share_vs_bof_control": (
            None
            if retained_result is None or int(bof_result.get("trade_count") or 0) <= 0
            else float(int(retained_result.get("trade_count") or 0) / int(bof_result.get("trade_count") or 1))
        ),
        "selected_to_fill_ratio": (
            None
            if not isinstance(pairing_diagnostics, dict)
            or int(pairing_diagnostics.get("paired_trade_count") or 0) <= 0
            else float(int(pairing_diagnostics.get("selected_entry_count") or 0))
            / float(int(pairing_diagnostics.get("paired_trade_count") or 1))
        ),
        "stability_flags": stability_flags,
        "stability_status": stability_status,
        "decision": decision,
        "conclusion": conclusion,
        "next_actions": next_actions,
        "notes": [
            "N1.12 只围绕 N1.11 retained branch，不重新打开跨 family 竞争。",
            "BOF quality branches 是 control 内部子集，因此 overlap 读数只作为 purity 约束，不作为独立 alpha 证明。",
        ],
    }


def read_normandy_bof_quality_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_bof_quality_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
