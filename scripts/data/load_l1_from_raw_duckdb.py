from __future__ import annotations

"""从 raw DuckDB 全量或大窗口装载执行库 L1。

适合初次建库、大范围重刷或静态资产口径变化后的整段刷新。
它不是每日增量主入口。
"""

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.fetcher import bootstrap_l1_from_raw_duckdb
from src.data.store import Store


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Load L1 tables from local raw DuckDB (snapshot-safe)")
    p.add_argument("--target-db", default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    p.add_argument("--source-db", default=r"G:\EmotionQuant_data\duckdb\emotionquant.duckdb")
    p.add_argument("--start", default="2023-01-01")
    p.add_argument("--end", default="2026-03-04")
    p.add_argument("--refresh-stock-info-only", action="store_true", default=False)
    return p


def main() -> int:
    args = build_parser().parse_args()

    target = Path(args.target_db).expanduser().resolve()
    source = Path(args.source_db).expanduser().resolve()
    store = Store(target)
    try:
        result = bootstrap_l1_from_raw_duckdb(
            store=store,
            source_db=source,
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
            refresh_stock_info_only=args.refresh_stock_info_only,
        )
        print(f"l1_trade_calendar={result.trade_calendar_rows}")
        print(f"l1_stock_daily={result.stock_daily_rows}")
        print(f"l1_index_daily={result.index_daily_rows}")
        print(f"l1_stock_info={result.stock_info_rows}")
        if result.stock_info_rows > 0:
            print(
                "l1_stock_info_effective_range="
                f"{result.stock_info_effective_from_min}..{result.stock_info_effective_from_max}"
            )
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
