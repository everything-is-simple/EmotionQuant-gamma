from __future__ import annotations

from datetime import date
import sys
import types

import duckdb
import pandas as pd

from src.data.fetcher import TuShareFetcher, bootstrap_l1_from_raw_duckdb
from src.data.store import Store


class _FakePro:
    def __init__(self) -> None:
        self._DataApi__token = ""
        self._DataApi__http_url = ""

    def stock_basic(self, exchange: str, list_status: str, fields: str) -> pd.DataFrame:
        assert exchange == ""
        assert "list_status" in fields
        rows = {
            "L": [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "list_date": "19910403",
                }
            ],
            "D": [
                {
                    "ts_code": "000002.SZ",
                    "name": "样本退市股",
                    "industry": "制造",
                    "market": "主板",
                    "list_status": "D",
                    "list_date": "20000101",
                }
            ],
            "P": [],
        }
        return pd.DataFrame(rows[list_status])


def test_fetch_stock_info_keeps_list_status(monkeypatch) -> None:
    fake_ts = types.SimpleNamespace(pro_api=lambda token: _FakePro())
    monkeypatch.setitem(sys.modules, "tushare", fake_ts)

    fetcher = TuShareFetcher(token="dummy-token")
    df = fetcher.fetch_stock_info()

    assert set(df["list_status"]) == {"L", "D"}
    assert "effective_from" in df.columns


def test_bootstrap_l1_from_raw_duckdb_loads_tables_and_updates_progress(tmp_path) -> None:
    source_db = tmp_path / "raw.duckdb"
    target_db = tmp_path / "target.duckdb"

    con = duckdb.connect(str(source_db))
    con.execute(
        """
        CREATE TABLE raw_trade_cal (
            cal_date VARCHAR,
            is_open INTEGER
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_trade_cal VALUES
        ('20260102', 1),
        ('20260103', 0),
        ('20260105', 1)
        """
    )
    con.execute(
        """
        CREATE TABLE raw_index_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            pre_close DOUBLE,
            pct_chg DOUBLE,
            vol DOUBLE,
            amount DOUBLE
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_index_daily VALUES
        ('000001.SH', '20260102', 10, 10.5, 9.8, 10.2, 10.0, 2.0, 100000, 500000)
        """
    )
    con.execute(
        """
        CREATE TABLE raw_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            pre_close DOUBLE,
            vol DOUBLE,
            amount DOUBLE,
            pct_chg DOUBLE
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_daily VALUES
        ('000001.SZ', '20260102', 10, 10.3, 9.9, 10.1, 9.8, 120000, 600000, 3.06)
        """
    )
    con.execute(
        """
        CREATE TABLE raw_daily_basic (
            ts_code VARCHAR,
            trade_date VARCHAR,
            total_mv DOUBLE,
            circ_mv DOUBLE
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_daily_basic VALUES
        ('000001.SZ', '20260102', 1000000, 800000)
        """
    )
    con.execute(
        """
        CREATE TABLE raw_stock_basic (
            ts_code VARCHAR,
            name VARCHAR,
            industry VARCHAR,
            market VARCHAR,
            list_status VARCHAR,
            list_date VARCHAR,
            trade_date VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_stock_basic VALUES
        ('000001.SZ', '平安银行', '银行', '主板', 'L', '19910403', '20260102'),
        ('000001.SZ', '平安银行', '银行', '主板', 'D', '19910403', '20260105')
        """
    )
    con.close()

    store = Store(target_db)
    try:
        result = bootstrap_l1_from_raw_duckdb(
            store=store,
            source_db=source_db,
            start=date(2026, 1, 2),
            end=date(2026, 1, 5),
        )

        assert result.trade_calendar_rows == 3
        assert result.index_daily_rows == 1
        assert result.stock_daily_rows == 1
        assert result.stock_info_rows == 2
        assert store.get_fetch_progress("trade_cal") == date(2026, 1, 5)
        assert store.get_fetch_progress("index_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_info") == date(2026, 1, 5)

        stock_info = store.read_df(
            "SELECT ts_code, list_status, effective_from FROM l1_stock_info ORDER BY effective_from"
        )
        stock_info["effective_from"] = pd.to_datetime(stock_info["effective_from"]).dt.date
        assert stock_info.to_dict(orient="records") == [
            {"ts_code": "000001.SZ", "list_status": "L", "effective_from": date(2026, 1, 2)},
            {"ts_code": "000001.SZ", "list_status": "D", "effective_from": date(2026, 1, 5)},
        ]
    finally:
        store.close()
