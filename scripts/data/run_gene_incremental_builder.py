from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.data.store import Store
from src.selector.gene_incremental import (
    compute_gene_incremental_for_codes,
    refresh_gene_market_surfaces,
    run_gene_incremental_builder,
    scan_gene_dirty_windows,
)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Gene incremental builder for dirty codes and lifespan surfaces")
    parser.add_argument("--start", required=True, help="Dirty window start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Dirty window end date (YYYY-MM-DD)")
    parser.add_argument("--db-path", default=None, help="DuckDB path override")
    parser.add_argument(
        "--mode",
        choices=["dirty-scan", "incremental", "market-only"],
        default="incremental",
        help="dirty-scan only, incremental rebuild, or market-only refresh",
    )
    parser.add_argument(
        "--codes",
        default="",
        help="Optional comma-separated stock codes; default scans all dirty codes in the window",
    )
    parser.add_argument(
        "--skip-market",
        action="store_true",
        help="Do not refresh market mirror/surface when mode=incremental",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON summary path; default writes to G:\\EmotionQuant-temp\\gene\\incremental\\",
    )
    return parser


def _default_output_path(db_path: Path, mode: str, start: date, end: date) -> Path:
    drive_root = Path(db_path.anchor) if db_path.anchor else Path("G:\\")
    return (
        drive_root
        / "EmotionQuant-temp"
        / "gene"
        / "incremental"
        / f"gene_incremental_{mode}_{start:%Y%m%d}_{end:%Y%m%d}.json"
    )


def _normalize_codes(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings()
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    codes = _normalize_codes(args.codes)
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else _default_output_path(db_path, args.mode.replace("-", "_"), start, end)
    )

    store = Store(db_path)
    try:
        if args.mode == "dirty-scan":
            payload = {
                "mode": "dirty-scan",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "dirty_windows": [window.__dict__ for window in scan_gene_dirty_windows(store, start=start, end=end, codes=codes)],
            }
        elif args.mode == "market-only":
            written = refresh_gene_market_surfaces(store, calc_date=end)
            payload = {
                "mode": "market-only",
                "calc_date": end.isoformat(),
                "written_rows": int(written),
            }
        elif codes:
            payload = compute_gene_incremental_for_codes(
                store,
                codes=codes,
                start=start,
                end=end,
                refresh_market=not args.skip_market,
                market_calc_date=end,
            )
        else:
            payload = run_gene_incremental_builder(
                store,
                start=start,
                end=end,
                refresh_market=not args.skip_market,
            )
    finally:
        store.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"gene_incremental_summary={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
