from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.pas_ablation import compute_diff_days, summarize_introduced_rows
from src.config import Settings
from src.data.store import Store
from src.run_metadata import finish_run, start_run
from src.selector.irs import (
    IRS_FACTOR_MODE_FULL,
    IRS_FACTOR_MODE_LITE,
    IRS_FACTOR_MODE_RSRV,
    compute_irs,
    normalize_irs_factor_mode,
)


@dataclass(frozen=True)
class IrsAblationScenario:
    label: str
    factor_mode: str


@dataclass
class IrsAblationRunResult:
    label: str
    factor_mode: str
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
    industry_rank_diff_days_vs_lite: int = 0
    execution_diff_days_vs_lite: int = 0


def build_irs_ablation_scenarios() -> list[IrsAblationScenario]:
    return [
        IrsAblationScenario(label="IRS_LITE", factor_mode=IRS_FACTOR_MODE_LITE),
        IrsAblationScenario(label="IRS_RSRV", factor_mode=IRS_FACTOR_MODE_RSRV),
        IrsAblationScenario(label="IRS_RSRVRTBDGN", factor_mode=IRS_FACTOR_MODE_FULL),
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


def _snapshot_runtime_metrics(store: Store, start: date, end: date, run_id: str) -> tuple[int, int, int]:
    signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    ranked_signals_count = int(
        store.read_scalar(
            """
            SELECT COUNT(*)
            FROM l3_signal_rank_exp
            WHERE run_id = ?
              AND signal_date BETWEEN ? AND ?
            """,
            (run_id, start, end),
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


def _read_industry_rank_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT date, industry, rank, score
        FROM l3_irs_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY date ASC, rank ASC, industry ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["date"] = frame["date"].apply(_to_iso)
    return frame


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


def _build_scenario_config(base: Settings, dtt_variant: str) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = dtt_variant
    return cfg


def run_irs_ablation(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    dtt_variant: str,
    patterns: list[str] | None = None,
    initial_cash: float | None = None,
    skip_rebuild_irs: bool = False,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    factor_modes: list[str] | None = None,
    use_db_as_working_copy: bool = False,
) -> dict[str, object]:
    source_db = Path(db_path).expanduser().resolve()
    selected_modes = [normalize_irs_factor_mode(mode) for mode in (factor_modes or [])]
    scenarios = [
        scenario
        for scenario in build_irs_ablation_scenarios()
        if not selected_modes or scenario.factor_mode in selected_modes
    ]
    if skip_rebuild_irs and len(scenarios) != 1:
        raise ValueError("skip_rebuild_irs can only be used with a single IRS factor mode scenario")

    if use_db_as_working_copy:
        db_file = source_db
    else:
        # 默认优先在 working copy 上跑 ablation，避免把主库 runtime 表和实验 trace 搅在一起。
        db_file = prepare_working_db(source_db, working_db_path) if working_db_path is not None else source_db
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    artifact_root_path.mkdir(parents=True, exist_ok=True)

    runs: list[IrsAblationRunResult] = []
    industry_frames: dict[str, pd.DataFrame] = {}
    selected_rank_frames: dict[str, pd.DataFrame] = {}
    buy_execution_frames: dict[str, pd.DataFrame] = {}

    for scenario in scenarios:
        cfg = _build_scenario_config(config, dtt_variant)

        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope=f"irs_ablation_{scenario.label.lower()}",
            modules=["selector", "strategy", "broker", "backtest", "report"],
            config=cfg,
            runtime_env="script",
            artifact_root=str(artifact_root_path),
            start=start,
            end=end,
        )
        meta_store.close()

        clear_store = Store(db_file)
        try:
            clear_runtime_tables(clear_store, run_id=run.run_id)
        finally:
            clear_store.close()

        if not skip_rebuild_irs:
            irs_store = Store(db_file)
            try:
                # 每个 scenario 都重建对应 factor_mode 的 l3_irs_daily，
                # 否则多场景对比会变成“共用同一份 IRS 结果”的假证据。
                compute_irs(
                    irs_store,
                    start,
                    end,
                    min_industries_per_day=cfg.irs_min_industries_per_day,
                    rt_lookback_days=cfg.irs_rt_lookback_days,
                    top_rank_threshold=cfg.irs_top_rank_threshold,
                    factor_mode=scenario.factor_mode,
                    factor_weight_rs=cfg.irs_factor_weight_rs,
                    factor_weight_rv=cfg.irs_factor_weight_rv,
                    factor_weight_rt=cfg.irs_factor_weight_rt,
                    factor_weight_bd=cfg.irs_factor_weight_bd,
                    factor_weight_gn=cfg.irs_factor_weight_gn,
                )
            finally:
                irs_store.close()

        try:
            result = run_backtest(
                db_path=db_file,
                config=cfg,
                start=start,
                end=end,
                patterns=patterns,
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

        snap = Store(db_file)
        try:
            signals_count, ranked_signals_count, trades_count = _snapshot_runtime_metrics(
                snap, start, end, run.run_id
            )
            industry_frames[scenario.label] = _read_industry_rank_frame(snap, start, end)
            selected_rank_frames[scenario.label] = _read_selected_rank_frame(snap, run.run_id)
            buy_execution_frames[scenario.label] = _read_buy_execution_frame(snap, start, end)
        finally:
            snap.close()

        runs.append(
            IrsAblationRunResult(
                label=scenario.label,
                factor_mode=scenario.factor_mode,
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
            )
        )

    baseline_label = "IRS_LITE"
    baseline_present = baseline_label in industry_frames
    baseline_industry = industry_frames.get(baseline_label, pd.DataFrame())
    baseline_ranked = selected_rank_frames.get(baseline_label, pd.DataFrame())
    baseline_execution = buy_execution_frames.get(baseline_label, pd.DataFrame())

    top_industry_changes_vs_lite: dict[str, dict[str, object]] = {}
    baseline_top_ranked = (
        baseline_industry[baseline_industry["rank"] <= config.irs_top_n].copy()
        if not baseline_industry.empty
        else baseline_industry
    )
    for run in runs:
        if run.label == baseline_label:
            continue
        if not baseline_present:
            continue
        target_industry = industry_frames.get(run.label, pd.DataFrame())
        target_top_ranked = (
            target_industry[target_industry["rank"] <= config.irs_top_n].copy()
            if not target_industry.empty
            else target_industry
        )
        run.industry_rank_diff_days_vs_lite = compute_diff_days(
            baseline_industry,
            target_industry,
            date_col="date",
            key_cols=("industry", "rank"),
        )
        run.execution_diff_days_vs_lite = compute_diff_days(
            baseline_execution,
            buy_execution_frames.get(run.label, pd.DataFrame()),
            date_col="execute_date",
            key_cols=("code", "signal_id"),
        )
        top_industry_changes_vs_lite[run.label] = summarize_introduced_rows(
            baseline_top_ranked,
            target_top_ranked,
            date_col="date",
            columns=("industry", "rank"),
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dtt_variant": dtt_variant,
        "patterns": patterns or config.pas_effective_patterns,
        "initial_cash": float(initial_cash if initial_cash is not None else config.backtest_initial_cash),
        "skip_rebuild_irs": bool(skip_rebuild_irs),
        "runs": [asdict(run) for run in runs],
        "baseline_label": baseline_label if baseline_present else None,
        "top_industry_changes_vs_lite": top_industry_changes_vs_lite,
        "selected_signal_changes_vs_lite": {
            run.label: summarize_introduced_rows(
                baseline_ranked,
                selected_rank_frames.get(run.label, pd.DataFrame()),
                date_col="signal_date",
                columns=("code", "signal_id", "final_rank"),
            )
            for run in runs
            if run.label != baseline_label and baseline_present
        },
    }


def write_irs_ablation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
