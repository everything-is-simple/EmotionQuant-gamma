from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from time import perf_counter

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.selector.gene_incremental import scan_gene_dirty_windows


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a formal daily-mainline smoke for Gene incremental build and emit benchmark summaries."
    )
    parser.add_argument("--start", default=None, help="Smoke window start date (YYYY-MM-DD); default=end")
    parser.add_argument("--end", default=None, help="Smoke window end date (YYYY-MM-DD); default=max L2 date")
    parser.add_argument("--db-path", default=None, help="DuckDB path override")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory override; default writes to G:\\EmotionQuant-temp\\gene\\incremental\\smoke\\",
    )
    parser.add_argument(
        "--dirty-sample-limit",
        type=int,
        default=20,
        help="How many dirty windows to keep inline in the summary payload",
    )
    return parser


def _default_output_dir(db_path: Path) -> Path:
    drive_root = Path(db_path.anchor) if db_path.anchor else Path("G:\\")
    return drive_root / "EmotionQuant-temp" / "gene" / "incremental" / "smoke"


def _resolve_window(store: Store, start_arg: str | None, end_arg: str | None) -> tuple[date, date]:
    end = _parse_date(end_arg)
    if end is None:
        end = store.get_max_date("l2_stock_adj_daily")
    if end is None:
        raise RuntimeError("Cannot resolve smoke end date from l2_stock_adj_daily.")
    start = _parse_date(start_arg) or end
    if start > end:
        raise ValueError("Smoke window start cannot be after end.")
    return start, end


def _calc_date_count(store: Store, table: str, calc_date: date) -> int:
    return int(store.read_scalar(f"SELECT COUNT(*) FROM {table} WHERE calc_date = ?", (calc_date,)) or 0)


def _conditioning_sample_count(store: Store, calc_date: date) -> int:
    return int(
        store.read_scalar(
            """
            SELECT COUNT(*)
            FROM l3_gene_conditioning_sample
            WHERE date <= ?
            """,
            (calc_date,),
        )
        or 0
    )


def _collect_table_snapshot(store: Store, calc_date: date) -> dict[str, object]:
    tables = {
        "l3_stock_gene": _calc_date_count(store, "l3_stock_gene", calc_date),
        "l3_stock_lifespan_surface": _calc_date_count(store, "l3_stock_lifespan_surface", calc_date),
        "l3_gene_factor_eval": _calc_date_count(store, "l3_gene_factor_eval", calc_date),
        "l3_gene_distribution_eval": _calc_date_count(store, "l3_gene_distribution_eval", calc_date),
        "l3_gene_validation_eval": _calc_date_count(store, "l3_gene_validation_eval", calc_date),
        "l3_gene_mirror": _calc_date_count(store, "l3_gene_mirror", calc_date),
        "l3_gene_market_lifespan_surface": _calc_date_count(store, "l3_gene_market_lifespan_surface", calc_date),
        "l3_gene_conditioning_eval": _calc_date_count(store, "l3_gene_conditioning_eval", calc_date),
        "l3_gene_conditioning_sample_leq_calc_date": _conditioning_sample_count(store, calc_date),
    }
    max_dates = {
        "l2_stock_adj_daily": str(store.get_max_date("l2_stock_adj_daily")),
        "l3_stock_gene": str(store.get_max_date("l3_stock_gene", date_col="calc_date")),
        "l3_gene_conditioning_eval": str(store.get_max_date("l3_gene_conditioning_eval", date_col="calc_date")),
    }
    return {
        "counts": tables,
        "max_dates": max_dates,
    }


def _delta_counts(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {key: int(after.get(key, 0) - before.get(key, 0)) for key in keys}


def _build_markdown_summary(payload: dict[str, object]) -> str:
    before_counts = payload["before"]["counts"]
    after_counts = payload["after"]["counts"]
    delta_counts = payload["delta"]["counts"]
    dirty_windows = payload["dirty_windows_sample"]
    lines = [
        "# Gene Incremental Daily Smoke",
        "",
        f"- Executed at: `{payload['executed_at']}`",
        f"- DB path: `{payload['db_path']}`",
        f"- Window: `{payload['start']}` -> `{payload['end']}`",
        f"- Dirty codes: `{payload['dirty_code_count']}`",
        f"- L3 build written rows: `{payload['build_written_rows']}`",
        "",
        "## Timings",
        "",
        f"- Dirty scan: `{payload['timings']['dirty_scan_seconds']:.3f}s`",
        f"- Mainline build_l3: `{payload['timings']['build_l3_seconds']:.3f}s`",
        "",
        "## Table Counts",
        "",
        "| Table | Before | After | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key in sorted(before_counts):
        lines.append(f"| `{key}` | {before_counts[key]} | {after_counts.get(key, 0)} | {delta_counts.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## Dirty Window Sample",
            "",
        ]
    )
    if dirty_windows:
        lines.append("| Code | Dirty Start | Dirty End | Rebuild Start | Source Rows | Existing Gene Max |")
        lines.append("| --- | --- | --- | --- | ---: | --- |")
        for item in dirty_windows:
            lines.append(
                f"| `{item['code']}` | `{item['dirty_start']}` | `{item['dirty_end']}` | "
                f"`{item['rebuild_start']}` | {item['source_row_count']} | `{item['existing_gene_max_calc_date']}` |"
            )
    else:
        lines.append("No dirty windows were found in the requested window.")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This smoke exercises the daily-mainline `build_layers(..., layers=['l3'])` path rather than the standalone Gene builder.",
            "- Counts include full `L3` window effects, so `MSS/IRS` work is part of the measured runtime.",
            "- Gene-specific evidence is reflected in the Gene table counts and dirty-code summary above.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings()
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else _default_output_dir(db_path)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    store = Store(db_path)
    try:
        start, end = _resolve_window(store, args.start, args.end)

        scan_started = perf_counter()
        dirty_windows = scan_gene_dirty_windows(store, start=start, end=end)
        dirty_scan_seconds = perf_counter() - scan_started

        before = _collect_table_snapshot(store, end)

        build_started = perf_counter()
        build_written_rows = int(
            build_layers(
                store=store,
                config=cfg,
                layers=["l3"],
                start=start,
                end=end,
                force=False,
            )
        )
        build_l3_seconds = perf_counter() - build_started

        after = _collect_table_snapshot(store, end)
    finally:
        store.close()

    executed_at = datetime.now().isoformat(timespec="seconds")
    stamp = f"{start:%Y%m%d}_{end:%Y%m%d}_{datetime.now():%H%M%S}"
    payload = {
        "executed_at": executed_at,
        "db_path": str(db_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "dirty_code_count": len(dirty_windows),
        "dirty_windows_sample": [asdict(window) for window in dirty_windows[: max(int(args.dirty_sample_limit), 0)]],
        "build_written_rows": build_written_rows,
        "timings": {
            "dirty_scan_seconds": float(dirty_scan_seconds),
            "build_l3_seconds": float(build_l3_seconds),
        },
        "before": before,
        "after": after,
        "delta": {
            "counts": _delta_counts(before["counts"], after["counts"]),
        },
    }

    json_path = output_dir / f"gene_incremental_daily_smoke_{stamp}.json"
    md_path = output_dir / f"gene_incremental_daily_smoke_{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md_path.write_text(_build_markdown_summary(payload), encoding="utf-8")
    print(f"gene_incremental_daily_smoke_json={json_path}")
    print(f"gene_incremental_daily_smoke_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
