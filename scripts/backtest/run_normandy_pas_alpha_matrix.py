from __future__ import annotations

# Normandy / N1-A matrix:
# 1. 仓库根目录只放代码/文档/配置；working DB 与运行缓存固定留在 TEMP_PATH / G:\EmotionQuant-temp。
# 2. 执行源库默认走 DATA_PATH/emotionquant.duckdb；若窗口缺数据，先按 RAW_DB_PATH / 本地旧库优先补齐，
#    再按 TUSHARE_PRIMARY_* -> TUSHARE_FALLBACK_* 兜底。
# 3. 本脚本固定使用 pattern-only DTT + 无 MSS gate + 无 IRS 硬过滤，并继续遵守 T+1 Open 执行语义。
# 4. 当前首轮矩阵只比较五单形态 `BOF/BPB/PB/TST/CPB` 与总集合 `YTC5_ANY`，
#    不把 `BOF+PB / PB+CPB` 这类组合场景混进 pattern taxonomy 证明。

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_pas_alpha import (
    NORMANDY_PAS_ALPHA_DTT_VARIANT,
    run_normandy_pas_alpha_matrix,
    write_normandy_pas_alpha_evidence,
)
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Normandy N1 PAS alpha first-round matrix backtest")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument(
        "--dtt-variant",
        default=NORMANDY_PAS_ALPHA_DTT_VARIANT,
        help="Controlled minimal DTT variant; default is v0_01_dtt_pattern_only",
    )
    parser.add_argument("--dtt-top-n", type=int, default=None, help="Optional DTT_TOP_N override")
    parser.add_argument("--max-positions", type=int, default=None, help="Optional MAX_POSITIONS override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<run_id>__pas_alpha_matrix.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    dtt_variant = sanitize_label(args.dtt_variant or NORMANDY_PAS_ALPHA_DTT_VARIANT)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"normandy-pas-alpha-matrix-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    summary_run_id = build_run_id(
        scope="normandy_pas_alpha_matrix",
        mode="dtt",
        variant=dtt_variant,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "pas_alpha_matrix", "json")
    )

    payload = run_normandy_pas_alpha_matrix(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        dtt_variant=dtt_variant,
        initial_cash=args.cash,
        rebuild_l3=not args.skip_rebuild_l3,
        working_db_path=working_db_path,
        artifact_root=cfg.resolved_temp_path / "artifacts",
        dtt_top_n=args.dtt_top_n,
        max_positions=args.max_positions,
    )
    payload["summary_run_id"] = summary_run_id
    path = write_normandy_pas_alpha_evidence(output_path, payload)
    print(f"normandy_pas_alpha_matrix={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
