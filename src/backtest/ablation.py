from __future__ import annotations

import json
import math
import shutil
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run
from src.strategy.ranker import (
    MSS_OVERLAY_DTT_VARIANT,
    apply_dtt_variant_runtime,
    resolve_dtt_variant,
)


@dataclass(frozen=True)
class AblationScenario:
    label: str
    pipeline_mode: str
    dtt_variant: str
    enable_mss_gate: bool
    enable_irs_filter: bool
    mss_variant: str
    mss_gate_mode: str
    mss_bullish_threshold: float
    mss_bearish_threshold: float
    irs_top_n: int


@dataclass(frozen=True)
class AblationRunResult:
    label: str
    pipeline_mode: str
    dtt_variant: str
    enable_mss_gate: bool
    enable_irs_filter: bool
    mss_variant: str
    mss_gate_mode: str
    mss_bullish_threshold: float
    mss_bearish_threshold: float
    irs_top_n: int
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


def build_selector_ablation_scenarios(config: Settings) -> list[AblationScenario]:
    requested_variant = config.dtt_variant_normalized
    mss_variant = (
        requested_variant
        if resolve_dtt_variant(requested_variant).carries_mss_overlay
        else MSS_OVERLAY_DTT_VARIANT
    )
    # Phase 4.1 允许把“最后一个 MSS 场景”切到当前唯一整改候选，
    # 无论是 carryover_buffer 还是 size_only_overlay，其余 legacy / pattern / irs 场景都保持固定，
    # 避免矩阵本身再发散成新 sweep。
    # 主线矩阵固定为 1 组 legacy 对照 + 3 组 DTT，不再沿用 week2 的阈值扫参模型。
    return [
        AblationScenario(
            label="legacy_bof_baseline",
            pipeline_mode="legacy",
            dtt_variant="legacy_bof_baseline",
            enable_mss_gate=True,
            enable_irs_filter=True,
            mss_variant=config.mss_variant,
            mss_gate_mode=config.mss_gate_mode,
            mss_bullish_threshold=config.mss_bullish_threshold,
            mss_bearish_threshold=config.mss_bearish_threshold,
            irs_top_n=config.irs_top_n,
        ),
        AblationScenario(
            label="v0_01_dtt_pattern_only",
            pipeline_mode="dtt",
            dtt_variant="v0_01_dtt_pattern_only",
            enable_mss_gate=False,
            enable_irs_filter=False,
            mss_variant=config.mss_variant,
            mss_gate_mode=config.mss_gate_mode,
            mss_bullish_threshold=config.mss_bullish_threshold,
            mss_bearish_threshold=config.mss_bearish_threshold,
            irs_top_n=config.irs_top_n,
        ),
        AblationScenario(
            label="v0_01_dtt_pattern_plus_irs_score",
            pipeline_mode="dtt",
            dtt_variant="v0_01_dtt_pattern_plus_irs_score",
            enable_mss_gate=False,
            enable_irs_filter=False,
            mss_variant=config.mss_variant,
            mss_gate_mode=config.mss_gate_mode,
            mss_bullish_threshold=config.mss_bullish_threshold,
            mss_bearish_threshold=config.mss_bearish_threshold,
            irs_top_n=config.irs_top_n,
        ),
        AblationScenario(
            label=mss_variant,
            pipeline_mode="dtt",
            dtt_variant=mss_variant,
            enable_mss_gate=False,
            enable_irs_filter=False,
            mss_variant=config.mss_variant,
            mss_gate_mode=config.mss_gate_mode,
            mss_bullish_threshold=config.mss_bullish_threshold,
            mss_bearish_threshold=config.mss_bearish_threshold,
            irs_top_n=config.irs_top_n,
        ),
    ]


RUN_SCOPED_RUNTIME_TABLES = (
    "broker_order_lifecycle_trace_exp",
    "mss_risk_overlay_trace_exp",
    "irs_industry_trace_exp",
    "pas_trigger_trace_exp",
    "selector_candidate_trace_exp",
    "l3_signal_rank_exp",
)

GLOBAL_RUNTIME_TABLES = (
    "l4_pattern_stats",
    "l4_daily_report",
    "l4_trades",
    "l4_orders",
    "l4_stock_trust",
    "l3_signals",
)


def clear_runtime_tables(store: Store, run_id: str | None = None) -> None:
    for table in GLOBAL_RUNTIME_TABLES:
        store.conn.execute(f"DELETE FROM {table}")

    if run_id is None:
        for table in RUN_SCOPED_RUNTIME_TABLES:
            store.conn.execute(f"DELETE FROM {table}")
        return

    for table in RUN_SCOPED_RUNTIME_TABLES:
        store.conn.execute(f"DELETE FROM {table} WHERE run_id = ?", (run_id,))


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _snapshot_ablation_metrics(store: Store, start: date, end: date) -> tuple[int, int, int]:
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


def _normalize_environment_breakdown(
    payload: dict[str, dict[str, float | int | None]]
) -> dict[str, dict[str, float | None]]:
    normalized: dict[str, dict[str, float | None]] = {}
    for env, metrics in payload.items():
        normalized[env] = {key: _finite_or_none(value) for key, value in metrics.items()}
    return normalized


def prepare_working_db(source_db: str | Path, working_db: str | Path) -> Path:
    source = Path(source_db).expanduser().resolve()
    target = Path(working_db).expanduser().resolve()
    # 当前主线强制采用“正式执行库 + TEMP working copy”模式：
    # - source 应该是 DATA_PATH 下的长期库
    # - target 应该是 TEMP_PATH/backtest 下的短生命周期副本
    # 这样能保持正式库稳定，也避免把实验副本误写到仓库目录。
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.copy2(source, target)
    wal_source = source.with_suffix(source.suffix + ".wal")
    wal_target = target.with_suffix(target.suffix + ".wal")
    if wal_source.exists():
        shutil.copy2(wal_source, wal_target)
    elif wal_target.exists():
        wal_target.unlink()
    return target


def run_selector_ablation(
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    patterns: list[str] | None = None,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict:
    source_db = Path(db_path).expanduser().resolve()
    db_file = prepare_working_db(source_db, working_db_path) if working_db_path is not None else source_db
    scenarios = build_selector_ablation_scenarios(config)
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    artifact_root_path.mkdir(parents=True, exist_ok=True)

    if rebuild_l3:
        build_store = Store(db_file)
        try:
            build_layers(build_store, config, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    runs: list[AblationRunResult] = []
    for scenario in scenarios:
        cfg = config.model_copy(deep=True)
        cfg.pipeline_mode = scenario.pipeline_mode
        cfg.enable_dtt_mode = scenario.pipeline_mode == "dtt"
        cfg.enable_mss_gate = scenario.enable_mss_gate
        cfg.enable_irs_filter = scenario.enable_irs_filter
        cfg.mss_variant = scenario.mss_variant
        cfg.mss_gate_mode = scenario.mss_gate_mode
        cfg.mss_bullish_threshold = scenario.mss_bullish_threshold
        cfg.mss_bearish_threshold = scenario.mss_bearish_threshold
        cfg.irs_top_n = scenario.irs_top_n
        if cfg.use_dtt_pipeline:
            # DTT label 现在也可能携带 Broker shrink 语义别名，
            # 必须在这里统一重放，避免 matrix / replay / attribution 各走各的 env 口径。
            cfg = apply_dtt_variant_runtime(cfg, scenario.dtt_variant)
        else:
            cfg.dtt_variant = scenario.dtt_variant

        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope="matrix",
            modules=["backtest", "selector", "strategy", "broker", "report"],
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

        try:
            # 每个 scenario 独立生成 run_id，便于把 sidecar 和证据文件一一追回到矩阵项。
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
            signals_count, ranked_signals_count, trades_count = _snapshot_ablation_metrics(snap, start, end)
        finally:
            snap.close()

        runs.append(
            AblationRunResult(
                label=scenario.label,
                pipeline_mode=scenario.pipeline_mode,
                dtt_variant=scenario.dtt_variant,
                enable_mss_gate=scenario.enable_mss_gate,
                enable_irs_filter=scenario.enable_irs_filter,
                mss_variant=scenario.mss_variant,
                mss_gate_mode=scenario.mss_gate_mode,
                mss_bullish_threshold=scenario.mss_bullish_threshold,
                mss_bearish_threshold=scenario.mss_bearish_threshold,
                irs_top_n=scenario.irs_top_n,
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

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns or ["bof"],
        "initial_cash": float(initial_cash if initial_cash is not None else config.backtest_initial_cash),
        "runs": [asdict(run) for run in runs],
    }


def write_ablation_evidence(output_path: str | Path, payload: dict) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
