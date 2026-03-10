from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run

ALL_PAS_PATTERNS = ("bof", "bpb", "pb", "tst", "cpb")


@dataclass(frozen=True)
class PasAblationScenario:
    label: str
    patterns: tuple[str, ...]
    single_pattern_mode: str
    quality_enabled: bool
    reference_enabled: bool

    @property
    def pattern_list(self) -> list[str]:
        return list(self.patterns)


@dataclass
class PasScenarioRunArtifacts:
    scenario: PasAblationScenario
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


def build_pas_ablation_scenarios(_config: Settings) -> list[PasAblationScenario]:
    return [
        PasAblationScenario(
            label="BOF",
            patterns=("bof",),
            single_pattern_mode="bof",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="BPB",
            patterns=("bpb",),
            single_pattern_mode="bpb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="PB",
            patterns=("pb",),
            single_pattern_mode="pb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="TST",
            patterns=("tst",),
            single_pattern_mode="tst",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="CPB",
            patterns=("cpb",),
            single_pattern_mode="cpb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="YTC5_ANY",
            patterns=ALL_PAS_PATTERNS,
            single_pattern_mode="",
            quality_enabled=False,
            reference_enabled=True,
        ),
        PasAblationScenario(
            label="YTC5_ANY_PLUS_QUALITY",
            patterns=ALL_PAS_PATTERNS,
            single_pattern_mode="",
            quality_enabled=True,
            reference_enabled=True,
        ),
    ]


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


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


def _build_scenario_config(base: Settings, scenario: PasAblationScenario, dtt_variant: str) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = dtt_variant
    cfg.pas_patterns = ",".join(scenario.patterns)
    cfg.pas_single_pattern_mode = scenario.single_pattern_mode
    cfg.pas_registry_enabled = True
    cfg.pas_quality_enabled = scenario.quality_enabled
    cfg.pas_reference_enabled = scenario.reference_enabled
    return cfg


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


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


def _signature_map(frame: pd.DataFrame, date_col: str, key_cols: tuple[str, ...]) -> dict[str, set[tuple[object, ...]]]:
    if frame.empty:
        return {}
    grouped: dict[str, set[tuple[object, ...]]] = {}
    for _, row in frame.iterrows():
        bucket = str(row[date_col])
        grouped.setdefault(bucket, set()).add(tuple(row[col] for col in key_cols))
    return grouped


def compute_diff_days(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    date_col: str,
    key_cols: tuple[str, ...],
) -> int:
    left_map = _signature_map(left, date_col, key_cols)
    right_map = _signature_map(right, date_col, key_cols)
    dates = set(left_map) | set(right_map)
    return sum(1 for bucket in dates if left_map.get(bucket, set()) != right_map.get(bucket, set()))


def summarize_introduced_rows(
    base: pd.DataFrame,
    target: pd.DataFrame,
    *,
    date_col: str,
    columns: tuple[str, ...],
    limit: int = 20,
) -> dict[str, object]:
    key_cols = (date_col, *columns)
    base_keys = set() if base.empty else {tuple(row[col] for col in key_cols) for _, row in base.iterrows()}
    added: list[dict[str, object]] = []
    if not target.empty:
        for _, row in target.iterrows():
            key = tuple(row[col] for col in key_cols)
            if key in base_keys:
                continue
            added.append({col: row[col] for col in key_cols})

    unique_rows: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for row in added:
        key = tuple(row[col] for col in key_cols)
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return {
        "count": len(unique_rows),
        "sample": unique_rows[:limit],
    }


def compute_pattern_overlap_rate(detected_trace_frame: pd.DataFrame) -> float:
    if detected_trace_frame.empty:
        return 0.0
    grouped = (
        detected_trace_frame.groupby(["signal_date", "code"], as_index=False)
        .agg(pattern_count=("pattern", "nunique"))
    )
    if grouped.empty:
        return 0.0
    overlap = int((grouped["pattern_count"] > 1).sum())
    return overlap / len(grouped)


def compute_trace_coverage(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return 0.0
    return float(frame[column].notna().mean())


def summarize_selected_pattern_distribution(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty:
        return {}
    counts = frame["pattern"].value_counts().sort_index()
    return {str(pattern): int(count) for pattern, count in counts.items()}


def summarize_quality_leaders(frame: pd.DataFrame, limit: int = 10) -> list[dict[str, object]]:
    if frame.empty or "pattern_quality_score" not in frame.columns:
        return []
    leaders = frame.dropna(subset=["pattern_quality_score"]).copy()
    if leaders.empty:
        return []
    leaders = leaders.sort_values(
        ["pattern_quality_score", "signal_date", "code"],
        ascending=[False, True, True],
    ).head(limit)
    rows: list[dict[str, object]] = []
    for _, row in leaders.iterrows():
        rows.append(
            {
                "signal_date": row["signal_date"],
                "code": row["code"],
                "pattern": row["pattern"],
                "pattern_quality_score": _finite_or_none(row["pattern_quality_score"]),
                "risk_reward_ref": _finite_or_none(row.get("risk_reward_ref")),
                "failure_handling_tag": row.get("failure_handling_tag"),
            }
        )
    return rows


def summarize_environment_bucket(environment_breakdown: dict[str, dict[str, float | None]]) -> dict[str, object] | None:
    if not environment_breakdown:
        return None
    ranked = [
        (
            bucket,
            metrics.get("expected_value"),
            metrics.get("profit_factor"),
            metrics.get("trade_count"),
        )
        for bucket, metrics in environment_breakdown.items()
    ]
    ranked.sort(
        key=lambda item: (
            -999.0 if item[1] is None else float(item[1]),
            -999.0 if item[2] is None else float(item[2]),
            -1 if item[3] is None else int(item[3]),
        ),
        reverse=True,
    )
    bucket, ev, pf, trade_count = ranked[0]
    return {
        "bucket": bucket,
        "expected_value": _finite_or_none(ev),
        "profit_factor": _finite_or_none(pf),
        "trade_count": None if trade_count is None else int(trade_count),
    }


def _run_pas_scenario(
    *,
    db_file: Path,
    base_config: Settings,
    scenario: PasAblationScenario,
    dtt_variant: str,
    start: date,
    end: date,
    initial_cash: float | None,
    artifact_root: Path,
) -> PasScenarioRunArtifacts:
    clear_store = Store(db_file)
    try:
        clear_runtime_tables(clear_store)
    finally:
        clear_store.close()

    cfg = _build_scenario_config(base_config, scenario, dtt_variant)
    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="pas_ablation",
        modules=["backtest", "selector", "strategy", "broker", "report"],
        config=cfg,
        runtime_env="script",
        artifact_root=str(artifact_root),
        start=start,
        end=end,
    )
    meta_store.close()

    try:
        result = run_backtest(
            db_path=db_file,
            config=cfg,
            start=start,
            end=end,
            patterns=scenario.pattern_list,
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

    return PasScenarioRunArtifacts(
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


def _serialize_scenario_result(
    result: PasScenarioRunArtifacts,
    *,
    bof_baseline: PasScenarioRunArtifacts,
) -> dict[str, object]:
    return {
        "label": result.scenario.label,
        "run_id": result.run_id,
        "patterns": result.scenario.pattern_list,
        "single_pattern_mode": result.scenario.single_pattern_mode or None,
        "quality_enabled": result.scenario.quality_enabled,
        "reference_enabled": result.scenario.reference_enabled,
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
        "pattern_overlap_rate": _finite_or_none(compute_pattern_overlap_rate(result.detected_trace_frame)),
        "quality_trace_coverage": _finite_or_none(compute_trace_coverage(result.selected_trace_frame, "pattern_quality_score")),
        "reference_trace_coverage": _finite_or_none(compute_trace_coverage(result.selected_trace_frame, "entry_ref")),
        "rank_diff_days_vs_bof": compute_diff_days(
            bof_baseline.selected_rank_frame,
            result.selected_rank_frame,
            date_col="signal_date",
            key_cols=("signal_id", "final_rank"),
        ),
        "execution_diff_days_vs_bof": compute_diff_days(
            bof_baseline.buy_execution_frame,
            result.buy_execution_frame,
            date_col="execute_date",
            key_cols=("signal_id", "quantity"),
        ),
        "introduced_selected_signals_vs_bof": summarize_introduced_rows(
            bof_baseline.selected_rank_frame,
            result.selected_rank_frame,
            date_col="signal_date",
            columns=("code", "signal_id", "final_rank"),
        ),
        "introduced_buy_trades_vs_bof": summarize_introduced_rows(
            bof_baseline.buy_execution_frame,
            result.buy_execution_frame,
            date_col="execute_date",
            columns=("code", "signal_id", "pattern", "quantity"),
        ),
        "best_environment_bucket": summarize_environment_bucket(result.environment_breakdown),
        "environment_breakdown": result.environment_breakdown,
        "top_quality_signals": summarize_quality_leaders(result.selected_trace_frame),
    }


def run_pas_ablation(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
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

    scenarios = build_pas_ablation_scenarios(config)
    runs = [
        _run_pas_scenario(
            db_file=db_file,
            base_config=config,
            scenario=scenario,
            dtt_variant=dtt_variant,
            start=start,
            end=end,
            initial_cash=initial_cash,
            artifact_root=artifact_root_path,
        )
        for scenario in scenarios
    ]

    bof_baseline = next(result for result in runs if result.scenario.label == "BOF")
    ytc_any = next(result for result in runs if result.scenario.label == "YTC5_ANY")
    ytc_any_quality = next(result for result in runs if result.scenario.label == "YTC5_ANY_PLUS_QUALITY")

    comparisons = {
        "quality_vs_any": {
            "rank_diff_days": compute_diff_days(
                ytc_any.selected_rank_frame,
                ytc_any_quality.selected_rank_frame,
                date_col="signal_date",
                key_cols=("signal_id", "final_rank"),
            ),
            "execution_diff_days": compute_diff_days(
                ytc_any.buy_execution_frame,
                ytc_any_quality.buy_execution_frame,
                date_col="execute_date",
                key_cols=("signal_id", "quantity"),
            ),
            "introduced_selected_signals": summarize_introduced_rows(
                ytc_any.selected_rank_frame,
                ytc_any_quality.selected_rank_frame,
                date_col="signal_date",
                columns=("code", "signal_id", "final_rank"),
            ),
            "introduced_buy_trades": summarize_introduced_rows(
                ytc_any.buy_execution_frame,
                ytc_any_quality.buy_execution_frame,
                date_col="execute_date",
                columns=("code", "signal_id", "pattern", "quantity"),
            ),
            "quality_trace_coverage": _finite_or_none(
                compute_trace_coverage(ytc_any_quality.selected_trace_frame, "pattern_quality_score")
            ),
            "reference_trace_coverage": _finite_or_none(
                compute_trace_coverage(ytc_any_quality.selected_trace_frame, "entry_ref")
            ),
            "note": (
                "quality 当前仍停留在 PAS trace/sidecar 解释层；若 rank_diff_days 或 execution_diff_days 非 0，"
                "表示 quality 已经影响运行时选择。"
            ),
        },
        "new_pattern_vs_bof": [
            {
                "label": result.scenario.label,
                "introduced_selected_signals": summarize_introduced_rows(
                    bof_baseline.selected_rank_frame,
                    result.selected_rank_frame,
                    date_col="signal_date",
                    columns=("code", "signal_id", "final_rank"),
                ),
                "introduced_buy_trades": summarize_introduced_rows(
                    bof_baseline.buy_execution_frame,
                    result.buy_execution_frame,
                    date_col="execute_date",
                    columns=("code", "signal_id", "pattern", "quantity"),
                ),
            }
            for result in runs
            if result.scenario.label != "BOF"
        ],
        "execution_friction": [
            {
                "label": result.scenario.label,
                "reject_rate": result.reject_rate,
                "skip_maxpos_count": result.skip_maxpos_count,
                "participation_rate": result.participation_rate,
                "execution_diff_days_vs_ytc5_any": compute_diff_days(
                    ytc_any.buy_execution_frame,
                    result.buy_execution_frame,
                    date_col="execute_date",
                    key_cols=("signal_id", "quantity"),
                ),
            }
            for result in runs
        ],
    }

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "scenarios": [
            {
                "label": scenario.label,
                "patterns": scenario.pattern_list,
                "single_pattern_mode": scenario.single_pattern_mode or None,
                "quality_enabled": scenario.quality_enabled,
                "reference_enabled": scenario.reference_enabled,
            }
            for scenario in scenarios
        ],
        "results": [
            _serialize_scenario_result(result, bof_baseline=bof_baseline)
            for result in runs
        ],
        "comparisons": comparisons,
    }


def write_pas_ablation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
