from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import run_selector_ablation, write_ablation_evidence
from src.config import get_settings


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Week2 Selector/Strategy ablation scenarios")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; when set the ablation runs on the copy instead of the live DB",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01/evidence/v0.01-selector-ablation-YYYYMMDD.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else REPO_ROOT / ".tmp" / "backtest" / f"selector-ablation-{date.today():%Y%m%d}.duckdb"
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT / "docs" / "spec" / "v0.01" / "evidence" / f"v0.01-selector-ablation-{date.today():%Y%m%d}.json"
    )

    payload = run_selector_ablation(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        patterns=patterns or ["bof"],
        initial_cash=args.cash,
        rebuild_l3=not args.skip_rebuild_l3,
        working_db_path=working_db_path,
    )
    path = write_ablation_evidence(output_path, payload)
    print(f"ablation_evidence={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
