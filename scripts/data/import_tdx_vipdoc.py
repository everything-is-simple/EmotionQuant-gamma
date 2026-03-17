#!/usr/bin/env python
from __future__ import annotations

"""导入本地通达信 vipdoc 日线主底座。

这条脚本只负责三张 raw 表：
- raw_daily
- raw_index_daily
- raw_trade_cal
"""

import struct
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import Settings

from bulk_download_vendor_common import (
    ProviderProgress,
    RawDuckDBCompatWriter,
    flush_table_batch,
    log_step,
    progress_path,
    resolve_paths,
    safe_int,
    validate_date_arg,
    yyyymmdd,
)

DAY_RECORD_STRUCT = struct.Struct("<IIIIIfII")
SUPPORTED_TABLES = ["raw_daily", "raw_index_daily", "raw_trade_cal"]


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="从通达信 vipdoc 导入日线数据到 EmotionQuant raw DuckDB",
    )
    parser.add_argument("--start", required=True, help="起始日期 YYYYMMDD")
    parser.add_argument("--end", required=True, help="结束日期 YYYYMMDD")
    parser.add_argument(
        "--vipdoc-root",
        required=True,
        help="通达信 vipdoc 目录，例如 D:\\通达信\\...\\vipdoc",
    )
    parser.add_argument(
        "--tables",
        default="raw_daily,raw_index_daily,raw_trade_cal",
        help="逗号分隔的输出表，支持 raw_daily/raw_index_daily/raw_trade_cal",
    )
    parser.add_argument("--db-path", default="", help="目标 raw DuckDB 路径")
    parser.add_argument("--parquet-root", default="", help="可选 Parquet 输出根目录")
    parser.add_argument("--write-parquet", action="store_true", default=False, help="同时输出 Parquet 镜像")
    parser.add_argument("--dry-run", action="store_true", default=False, help="只探测，不实际写入")
    parser.add_argument("--batch-size", type=int, default=200, help="写库批大小")
    parser.add_argument(
        "--index-prefixes",
        default="sh:000,880,881;sz:399",
        help="指数/行业板块代码前缀规则，格式如 sh:000,880,881;sz:399",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help=".env 路径",
    )
    return parser


def parse_tables_arg(raw: str) -> list[str]:
    tables = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(tables) - set(SUPPORTED_TABLES))
    if unknown:
        raise ValueError(f"未知表名: {', '.join(unknown)}")
    return tables


def parse_index_prefixes(raw: str) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for part in raw.split(";"):
        item = part.strip()
        if not item or ":" not in item:
            continue
        market, prefixes = item.split(":", 1)
        result[market.strip().lower()] = tuple(
            prefix.strip() for prefix in prefixes.split(",") if prefix.strip()
        )
    return result


def iter_day_rows(day_file: Path) -> Iterator[tuple[str, float, float, float, float, float, int]]:
    raw = day_file.read_bytes()
    for offset in range(0, len(raw), DAY_RECORD_STRUCT.size):
        chunk = raw[offset : offset + DAY_RECORD_STRUCT.size]
        if len(chunk) < DAY_RECORD_STRUCT.size:
            continue
        trade_date_i, open_i, high_i, low_i, close_i, amount_f, volume_i, _ = DAY_RECORD_STRUCT.unpack(chunk)
        if trade_date_i <= 0:
            continue
        trade_date = str(trade_date_i)
        yield (
            trade_date,
            open_i / 100.0,
            high_i / 100.0,
            low_i / 100.0,
            close_i / 100.0,
            float(amount_f),
            int(volume_i),
        )


def tdx_to_ts_code(market: str, symbol: str) -> str:
    return f"{symbol.upper()}.{market.upper()}"


def is_index_symbol(market: str, symbol: str, index_prefixes: dict[str, tuple[str, ...]]) -> bool:
    return any(symbol.startswith(prefix) for prefix in index_prefixes.get(market.lower(), ()))


def is_stock_symbol(market: str, symbol: str) -> bool:
    if market == "bj":
        return True
    if market == "sh":
        return symbol.startswith(("600", "601", "603", "605", "688", "689", "900"))
    if market == "sz":
        return symbol.startswith(("000", "001", "002", "003", "200", "300", "301"))
    return False


def build_trade_calendar(trade_dates: set[str]) -> list[dict[str, object]]:
    ordered = sorted(trade_dates)
    records: list[dict[str, object]] = []
    previous = ""
    for trade_date in ordered:
        records.append(
            {
                "exchange": "SSE",
                "trade_date": trade_date,
                "is_open": 1,
                "cal_date": trade_date,
                "pretrade_date": previous,
            }
        )
        previous = trade_date
    return records


def run() -> int:
    # 走线：
    # `vipdoc/*.day -> 识别股票/指数 -> 组装 raw 记录 -> 批量写入 raw DuckDB`
    parser = build_parser()
    args = parser.parse_args()

    start_date = validate_date_arg(args.start)
    end_date = validate_date_arg(args.end)
    vipdoc_root = Path(args.vipdoc_root).expanduser().resolve()
    if not vipdoc_root.exists():
        raise FileNotFoundError(f"vipdoc 目录不存在: {vipdoc_root}")

    tables = parse_tables_arg(args.tables)
    index_prefixes = parse_index_prefixes(args.index_prefixes)

    settings = Settings.from_env(env_file=args.env_file)
    db_path, parquet_root = resolve_paths(settings, args.db_path, args.parquet_root)
    progress = ProviderProgress(
        provider="tdx_vipdoc",
        start_date=start_date,
        end_date=end_date,
        started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    progress_file = progress_path(settings, "tdx_vipdoc")

    writer = None if args.dry_run else RawDuckDBCompatWriter(db_path)
    table_buffers: dict[str, list[dict[str, object]]] = defaultdict(list)
    trade_dates: set[str] = set()
    stock_file_count = 0
    index_file_count = 0
    skipped_file_count = 0

    try:
        for market in ("sh", "sz", "bj"):
            lday_dir = vipdoc_root / market / "lday"
            if not lday_dir.exists():
                progress.notes.append(f"缺少目录: {lday_dir}")
                continue

            day_files = sorted(lday_dir.glob("*.day"))
            log_step(f"扫描 {market} 市场 lday: {len(day_files)} files")
            for day_file in day_files:
                stem = day_file.stem.lower()
                if len(stem) < 8:
                    skipped_file_count += 1
                    continue
                symbol = stem[-6:]
                ts_code = tdx_to_ts_code(market, symbol)

                target_table = ""
                if "raw_index_daily" in tables and is_index_symbol(market, symbol, index_prefixes):
                    target_table = "raw_index_daily"
                    index_file_count += 1
                elif "raw_daily" in tables and is_stock_symbol(market, symbol):
                    target_table = "raw_daily"
                    stock_file_count += 1
                else:
                    skipped_file_count += 1
                    continue

                previous_close: float | None = None
                wrote_any = False
                for trade_date, open_px, high_px, low_px, close_px, amount, volume in iter_day_rows(day_file):
                    if trade_date < start_date or trade_date > end_date:
                        previous_close = close_px
                        continue
                    change = None if previous_close is None else close_px - previous_close
                    pct_chg = None if previous_close in (None, 0) else (change / previous_close) * 100.0
                    trade_dates.add(trade_date)
                    wrote_any = True

                    if target_table == "raw_daily":
                        table_buffers[target_table].append(
                            {
                                "ts_code": ts_code,
                                "stock_code": symbol,
                                "trade_date": trade_date,
                                "open": open_px,
                                "high": high_px,
                                "low": low_px,
                                "close": close_px,
                                "vol": safe_int(volume / 100) if volume is not None else None,
                                "amount": amount,
                                "pre_close": previous_close,
                                "change": change,
                                "pct_chg": pct_chg,
                            }
                        )
                    else:
                        table_buffers[target_table].append(
                            {
                                "ts_code": ts_code,
                                "trade_date": trade_date,
                                "close": close_px,
                                "open": open_px,
                                "high": high_px,
                                "low": low_px,
                                "pre_close": previous_close,
                                "change": change,
                                "pct_chg": pct_chg,
                                "vol": safe_int(volume / 100) if volume is not None else None,
                                "amount": amount,
                            }
                        )

                    if len(table_buffers[target_table]) >= args.batch_size:
                        written = flush_table_batch(
                            writer,
                            parquet_root,
                            target_table,
                            table_buffers[target_table],
                            write_parquet=args.write_parquet,
                        )
                        progress.total_rows += written
                    previous_close = close_px

                if wrote_any:
                    progress.completed_units += 1

        if "raw_trade_cal" in tables and trade_dates:
            table_buffers["raw_trade_cal"].extend(build_trade_calendar(trade_dates))

        for table_name, buffer in table_buffers.items():
            written = flush_table_batch(
                writer,
                parquet_root,
                table_name,
                buffer,
                write_parquet=args.write_parquet,
            )
            progress.total_rows += written

        progress.notes.extend(
            [
                f"stock_files={stock_file_count}",
                f"index_files={index_file_count}",
                f"skipped_files={skipped_file_count}",
                f"trade_dates={len(trade_dates)}",
            ]
        )
        progress.save(progress_file)
        log_step(
            "TDX vipdoc 导入完成: "
            f"rows={progress.total_rows}, stock_files={stock_file_count}, "
            f"index_files={index_file_count}, trade_dates={len(trade_dates)}"
        )
        return 0
    finally:
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    raise SystemExit(run())
