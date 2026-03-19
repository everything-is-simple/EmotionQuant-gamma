from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.data.store import Store
from src.report.market_lifespan_report import (
    build_market_lifespan_report_payload,
    load_market_lifespan_surface_frame,
    write_market_lifespan_report_bundle,
)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _default_report_root(config_db_path: Path, calc_date: date) -> Path:
    drive_root = Path(config_db_path.anchor) if config_db_path.anchor else Path("G:\\")
    return drive_root / "EmotionQuant-report" / "gene_market_lifespan" / calc_date.strftime("%Y%m%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build formal market lifespan framework report outputs")
    parser.add_argument("--db-path", default=None, help="DuckDB path override")
    parser.add_argument("--calc-date", default=None, help="Calculation date (YYYY-MM-DD); default latest")
    parser.add_argument("--entity-scope", default="MARKET", help="Entity scope; default MARKET")
    parser.add_argument("--entity-code", default=None, help="Entity code; default first market entity on calc_date")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output directory; default G:\\EmotionQuant-report\\gene_market_lifespan\\<calc_date>",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings()
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path

    store = Store(db_path)
    try:
        calc_date, entity_code, frame = load_market_lifespan_surface_frame(
            store,
            calc_date=_parse_date(args.calc_date),
            entity_scope=str(args.entity_scope).upper(),
            entity_code=args.entity_code,
        )
        payload = build_market_lifespan_report_payload(
            frame,
            calc_date=calc_date,
            entity_scope=str(args.entity_scope).upper(),
            entity_code=entity_code,
        )
    finally:
        store.close()

    output_root = (
        Path(args.output_root).expanduser().resolve()
        if args.output_root
        else _default_report_root(db_path, calc_date)
    )
    outputs = write_market_lifespan_report_bundle(output_root, payload)
    for label, path in outputs.items():
        print(f"{label}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
