from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import Settings
from src.data.store import Store
from src.data.sw_industry import build_l1_sw_industry_member_rows, normalize_sw_l1_classify
from src.logging_utils import logger

_retry_logger = logging.getLogger("emotionquant.fetcher.retry")
_RAW_ATTACH_ALIAS = "rawdb_bootstrap"


def _to_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _month_slices(start: date, end: date) -> list[tuple[date, date]]:
    result: list[tuple[date, date]] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        if cursor.month == 12:
            month_end = date(cursor.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(cursor.year, cursor.month + 1, 1) - timedelta(days=1)
        slice_start = max(start, cursor)
        slice_end = min(end, month_end)
        result.append((slice_start, slice_end))
        cursor = month_end + timedelta(days=1)
    return result


class DataFetcher(ABC):
    @abstractmethod
    def fetch_stock_daily(self, start: date, end: date) -> pd.DataFrame:
        pass

    @abstractmethod
    def fetch_index_daily(self, codes: list[str], start: date, end: date) -> pd.DataFrame:
        pass

    @abstractmethod
    def fetch_stock_info(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def fetch_trade_calendar(self, start: date, end: date) -> pd.DataFrame:
        pass

    @abstractmethod
    def fetch_sw_industry_members(self, start: date, end: date) -> pd.DataFrame:
        pass


class TuShareFetcher(DataFetcher):
    def __init__(self, token: str, http_url: str | None = None, sleep_interval: float = 0.3):
        if not token:
            raise ValueError("TuShare token is required for TuShareFetcher")
        import tushare as ts

        self.pro = ts.pro_api(token)
        # 部分网关通道要求显式覆写底层 token/http_url 字段。
        self.pro._DataApi__token = token
        if http_url:
            self.pro._DataApi__http_url = http_url
        self.http_url = http_url or ""
        self.sleep_interval = sleep_interval

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(_retry_logger, logging.WARNING),
        reraise=True,
    )
    def _call_api(self, func: Callable, **kwargs) -> pd.DataFrame:
        return func(**kwargs)

    def fetch_stock_daily(self, start: date, end: date) -> pd.DataFrame:
        chunks: list[pd.DataFrame] = []
        for batch_start, batch_end in _month_slices(start, end):
            df_daily = self._call_api(
                self.pro.daily, start_date=_to_yyyymmdd(batch_start), end_date=_to_yyyymmdd(batch_end)
            )
            df_basic = self._call_api(
                self.pro.daily_basic,
                start_date=_to_yyyymmdd(batch_start),
                end_date=_to_yyyymmdd(batch_end),
                fields="ts_code,trade_date,total_mv,circ_mv",
            )
            # 某些通道 daily 不返回 adj_factor / 涨跌停价，按月补齐后再统一落库。
            df_adj = self._call_api(
                self.pro.adj_factor,
                start_date=_to_yyyymmdd(batch_start),
                end_date=_to_yyyymmdd(batch_end),
            )
            df_limit = self._call_api(
                self.pro.stk_limit,
                start_date=_to_yyyymmdd(batch_start),
                end_date=_to_yyyymmdd(batch_end),
            )
            if df_daily is None or df_daily.empty:
                continue
            merged = df_daily.merge(df_basic, on=["ts_code", "trade_date"], how="left")
            if (
                df_adj is not None
                and not df_adj.empty
                and {"ts_code", "trade_date", "adj_factor"}.issubset(df_adj.columns)
            ):
                merged = merged.merge(
                    df_adj[["ts_code", "trade_date", "adj_factor"]],
                    on=["ts_code", "trade_date"],
                    how="left",
                )
            if (
                df_limit is not None
                and not df_limit.empty
                and {"ts_code", "trade_date", "up_limit", "down_limit"}.issubset(df_limit.columns)
            ):
                merged = merged.merge(
                    df_limit[["ts_code", "trade_date", "up_limit", "down_limit"]],
                    on=["ts_code", "trade_date"],
                    how="left",
                )
            merged = merged.rename(columns={"trade_date": "date", "vol": "volume"})
            merged["date"] = pd.to_datetime(merged["date"], format="%Y%m%d").dt.date
            merged["is_halt"] = merged.get("is_halt", False)
            if "adj_factor" not in merged.columns:
                merged["adj_factor"] = 1.0
            if "up_limit" not in merged.columns:
                merged["up_limit"] = None
            if "down_limit" not in merged.columns:
                merged["down_limit"] = None
            if "total_mv" not in merged.columns:
                merged["total_mv"] = None
            if "circ_mv" not in merged.columns:
                merged["circ_mv"] = None
            chunks.append(
                merged[
                    [
                        "ts_code",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "pre_close",
                        "volume",
                        "amount",
                        "pct_chg",
                        "adj_factor",
                        "is_halt",
                        "up_limit",
                        "down_limit",
                        "total_mv",
                        "circ_mv",
                    ]
                ]
            )
            time.sleep(self.sleep_interval)
        if not chunks:
            return pd.DataFrame()
        return pd.concat(chunks, ignore_index=True)

    def fetch_index_daily(self, codes: list[str], start: date, end: date) -> pd.DataFrame:
        chunks: list[pd.DataFrame] = []
        for ts_code in codes:
            df = self._call_api(
                self.pro.index_daily,
                ts_code=ts_code,
                start_date=_to_yyyymmdd(start),
                end_date=_to_yyyymmdd(end),
            )
            if df is None or df.empty:
                continue
            df = df.rename(columns={"trade_date": "date", "vol": "volume"})
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.date
            chunks.append(
                df[
                    [
                        "ts_code",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "pre_close",
                        "pct_chg",
                        "volume",
                        "amount",
                    ]
                ]
            )
            time.sleep(self.sleep_interval)
        if not chunks:
            return pd.DataFrame()
        return pd.concat(chunks, ignore_index=True)

    def fetch_stock_info(self) -> pd.DataFrame:
        snapshots: list[pd.DataFrame] = []
        for list_status in ("L", "D", "P"):
            df = self._call_api(
                self.pro.stock_basic,
                exchange="",
                list_status=list_status,
                fields="ts_code,name,industry,market,list_status,list_date",
            )
            if df is None or df.empty:
                continue
            snapshots.append(df)

        if not snapshots:
            return pd.DataFrame()
        basic = pd.concat(snapshots, ignore_index=True)
        basic = basic.drop_duplicates(subset=["ts_code"], keep="first")
        basic = basic.rename(columns={"list_date": "list_date_raw"})
        basic["is_st"] = basic["name"].str.contains("ST", na=False)
        basic["list_date"] = pd.to_datetime(basic["list_date_raw"], format="%Y%m%d", errors="coerce").dt.date
        # 现行 API 只能提供“当前快照”，这里至少保留 list_status。
        # effective_from 仍以 list_date 优先；缺失时回退到抓取当天，保证主键非空。
        basic["effective_from"] = basic["list_date"].fillna(date.today())
        return basic[
            [
                "ts_code",
                "name",
                "industry",
                "market",
                "list_status",
                "is_st",
                "list_date",
                "effective_from",
            ]
        ]

    def fetch_trade_calendar(self, start: date, end: date) -> pd.DataFrame:
        cal = self._call_api(
            self.pro.trade_cal,
            exchange="SSE",
            start_date=_to_yyyymmdd(start),
            end_date=_to_yyyymmdd(end),
        )
        if cal is None or cal.empty:
            return pd.DataFrame()
        cal = cal.rename(columns={"cal_date": "date", "is_open": "is_trade_day"})
        cal["date"] = pd.to_datetime(cal["date"], format="%Y%m%d").dt.date
        cal["is_trade_day"] = cal["is_trade_day"].astype(int) == 1
        cal = cal.sort_values("date")
        trade_dates = cal.loc[cal["is_trade_day"], "date"].tolist()
        prev_map = {}
        next_map = {}
        for i, d in enumerate(trade_dates):
            prev_map[d] = trade_dates[i - 1] if i > 0 else None
            next_map[d] = trade_dates[i + 1] if i < len(trade_dates) - 1 else None
        cal["prev_trade_day"] = cal["date"].map(prev_map)
        cal["next_trade_day"] = cal["date"].map(next_map)
        return cal[["date", "is_trade_day", "prev_trade_day", "next_trade_day"]]

    def fetch_sw_industry_members(self, start: date, end: date) -> pd.DataFrame:
        """
        远端模式拉取 SW2021 一级行业完整成员快照。
        当前成员(Y) + 历史移出成员(N) 一起拉取，避免执行库只看到现行成分。
        """
        classify = self._call_api(self.pro.index_classify, level="L1", src="SW2021")
        normalized_classify = normalize_sw_l1_classify(classify)
        if normalized_classify.empty:
            return pd.DataFrame()

        member_api = getattr(self.pro, "index_member_all", None)
        if member_api is None:
            logger.warning("TuShare index_member_all API unavailable; skip SW industry members.")
            return pd.DataFrame()

        member_frames: list[pd.DataFrame] = []
        for l1_code in normalized_classify["index_code"].tolist():
            for is_new in ("Y", "N"):
                df = self._call_api(member_api, l1_code=l1_code, is_new=is_new)
                if df is not None and not df.empty:
                    member_frames.append(df)
                time.sleep(self.sleep_interval)

        return build_l1_sw_industry_member_rows(classify, member_frames, source_trade_date=end)


class AKShareFetcher(DataFetcher):
    """
    Backup fetcher. v0.01 provides structural compatibility;
    field mapping can be expanded without changing caller contracts.
    """

    def fetch_stock_daily(self, start: date, end: date) -> pd.DataFrame:
        import akshare as ak

        _ = ak  # Keep import for runtime availability check.
        logger.warning("AKShare stock_daily mapping is minimal in v0.01.")
        return pd.DataFrame()

    def fetch_index_daily(self, codes: list[str], start: date, end: date) -> pd.DataFrame:
        import akshare as ak

        _ = ak
        logger.warning("AKShare index_daily mapping is minimal in v0.01.")
        return pd.DataFrame()

    def fetch_stock_info(self) -> pd.DataFrame:
        import akshare as ak

        _ = ak
        logger.warning("AKShare stock_info mapping is minimal in v0.01.")
        return pd.DataFrame()

    def fetch_trade_calendar(self, start: date, end: date) -> pd.DataFrame:
        import akshare as ak

        _ = ak
        logger.warning("AKShare trade_calendar mapping is minimal in v0.01.")
        return pd.DataFrame()

    def fetch_sw_industry_members(self, start: date, end: date) -> pd.DataFrame:
        import akshare as ak

        _ = ak
        logger.warning("AKShare sw industry member mapping is minimal in v0.01.")
        return pd.DataFrame()


@dataclass(frozen=True)
class RawBootstrapResult:
    source_db: Path
    target_db: Path
    trade_calendar_rows: int
    stock_daily_rows: int
    index_daily_rows: int
    stock_info_rows: int
    sw_industry_member_rows: int
    stock_info_effective_from_min: date | None
    stock_info_effective_from_max: date | None


@dataclass(frozen=True)
class RawPartitionRepairResult:
    source_db: Path
    target_db: Path
    start: date
    end: date
    stock_daily_rows: int
    index_daily_rows: int


def _escape_duckdb_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def bootstrap_l1_from_raw_duckdb(
    store: Store,
    source_db: str | Path,
    start: date,
    end: date,
    refresh_stock_info_only: bool = False,
) -> RawBootstrapResult:
    source = Path(source_db).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Raw DuckDB source not found: {source}")
    if source == store.db_path:
        raise ValueError("Raw DuckDB source must be different from target execution DB.")

    attached = False
    in_tx = False
    try:
        store.conn.execute(f"ATTACH '{_escape_duckdb_path(source)}' AS {_RAW_ATTACH_ALIAS}")
        attached = True
        store.conn.execute("BEGIN")
        in_tx = True

        # 兼容旧执行库：为 stock_info 补齐 list_status 列，避免导入失败。
        store.conn.execute("ALTER TABLE l1_stock_info ADD COLUMN IF NOT EXISTS list_status VARCHAR DEFAULT 'L'")

        if refresh_stock_info_only:
            store.conn.execute("DELETE FROM l1_stock_info")
            store.conn.execute("DELETE FROM l1_sw_industry_member")
        else:
            for table in (
                "l1_trade_calendar",
                "l1_stock_daily",
                "l1_index_daily",
                "l1_stock_info",
                "l1_sw_industry_member",
            ):
                store.conn.execute(f"DELETE FROM {table}")

            store.conn.execute(
                f"""
                INSERT INTO l1_trade_calendar(date, is_trade_day, prev_trade_day, next_trade_day)
                WITH cal AS (
                  SELECT
                    STRPTIME(cal_date, '%Y%m%d')::DATE AS date,
                    (is_open = 1) AS is_trade_day
                  FROM {_RAW_ATTACH_ALIAS}.raw_trade_cal
                  WHERE STRPTIME(cal_date, '%Y%m%d')::DATE BETWEEN ? AND ?
                ),
                td AS (
                  SELECT date FROM cal WHERE is_trade_day = TRUE ORDER BY date
                ),
                td_link AS (
                  SELECT
                    date,
                    LAG(date) OVER (ORDER BY date) AS prev_trade_day,
                    LEAD(date) OVER (ORDER BY date) AS next_trade_day
                  FROM td
                )
                SELECT c.date, c.is_trade_day, l.prev_trade_day, l.next_trade_day
                FROM cal c LEFT JOIN td_link l USING(date)
                ORDER BY c.date
                """,
                [start, end],
            )

            store.conn.execute(
                f"""
                INSERT INTO l1_index_daily(ts_code, date, open, high, low, close, pre_close, pct_chg, volume, amount)
                SELECT
                  ts_code,
                  STRPTIME(trade_date, '%Y%m%d')::DATE AS date,
                  open, high, low, close, pre_close, pct_chg,
                  vol AS volume,
                  amount
                FROM {_RAW_ATTACH_ALIAS}.raw_index_daily
                WHERE ts_code = '000001.SH'
                  AND STRPTIME(trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
                """,
                [start, end],
            )

            store.conn.execute(
                f"""
                INSERT INTO l1_stock_daily(
                  ts_code, date, open, high, low, close, pre_close, volume, amount, pct_chg,
                  adj_factor, is_halt, up_limit, down_limit, total_mv, circ_mv
                )
                SELECT
                  d.ts_code,
                  STRPTIME(d.trade_date, '%Y%m%d')::DATE AS date,
                  d.open, d.high, d.low, d.close, d.pre_close,
                  d.vol AS volume,
                  d.amount,
                  d.pct_chg,
                  1.0 AS adj_factor,
                  (COALESCE(d.vol, 0) = 0) AS is_halt,
                  NULL::DOUBLE AS up_limit,
                  NULL::DOUBLE AS down_limit,
                  b.total_mv,
                  b.circ_mv
                FROM {_RAW_ATTACH_ALIAS}.raw_daily d
                LEFT JOIN {_RAW_ATTACH_ALIAS}.raw_daily_basic b
                  ON d.ts_code = b.ts_code AND d.trade_date = b.trade_date
                WHERE STRPTIME(d.trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
                """,
                [start, end],
            )

        stock_info_frame = store.conn.execute(
            f"""
            SELECT
              ts_code,
              name,
              industry,
              market,
              COALESCE(list_status, 'L') AS list_status,
              list_date,
              STRPTIME(trade_date, '%Y%m%d')::DATE AS effective_from
            FROM {_RAW_ATTACH_ALIAS}.raw_stock_basic
            WHERE STRPTIME(trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            ORDER BY ts_code ASC, effective_from ASC
            """,
            [start, end],
        ).df()
        if not stock_info_frame.empty:
            stock_info_frame = stock_info_frame.copy()
            stock_info_frame["effective_from"] = pd.to_datetime(stock_info_frame["effective_from"]).dt.date
            stock_info_frame["list_status"] = stock_info_frame["list_status"].fillna("L").astype(str)
            stock_info_frame["list_date"] = pd.to_datetime(
                stock_info_frame["list_date"],
                format="%Y%m%d",
                errors="coerce",
            ).dt.date
            stock_info_frame = (
                stock_info_frame.sort_values(["ts_code", "effective_from"], ascending=[True, True])
                .drop_duplicates(subset=["ts_code", "effective_from"], keep="last")
                .reset_index(drop=True)
            )
            for column in ["name", "industry", "market", "list_status", "list_date"]:
                stock_info_frame[f"prev_{column}"] = stock_info_frame.groupby("ts_code")[column].shift(1)

            change_mask = stock_info_frame["prev_name"].isna()
            for column in ["name", "industry", "market", "list_status", "list_date"]:
                current = stock_info_frame[column].astype("string").fillna("")
                previous = stock_info_frame[f"prev_{column}"].astype("string").fillna("")
                change_mask |= current != previous

            changed_stock_info = stock_info_frame.loc[
                change_mask,
                ["ts_code", "name", "industry", "market", "list_status", "list_date", "effective_from"],
            ].copy()
            changed_stock_info["is_st"] = changed_stock_info["name"].fillna("").str.contains("ST", regex=False)
            changed_stock_info = changed_stock_info[
                ["ts_code", "name", "industry", "market", "list_status", "is_st", "list_date", "effective_from"]
            ]
            store.bulk_upsert("l1_stock_info", changed_stock_info)

        try:
            store.conn.execute(
                f"""
                INSERT INTO l1_sw_industry_member(
                  industry_code, industry_name, ts_code, in_date, out_date, is_new, source_trade_date
                )
                WITH sw_l1 AS (
                  SELECT index_code, industry_name
                  FROM (
                    SELECT
                      index_code,
                      industry_name,
                      STRPTIME(trade_date, '%Y%m%d')::DATE AS snapshot_date,
                      ROW_NUMBER() OVER (
                        PARTITION BY index_code
                        ORDER BY STRPTIME(trade_date, '%Y%m%d')::DATE DESC
                      ) AS rn
                    FROM {_RAW_ATTACH_ALIAS}.raw_index_classify
                    WHERE src = 'SW2021'
                      AND level = 'L1'
                      AND industry_name NOT LIKE '行业%'
                  )
                  WHERE rn = 1
                ),
                  dedup AS (
                    SELECT
                      m.index_code AS industry_code,
                      sw.industry_name AS industry_name,
                      COALESCE(NULLIF(m.ts_code, ''), NULLIF(m.con_code, '')) AS ts_code,
                    STRPTIME(m.in_date, '%Y%m%d')::DATE AS in_date,
                    CASE
                      WHEN NULLIF(m.out_date, '') IS NULL THEN NULL
                      ELSE STRPTIME(m.out_date, '%Y%m%d')::DATE
                    END AS out_date,
                      COALESCE(m.is_new, '') AS is_new,
                      STRPTIME(m.trade_date, '%Y%m%d')::DATE AS source_trade_date,
                      ROW_NUMBER() OVER (
                        PARTITION BY
                          m.index_code,
                          COALESCE(NULLIF(m.ts_code, ''), NULLIF(m.con_code, '')),
                          STRPTIME(m.in_date, '%Y%m%d')::DATE
                        ORDER BY
                          CASE WHEN NULLIF(m.out_date, '') IS NULL THEN 1 ELSE 0 END ASC,
                          CASE
                            WHEN NULLIF(m.out_date, '') IS NULL THEN NULL
                            ELSE STRPTIME(m.out_date, '%Y%m%d')::DATE
                          END DESC,
                          STRPTIME(m.trade_date, '%Y%m%d')::DATE DESC
                      ) AS rn
                    FROM {_RAW_ATTACH_ALIAS}.raw_index_member m
                    INNER JOIN sw_l1 sw
                      ON sw.index_code = m.index_code
                  WHERE COALESCE(NULLIF(m.ts_code, ''), NULLIF(m.con_code, '')) IS NOT NULL
                    AND STRPTIME(m.in_date, '%Y%m%d')::DATE <= ?
                    AND (
                      NULLIF(m.out_date, '') IS NULL
                      OR STRPTIME(m.out_date, '%Y%m%d')::DATE >= ?
                    )
                )
                SELECT
                  industry_code,
                  industry_name,
                  ts_code,
                  in_date,
                  out_date,
                  is_new,
                  source_trade_date
                FROM dedup
                WHERE rn = 1
                """,
                [end, start],
            )
        except Exception as exc:
            logger.warning(f"raw SW industry bootstrap skipped: {exc}")

        stock_info_max = store.read_scalar("SELECT MAX(effective_from) FROM l1_stock_info")
        store.update_fetch_progress("stock_info", stock_info_max, status="OK")
        store.update_fetch_progress(
            "sw_industry_member",
            store.read_scalar("SELECT MAX(source_trade_date) FROM l1_sw_industry_member"),
            status="OK",
        )
        if not refresh_stock_info_only:
            store.update_fetch_progress("trade_cal", store.get_max_date("l1_trade_calendar"), status="OK")
            store.update_fetch_progress("index_daily", store.get_max_date("l1_index_daily"), status="OK")
            store.update_fetch_progress("stock_daily", store.get_max_date("l1_stock_daily"), status="OK")

        store.conn.execute("COMMIT")
        in_tx = False
    except Exception:
        if in_tx:
            store.conn.execute("ROLLBACK")
        raise
    finally:
        if attached:
            try:
                store.conn.execute(f"DETACH {_RAW_ATTACH_ALIAS}")
            except Exception:
                pass

    stock_info_range = store.conn.execute(
        "SELECT MIN(effective_from), MAX(effective_from) FROM l1_stock_info"
    ).fetchone()
    return RawBootstrapResult(
        source_db=source,
        target_db=store.db_path,
        trade_calendar_rows=int(store.read_scalar("SELECT COUNT(*) FROM l1_trade_calendar") or 0),
        stock_daily_rows=int(store.read_scalar("SELECT COUNT(*) FROM l1_stock_daily") or 0),
        index_daily_rows=int(store.read_scalar("SELECT COUNT(*) FROM l1_index_daily") or 0),
        stock_info_rows=int(store.read_scalar("SELECT COUNT(*) FROM l1_stock_info") or 0),
        sw_industry_member_rows=int(store.read_scalar("SELECT COUNT(*) FROM l1_sw_industry_member") or 0),
        stock_info_effective_from_min=stock_info_range[0] if stock_info_range else None,
        stock_info_effective_from_max=stock_info_range[1] if stock_info_range else None,
    )


def repair_l1_partitions_from_raw_duckdb(
    store: Store,
    source_db: str | Path,
    start: date,
    end: date,
) -> RawPartitionRepairResult:
    source = Path(source_db).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Raw DuckDB source not found: {source}")
    if source == store.db_path:
        raise ValueError("Raw DuckDB source must be different from target execution DB.")
    if start > end:
        raise ValueError(f"Invalid repair range: {start} > {end}")

    attached = False
    in_tx = False
    try:
        store.conn.execute(f"ATTACH '{_escape_duckdb_path(source)}' AS {_RAW_ATTACH_ALIAS}")
        attached = True
        store.conn.execute("BEGIN")
        in_tx = True

        # 只替换目标日期分区，避免局部修复时误删整张执行表。
        store.conn.execute("DELETE FROM l1_stock_daily WHERE date BETWEEN ? AND ?", [start, end])
        store.conn.execute(
            f"""
            INSERT INTO l1_stock_daily(
              ts_code, date, open, high, low, close, pre_close, volume, amount, pct_chg,
              adj_factor, is_halt, up_limit, down_limit, total_mv, circ_mv
            )
            SELECT
              d.ts_code,
              STRPTIME(d.trade_date, '%Y%m%d')::DATE AS date,
              d.open, d.high, d.low, d.close, d.pre_close,
              d.vol AS volume,
              d.amount,
              d.pct_chg,
              1.0 AS adj_factor,
              (COALESCE(d.vol, 0) = 0) AS is_halt,
              NULL::DOUBLE AS up_limit,
              NULL::DOUBLE AS down_limit,
              b.total_mv,
              b.circ_mv
            FROM {_RAW_ATTACH_ALIAS}.raw_daily d
            LEFT JOIN {_RAW_ATTACH_ALIAS}.raw_daily_basic b
              ON d.ts_code = b.ts_code AND d.trade_date = b.trade_date
            WHERE STRPTIME(d.trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            """,
            [start, end],
        )

        # index_daily 当前执行库只消费上证指数分区；局部修复时保持同一口径。
        store.conn.execute("DELETE FROM l1_index_daily WHERE date BETWEEN ? AND ?", [start, end])
        store.conn.execute(
            f"""
            INSERT INTO l1_index_daily(ts_code, date, open, high, low, close, pre_close, pct_chg, volume, amount)
            SELECT
              ts_code,
              STRPTIME(trade_date, '%Y%m%d')::DATE AS date,
              open, high, low, close, pre_close, pct_chg,
              vol AS volume,
              amount
            FROM {_RAW_ATTACH_ALIAS}.raw_index_daily
            WHERE ts_code = '000001.SH'
              AND STRPTIME(trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            """,
            [start, end],
        )

        stock_daily_max = store.get_max_date("l1_stock_daily")
        index_daily_max = store.get_max_date("l1_index_daily")
        store.update_fetch_progress("stock_daily", stock_daily_max, status="OK")
        store.update_fetch_progress("index_daily", index_daily_max, status="OK")

        store.conn.execute("COMMIT")
        in_tx = False
    except Exception:
        if in_tx:
            store.conn.execute("ROLLBACK")
        raise
    finally:
        if attached:
            try:
                store.conn.execute(f"DETACH {_RAW_ATTACH_ALIAS}")
            except Exception:
                pass

    return RawPartitionRepairResult(
        source_db=source,
        target_db=store.db_path,
        start=start,
        end=end,
        stock_daily_rows=int(
            store.read_scalar("SELECT COUNT(*) FROM l1_stock_daily WHERE date BETWEEN ? AND ?", (start, end)) or 0
        ),
        index_daily_rows=int(
            store.read_scalar("SELECT COUNT(*) FROM l1_index_daily WHERE date BETWEEN ? AND ?", (start, end)) or 0
        ),
    )


def _probe_tushare_channel(token: str, http_url: str | None) -> TuShareFetcher:
    fetcher = TuShareFetcher(token=token, http_url=http_url)
    probe_day = date.today()
    # 探活以交易日历为准：最快、字段稳定、可直接验证鉴权。
    fetcher.fetch_trade_calendar(probe_day, probe_day)
    return fetcher


def create_fetcher(config: Settings) -> DataFetcher:
    channels: list[tuple[str, str, str | None]] = []

    if config.tushare_primary_token:
        channels.append(("primary", config.tushare_primary_token, config.tushare_primary_http_url or None))
    if config.tushare_fallback_token:
        channels.append(("fallback", config.tushare_fallback_token, config.tushare_fallback_http_url or None))
    if config.tushare_token:
        # 兼容旧配置：若只配了单 token，作为最后一个 TuShare 通道尝试。
        channels.append(("legacy", config.tushare_token, None))

    errors: list[str] = []
    for name, token, http_url in channels:
        if not token:
            continue
        try:
            fetcher = _probe_tushare_channel(token=token, http_url=http_url)
            suffix = f" via {http_url}" if http_url else ""
            logger.info(f"TuShare channel active: {name}{suffix}")
            return fetcher
        except Exception as exc:
            errors.append(f"{name}:{exc}")
            logger.warning(f"TuShare channel failed ({name}): {exc}")

    if config.akshare_enabled:
        if errors:
            logger.warning(f"All TuShare channels unavailable, fallback to AKShare: {' | '.join(errors)}")
        else:
            logger.warning("No TuShare token configured, fallback to AKShare.")
        return AKShareFetcher()

    detail = " | ".join(errors) if errors else "no token configured"
    raise RuntimeError(f"No available data channel: {detail}")


def _safe_next_trade_day(store: Store, d: date) -> date:
    nxt = store.next_trade_date(d)
    if nxt is None:
        return d + timedelta(days=1)
    return nxt


def fetch_incremental(
    store: Store,
    fetcher: DataFetcher,
    data_type: str,
    target_table: str,
    start: date | None = None,
    end: date | None = None,
) -> int:
    end_date = end or date.today()
    if start is None:
        last_success = store.get_fetch_progress(data_type)
        if last_success is None:
            start_date = end_date - timedelta(days=365 * 3)
        else:
            start_date = _safe_next_trade_day(store, last_success)
    else:
        start_date = start

    if start_date > end_date:
        return 0

    if data_type == "trade_cal":
        df = fetcher.fetch_trade_calendar(start_date, end_date)
    elif data_type == "stock_info":
        df = fetcher.fetch_stock_info()
    elif data_type == "stock_daily":
        df = fetcher.fetch_stock_daily(start_date, end_date)
    elif data_type == "index_daily":
        df = fetcher.fetch_index_daily(["000001.SH"], start_date, end_date)
    elif data_type == "sw_industry_member":
        df = fetcher.fetch_sw_industry_members(start_date, end_date)
    else:
        raise ValueError(f"Unsupported data_type: {data_type}")

    if df is None or df.empty:
        store.update_fetch_progress(data_type, store.get_fetch_progress(data_type), status="OK")
        return 0

    written = store.bulk_upsert(target_table, df)
    store.update_fetch_progress(data_type, end_date, status="OK")
    return written
