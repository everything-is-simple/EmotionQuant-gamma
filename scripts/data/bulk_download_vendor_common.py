#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import duckdb
import pandas as pd

from src.config import Settings

# 这里刻意沿用老 raw 库的表名和字段顺序。
# 新脚本可以换数据源，但只要仍往这些表写，后面的 L1/L2 构建链就不需要先整体重写。
RAW_TABLE_SCHEMAS: dict[str, list[tuple[str, str]]] = {
    "raw_daily": [
        ("ts_code", "VARCHAR"),
        ("stock_code", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("open", "DOUBLE"),
        ("high", "DOUBLE"),
        ("low", "DOUBLE"),
        ("close", "DOUBLE"),
        ("vol", "BIGINT"),
        ("amount", "DOUBLE"),
        ("pre_close", "DOUBLE"),
        ("change", "DOUBLE"),
        ("pct_chg", "DOUBLE"),
    ],
    "raw_daily_basic": [
        ("ts_code", "VARCHAR"),
        ("stock_code", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("pe_ttm", "DOUBLE"),
        ("pb", "DOUBLE"),
        ("turnover_rate", "DOUBLE"),
        ("total_mv", "DOUBLE"),
        ("close", "DOUBLE"),
        ("turnover_rate_f", "DOUBLE"),
        ("volume_ratio", "DOUBLE"),
        ("pe", "DOUBLE"),
        ("ps", "DOUBLE"),
        ("ps_ttm", "DOUBLE"),
        ("dv_ratio", "DOUBLE"),
        ("dv_ttm", "DOUBLE"),
        ("total_share", "DOUBLE"),
        ("float_share", "DOUBLE"),
        ("free_share", "DOUBLE"),
        ("circ_mv", "DOUBLE"),
    ],
    "raw_index_daily": [
        ("ts_code", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("close", "DOUBLE"),
        ("open", "DOUBLE"),
        ("high", "DOUBLE"),
        ("low", "DOUBLE"),
        ("pre_close", "DOUBLE"),
        ("change", "DOUBLE"),
        ("pct_chg", "DOUBLE"),
        ("vol", "BIGINT"),
        ("amount", "DOUBLE"),
    ],
    "raw_limit_list": [
        ("ts_code", "VARCHAR"),
        ("stock_code", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("limit_type", "VARCHAR"),
        ("fd_amount", "DOUBLE"),
        ("industry", "VARCHAR"),
        ("name", "VARCHAR"),
        ("close", "DOUBLE"),
        ("pct_chg", "DOUBLE"),
        ("amount", "DOUBLE"),
        ("limit_amount", "DOUBLE"),
        ("float_mv", "DOUBLE"),
        ("total_mv", "DOUBLE"),
        ("turnover_ratio", "DOUBLE"),
        ("first_time", "VARCHAR"),
        ("last_time", "VARCHAR"),
        ("open_times", "BIGINT"),
        ("up_stat", "VARCHAR"),
        ("limit_times", "DOUBLE"),
        ("limit", "VARCHAR"),
    ],
    "raw_stock_basic": [
        ("ts_code", "VARCHAR"),
        ("symbol", "VARCHAR"),
        ("name", "VARCHAR"),
        ("area", "VARCHAR"),
        ("industry", "VARCHAR"),
        ("cnspell", "VARCHAR"),
        ("market", "VARCHAR"),
        ("list_date", "VARCHAR"),
        ("act_name", "VARCHAR"),
        ("act_ent_type", "VARCHAR"),
        ("stock_code", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("list_status", "VARCHAR"),
    ],
    "raw_index_classify": [
        ("index_code", "VARCHAR"),
        ("industry_name", "VARCHAR"),
        ("level", "VARCHAR"),
        ("industry_code", "VARCHAR"),
        ("src", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("is_pub", "VARCHAR"),
        ("parent_code", "VARCHAR"),
    ],
    "raw_index_member": [
        ("index_code", "VARCHAR"),
        ("con_code", "VARCHAR"),
        ("in_date", "VARCHAR"),
        ("out_date", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("ts_code", "VARCHAR"),
        ("stock_code", "VARCHAR"),
        ("is_new", "VARCHAR"),
    ],
    "raw_trade_cal": [
        ("exchange", "VARCHAR"),
        ("trade_date", "VARCHAR"),
        ("is_open", "BIGINT"),
        ("cal_date", "VARCHAR"),
        ("pretrade_date", "VARCHAR"),
    ],
}

RAW_TABLE_KEYS: dict[str, list[str]] = {
    "raw_daily": ["ts_code", "trade_date"],
    "raw_daily_basic": ["ts_code", "trade_date"],
    "raw_index_daily": ["ts_code", "trade_date"],
    "raw_limit_list": ["ts_code", "trade_date"],
    "raw_stock_basic": ["ts_code", "trade_date"],
    "raw_index_classify": ["index_code", "trade_date"],
    "raw_index_member": ["index_code", "ts_code", "in_date", "trade_date"],
    "raw_trade_cal": ["cal_date"],
}

DEFAULT_RAW_TABLES = [
    "raw_trade_cal",
    "raw_stock_basic",
    "raw_daily",
    "raw_daily_basic",
    "raw_index_daily",
    "raw_index_classify",
    "raw_index_member",
]

MAJOR_INDEX_CODES = [
    "000001.SH",
    "399001.SZ",
    "399006.SZ",
    "000688.SH",
    "000300.SH",
    "000905.SH",
    "000852.SH",
]


@dataclass
class ProviderProgress:
    provider: str
    start_date: str
    end_date: str
    started_at: str
    total_rows: int = 0
    completed_units: int = 0
    failed_units: int = 0
    skipped_units: int = 0
    notes: list[str] = field(default_factory=list)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def yyyymmdd(value: str | date | None) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    raw = str(value).strip()
    if not raw:
        return ""
    return raw.replace("-", "").replace("/", "")


def ts_to_stock_code(ts_code: str | None) -> str:
    text = str(ts_code or "").strip().upper()
    return text[:6] if len(text) >= 6 else ""


def baostock_to_ts_code(code: str | None) -> str:
    raw = str(code or "").strip().lower()
    if "." not in raw:
        return raw.upper()
    market, symbol = raw.split(".", 1)
    if market == "sh":
        return f"{symbol.upper()}.SH"
    if market == "sz":
        return f"{symbol.upper()}.SZ"
    if market == "bj":
        return f"{symbol.upper()}.BJ"
    return raw.upper()


def plain_to_ts_code(symbol: str | None) -> str:
    code = str(symbol or "").strip().upper()
    if not code:
        return ""
    if "." in code:
        return code
    if code.startswith(("6", "9")):
        return f"{code}.SH"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SZ"


def safe_float(value: Any) -> float | None:
    if value in (None, "", "None", "nan", "NaN"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def safe_int(value: Any) -> int | None:
    if value in (None, "", "None", "nan", "NaN"):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def stable_industry_code(prefix: str, industry_name: str) -> str:
    digest = hashlib.md5(industry_name.strip().encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}_{digest}"


def normalize_records(table_name: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []

    schema = RAW_TABLE_SCHEMAS[table_name]
    columns = [name for name, _ in schema]
    normalized: list[dict[str, Any]] = []
    for row in records:
        item = {column: row.get(column) for column in columns}
        if "ts_code" in item and item.get("stock_code") in (None, ""):
            item["stock_code"] = ts_to_stock_code(item.get("ts_code"))
        for key in ("trade_date", "cal_date", "pretrade_date", "list_date", "in_date", "out_date"):
            if key in item:
                item[key] = yyyymmdd(item.get(key))
        normalized.append(item)
    return normalized


class RawDuckDBCompatWriter:
    """按老 raw 表 contract 落盘，但去重逻辑改为按业务键，而不是按整天整表删分区。"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(db_path))
        self.total_written = 0

    def close(self) -> None:
        self.conn.close()

    def ensure_table(self, table_name: str) -> None:
        schema = RAW_TABLE_SCHEMAS[table_name]
        ddl = ", ".join(f"{name} {dtype}" for name, dtype in schema)
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({ddl})")

    def get_existing_trade_dates(self, table_name: str) -> set[str]:
        try:
            return {
                str(row[0])
                for row in self.conn.execute(
                    f"SELECT DISTINCT CAST(trade_date AS VARCHAR) FROM {table_name}"
                ).fetchall()
                if row[0] is not None
            }
        except Exception:
            return set()

    def write_records(self, table_name: str, records: list[dict[str, Any]]) -> int:
        normalized = normalize_records(table_name, records)
        if not normalized:
            return 0

        self.ensure_table(table_name)
        df = pd.DataFrame.from_records(normalized)
        self.conn.register("incoming_df", df)
        try:
            keys = RAW_TABLE_KEYS[table_name]
            match_clause = " AND ".join(
                f"COALESCE(CAST(t.{key} AS VARCHAR), '') = COALESCE(CAST(i.{key} AS VARCHAR), '')"
                for key in keys
            )
            self.conn.execute("BEGIN")
            try:
                self.conn.execute(
                    f"DELETE FROM {table_name} AS t USING incoming_df AS i WHERE {match_clause}"
                )
                column_sql = ", ".join(name for name, _ in RAW_TABLE_SCHEMAS[table_name])
                self.conn.execute(
                    f"INSERT INTO {table_name} ({column_sql}) SELECT {column_sql} FROM incoming_df"
                )
                self.conn.execute("COMMIT")
            except Exception:
                self.conn.execute("ROLLBACK")
                raise
        finally:
            self.conn.unregister("incoming_df")

        count = len(df)
        self.total_written += count
        return count


def write_parquet_by_keys(parquet_root: Path, table_name: str, records: list[dict[str, Any]]) -> None:
    normalized = normalize_records(table_name, records)
    if not normalized:
        return

    output_path = parquet_root / f"{table_name}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame.from_records(normalized)
    if output_path.exists():
        existing = pd.read_parquet(output_path)
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=RAW_TABLE_KEYS[table_name], keep="last")
    df.to_parquet(output_path, index=False)


def resolve_paths(settings: Settings, db_path_arg: str, parquet_root_arg: str) -> tuple[Path, Path]:
    if db_path_arg.strip():
        db_path = Path(db_path_arg.strip()).expanduser().resolve()
    else:
        db_path = Path(settings.duckdb_dir) / "emotionquant.duckdb"

    if parquet_root_arg.strip():
        parquet_root = Path(parquet_root_arg.strip()).expanduser().resolve()
    else:
        parquet_root = Path(settings.parquet_path) / "l1"

    parquet_root.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path, parquet_root


def build_common_parser(provider_name: str, default_tables: list[str] | None = None) -> argparse.ArgumentParser:
    supported = default_tables or DEFAULT_RAW_TABLES
    parser = argparse.ArgumentParser(
        description=f"EmotionQuant {provider_name} raw 下载落盘工具",
    )
    parser.add_argument("--start", required=True, help="起始日期 YYYYMMDD")
    parser.add_argument("--end", required=True, help="结束日期 YYYYMMDD")
    parser.add_argument("--tables", default=",".join(supported), help="逗号分隔的 raw 表清单")
    parser.add_argument("--db-path", default="", help="目标 raw DuckDB 路径")
    parser.add_argument("--parquet-root", default="", help="可选 Parquet 输出根目录")
    parser.add_argument("--skip-existing", action="store_true", default=False, help="按 trade_date 跳过已存在日期")
    parser.add_argument("--write-parquet", action="store_true", default=False, help="同时输出 Parquet 镜像")
    parser.add_argument("--dry-run", action="store_true", default=False, help="只探测，不实际写入")
    parser.add_argument("--code-limit", type=int, default=0, help="只跑前 N 只股票，用于抽样")
    parser.add_argument("--batch-size", type=int, default=50, help="按代码批量刷写大小")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="每次供应商请求后的暂停秒数")
    parser.add_argument("--env-file", default=".env", help=".env 路径")
    return parser


def parse_tables_arg(raw: str) -> list[str]:
    tables = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(tables) - set(RAW_TABLE_SCHEMAS))
    if unknown:
        raise ValueError(f"未知表名: {', '.join(unknown)}")
    return tables


def validate_date_arg(raw: str) -> str:
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(f"日期格式错误: {raw}")
    return raw


def progress_path(settings: Settings, provider_name: str) -> Path:
    return settings.resolved_temp_path / "artifacts" / f"bulk_download_{provider_name}_progress.json"


def flush_table_batch(
    writer: RawDuckDBCompatWriter | None,
    parquet_root: Path,
    table_name: str,
    buffer: list[dict[str, Any]],
    *,
    write_parquet: bool,
) -> int:
    if not buffer:
        return 0
    count = 0
    if writer is not None:
        count = writer.write_records(table_name, buffer)
    if write_parquet:
        write_parquet_by_keys(parquet_root, table_name, buffer)
    buffer.clear()
    return count


def log_step(message: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {message}")

