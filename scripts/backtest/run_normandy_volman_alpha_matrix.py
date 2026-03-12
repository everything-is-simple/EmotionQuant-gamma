from __future__ import annotations

# Normandy / N1.5-B matrix:
# 1. 当前第一批固定对象只有 `BOF_CONTROL / RB_FAKE / SB / FB`，不把 `IRB / DD / BB / ARB` 提前升格。
# 2. 默认走真实 matrix 回放；`--scaffold-only` 只作为契约快照导出入口保留。
# 3. 仓库根目录只放代码/文档/配置；working DB 与运行缓存固定留在 TEMP_PATH / G:\EmotionQuant-temp。

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_volman_alpha import (
    NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
    run_normandy_volman_alpha_matrix,
    write_normandy_volman_alpha_evidence,
)
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Normandy N1.5 Volman second-alpha matrix backtest")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument(
        "--dtt-variant",
        default=NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
        help="Controlled minimal DTT variant; default is v0_01_dtt_pattern_only",
    )
    parser.add_argument("--dtt-top-n", type=int, default=None, help="Optional DTT_TOP_N override")
    parser.add_argument("--max-positions", type=int, default=None, help="Optional MAX_POSITIONS override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest working copy",
    )
    parser.add_argument(
        "--scaffold-only",
        action="store_true",
        help="Emit detector-contract scaffold JSON instead of attempting a real matrix run",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<run_id>__volman_alpha_matrix.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    dtt_variant = sanitize_label(args.dtt_variant or NORMANDY_VOLMAN_ALPHA_DTT_VARIANT)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"normandy-volman-alpha-matrix-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    summary_run_id = build_run_id(
        scope="normandy_volman_alpha_matrix",
        mode="dtt",
        variant=dtt_variant,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "volman_alpha_matrix", "json")
    )

    try:
        payload = run_normandy_volman_alpha_matrix(
            db_path=db_path,
            config=cfg,
            start=start,
            end=end,
            dtt_variant=dtt_variant,
            dtt_top_n=args.dtt_top_n,
            max_positions=args.max_positions,
            working_db_path=working_db_path,
            artifact_root=cfg.resolved_temp_path / "artifacts",
            scaffold_only=args.scaffold_only,
        )
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload["summary_run_id"] = summary_run_id
    path = write_normandy_volman_alpha_evidence(output_path, payload)
    print(f"normandy_volman_alpha_matrix={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
