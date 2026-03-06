from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import prepare_working_db
from src.config import get_settings
from src.data.store import Store
from src.selector.audit import summarize_selector_distributions, write_selector_distribution_evidence


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Week2 MSS/IRS distribution on real selector outputs")
    parser.add_argument("--start", required=True, help="Audit start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Audit end date (YYYY-MM-DD)")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses a temp copy instead of reading the live DB",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-YYYYMMDD.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    source_db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else REPO_ROOT / ".tmp" / "audit" / f"selector-distribution-{date.today():%Y%m%d}.duckdb"
    )
    db_path = prepare_working_db(source_db_path, working_db_path)
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT
        / "docs"
        / "spec"
        / "v0.01"
        / "evidence"
        / f"v0.01-selector-distribution-audit-{date.today():%Y%m%d}.json"
    )

    store = Store(db_path)
    try:
        payload = summarize_selector_distributions(store, start, end)
        payload["source_db_path"] = str(source_db_path)
        payload["db_path"] = str(db_path)
    finally:
        store.close()

    path = write_selector_distribution_evidence(output_path, payload)
    print(f"selector_distribution_audit={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
