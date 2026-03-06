from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Callable
import logging

import pandas as pd
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import Settings
from src.logging_utils import logger
from src.data.store import Store

_retry_logger = logging.getLogger("emotionquant.fetcher.retry")


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
    else:
        raise ValueError(f"Unsupported data_type: {data_type}")

    if df is None or df.empty:
        store.update_fetch_progress(data_type, store.get_fetch_progress(data_type), status="OK")
        return 0

    written = store.bulk_upsert(target_table, df)
    store.update_fetch_progress(data_type, end_date, status="OK")
    return written
