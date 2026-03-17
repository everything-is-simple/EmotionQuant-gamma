#!/usr/bin/env python
from __future__ import annotations

"""导入本地通达信静态资产快照。

这条脚本负责补齐 vipdoc 没有的三块：
- raw_stock_basic
- raw_index_classify
- raw_index_member
"""

"""导入本地通达信静态资产快照。

这条脚本补的是 vipdoc 没有的三块：
- raw_stock_basic
- raw_index_classify
- raw_index_member
"""

import argparse
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import duckdb
import pandas as pd
from mootdx import consts
from mootdx.quotes import Quotes
from mootdx.reader import Reader

from src.config import Settings

from bulk_download_vendor_common import (
    ProviderProgress,
    RawDuckDBCompatWriter,
    log_step,
    plain_to_ts_code,
    progress_path,
    resolve_paths,
    stable_industry_code,
    ts_to_stock_code,
    yyyymmdd,
)

SUPPORTED_TABLES = ["raw_stock_basic", "raw_index_classify", "raw_index_member"]
DBF_HEADER_STRUCT = struct.Struct("<BBBBIHH20x")


@dataclass(frozen=True)
class StockBasicFallback:
    name: str
    industry: str
    market: str
    list_date: str
    list_status: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从本地通达信 T0002/hq_cache 导入静态资产到 EmotionQuant raw DuckDB",
    )
    parser.add_argument(
        "--tdx-root",
        required=True,
        help="通达信根目录，例如 G:\\new-tdx\\new-tdx",
    )
    parser.add_argument(
        "--snapshot-date",
        default="",
        help="静态快照日期 YYYYMMDD；默认从 raw_trade_cal 最大 trade_date 推断",
    )
    parser.add_argument(
        "--tables",
        default="raw_stock_basic,raw_index_classify,raw_index_member",
        help="逗号分隔的输出表",
    )
    parser.add_argument("--db-path", default="", help="目标 raw DuckDB 路径")
    parser.add_argument("--parquet-root", default="", help="可选 Parquet 输出根目录")
    parser.add_argument("--write-parquet", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument(
        "--disable-quotes-fallback",
        action="store_true",
        default=False,
        help="禁用 mootdx 实时接口股票列表兜底补名",
    )
    parser.add_argument("--env-file", default=".env", help=".env 路径")
    return parser


def parse_tables_arg(raw: str) -> list[str]:
    tables = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(tables) - set(SUPPORTED_TABLES))
    if unknown:
        raise ValueError(f"未知表名: {', '.join(unknown)}")
    return tables


def parse_dbf_records(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    _, _, _, _, num_records, header_len, record_len = DBF_HEADER_STRUCT.unpack(raw[:32])
    fields: list[tuple[str, str, int, int]] = []
    cursor = 32
    while raw[cursor] != 0x0D:
        desc = raw[cursor : cursor + 32]
        name = desc[:11].split(b"\x00", 1)[0].decode("ascii", "ignore")
        field_type = chr(desc[11])
        field_len = desc[16]
        decimals = desc[17]
        fields.append((name, field_type, field_len, decimals))
        cursor += 32

    records: list[dict[str, str]] = []
    base = header_len
    for idx in range(num_records):
        record = raw[base + idx * record_len : base + (idx + 1) * record_len]
        if not record or record[0] == 0x2A:
            continue
        offset = 1
        item: dict[str, str] = {}
        for field_name, _, field_len, _ in fields:
            value = record[offset : offset + field_len]
            offset += field_len
            item[field_name] = value.decode("gbk", "ignore").strip().strip("\x00")
        records.append(item)
    return records


def load_latest_stock_basic_fallback(db_path: Path) -> dict[str, StockBasicFallback]:
    if not db_path.exists():
        return {}
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT ts_code, name, industry, market, list_date, list_status
            FROM (
              SELECT
                ts_code,
                name,
                industry,
                market,
                list_date,
                list_status,
                ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) AS rn
              FROM raw_stock_basic
            )
            WHERE rn = 1
            """
        ).fetchall()
    except duckdb.Error:
        rows = []
    finally:
        con.close()

    result: dict[str, StockBasicFallback] = {}
    for ts_code, name, industry, market, list_date, list_status in rows:
        result[str(ts_code)] = StockBasicFallback(
            name=str(name or "").strip(),
            industry=str(industry or "").strip(),
            market=str(market or "").strip(),
            list_date=yyyymmdd(list_date),
            list_status=str(list_status or "L").strip() or "L",
        )
    return result


def infer_snapshot_date(db_path: Path) -> str:
    if db_path.exists():
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            value = con.execute("SELECT MAX(trade_date) FROM raw_trade_cal").fetchone()[0]
            if value:
                return yyyymmdd(value)
        except duckdb.Error:
            pass
        finally:
            con.close()
    return datetime.now().strftime("%Y%m%d")


def build_local_security_maps(vipdoc_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    ts_code_to_market: dict[str, str] = {}
    plain_code_to_ts: dict[str, str] = {}
    for market, suffix in (("sh", "SH"), ("sz", "SZ"), ("bj", "BJ")):
        lday_dir = vipdoc_root / market / "lday"
        if not lday_dir.exists():
            continue
        for file in lday_dir.glob("*.day"):
            code = file.stem[-6:].upper()
            ts_code = f"{code}.{suffix}"
            ts_code_to_market[ts_code] = suffix
            plain_code_to_ts.setdefault(code, ts_code)
    return ts_code_to_market, plain_code_to_ts


def map_sc_to_market(sc: str) -> str:
    return {"0": "SZ", "1": "SH", "2": "BJ"}.get(str(sc).strip(), "")


def is_stock_symbol(market: str, symbol: str) -> bool:
    if market == "BJ":
        return symbol.startswith(("4", "8"))
    if market == "SH":
        return symbol.startswith(("600", "601", "603", "605", "688", "689", "900"))
    if market == "SZ":
        return symbol.startswith(("000", "001", "002", "003", "200", "300", "301"))
    return False


def parse_tdxzs_cfg(path: Path) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    ref_to_name: dict[str, str] = {}
    name_to_meta: dict[str, dict[str, str]] = {}
    for raw_line in path.read_text(encoding="gbk", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or "|" not in line:
            continue
        parts = [item.strip() for item in line.split("|")]
        if len(parts) < 6:
            continue
        industry_name, code, level_code, subtype_code, _, ref_code = parts[:6]
        if ref_code:
            ref_to_name[ref_code] = industry_name
        if industry_name and code:
            name_to_meta[industry_name] = {
                "code": code,
                "level_code": level_code,
                "subtype_code": subtype_code,
                "ref_code": ref_code,
            }
    return ref_to_name, name_to_meta


def parse_tdxhy_cfg(path: Path, ref_to_name: dict[str, str]) -> dict[str, str]:
    stock_to_industry: dict[str, str] = {}
    for raw_line in path.read_text(encoding="gbk", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or "|" not in line:
            continue
        parts = [item.strip() for item in line.split("|")]
        if len(parts) < 3:
            continue
        _, code, tdx_industry_code = parts[:3]
        if not code:
            continue
        industry_name = ref_to_name.get(tdx_industry_code, "")
        if industry_name:
            stock_to_industry[code.upper()] = industry_name
    return stock_to_industry


def build_quotes_name_map(disabled: bool) -> dict[str, str]:
    if disabled:
        return {}
    client = Quotes.factory(market="std")
    frames: list[pd.DataFrame] = []
    try:
        for market, suffix in ((consts.MARKET_SH, "SH"), (consts.MARKET_SZ, "SZ")):
            frame = client.stocks(market=market)
            if frame is None or frame.empty:
                continue
            frame = frame.copy()
            frame["ts_code"] = frame["code"].astype(str).str.upper() + f".{suffix}"
            frames.append(frame[["ts_code", "name"]])
    finally:
        client.close()

    if not frames:
        return {}
    merged = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["ts_code"], keep="first")
    return {str(row.ts_code): str(row.name).replace("\x00", "").strip() for row in merged.itertuples(index=False)}


def build_stock_basic_records(
    base_records: Iterable[dict[str, str]],
    snapshot_date: str,
    fallback_map: dict[str, StockBasicFallback],
    stock_to_industry: dict[str, str],
    ts_code_to_market: dict[str, str],
    quote_name_map: dict[str, str],
) -> list[dict[str, Any]]:
    # 当前快照版 stock_basic 的装配逻辑：
    # 1. base.dbf 给主清单
    # 2. tdxhy.cfg 给行业归属
    # 3. quotes/fallback 只在本地缓存缺名字时补名称
    # 4. 最终落成 raw_stock_basic 的当日快照
    records: list[dict[str, Any]] = []
    for row in base_records:
        symbol = str(row.get("GPDM", "")).strip().upper()
        market = map_sc_to_market(row.get("SC", ""))
        if not symbol or not market or not is_stock_symbol(market, symbol):
            continue

        ts_code = f"{symbol}.{market}"
        fallback = fallback_map.get(ts_code)
        list_date = yyyymmdd(row.get("SSDATE")) or (fallback.list_date if fallback else "")
        industry_name = stock_to_industry.get(symbol, "")
        if not industry_name and fallback:
            industry_name = fallback.industry

        if symbol.startswith(("4", "8")):
            default_status = "L" if ts_code in ts_code_to_market else "D"
        else:
            default_status = "L"
        list_status = (fallback.list_status if fallback else "") or default_status

        name = ""
        if fallback:
            name = fallback.name
        if not name:
            name = quote_name_map.get(ts_code, "")

        records.append(
            {
                "ts_code": ts_code,
                "symbol": symbol,
                "name": name,
                "area": "",
                "industry": industry_name,
                "cnspell": "",
                "market": market,
                "list_date": list_date,
                "act_name": "",
                "act_ent_type": "",
                "stock_code": symbol,
                "trade_date": snapshot_date,
                "list_status": list_status,
            }
        )
    dedup = {(item["ts_code"], item["trade_date"]): item for item in records}
    return list(dedup.values())


def choose_index_code(
    block_name: str,
    source_label: str,
    name_to_meta: dict[str, dict[str, str]],
    plain_code_to_ts: dict[str, str],
) -> tuple[str, str]:
    meta = name_to_meta.get(block_name)
    if meta:
        local_code = meta["code"].upper()
        return plain_code_to_ts.get(local_code, f"{local_code}.SH"), meta.get("ref_code", "")
    return stable_industry_code(source_label, f"{source_label}|{block_name}"), ""


def build_index_snapshot_records(
    reader: Reader,
    snapshot_date: str,
    name_to_meta: dict[str, dict[str, str]],
    plain_code_to_ts: dict[str, str],
    stock_list_date_map: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    classify_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    source_specs = [
        ("block_zs", "TDX_BLOCK_ZS", "INDEX_BUCKET"),
        ("block_gn", "TDX_BLOCK_GN", "CONCEPT_BUCKET"),
        ("block_fg", "TDX_BLOCK_FG", "STYLE_BUCKET"),
    ]

    for symbol, src, level in source_specs:
        frame = reader.block(symbol=symbol, group=False)
        if frame is None or frame.empty:
            continue
        for block_name, group in frame.groupby("blockname", sort=False):
            block_name = str(block_name).replace("\x00", "").strip()
            if not block_name:
                continue
            index_code, parent_code = choose_index_code(block_name, src, name_to_meta, plain_code_to_ts)
            classify_rows.append(
                {
                    "index_code": index_code,
                    "industry_name": block_name,
                    "level": level,
                    "industry_code": index_code,
                    "src": src,
                    "trade_date": snapshot_date,
                    "is_pub": "1",
                    "parent_code": parent_code,
                }
            )
            for member_code in group["code"].astype(str).tolist():
                local_code = member_code.strip().upper()
                ts_code = plain_code_to_ts.get(local_code, plain_to_ts_code(local_code))
                in_date = stock_list_date_map.get(ts_code or "", snapshot_date)
                member_rows.append(
                    {
                        "index_code": index_code,
                        "con_code": ts_code or local_code,
                        "in_date": in_date,
                        "out_date": "",
                        "trade_date": snapshot_date,
                        "ts_code": ts_code or "",
                        "stock_code": ts_to_stock_code(ts_code) if ts_code else local_code,
                        "is_new": "Y",
                    }
                )

    custom_frame = reader.block_new(group=False)
    if custom_frame is not None and not custom_frame.empty:
        for block_name, group in custom_frame.groupby("blockname", sort=False):
            block_name = str(block_name).replace("\x00", "").strip()
            if not block_name:
                continue
            index_code = stable_industry_code("TDX_BLOCK_CUSTOM", block_name)
            classify_rows.append(
                {
                    "index_code": index_code,
                    "industry_name": block_name,
                    "level": "CUSTOM_BUCKET",
                    "industry_code": index_code,
                    "src": "TDX_BLOCK_CUSTOM",
                    "trade_date": snapshot_date,
                    "is_pub": "0",
                    "parent_code": "",
                }
            )
            for member_code in group["code"].astype(str).tolist():
                local_code = member_code.strip().upper()
                ts_code = plain_code_to_ts.get(local_code, plain_to_ts_code(local_code))
                in_date = stock_list_date_map.get(ts_code or "", snapshot_date)
                member_rows.append(
                    {
                        "index_code": index_code,
                        "con_code": ts_code or local_code,
                        "in_date": in_date,
                        "out_date": "",
                        "trade_date": snapshot_date,
                        "ts_code": ts_code or "",
                        "stock_code": ts_to_stock_code(ts_code) if ts_code else local_code,
                        "is_new": "Y",
                    }
                )

    dedup_classify = {(row["index_code"], row["trade_date"]): row for row in classify_rows}
    dedup_member = {
        (row["index_code"], row["con_code"], row["in_date"], row["trade_date"]): row
        for row in member_rows
    }
    return list(dedup_classify.values()), list(dedup_member.values())


def run() -> int:
    args = build_parser().parse_args()
    tables = parse_tables_arg(args.tables)

    settings = Settings.from_env(env_file=args.env_file)
    db_path, _ = resolve_paths(settings, args.db_path, args.parquet_root)
    snapshot_date = yyyymmdd(args.snapshot_date) or infer_snapshot_date(db_path)

    tdx_root = Path(args.tdx_root).expanduser().resolve()
    vipdoc_root = tdx_root / "vipdoc"
    hq_cache_root = tdx_root / "T0002" / "hq_cache"
    if not vipdoc_root.exists():
        raise FileNotFoundError(f"vipdoc 目录不存在: {vipdoc_root}")
    if not hq_cache_root.exists():
        raise FileNotFoundError(f"hq_cache 目录不存在: {hq_cache_root}")

    progress = ProviderProgress(
        provider="tdx_static_assets",
        start_date=snapshot_date,
        end_date=snapshot_date,
        started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    progress_file = progress_path(settings, "tdx_static_assets")

    base_records = parse_dbf_records(hq_cache_root / "base.dbf")
    ref_to_name, name_to_meta = parse_tdxzs_cfg(hq_cache_root / "tdxzs.cfg")
    stock_to_industry = parse_tdxhy_cfg(hq_cache_root / "tdxhy.cfg", ref_to_name)
    fallback_map = load_latest_stock_basic_fallback(db_path)
    ts_code_to_market, plain_code_to_ts = build_local_security_maps(vipdoc_root)
    quote_name_map = build_quotes_name_map(args.disable_quotes_fallback)
    reader = Reader.factory(market="std", tdxdir=str(tdx_root))

    stock_basic_records = build_stock_basic_records(
        base_records=base_records,
        snapshot_date=snapshot_date,
        fallback_map=fallback_map,
        stock_to_industry=stock_to_industry,
        ts_code_to_market=ts_code_to_market,
        quote_name_map=quote_name_map,
    )
    stock_list_date_map = {
        str(row["ts_code"]): yyyymmdd(row.get("list_date"))
        for row in stock_basic_records
        if str(row.get("ts_code", "")).strip() and yyyymmdd(row.get("list_date"))
    }
    index_classify_records, index_member_records = build_index_snapshot_records(
        reader=reader,
        snapshot_date=snapshot_date,
        name_to_meta=name_to_meta,
        plain_code_to_ts=plain_code_to_ts,
        stock_list_date_map=stock_list_date_map,
    )

    progress.notes.extend(
        [
            f"snapshot_date={snapshot_date}",
            f"base_dbf_records={len(base_records)}",
            f"stock_basic_records={len(stock_basic_records)}",
            f"index_classify_records={len(index_classify_records)}",
            f"index_member_records={len(index_member_records)}",
            f"quotes_name_map={len(quote_name_map)}",
            f"fallback_stock_basic={len(fallback_map)}",
        ]
    )

    if args.dry_run:
        progress.total_rows = (
            (len(stock_basic_records) if "raw_stock_basic" in tables else 0)
            + (len(index_classify_records) if "raw_index_classify" in tables else 0)
            + (len(index_member_records) if "raw_index_member" in tables else 0)
        )
        progress.completed_units = len(tables)
        progress.save(progress_file)
        log_step(
            "TDX 静态资产 dry-run 完成: "
            f"stock_basic={len(stock_basic_records)}, "
            f"index_classify={len(index_classify_records)}, "
            f"index_member={len(index_member_records)}"
        )
        return 0

    writer = RawDuckDBCompatWriter(db_path)
    try:
        if "raw_stock_basic" in tables:
            progress.total_rows += writer.write_records("raw_stock_basic", stock_basic_records)
            progress.completed_units += 1
        if "raw_index_classify" in tables:
            progress.total_rows += writer.write_records("raw_index_classify", index_classify_records)
            progress.completed_units += 1
        if "raw_index_member" in tables:
            progress.total_rows += writer.write_records("raw_index_member", index_member_records)
            progress.completed_units += 1
    finally:
        writer.close()

    progress.save(progress_file)
    log_step(
        "TDX 静态资产导入完成: "
        f"rows={progress.total_rows}, "
        f"stock_basic={len(stock_basic_records)}, "
        f"index_classify={len(index_classify_records)}, "
        f"index_member={len(index_member_records)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
