from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_fb_refinement import (
    NORMANDY_FB_REFINEMENT_DTT_VARIANT,
    run_normandy_fb_refinement_matrix,
)
from src.backtest.normandy_volman_alpha import (
    read_normandy_volman_alpha_payload,
    write_normandy_volman_alpha_evidence,
)
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _resolve_latest_matrix_path(output_root: Path) -> Path:
    candidates = sorted(
        output_root.glob("*__volman_alpha_matrix.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No volman_alpha_matrix evidence found under {output_root}")
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Normandy FB cleaner vs boundary refinement matrix")
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Optional upstream Volman matrix path; default resolves the latest normandy/03-execution/evidence/*__volman_alpha_matrix.json",
    )
    parser.add_argument("--start", default=None, help="Backtest start date override (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="Backtest end date override (YYYY-MM-DD)")
    parser.add_argument(
        "--dtt-variant",
        default=None,
        help="Controlled minimal DTT variant override; default inherits from upstream Volman matrix",
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
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<run_id>__fb_refinement_matrix.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    matrix_path = (
        Path(args.matrix_path).expanduser().resolve()
        if args.matrix_path
        else _resolve_latest_matrix_path(output_root)
    )
    upstream_matrix = read_normandy_volman_alpha_payload(matrix_path)
    start = _parse_date(args.start or str(upstream_matrix["start"]))
    end = _parse_date(args.end or str(upstream_matrix["end"]))
    dtt_variant = sanitize_label(
        args.dtt_variant or str(upstream_matrix.get("dtt_variant") or NORMANDY_FB_REFINEMENT_DTT_VARIANT)
    )
    db_path = (
        Path(args.db_path).expanduser().resolve()
        if args.db_path
        else Path(str(upstream_matrix.get("source_db_path") or upstream_matrix.get("db_path") or cfg.db_path))
        .expanduser()
        .resolve()
    )
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"normandy-fb-refinement-{date.today():%Y%m%d}.duckdb"
    )

    summary_run_id = build_run_id(
        scope="normandy_fb_refinement_matrix",
        mode="dtt",
        variant=dtt_variant,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "fb_refinement_matrix", "json")
    )

    payload = run_normandy_fb_refinement_matrix(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        dtt_variant=dtt_variant,
        dtt_top_n=args.dtt_top_n,
        max_positions=args.max_positions,
        working_db_path=working_db_path,
        artifact_root=cfg.resolved_temp_path / "artifacts",
    )
    payload["summary_run_id"] = summary_run_id
    payload["upstream_matrix_path"] = str(matrix_path)
    path = write_normandy_volman_alpha_evidence(output_path, payload)
    print(f"normandy_fb_refinement_matrix={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
