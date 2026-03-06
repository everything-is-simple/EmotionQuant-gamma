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
        self.member_calls: list[tuple[str, str]] = []

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

    def index_classify(self, level: str, src: str) -> pd.DataFrame:
        assert level == "L1"
        assert src == "SW2021"
        return pd.DataFrame(
            [
                {"index_code": "801780.SI", "industry_name": "银行"},
                {"index_code": "801080.SI", "industry_name": "电子"},
            ]
        )

    def index_member_all(self, l1_code: str, is_new: str) -> pd.DataFrame:
        self.member_calls.append((l1_code, is_new))
        rows = {
            ("801780.SI", "Y"): [
                {
                    "l1_code": "801780.SI",
                    "l1_name": "银行",
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "in_date": "19910403",
                    "out_date": "",
                    "is_new": "Y",
                }
            ],
            ("801780.SI", "N"): [
                {
                    "l1_code": "801780.SI",
                    "l1_name": "银行",
                    "ts_code": "600001.SH",
                    "name": "历史银行股",
                    "in_date": "20000101",
                    "out_date": "20100101",
                    "is_new": "N",
                }
            ],
            ("801080.SI", "Y"): [
                {
                    "l1_code": "801080.SI",
                    "l1_name": "电子",
                    "ts_code": "000100.SZ",
                    "name": "样本电子股",
                    "in_date": "20000101",
                    "out_date": "",
                    "is_new": "Y",
                }
            ],
            ("801080.SI", "N"): [],
        }
        return pd.DataFrame(rows.get((l1_code, is_new), []))


def test_fetch_stock_info_keeps_list_status(monkeypatch) -> None:
    fake_ts = types.SimpleNamespace(pro_api=lambda token: _FakePro())
    monkeypatch.setitem(sys.modules, "tushare", fake_ts)

    fetcher = TuShareFetcher(token="dummy-token")
    df = fetcher.fetch_stock_info()

    assert set(df["list_status"]) == {"L", "D"}
    assert "effective_from" in df.columns


def test_fetch_sw_industry_members_returns_l1_mapping(monkeypatch) -> None:
    fake_pro = _FakePro()
    fake_ts = types.SimpleNamespace(pro_api=lambda token: fake_pro)
    monkeypatch.setitem(sys.modules, "tushare", fake_ts)

    fetcher = TuShareFetcher(token="dummy-token", sleep_interval=0.0)
    df = fetcher.fetch_sw_industry_members(start=date(2026, 1, 1), end=date(2026, 1, 5))

    assert set(df["industry_name"]) == {"银行", "电子"}
    assert set(df["ts_code"]) == {"000001.SZ", "000100.SZ", "600001.SH"}
    assert set(fake_pro.member_calls) == {
        ("801780.SI", "Y"),
        ("801780.SI", "N"),
        ("801080.SI", "Y"),
        ("801080.SI", "N"),
    }
    assert "source_trade_date" in df.columns


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
    con.execute(
        """
        CREATE TABLE raw_index_classify (
            index_code VARCHAR,
            industry_name VARCHAR,
            level VARCHAR,
            industry_code VARCHAR,
            src VARCHAR,
            trade_date VARCHAR,
            is_pub VARCHAR,
            parent_code VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_index_classify VALUES
        ('801780.SI', '银行', 'L1', '801780', 'SW2021', '20240701', '1', NULL)
        """
    )
    con.execute(
        """
        CREATE TABLE raw_index_member (
            index_code VARCHAR,
            con_code VARCHAR,
            in_date VARCHAR,
            out_date VARCHAR,
            trade_date VARCHAR,
            ts_code VARCHAR,
            stock_code VARCHAR,
            is_new VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO raw_index_member VALUES
        ('801780.SI', '000001.SZ', '19910403', '', '20260102', '000001.SZ', '000001', 'Y'),
        ('801780.SI', '000001.SZ', '19910403', '20260104', '20260105', '000001.SZ', '000001', 'N')
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
        assert result.sw_industry_member_rows == 1
        assert store.get_fetch_progress("trade_cal") == date(2026, 1, 5)
        assert store.get_fetch_progress("index_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_info") == date(2026, 1, 5)
        assert store.get_fetch_progress("sw_industry_member") == date(2026, 1, 5)

        stock_info = store.read_df(
            "SELECT ts_code, list_status, effective_from FROM l1_stock_info ORDER BY effective_from"
        )
        stock_info["effective_from"] = pd.to_datetime(stock_info["effective_from"]).dt.date
        assert stock_info.to_dict(orient="records") == [
            {"ts_code": "000001.SZ", "list_status": "L", "effective_from": date(2026, 1, 2)},
            {"ts_code": "000001.SZ", "list_status": "D", "effective_from": date(2026, 1, 5)},
        ]
        sw_map = store.read_df(
            "SELECT industry_name, ts_code, in_date, out_date, is_new "
            "FROM l1_sw_industry_member ORDER BY ts_code, in_date"
        )
        sw_map["in_date"] = pd.to_datetime(sw_map["in_date"]).dt.date
        sw_map["out_date"] = pd.to_datetime(sw_map["out_date"]).dt.date
        assert sw_map.to_dict(orient="records") == [
            {
                "industry_name": "银行",
                "ts_code": "000001.SZ",
                "in_date": date(1991, 4, 3),
                "out_date": date(2026, 1, 4),
                "is_new": "N",
            }
        ]
    finally:
        store.close()
