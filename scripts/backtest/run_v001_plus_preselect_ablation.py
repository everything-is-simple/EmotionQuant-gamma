from __future__ import annotations

# Preselect ablation:
# - 这里固定只扫当前 pattern_* DTT 主线，不再沿用旧 bof_* variant 命名。
# - 源库读 DATA_PATH，工作副本写 TEMP_PATH；若源库窗口缺数据，补数顺序仍遵守旧库优先和双 TuShare 兜底。

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.engine import run_backtest
from src.config import get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import build_artifact_name, build_run_id, finish_run, start_run


@dataclass(frozen=True)
class PreselectScenario:
    label: str
    dtt_variant: str
    candidate_top_n: int
    preselect_score_mode: str


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _parse_int_list(text: str) -> list[int]:
    values = [int(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise ValueError("至少需要 1 个 candidate_top_n。")
    return values


def _parse_mode_list(text: str) -> list[str]:
    values = [item.strip().lower() for item in text.split(",") if item.strip()]
    if not values:
        raise ValueError("至少需要 1 个 preselect_score_mode。")
    return values


def _clear_runtime_tables(store: Store) -> None:
    # 每个场景都从同一份工作副本快照起跑，避免上一个场景的 L3/L4 结果串到下一个场景。
    for table in (
        "l4_pattern_stats",
        "l4_daily_report",
        "l4_trades",
        "l4_orders",
        "l4_stock_trust",
        "l3_signals",
        "l3_signal_rank_exp",
    ):
        store.conn.execute(f"DELETE FROM {table}")


def _prepare_working_db(source_db: Path, target_db: Path) -> Path:
    target_db.parent.mkdir(parents=True, exist_ok=True)
    if target_db.exists():
        target_db.unlink()
    shutil.copy2(source_db, target_db)
    wal_source = source_db.with_suffix(source_db.suffix + ".wal")
    wal_target = target_db.with_suffix(target_db.suffix + ".wal")
    if wal_source.exists():
        shutil.copy2(wal_source, wal_target)
    elif wal_target.exists():
        wal_target.unlink()
    return target_db


def _build_scenarios(candidate_top_ns: list[int], modes: list[str]) -> list[PreselectScenario]:
    # 这里固定扫两条 DTT 主线：纯 BOF 与 BOF+IRS，专门看初选是否改变后续交易结果。
    scenarios: list[PreselectScenario] = []
    variants = ["v0_01_dtt_pattern_only", "v0_01_dtt_pattern_plus_irs_score"]
    for variant in variants:
        for top_n in candidate_top_ns:
            for mode in modes:
                scenarios.append(
                    PreselectScenario(
                        label=f"{variant}__top{top_n}__{mode}",
                        dtt_variant=variant,
                        candidate_top_n=top_n,
                        preselect_score_mode=mode,
                    )
                )
    return scenarios


def _snapshot_metrics(store: Store, start: date, end: date) -> dict[str, int]:
    return {
        "signals_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
        "ranked_signals_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_signal_rank_exp WHERE signal_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
        "trades_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l4_trades WHERE execute_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run v0.01-plus preselect ablation matrix")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--candidate-top-ns", default="50,100,150", help="Comma-separated candidate_top_n values")
    parser.add_argument(
        "--preselect-modes",
        default="amount_plus_volume_ratio,amount_only,volume_ratio_only",
        help="Comma-separated preselect score modes",
    )
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__preselect_ablation.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
    candidate_top_ns = _parse_int_list(args.candidate_top_ns)
    preselect_modes = _parse_mode_list(args.preselect_modes)

    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"preselect-ablation-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    output_root.mkdir(parents=True, exist_ok=True)
    summary_run_id = build_run_id(
        scope="preselect_ablation",
        mode="dtt",
        variant="selector_preselect_matrix",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "preselect_ablation", "json")
    )

    db_file = _prepare_working_db(source_db, working_db)
    if not args.skip_rebuild_l3:
        # L3 与初选消融无关，只需在工作副本上统一重建一次即可。
        build_store = Store(db_file)
        try:
            build_layers(build_store, cfg, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    scenarios = _build_scenarios(candidate_top_ns, preselect_modes)
    results: list[dict[str, object]] = []
    for scenario in scenarios:
        clear_store = Store(db_file)
        try:
            _clear_runtime_tables(clear_store)
        finally:
            clear_store.close()

        run_cfg = cfg.model_copy(deep=True)
        run_cfg.pipeline_mode = "dtt"
        run_cfg.enable_dtt_mode = True
        run_cfg.dtt_variant = scenario.dtt_variant
        run_cfg.candidate_top_n = scenario.candidate_top_n
        run_cfg.preselect_score_mode = scenario.preselect_score_mode

        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope="preselect_ablation",
            modules=["backtest", "selector", "strategy", "broker", "report"],
            config=run_cfg,
            runtime_env="script",
            artifact_root=str(cfg.resolved_temp_path / "artifacts"),
            start=start,
            end=end,
        )
        meta_store.close()

        try:
            result = run_backtest(
                db_path=db_file,
                config=run_cfg,
                start=start,
                end=end,
                patterns=patterns or ["bof"],
                initial_cash=args.cash,
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

        snap_store = Store(db_file)
        try:
            snapshot = _snapshot_metrics(snap_store, start, end)
        finally:
            snap_store.close()

        results.append(
            {
                **asdict(scenario),
                "run_id": run.run_id,
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
                "signals_count": snapshot["signals_count"],
                "ranked_signals_count": snapshot["ranked_signals_count"],
                "trades_count": snapshot["trades_count"],
                "environment_breakdown": result.environment_breakdown,
            }
        )

    payload = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns or ["bof"],
        "candidate_top_ns": candidate_top_ns,
        "preselect_modes": preselect_modes,
        "results": results,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"preselect_ablation={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
