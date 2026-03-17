#!/usr/bin/env python
from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import baostock as bs
import pandas as pd

from src.config import Settings

from bulk_download_vendor_common import (
    DEFAULT_RAW_TABLES,
    MAJOR_INDEX_CODES,
    ProviderProgress,
    RawDuckDBCompatWriter,
    baostock_to_ts_code,
    build_common_parser,
    flush_table_batch,
    log_step,
    parse_tables_arg,
    progress_path,
    resolve_paths,
    safe_float,
    safe_int,
    stable_industry_code,
    ts_to_stock_code,
    validate_date_arg,
    yyyymmdd,
)

SUPPORTED_TABLES = [table for table in DEFAULT_RAW_TABLES if table != "raw_limit_list"]


def _query_all_rows(result: Any) -> list[dict[str, Any]]:
    fields = list(getattr(result, "fields", []) or [])
    rows: list[dict[str, Any]] = []
    while result.error_code == "0" and result.next():
        values = result.get_row_data()
        rows.append(dict(zip(fields, values)))
    return rows


def _ts_to_baostock_code(ts_code: str) -> str:
    symbol, market = ts_code.split(".", 1)
    return f"{market.lower()}.{symbol.lower()}"


def _fetch_trade_calendar(start_date: str, end_date: str) -> tuple[list[dict[str, Any]], list[str]]:
    rs = bs.query_trade_dates(
        start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
        end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
    )
    rows = _query_all_rows(rs)
    records: list[dict[str, Any]] = []
    open_days: list[str] = []
    previous_open = ""
    for row in rows:
        cal_date = yyyymmdd(row.get("calendar_date"))
        is_open = safe_int(row.get("is_trading_day")) or 0
        if is_open == 1:
            open_days.append(cal_date)
        records.append(
            {
                "exchange": "SSE",
                "trade_date": cal_date if is_open == 1 else "",
                "is_open": is_open,
                "cal_date": cal_date,
                "pretrade_date": previous_open,
            }
        )
        if is_open == 1:
            previous_open = cal_date
    return records, open_days


def _fetch_industry_snapshot(snapshot_date: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    rs = bs.query_stock_industry(
        date=f"{snapshot_date[:4]}-{snapshot_date[4:6]}-{snapshot_date[6:]}"
    )
    rows = _query_all_rows(rs)
    if not rows:
        return [], [], {}

    classify_records: list[dict[str, Any]] = []
    member_records: list[dict[str, Any]] = []
    industry_code_map: dict[str, str] = {}

    for row in rows:
        industry_name = str(row.get("industry", "")).strip()
        if not industry_name:
            continue
        industry_classification = str(row.get("industryClassification", "")).strip()
        index_code = industry_code_map.setdefault(
            industry_name,
            stable_industry_code("BSIND", industry_name),
        )
        classify_records.append(
            {
                "index_code": index_code,
                "industry_name": industry_name,
                "level": "L1",
                "industry_code": index_code,
                "src": "BAOSTOCK_CSRC",
                "trade_date": yyyymmdd(row.get("updateDate")) or snapshot_date,
                "is_pub": "",
                "parent_code": industry_classification,
            }
        )
        ts_code = baostock_to_ts_code(row.get("code"))
        member_records.append(
            {
                "index_code": index_code,
                "con_code": ts_code,
                "in_date": snapshot_date,
                "out_date": "",
                "trade_date": yyyymmdd(row.get("updateDate")) or snapshot_date,
                "ts_code": ts_code,
                "stock_code": ts_to_stock_code(ts_code),
                "is_new": "Y",
            }
        )

    dedup_classify = {
        (row["index_code"], row["trade_date"]): row for row in classify_records
    }
    dedup_member = {
        (row["index_code"], row["ts_code"], row["trade_date"]): row for row in member_records
    }
    stock_industry_map = {
        baostock_to_ts_code(row.get("code")): str(row.get("industry", "")).strip()
        for row in rows
        if str(row.get("industry", "")).strip()
    }
    return list(dedup_classify.values()), list(dedup_member.values()), stock_industry_map


def _fetch_stock_basic(snapshot_date: str, stock_industry_map: dict[str, str]) -> list[dict[str, Any]]:
    rs = bs.query_stock_basic()
    rows = _query_all_rows(rs)
    records: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("type", "")).strip() != "1":
            continue
        ts_code = baostock_to_ts_code(row.get("code"))
        if not ts_code:
            continue
        list_date = yyyymmdd(row.get("ipoDate"))
        out_date = yyyymmdd(row.get("outDate"))
        market = ts_code.split(".", 1)[1]
        records.append(
            {
                "ts_code": ts_code,
                "symbol": ts_to_stock_code(ts_code),
                "name": str(row.get("code_name", "")).strip(),
                "area": "",
                "industry": stock_industry_map.get(ts_code, ""),
                "cnspell": "",
                "market": market,
                "list_date": list_date,
                "act_name": "",
                "act_ent_type": "",
                "stock_code": ts_to_stock_code(ts_code),
                "trade_date": snapshot_date,
                "list_status": "D" if out_date else "L",
            }
        )
    return records


def _fetch_stock_daily_range(
    ts_code: str,
    start_date: str,
    end_date: str,
    target_trade_dates: set[str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rs = bs.query_history_k_data_plus(
        _ts_to_baostock_code(ts_code),
        "date,code,open,high,low,close,preclose,volume,amount,pctChg",
        start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
        end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
        frequency="d",
        adjustflag="3",
    )
    rows = _query_all_rows(rs)
    raw_daily: list[dict[str, Any]] = []
    raw_daily_basic: list[dict[str, Any]] = []
    stock_code = ts_to_stock_code(ts_code)
    for row in rows:
        trade_date = yyyymmdd(row.get("date"))
        if target_trade_dates is not None and trade_date not in target_trade_dates:
            continue
        close = safe_float(row.get("close"))
        pre_close = safe_float(row.get("preclose"))
        change = (close - pre_close) if close is not None and pre_close is not None else None
        raw_daily.append(
            {
                "ts_code": ts_code,
                "stock_code": stock_code,
                "trade_date": trade_date,
                "open": safe_float(row.get("open")),
                "high": safe_float(row.get("high")),
                "low": safe_float(row.get("low")),
                "close": close,
                "vol": safe_int(row.get("volume")),
                "amount": safe_float(row.get("amount")),
                "pre_close": pre_close,
                "change": change,
                "pct_chg": safe_float(row.get("pctChg")),
            }
        )
        # BaoStock 没有 Tushare 那套 daily_basic 历史全字段。
        # 这里先保留兼容壳：至少把 ts_code/trade_date/close 落盘，其余字段显式留空。
        raw_daily_basic.append(
            {
                "ts_code": ts_code,
                "stock_code": stock_code,
                "trade_date": trade_date,
                "pe_ttm": None,
                "pb": None,
                "turnover_rate": None,
                "total_mv": None,
                "close": close,
                "turnover_rate_f": None,
                "volume_ratio": None,
                "pe": None,
                "ps": None,
                "ps_ttm": None,
                "dv_ratio": None,
                "dv_ttm": None,
                "total_share": None,
                "float_share": None,
                "free_share": None,
                "circ_mv": None,
            }
        )
    return raw_daily, raw_daily_basic


def _fetch_index_daily(
    start_date: str,
    end_date: str,
    target_trade_dates: set[str] | None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ts_code in MAJOR_INDEX_CODES:
        rs = bs.query_history_k_data_plus(
            _ts_to_baostock_code(ts_code),
            "date,code,open,high,low,close,preclose,volume,amount,pctChg",
            start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
            end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
            frequency="d",
        )
        rows = _query_all_rows(rs)
        for row in rows:
            trade_date = yyyymmdd(row.get("date"))
            if target_trade_dates is not None and trade_date not in target_trade_dates:
                continue
            close = safe_float(row.get("close"))
            pre_close = safe_float(row.get("preclose"))
            records.append(
                {
                    "ts_code": ts_code,
                    "trade_date": trade_date,
                    "close": close,
                    "open": safe_float(row.get("open")),
                    "high": safe_float(row.get("high")),
                    "low": safe_float(row.get("low")),
                    "pre_close": pre_close,
                    "change": (close - pre_close) if close is not None and pre_close is not None else None,
                    "pct_chg": safe_float(row.get("pctChg")),
                    "vol": safe_int(row.get("volume")),
                    "amount": safe_float(row.get("amount")),
                }
            )
    return records


def run() -> int:
    parser = build_common_parser("BaoStock", SUPPORTED_TABLES)
    parser.add_argument(
        "--allow-large-window",
        action="store_true",
        default=False,
        help="显式允许大窗口全量抓取；默认关闭，避免误打 BaoStock 黑名单。",
    )
    parser.add_argument(
        "--safe-max-days",
        type=int,
        default=62,
        help="安全模式下允许的最大自然日窗口，默认 62 天。",
    )
    args = parser.parse_args()
    start_date = validate_date_arg(args.start)
    end_date = validate_date_arg(args.end)
    tables = parse_tables_arg(args.tables)

    settings = Settings.from_env(env_file=args.env_file)
    db_path, parquet_root = resolve_paths(settings, args.db_path, args.parquet_root)
    progress = ProviderProgress(
        provider="baostock",
        start_date=start_date,
        end_date=end_date,
        started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    progress_file = progress_path(settings, "baostock")

    if "raw_limit_list" in tables:
        progress.notes.append("BaoStock 不提供 limit_list 等价历史源，已自动跳过 raw_limit_list。")
        tables = [table for table in tables if table != "raw_limit_list"]

    writer = None if args.dry_run else RawDuckDBCompatWriter(db_path)
    try:
        log_step("登录 BaoStock")
        login_result = bs.login()
        if str(login_result.error_code) != "0":
            raise RuntimeError(f"BaoStock 登录失败: {login_result.error_msg}")

        log_step(f"目标 raw 库: {db_path}")
        if args.write_parquet:
            log_step(f"Parquet 镜像: {parquet_root}")

        trade_calendar_records, open_days = _fetch_trade_calendar(start_date, end_date)
        log_step(f"交易日历就绪: {len(open_days)} 个开市日")

        if args.dry_run:
            print(f"[dry-run] tables={tables}")
            print(f"[dry-run] open_days={len(open_days)} range={start_date}..{end_date}")
            return 0

        if "raw_trade_cal" in tables:
            progress.total_rows += writer.write_records("raw_trade_cal", trade_calendar_records)
            if args.write_parquet:
                from bulk_download_vendor_common import write_parquet_by_keys

                write_parquet_by_keys(parquet_root, "raw_trade_cal", trade_calendar_records)

        industry_classify_records: list[dict[str, Any]] = []
        industry_member_records: list[dict[str, Any]] = []
        stock_industry_map: dict[str, str] = {}
        if "raw_index_classify" in tables or "raw_index_member" in tables or "raw_stock_basic" in tables:
            industry_classify_records, industry_member_records, stock_industry_map = _fetch_industry_snapshot(end_date)
            log_step(
                f"行业快照就绪: classify={len(industry_classify_records)} member={len(industry_member_records)}"
            )

        if "raw_index_classify" in tables:
            progress.total_rows += writer.write_records("raw_index_classify", industry_classify_records)
            if args.write_parquet:
                from bulk_download_vendor_common import write_parquet_by_keys

                write_parquet_by_keys(parquet_root, "raw_index_classify", industry_classify_records)
        if "raw_index_member" in tables:
            progress.total_rows += writer.write_records("raw_index_member", industry_member_records)
            if args.write_parquet:
                from bulk_download_vendor_common import write_parquet_by_keys

                write_parquet_by_keys(parquet_root, "raw_index_member", industry_member_records)

        stock_basic_records: list[dict[str, Any]] = []
        if "raw_stock_basic" in tables or "raw_daily" in tables or "raw_daily_basic" in tables:
            stock_basic_records = _fetch_stock_basic(end_date, stock_industry_map)
            log_step(f"股票清单就绪: {len(stock_basic_records)} 只")
            total_code_count = len(stock_basic_records)
            if args.code_limit > 0:
                stock_basic_records = stock_basic_records[: args.code_limit]
                log_step(f"按 --code-limit 截断后: {len(stock_basic_records)} 只")
            start_dt = pd.to_datetime(start_date, format="%Y%m%d")
            end_dt = pd.to_datetime(end_date, format="%Y%m%d")
            window_days = int((end_dt - start_dt).days) + 1
            estimated_request_count = len(stock_basic_records) + len(MAJOR_INDEX_CODES) + 3
            if (
                not args.allow_large_window
                and args.code_limit == 0
                and window_days > args.safe_max_days
            ):
                raise RuntimeError(
                    "BaoStock 安全模式阻止了大窗口全量抓取。"
                    f" 当前窗口 {window_days} 天、预估请求 {estimated_request_count} 次、股票 {total_code_count} 只。"
                    " 请优先复用旧 raw 库，只补缺口；若确认需要全量抓取，再显式加 --allow-large-window。"
                )

        if "raw_stock_basic" in tables:
            progress.total_rows += writer.write_records("raw_stock_basic", stock_basic_records)
            if args.write_parquet:
                from bulk_download_vendor_common import write_parquet_by_keys

                write_parquet_by_keys(parquet_root, "raw_stock_basic", stock_basic_records)

        target_trade_dates: set[str] | None = None
        target_index_trade_dates: set[str] | None = None
        if args.skip_existing and "raw_daily" in tables:
            existing = writer.get_existing_trade_dates("raw_daily")
            target_trade_dates = set(open_days) - existing
            log_step(f"raw_daily 缺口交易日: {len(target_trade_dates)}")
        if args.skip_existing and "raw_index_daily" in tables:
            existing = writer.get_existing_trade_dates("raw_index_daily")
            target_index_trade_dates = set(open_days) - existing
            log_step(f"raw_index_daily 缺口交易日: {len(target_index_trade_dates)}")

        buffers: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if "raw_daily" in tables or "raw_daily_basic" in tables:
            for idx, row in enumerate(stock_basic_records, start=1):
                daily_records, basic_records = _fetch_stock_daily_range(
                    row["ts_code"],
                    start_date,
                    end_date,
                    target_trade_dates,
                )
                if "raw_daily" in tables:
                    buffers["raw_daily"].extend(daily_records)
                if "raw_daily_basic" in tables:
                    buffers["raw_daily_basic"].extend(basic_records)
                progress.completed_units += 1

                if idx % args.batch_size == 0 or idx == len(stock_basic_records):
                    for table_name in ("raw_daily", "raw_daily_basic"):
                        if table_name in tables:
                            progress.total_rows += flush_table_batch(
                                writer,
                                parquet_root,
                                table_name,
                                buffers[table_name],
                                write_parquet=args.write_parquet,
                            )
                    log_step(f"股票日线进度: {idx}/{len(stock_basic_records)}")
                    progress.save(progress_file)
                if args.sleep_seconds > 0:
                    time.sleep(args.sleep_seconds)

        if "raw_index_daily" in tables:
            index_records = _fetch_index_daily(start_date, end_date, target_index_trade_dates)
            progress.total_rows += writer.write_records("raw_index_daily", index_records)
            if args.write_parquet:
                from bulk_download_vendor_common import write_parquet_by_keys

                write_parquet_by_keys(parquet_root, "raw_index_daily", index_records)

        progress.save(progress_file)
        log_step(
            f"BaoStock 下载完成: total_rows={progress.total_rows} completed_units={progress.completed_units}"
        )
        return 0
    finally:
        try:
            bs.logout()
        except Exception:
            pass
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    raise SystemExit(run())
