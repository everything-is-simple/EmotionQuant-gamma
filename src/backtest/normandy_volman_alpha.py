from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

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
from src.strategy.strategy import _build_pas_trace_row
from src.strategy.volman_detectors import FbDetector, RbFakeDetector, SbDetector

NORMANDY_VOLMAN_ALPHA_DTT_VARIANT = "v0_01_dtt_pattern_only"
NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES = 20
NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION = 0.05
NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT = 0.85
NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES = 20
NORMANDY_VOLMAN_HISTORY_COLUMNS = [
    "code",
    "date",
    "adj_low",
    "adj_close",
    "adj_open",
    "adj_high",
    "volume",
    "volume_ma20",
    "ma20",
    "volume_ratio",
]


@dataclass(frozen=True)
class NormandyVolmanAlphaScenario:
    label: str
    family: str
    detector_key: str
    signal_pattern: str
    detector_ready: bool
    control: bool
    detector_status: str
    notes: str
    backing_pas_pattern: str | None = None


@dataclass
class NormandyVolmanAlphaRunArtifacts:
    scenario: NormandyVolmanAlphaScenario
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


def build_normandy_volman_alpha_scenarios(_config: Settings | None = None) -> list[NormandyVolmanAlphaScenario]:
    return [
        NormandyVolmanAlphaScenario(
            label="BOF_CONTROL",
            family="BOF_CONTROL",
            detector_key="bof_control",
            signal_pattern="bof",
            detector_ready=True,
            control=True,
            detector_status="ready",
            notes="Current validated baseline detector; fixed control for N1.5.",
            backing_pas_pattern="bof",
        ),
        NormandyVolmanAlphaScenario(
            label="RB_FAKE",
            family="RB_FAKE",
            detector_key="rb_fake",
            signal_pattern="rb_fake",
            detector_ready=True,
            control=False,
            detector_status="ready",
            notes="Volman range-boundary fake breakout failure candidate.",
        ),
        NormandyVolmanAlphaScenario(
            label="SB",
            family="SB",
            detector_key="sb",
            signal_pattern="sb",
            detector_ready=True,
            control=False,
            detector_status="ready",
            notes="Volman second-break continuation candidate; must remain in first batch.",
        ),
        NormandyVolmanAlphaScenario(
            label="FB",
            family="FB",
            detector_key="fb",
            signal_pattern="fb",
            detector_ready=True,
            control=False,
            detector_status="ready",
            notes="Volman first-break / first-pullback continuation candidate.",
        ),
    ]


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _sort_scorecard_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda item: (
            1 if bool(item.get("second_alpha_candidate")) else 0,
            1 if bool(item.get("sample_density_ok")) else 0,
            1 if bool(item.get("positive_edge_ok")) else 0,
            -999.0 if item.get("expected_value") is None else float(item["expected_value"]),
            -999.0 if item.get("profit_factor") is None else float(item["profit_factor"]),
            -1.0 if item.get("participation_rate") is None else float(item["participation_rate"]),
            int(item.get("trade_count") or 0),
        ),
        reverse=True,
    )


def _pending_detector_labels(scenarios: list[NormandyVolmanAlphaScenario]) -> list[str]:
    return [scenario.label for scenario in scenarios if not scenario.detector_ready]


def _build_scaffold_execution_mode(
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
        "control_label": "BOF_CONTROL",
    }


def _build_detector(config: Settings, scenario: NormandyVolmanAlphaScenario):
    if scenario.detector_key == "bof_control":
        return BofDetector(config)
    if scenario.detector_key == "rb_fake":
        return RbFakeDetector(config)
    if scenario.detector_key == "sb":
        return SbDetector(config)
    if scenario.detector_key == "fb":
        return FbDetector(config)
    raise ValueError(f"Unsupported Normandy Volman detector: {scenario.detector_key}")


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_environment_breakdown(
    payload: dict[str, dict[str, float | int | None]]
) -> dict[str, dict[str, float | None]]:
    normalized: dict[str, dict[str, float | None]] = {}
    for bucket, metrics in payload.items():
        normalized[bucket] = {key: _finite_or_none(value) for key, value in metrics.items()}
    return normalized


def _snapshot_runtime_metrics(store: Store, start: date, end: date) -> tuple[int, int, int]:
    signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    ranked_signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signal_rank_exp WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    trades_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l4_trades WHERE execute_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    return signals_count, ranked_signals_count, trades_count


def _read_selected_rank_frame(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT signal_date, code, signal_id, final_rank, final_score
        FROM l3_signal_rank_exp
        WHERE run_id = ? AND selected = TRUE
        ORDER BY signal_date ASC, final_rank ASC, signal_id ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    return frame


def _read_buy_execution_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT o.signal_id, t.execute_date, t.code, t.pattern, t.quantity
        FROM l4_trades t
        INNER JOIN l4_orders o
            ON o.order_id = t.order_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date ASC, t.code ASC, o.signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _read_detected_trace_frame(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT signal_date, code, detector AS pattern, selected_pattern, registry_run_label
        FROM pas_trigger_trace_exp
        WHERE run_id = ? AND detected = TRUE
        ORDER BY signal_date ASC, code ASC, detector ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    return frame


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
            reference_status
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
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    return frame


def _load_candidate_histories_batch(
    store: Store,
    codes: list[str],
    asof_date: date,
    lookback_days: int,
) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame(columns=NORMANDY_VOLMAN_HISTORY_COLUMNS)

    placeholders = ", ".join(["?"] * len(codes))
    sql = f"""
        WITH recent AS (
            SELECT
                code,
                date,
                adj_low,
                adj_close,
                adj_open,
                adj_high,
                volume,
                volume_ma20,
                ma20,
                volume_ratio,
                ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) AS rn
            FROM l2_stock_adj_daily
            WHERE code IN ({placeholders})
              AND date <= ?
        )
        SELECT code, date, adj_low, adj_close, adj_open, adj_high, volume, volume_ma20, ma20, volume_ratio
        FROM recent
        WHERE rn <= ?
        ORDER BY code ASC, date ASC
    """
    params = tuple(codes) + (asof_date, lookback_days)
    return store.read_df(sql, params)


def _generate_normandy_volman_signals(
    store: Store,
    candidates: list[StockCandidate],
    asof_date: date,
    scenario: NormandyVolmanAlphaScenario,
    config: Settings,
    run_id: str | None = None,
) -> list[Signal]:
    if not candidates:
        return []

    detector = _build_detector(config, scenario)
    history_days_required = max(int(getattr(detector, "required_window", config.pas_lookback_days)), 1)
    histories = _load_candidate_histories_batch(
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
            history = pd.DataFrame(columns=NORMANDY_VOLMAN_HISTORY_COLUMNS)
        signal, trace_payload = detector.evaluate(candidate.code, asof_date, history)
        payload = dict(trace_payload)
        payload["pattern"] = scenario.signal_pattern
        payload["pattern_group"] = scenario.family
        payload["registry_run_label"] = scenario.label
        payload["selected_pattern"] = scenario.signal_pattern if signal is not None else None

        if signal is not None and signal.pattern != scenario.signal_pattern:
            signal = signal.model_copy(
                update={
                    "signal_id": signal.signal_id.replace(signal.pattern, scenario.signal_pattern),
                    "pattern": scenario.signal_pattern,
                    "reason_code": f"PAS_{scenario.signal_pattern.upper()}",
                }
            )
            payload["signal_id"] = signal.signal_id
            payload["reason_code"] = signal.reason_code

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
        if signal is not None:
            raw_signals.append(signal)

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


def _run_normandy_volman_backtest(
    *,
    db_path: str | Path,
    config: Settings,
    scenario: NormandyVolmanAlphaScenario,
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
            signals = _generate_normandy_volman_signals(
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
    cfg.pas_quality_enabled = False
    cfg.pas_reference_enabled = False
    if dtt_top_n is not None:
        cfg.dtt_top_n = max(1, int(dtt_top_n))
    if max_positions is not None:
        cfg.max_positions = max(1, int(max_positions))
    return cfg


def _run_normandy_volman_scenario(
    *,
    db_file: Path,
    base_config: Settings,
    scenario: NormandyVolmanAlphaScenario,
    dtt_variant: str,
    start: date,
    end: date,
    initial_cash: float | None,
    artifact_root: Path,
    dtt_top_n: int | None,
    max_positions: int | None,
) -> NormandyVolmanAlphaRunArtifacts:
    cfg = _build_scenario_config(
        base_config,
        dtt_variant=dtt_variant,
        dtt_top_n=dtt_top_n,
        max_positions=max_positions,
    )
    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="normandy_volman_alpha",
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
        result = _run_normandy_volman_backtest(
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
        signals_count, ranked_signals_count, trades_count = _snapshot_runtime_metrics(snapshot_store, start, end)
        selected_rank_frame = _read_selected_rank_frame(snapshot_store, run.run_id)
        buy_execution_frame = _read_buy_execution_frame(snapshot_store, start, end)
        detected_trace_frame = _read_detected_trace_frame(snapshot_store, run.run_id)
        selected_trace_frame = _read_selected_trace_frame(snapshot_store, run.run_id)
    finally:
        snapshot_store.close()

    return NormandyVolmanAlphaRunArtifacts(
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
        environment_breakdown=_normalize_environment_breakdown(result.environment_breakdown),
        selected_rank_frame=selected_rank_frame,
        buy_execution_frame=buy_execution_frame,
        detected_trace_frame=detected_trace_frame,
        selected_trace_frame=selected_trace_frame,
    )


def _buy_trade_keys(frame: pd.DataFrame) -> set[tuple[str, str]]:
    if frame.empty:
        return set()
    return {
        (str(row["execute_date"]), str(row["code"]))
        for _, row in frame.iterrows()
    }


def _compute_buy_overlap_rate(control_frame: pd.DataFrame, target_frame: pd.DataFrame) -> float | None:
    target_keys = _buy_trade_keys(target_frame)
    if not target_keys:
        return None
    control_keys = _buy_trade_keys(control_frame)
    return len(control_keys & target_keys) / len(target_keys)


def _count_incremental_buy_trades(control_frame: pd.DataFrame, target_frame: pd.DataFrame) -> int:
    control_keys = _buy_trade_keys(control_frame)
    target_keys = _buy_trade_keys(target_frame)
    return len(target_keys - control_keys)


def _serialize_scenario_result(
    result: NormandyVolmanAlphaRunArtifacts,
    *,
    bof_control: NormandyVolmanAlphaRunArtifacts,
) -> dict[str, object]:
    overlap_rate = 1.0 if result.scenario.control else _compute_buy_overlap_rate(
        bof_control.buy_execution_frame,
        result.buy_execution_frame,
    )
    incremental_buy_trades = 0 if result.scenario.control else _count_incremental_buy_trades(
        bof_control.buy_execution_frame,
        result.buy_execution_frame,
    )
    return {
        "label": result.scenario.label,
        "family": result.scenario.family,
        "detector_key": result.scenario.detector_key,
        "signal_pattern": result.scenario.signal_pattern,
        "control": result.scenario.control,
        "detector_status": result.scenario.detector_status,
        "backing_pas_pattern": result.scenario.backing_pas_pattern,
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


def _build_matrix_summary(results: list[dict[str, object]]) -> list[dict[str, object]]:
    control = next(item for item in results if item["label"] == "BOF_CONTROL")
    control_ev = _finite_or_none(control.get("expected_value"))  # type: ignore[arg-type]
    control_pf = _finite_or_none(control.get("profit_factor"))  # type: ignore[arg-type]
    control_mdd = _finite_or_none(control.get("max_drawdown"))  # type: ignore[arg-type]
    control_participation = _finite_or_none(control.get("participation_rate"))  # type: ignore[arg-type]

    summary_rows: list[dict[str, object]] = []
    for result in results:
        ev = _finite_or_none(result.get("expected_value"))  # type: ignore[arg-type]
        pf = _finite_or_none(result.get("profit_factor"))  # type: ignore[arg-type]
        mdd = _finite_or_none(result.get("max_drawdown"))  # type: ignore[arg-type]
        participation = _finite_or_none(result.get("participation_rate"))  # type: ignore[arg-type]
        summary_rows.append(
            {
                "label": result["label"],
                "family": result["family"],
                "signal_pattern": result["signal_pattern"],
                "trade_count": int(result.get("trade_count") or 0),
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "overlap_rate_vs_bof_control": _finite_or_none(result.get("overlap_rate_vs_bof_control")),  # type: ignore[arg-type]
                "incremental_buy_trades_vs_bof_control": int(result.get("incremental_buy_trades_vs_bof_control") or 0),
                "expected_value_delta_vs_bof_control": (
                    None if ev is None or control_ev is None else ev - control_ev
                ),
                "profit_factor_delta_vs_bof_control": (
                    None if pf is None or control_pf is None else pf - control_pf
                ),
                "max_drawdown_delta_vs_bof_control": (
                    None if mdd is None or control_mdd is None else mdd - control_mdd
                ),
                "participation_delta_vs_bof_control": (
                    None
                    if participation is None or control_participation is None
                    else participation - control_participation
                ),
            }
        )
    return summary_rows


def build_normandy_volman_alpha_scaffold_payload(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str = NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
    dtt_top_n: int | None = None,
    max_positions: int | None = None,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, object]:
    source_db = Path(db_path).expanduser().resolve()
    db_file = Path(working_db_path).expanduser().resolve() if working_db_path is not None else source_db
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    scenarios = build_normandy_volman_alpha_scenarios(config)
    pending_detectors = _pending_detector_labels(scenarios)
    ready_labels = [scenario.label for scenario in scenarios if scenario.detector_ready]
    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "detector_contract_only",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "execution_mode": _build_scaffold_execution_mode(
            config,
            dtt_variant=dtt_variant,
            dtt_top_n=dtt_top_n,
            max_positions=max_positions,
        ),
        "scenarios": [
            {
                "label": scenario.label,
                "family": scenario.family,
                "detector_key": scenario.detector_key,
                "signal_pattern": scenario.signal_pattern,
                "detector_ready": scenario.detector_ready,
                "detector_status": scenario.detector_status,
                "control": scenario.control,
                "backing_pas_pattern": scenario.backing_pas_pattern,
                "notes": scenario.notes,
            }
            for scenario in scenarios
        ],
        "pending_detectors": pending_detectors,
        "ready_detectors": ready_labels,
        "results": [],
        "conclusion": (
            "Scaffold-only export requested; current first-batch detectors: "
            f"{', '.join(ready_labels)}."
        ),
    }


def run_normandy_volman_alpha_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str = NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    dtt_top_n: int | None = None,
    max_positions: int | None = None,
    scaffold_only: bool = False,
) -> dict[str, object]:
    if scaffold_only:
        return build_normandy_volman_alpha_scaffold_payload(
            db_path=db_path,
            config=config,
            start=start,
            end=end,
            dtt_variant=dtt_variant,
            dtt_top_n=dtt_top_n,
            max_positions=max_positions,
            working_db_path=working_db_path,
            artifact_root=artifact_root,
        )

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

    scenarios = build_normandy_volman_alpha_scenarios(config)
    runs = [
        _run_normandy_volman_scenario(
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
        for scenario in scenarios
    ]
    bof_control = next(result for result in runs if result.scenario.label == "BOF_CONTROL")
    serialized_results = [
        _serialize_scenario_result(result, bof_control=bof_control)
        for result in runs
    ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "execution_mode": _build_scaffold_execution_mode(
            config,
            dtt_variant=dtt_variant,
            dtt_top_n=dtt_top_n,
            max_positions=max_positions,
        ),
        "scenarios": [
            {
                "label": scenario.label,
                "family": scenario.family,
                "detector_key": scenario.detector_key,
                "signal_pattern": scenario.signal_pattern,
                "detector_status": scenario.detector_status,
                "control": scenario.control,
                "backing_pas_pattern": scenario.backing_pas_pattern,
            }
            for scenario in scenarios
        ],
        "matrix_summary": _build_matrix_summary(serialized_results),
        "results": serialized_results,
    }


def _sample_density_ok(trade_count: int, participation_rate: float | None) -> bool:
    return trade_count >= NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES or (
        participation_rate is not None and participation_rate >= NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION
    )


def _complementary_edge_ok(overlap_rate: float | None, incremental_trades: int) -> bool:
    if overlap_rate is not None and overlap_rate <= NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT:
        return True
    return incremental_trades >= NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES


def _build_digest_scorecard(matrix_payload: dict[str, object]) -> list[dict[str, object]]:
    raw_results = matrix_payload.get("results")
    if not isinstance(raw_results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (item for item in raw_results if isinstance(item, dict) and item.get("label") == "BOF_CONTROL"),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include BOF_CONTROL baseline")

    control_ev = _finite_or_none(control.get("expected_value"))  # type: ignore[arg-type]
    control_pf = _finite_or_none(control.get("profit_factor"))  # type: ignore[arg-type]
    scorecard: list[dict[str, object]] = []
    for result in raw_results:
        if not isinstance(result, dict):
            continue
        label = str(result.get("label") or "")
        trade_count = int(result.get("trade_count") or 0)
        ev = _finite_or_none(result.get("expected_value"))  # type: ignore[arg-type]
        pf = _finite_or_none(result.get("profit_factor"))  # type: ignore[arg-type]
        mdd = _finite_or_none(result.get("max_drawdown"))  # type: ignore[arg-type]
        participation = _finite_or_none(result.get("participation_rate"))  # type: ignore[arg-type]
        overlap_rate = _finite_or_none(result.get("overlap_rate_vs_bof_control"))  # type: ignore[arg-type]
        incremental_trades = int(result.get("incremental_buy_trades_vs_bof_control") or 0)
        positive_edge_ok = label != "BOF_CONTROL" and ev is not None and ev > 0 and pf is not None and pf >= 1.0
        sample_density_ok = _sample_density_ok(trade_count, participation)
        complementary_edge_ok = label != "BOF_CONTROL" and _complementary_edge_ok(overlap_rate, incremental_trades)
        second_alpha_candidate = bool(positive_edge_ok and sample_density_ok and complementary_edge_ok)
        scorecard.append(
            {
                "label": label,
                "family": result.get("family") or label,
                "trade_count": trade_count,
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "overlap_rate_vs_bof_control": overlap_rate,
                "incremental_buy_trades_vs_bof_control": incremental_trades,
                "expected_value_delta_vs_bof_control": (
                    None if ev is None or control_ev is None else ev - control_ev
                ),
                "profit_factor_delta_vs_bof_control": (
                    None if pf is None or control_pf is None else pf - control_pf
                ),
                "positive_edge_ok": positive_edge_ok,
                "sample_density_ok": sample_density_ok,
                "complementary_edge_ok": complementary_edge_ok,
                "second_alpha_candidate": second_alpha_candidate,
            }
        )
    return _sort_scorecard_rows(scorecard)


def build_normandy_volman_alpha_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        pending_detectors = matrix_payload.get("pending_detectors")
        pending = [str(item) for item in pending_detectors] if isinstance(pending_detectors, list) else []
        conclusion = (
            "Current Volman N1.5 matrix is still detector_contract_only; "
            f"pending detectors: {', '.join(pending)}."
            if pending
            else "Current Volman N1.5 matrix is detector_contract_only scaffold export only."
        )
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
            "matrix_path": matrix_payload.get("matrix_path"),
            "start": matrix_payload.get("start"),
            "end": matrix_payload.get("end"),
            "dtt_variant": matrix_payload.get("dtt_variant"),
            "matrix_status": matrix_status,
            "control_label": "BOF_CONTROL",
            "second_alpha_candidates": [],
            "pending_detectors": pending,
            "candidate_rule": {
                "expected_value_must_be_positive": True,
                "profit_factor_floor": 1.0,
                "min_trade_count": NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES,
                "min_participation_rate": NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION,
                "max_overlap_for_independent": NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT,
                "min_incremental_trades": NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES,
            },
            "scorecard": [],
            "provenance_leader": None,
            "conclusion": conclusion,
        }

    scorecard = _build_digest_scorecard(matrix_payload)
    non_control_rows = [row for row in scorecard if row["label"] != "BOF_CONTROL"]
    second_alpha_candidates = [row for row in scorecard if bool(row["second_alpha_candidate"])]
    provenance_leader = (
        second_alpha_candidates[0]["label"]
        if second_alpha_candidates
        else (non_control_rows[0]["label"] if non_control_rows else "BOF_CONTROL")
    )
    if second_alpha_candidates:
        labels = ", ".join(str(row["label"]) for row in second_alpha_candidates)
        conclusion = (
            f"{labels} 当前满足正 EV、样本密度和增量 alpha 门槛；"
            f"优先围绕 {provenance_leader} 继续做第二层 provenance。"
        )
    else:
        conclusion = (
            "当前还没有非 BOF_CONTROL 候选同时满足正 EV、样本密度和增量 alpha 门槛；"
            f"{provenance_leader} 先保留为观测领先者。"
        )

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
            "min_trade_count": NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES,
            "min_participation_rate": NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION,
            "max_overlap_for_independent": NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT,
            "min_incremental_trades": NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES,
        },
        "scorecard": scorecard,
        "provenance_leader": provenance_leader,
        "second_alpha_candidates": [row["label"] for row in second_alpha_candidates],
        "pending_detectors": [],
        "conclusion": conclusion,
    }


def read_normandy_volman_alpha_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_volman_alpha_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
