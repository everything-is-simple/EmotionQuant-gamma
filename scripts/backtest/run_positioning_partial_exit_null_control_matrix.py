from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.partial_exit_null_control import (
    POSITIONING_PARTIAL_EXIT_NULL_CONTROL_SCOPE,
    build_partial_exit_null_control_scenarios,
    run_partial_exit_null_control_matrix,
    write_partial_exit_null_control_evidence,
)
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Positioning P7 partial-exit null control matrix")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_* tables in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Output JSON path; default positioning/03-execution/evidence/"
            "<run_id>__partial_exit_null_control_matrix.json"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    initial_cash = float(args.cash if args.cash is not None else cfg.backtest_initial_cash)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"positioning-partial-exit-null-control-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "positioning" / "03-execution" / "evidence"
    scenarios = build_partial_exit_null_control_scenarios(cfg, initial_cash=initial_cash)
    variant_slug = sanitize_label("bof_control_no_irs_no_mss_partial_exit")
    summary_run_id = build_run_id(
        scope=POSITIONING_PARTIAL_EXIT_NULL_CONTROL_SCOPE,
        mode="dtt",
        variant=variant_slug,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "partial_exit_null_control_matrix", "json")
    )

    payload = run_partial_exit_null_control_matrix(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        initial_cash=initial_cash,
        rebuild_l3=not args.skip_rebuild_l3,
        working_db_path=working_db_path,
        artifact_root=cfg.resolved_temp_path / "artifacts",
    )
    payload["summary_run_id"] = summary_run_id
    payload["scenario_labels"] = [scenario.label for scenario in scenarios]
    path = write_partial_exit_null_control_evidence(output_path, payload)
    print(f"positioning_partial_exit_null_control_matrix={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
