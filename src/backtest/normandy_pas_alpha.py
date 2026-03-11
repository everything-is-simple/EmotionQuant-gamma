from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.pas_ablation import (
    compute_diff_days,
    compute_pattern_overlap_rate,
    compute_trace_coverage,
    summarize_environment_bucket,
    summarize_introduced_rows,
    summarize_selected_pattern_distribution,
)
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run

NORMANDY_PAS_ALPHA_DTT_VARIANT = "v0_01_dtt_pattern_only"
NORMANDY_CANDIDATE_MIN_TRADES = 20
NORMANDY_CANDIDATE_MIN_PARTICIPATION = 0.05
YTC5_ANY_PATTERNS = ("bpb", "pb", "tst", "cpb", "bof")
DISPLAY_PATTERN_NAMES = {
    "bof": "BOF",
    "bpb": "BPB",
    "pb": "PB",
    "tst": "TST",
    "cpb": "CPB",
}


@dataclass(frozen=True)
class NormandyPasAlphaScenario:
    label: str
    patterns: tuple[str, ...]
    single_pattern_mode: str
    quality_enabled: bool
    reference_enabled: bool

    @property
    def pattern_list(self) -> list[str]:
        return list(self.patterns)

    @property
    def pattern_family_labels(self) -> list[str]:
        return [DISPLAY_PATTERN_NAMES.get(pattern, pattern.upper()) for pattern in self.patterns]


@dataclass
class NormandyPasAlphaRunArtifacts:
    scenario: NormandyPasAlphaScenario
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


def build_normandy_pas_alpha_scenarios(_config: Settings | None = None) -> list[NormandyPasAlphaScenario]:
    return [
        NormandyPasAlphaScenario(
            label="BOF",
            patterns=("bof",),
            single_pattern_mode="bof",
            quality_enabled=False,
            reference_enabled=True,
        ),
        NormandyPasAlphaScenario(
            label="BPB",
            patterns=("bpb",),
            single_pattern_mode="bpb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        NormandyPasAlphaScenario(
            label="PB",
            patterns=("pb",),
            single_pattern_mode="pb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        NormandyPasAlphaScenario(
            label="TST",
            patterns=("tst",),
            single_pattern_mode="tst",
            quality_enabled=False,
            reference_enabled=True,
        ),
        NormandyPasAlphaScenario(
            label="CPB",
            patterns=("cpb",),
            single_pattern_mode="cpb",
            quality_enabled=False,
            reference_enabled=True,
        ),
        NormandyPasAlphaScenario(
            label="YTC5_ANY",
            patterns=YTC5_ANY_PATTERNS,
            single_pattern_mode="",
            quality_enabled=False,
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


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


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


def _build_scenario_config(
    base: Settings,
    scenario: NormandyPasAlphaScenario,
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
    cfg.pas_combination = "ANY"
    cfg.pas_patterns = ",".join(scenario.patterns)
    cfg.pas_single_pattern_mode = scenario.single_pattern_mode
    cfg.pas_registry_enabled = True
    cfg.pas_quality_enabled = scenario.quality_enabled
    cfg.pas_reference_enabled = scenario.reference_enabled
    if dtt_top_n is not None:
        cfg.dtt_top_n = max(1, int(dtt_top_n))
    if max_positions is not None:
        cfg.max_positions = max(1, int(max_positions))
    return cfg


def _run_normandy_pas_scenario(
    *,
    db_file: Path,
    base_config: Settings,
    scenario: NormandyPasAlphaScenario,
    dtt_variant: str,
    start: date,
    end: date,
    initial_cash: float | None,
    artifact_root: Path,
    dtt_top_n: int | None,
    max_positions: int | None,
) -> NormandyPasAlphaRunArtifacts:
    cfg = _build_scenario_config(
        base_config,
        scenario,
        dtt_variant=dtt_variant,
        dtt_top_n=dtt_top_n,
        max_positions=max_positions,
    )
    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="normandy_pas_alpha",
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

    return NormandyPasAlphaRunArtifacts(
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
    result: NormandyPasAlphaRunArtifacts,
    *,
    bof_baseline: NormandyPasAlphaRunArtifacts,
) -> dict[str, object]:
    return {
        "label": result.scenario.label,
        "run_id": result.run_id,
        "patterns": result.scenario.pattern_list,
        "pattern_families": result.scenario.pattern_family_labels,
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
    }


def _build_matrix_summary(results: list[dict[str, object]]) -> list[dict[str, object]]:
    bof_result = next(item for item in results if item["label"] == "BOF")
    bof_ev = _finite_or_none(bof_result.get("expected_value"))  # type: ignore[arg-type]
    bof_pf = _finite_or_none(bof_result.get("profit_factor"))  # type: ignore[arg-type]
    bof_mdd = _finite_or_none(bof_result.get("max_drawdown"))  # type: ignore[arg-type]
    bof_part = _finite_or_none(bof_result.get("participation_rate"))  # type: ignore[arg-type]

    matrix_rows: list[dict[str, object]] = []
    for result in results:
        ev = _finite_or_none(result.get("expected_value"))  # type: ignore[arg-type]
        pf = _finite_or_none(result.get("profit_factor"))  # type: ignore[arg-type]
        mdd = _finite_or_none(result.get("max_drawdown"))  # type: ignore[arg-type]
        participation = _finite_or_none(result.get("participation_rate"))  # type: ignore[arg-type]
        matrix_rows.append(
            {
                "label": result["label"],
                "patterns": result["patterns"],
                "pattern_families": result["pattern_families"],
                "trade_count": int(result.get("trade_count") or 0),
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "expected_value_delta_vs_bof": None if ev is None or bof_ev is None else ev - bof_ev,
                "profit_factor_delta_vs_bof": None if pf is None or bof_pf is None else pf - bof_pf,
                "max_drawdown_delta_vs_bof": None if mdd is None or bof_mdd is None else mdd - bof_mdd,
                "participation_delta_vs_bof": (
                    None if participation is None or bof_part is None else participation - bof_part
                ),
            }
        )
    return matrix_rows


def run_normandy_pas_alpha_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str = NORMANDY_PAS_ALPHA_DTT_VARIANT,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    dtt_top_n: int | None = None,
    max_positions: int | None = None,
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

    scenarios = build_normandy_pas_alpha_scenarios(config)
    runs = [
        _run_normandy_pas_scenario(
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
    bof_baseline = next(result for result in runs if result.scenario.label == "BOF")
    serialized_results = [
        _serialize_scenario_result(result, bof_baseline=bof_baseline)
        for result in runs
    ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "execution_mode": {
            "pipeline_mode": "dtt",
            "enable_mss_gate": False,
            "enable_irs_filter": False,
            "pas_combination": "ANY",
            "quality_enabled": False,
            "reference_enabled": True,
            "dtt_top_n": int(dtt_top_n if dtt_top_n is not None else config.dtt_top_n),
            "max_positions": int(max_positions if max_positions is not None else config.max_positions),
        },
        "scenarios": [
            {
                "label": scenario.label,
                "patterns": scenario.pattern_list,
                "pattern_families": scenario.pattern_family_labels,
                "single_pattern_mode": scenario.single_pattern_mode or None,
                "quality_enabled": scenario.quality_enabled,
                "reference_enabled": scenario.reference_enabled,
            }
            for scenario in scenarios
        ],
        "matrix_summary": _build_matrix_summary(serialized_results),
        "results": serialized_results,
    }


def _sort_scorecard_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda item: (
            -999.0 if item["expected_value"] is None else float(item["expected_value"]),
            -999.0 if item["profit_factor"] is None else float(item["profit_factor"]),
            -1.0 if item["participation_rate"] is None else float(item["participation_rate"]),
            -999.0 if item["max_drawdown"] is None else -float(item["max_drawdown"]),
            int(item["trade_count"]),
        ),
        reverse=True,
    )


def _sample_density_threshold(bof_participation: float | None) -> float:
    if bof_participation is None:
        return NORMANDY_CANDIDATE_MIN_PARTICIPATION
    return max(NORMANDY_CANDIDATE_MIN_PARTICIPATION, float(bof_participation) * 0.5)


def _build_digest_scorecard(matrix_payload: dict[str, object]) -> list[dict[str, object]]:
    raw_results = matrix_payload.get("results")
    if not isinstance(raw_results, list):
        raise ValueError("matrix_payload.results must be a list")

    bof_result = next((item for item in raw_results if isinstance(item, dict) and item.get("label") == "BOF"), None)
    if bof_result is None:
        raise ValueError("matrix_payload.results must include BOF baseline")

    bof_ev = _finite_or_none(bof_result.get("expected_value"))  # type: ignore[arg-type]
    bof_pf = _finite_or_none(bof_result.get("profit_factor"))  # type: ignore[arg-type]
    bof_mdd = _finite_or_none(bof_result.get("max_drawdown"))  # type: ignore[arg-type]
    bof_participation = _finite_or_none(bof_result.get("participation_rate"))  # type: ignore[arg-type]
    participation_threshold = _sample_density_threshold(bof_participation)

    scorecard: list[dict[str, object]] = []
    for result in raw_results:
        if not isinstance(result, dict):
            continue
        ev = _finite_or_none(result.get("expected_value"))  # type: ignore[arg-type]
        pf = _finite_or_none(result.get("profit_factor"))  # type: ignore[arg-type]
        mdd = _finite_or_none(result.get("max_drawdown"))  # type: ignore[arg-type]
        participation = _finite_or_none(result.get("participation_rate"))  # type: ignore[arg-type]
        trade_count = int(result.get("trade_count") or 0)
        entry_edge_wins_vs_bof = (
            result.get("label") != "BOF"
            and ev is not None
            and bof_ev is not None
            and ev > bof_ev
            and pf is not None
            and pf >= max(1.0, bof_pf or 0.0)
        )
        sample_density_ok = trade_count >= NORMANDY_CANDIDATE_MIN_TRADES or (
            participation is not None and participation >= participation_threshold
        )
        n2_candidate = bool(entry_edge_wins_vs_bof and sample_density_ok)
        scorecard.append(
            {
                "label": result["label"],
                "patterns": result.get("patterns") or [],
                "pattern_families": result.get("pattern_families") or [],
                "trade_count": trade_count,
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "expected_value_delta_vs_bof": None if ev is None or bof_ev is None else ev - bof_ev,
                "profit_factor_delta_vs_bof": None if pf is None or bof_pf is None else pf - bof_pf,
                "max_drawdown_delta_vs_bof": None if mdd is None or bof_mdd is None else mdd - bof_mdd,
                "participation_delta_vs_bof": (
                    None if participation is None or bof_participation is None else participation - bof_participation
                ),
                "entry_edge_wins_vs_bof": entry_edge_wins_vs_bof,
                "sample_density_ok": sample_density_ok,
                "n2_candidate": n2_candidate,
            }
        )
    return _sort_scorecard_rows(scorecard)


def _family_vote(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    votes: dict[str, int] = {}
    for row in rows:
        families = row.get("pattern_families")
        if not isinstance(families, list):
            continue
        for family in dict.fromkeys(str(item) for item in families):
            votes[family] = votes.get(family, 0) + 1
    ranked = sorted(votes.items(), key=lambda item: (-item[1], item[0]))
    return [{"family": family, "vote_count": count} for family, count in ranked]


def build_normandy_pas_alpha_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    scorecard = _build_digest_scorecard(matrix_payload)
    non_bof_rows = [row for row in scorecard if row["label"] != "BOF"]
    n2_candidates = [row for row in scorecard if bool(row["n2_candidate"])]
    family_vote_source = n2_candidates if n2_candidates else non_bof_rows[:1]
    family_votes = _family_vote(family_vote_source)
    provenance_leader = (
        n2_candidates[0]["label"] if n2_candidates else (non_bof_rows[0]["label"] if non_bof_rows else "BOF")
    )
    control_labels = [row["label"] for row in scorecard if row["label"] == "BOF" or not bool(row["n2_candidate"])]

    if n2_candidates:
        candidate_labels = ", ".join(str(row["label"]) for row in n2_candidates)
        top_family = family_votes[0]["family"] if family_votes else "UNKNOWN"
        conclusion = (
            f"{candidate_labels} 在最简执行口径下相对 BOF 给出更强 raw entry edge，"
            f"当前优先按 {top_family} family 进入 N2 / exit decomposition。"
        )
    else:
        observation_label = provenance_leader
        conclusion = (
            f"当前没有非 BOF shape 同时满足 entry edge 与样本密度门槛；"
            f"{observation_label} 先保留为观测领先者，BOF 继续作为 N2 前的固定对照。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "start": matrix_payload.get("start"),
        "end": matrix_payload.get("end"),
        "dtt_variant": matrix_payload.get("dtt_variant"),
        "candidate_rule": {
            "expected_value_must_beat_bof": True,
            "profit_factor_floor": "max(1.0, BOF)",
            "min_trade_count": NORMANDY_CANDIDATE_MIN_TRADES,
            "min_participation_rate": NORMANDY_CANDIDATE_MIN_PARTICIPATION,
            "relative_participation_floor_vs_bof": 0.5,
        },
        "scorecard": scorecard,
        "provenance_leader": provenance_leader,
        "likely_raw_alpha_family_votes": family_votes,
        "n2_candidates": [row["label"] for row in n2_candidates],
        "control_labels": control_labels,
        "conclusion": conclusion,
    }


def read_normandy_pas_alpha_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_pas_alpha_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
