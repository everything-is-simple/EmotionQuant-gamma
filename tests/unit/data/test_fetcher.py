from __future__ import annotations

import sys
import types
from datetime import date

import duckdb
import pandas as pd

from src.data.fetcher import (
    TuShareFetcher,
    bootstrap_l1_from_raw_duckdb,
    repair_l1_partitions_from_raw_duckdb,
)
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


def test_fetch_industry_members_returns_l1_mapping(monkeypatch) -> None:
    fake_pro = _FakePro()
    fake_ts = types.SimpleNamespace(pro_api=lambda token: fake_pro)
    monkeypatch.setitem(sys.modules, "tushare", fake_ts)

    fetcher = TuShareFetcher(token="dummy-token", sleep_interval=0.0)
    df = fetcher.fetch_industry_members(start=date(2026, 1, 1), end=date(2026, 1, 5))

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
        assert result.industry_member_rows == 1
        assert store.get_fetch_progress("trade_cal") == date(2026, 1, 5)
        assert store.get_fetch_progress("index_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_daily") == date(2026, 1, 2)
        assert store.get_fetch_progress("stock_info") == date(2026, 1, 5)
        assert store.get_fetch_progress("industry_member") == date(2026, 1, 5)

        stock_info = store.read_df(
            "SELECT ts_code, list_status, effective_from FROM l1_stock_info ORDER BY effective_from"
        )
        stock_info["effective_from"] = pd.to_datetime(stock_info["effective_from"]).dt.date
        assert stock_info.to_dict(orient="records") == [
            {"ts_code": "000001.SZ", "list_status": "L", "effective_from": date(2026, 1, 2)},
            {"ts_code": "000001.SZ", "list_status": "D", "effective_from": date(2026, 1, 5)},
        ]
        stock_daily = store.read_df(
            "SELECT ts_code, date, pre_close, up_limit, down_limit FROM l1_stock_daily ORDER BY ts_code, date"
        )
        stock_daily["date"] = pd.to_datetime(stock_daily["date"]).dt.date
        assert stock_daily.to_dict(orient="records") == [
            {
                "ts_code": "000001.SZ",
                "date": date(2026, 1, 2),
                "pre_close": 9.8,
                "up_limit": 10.78,
                "down_limit": 8.82,
            }
        ]
        sw_map = store.read_df(
            "SELECT industry_name, ts_code, in_date, out_date, is_new "
            "FROM l1_industry_member ORDER BY ts_code, in_date"
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


def test_repair_l1_partitions_from_raw_duckdb_replaces_range_only(tmp_path) -> None:
    source_db = tmp_path / "raw_repair.duckdb"
    target_db = tmp_path / "target_repair.duckdb"

    con = duckdb.connect(str(source_db))
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
        ('000001.SZ', '20260210', 10, 10.5, 9.8, 10.2, 10.0, 1000, 10000, 2.0),
        ('000002.SZ', '20260210', 20, 20.5, 19.8, 20.2, 20.0, 2000, 20000, 1.0),
        ('000001.SZ', '20260211', 10.2, 10.6, 10.0, 10.4, 10.2, 1100, 11000, 1.5)
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
        ('000001.SZ', '20260210', 1000000, 800000),
        ('000002.SZ', '20260210', 2000000, 1500000),
        ('000001.SZ', '20260211', 1001000, 801000)
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
        ('000001.SH', '20260210', 1, 1, 1, 1, 1, 0, 10, 10),
        ('000001.SH', '20260211', 1, 1, 1, 1, 1, 0, 10, 10)
        """
    )
    con.close()

    store = Store(target_db)
    try:
        store.bulk_upsert(
            "l1_stock_daily",
            pd.DataFrame(
                [
                    {
                        "ts_code": "000099.SZ",
                        "date": date(2026, 2, 9),
                        "open": 1.0,
                        "high": 1.0,
                        "low": 1.0,
                        "close": 1.0,
                        "pre_close": 1.0,
                        "volume": 1.0,
                        "amount": 1.0,
                        "pct_chg": 0.0,
                        "adj_factor": 1.0,
                        "is_halt": False,
                        "up_limit": None,
                        "down_limit": None,
                        "total_mv": 1.0,
                        "circ_mv": 1.0,
                    },
                    {
                        "ts_code": "000001.SZ",
                        "date": date(2026, 2, 10),
                        "open": 99.0,
                        "high": 99.0,
                        "low": 99.0,
                        "close": 99.0,
                        "pre_close": 99.0,
                        "volume": 99.0,
                        "amount": 99.0,
                        "pct_chg": 0.0,
                        "adj_factor": 1.0,
                        "is_halt": False,
                        "up_limit": None,
                        "down_limit": None,
                        "total_mv": 99.0,
                        "circ_mv": 99.0,
                    },
                ]
            ),
        )

        result = repair_l1_partitions_from_raw_duckdb(
            store=store,
            source_db=source_db,
            start=date(2026, 2, 10),
            end=date(2026, 2, 11),
        )

        assert result.stock_daily_rows == 3
        assert result.index_daily_rows == 2
        stock_daily = store.read_df(
            "SELECT ts_code, date, close, pre_close, up_limit, down_limit FROM l1_stock_daily ORDER BY date, ts_code"
        )
        stock_daily["date"] = pd.to_datetime(stock_daily["date"]).dt.date
        assert stock_daily[["ts_code", "date", "close", "pre_close"]].to_dict(orient="records") == [
            {"ts_code": "000099.SZ", "date": date(2026, 2, 9), "close": 1.0, "pre_close": 1.0},
            {"ts_code": "000001.SZ", "date": date(2026, 2, 10), "close": 10.2, "pre_close": 10.0},
            {"ts_code": "000002.SZ", "date": date(2026, 2, 10), "close": 20.2, "pre_close": 20.0},
            {"ts_code": "000001.SZ", "date": date(2026, 2, 11), "close": 10.4, "pre_close": 10.2},
        ]
        assert pd.isna(stock_daily.iloc[0]["up_limit"])
        assert pd.isna(stock_daily.iloc[0]["down_limit"])
        assert stock_daily.iloc[1]["up_limit"] == 11.0
        assert stock_daily.iloc[1]["down_limit"] == 9.0
        assert stock_daily.iloc[2]["up_limit"] == 22.0
        assert stock_daily.iloc[2]["down_limit"] == 18.0
        assert stock_daily.iloc[3]["up_limit"] == 11.22
        assert stock_daily.iloc[3]["down_limit"] == 9.18
    finally:
        store.close()


def test_bootstrap_local_price_limits_keep_gem_new_listing_unlimited(tmp_path) -> None:
    source_db = tmp_path / "raw_gem_limit.duckdb"
    target_db = tmp_path / "target_gem_limit.duckdb"

    con = duckdb.connect(str(source_db))
    con.execute("CREATE TABLE raw_trade_cal (cal_date VARCHAR, is_open INTEGER)")
    con.execute("INSERT INTO raw_trade_cal VALUES ('20260316', 1), ('20260317', 1)")
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
        ('000001.SH', '20260317', 1, 1, 1, 1, 1, 0, 10, 10)
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
        ('300001.SZ', '20260317', 15.0, 16.0, 14.5, 15.5, 15.0, 1000, 10000, 3.33)
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
        ('300001.SZ', '20260317', 1000000, 800000)
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
        ('300001.SZ', '创业新股', '电子', 'SZ', 'L', '20260317', '20260317')
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
    con.close()

    store = Store(target_db)
    try:
        bootstrap_l1_from_raw_duckdb(
            store=store,
            source_db=source_db,
            start=date(2026, 3, 17),
            end=date(2026, 3, 17),
        )
        row = store.read_df(
            "SELECT ts_code, up_limit, down_limit FROM l1_stock_daily WHERE ts_code = '300001.SZ'"
        ).iloc[0]
        assert pd.isna(row["up_limit"])
        assert pd.isna(row["down_limit"])
    finally:
        store.close()
