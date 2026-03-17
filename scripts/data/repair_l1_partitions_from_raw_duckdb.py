from __future__ import annotations

"""按日期窗口修复执行库 L1。

这是当前每日增量更新最重要的执行库入口。
raw 库更新后，优先用它把最近 1~5 个交易日重刷进执行库。
"""

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.fetcher import repair_l1_partitions_from_raw_duckdb
from src.data.store import Store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repair execution L1 partitions from local raw DuckDB")
    parser.add_argument("--target-db", default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    parser.add_argument("--source-db", default=r"G:\EmotionQuant_data\duckdb\emotionquant.duckdb")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target = Path(args.target_db).expanduser().resolve()
    source = Path(args.source_db).expanduser().resolve()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    store = Store(target)
    try:
        result = repair_l1_partitions_from_raw_duckdb(
            store=store,
            source_db=source,
            start=start,
            end=end,
        )
        print(f"l1_stock_daily_repaired={result.stock_daily_rows}")
        print(f"l1_index_daily_repaired={result.index_daily_rows}")
        print(f"repair_range={result.start}..{result.end}")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
