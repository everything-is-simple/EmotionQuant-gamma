from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.data.cleaner import clean_industry_daily, clean_market_snapshot, clean_stock_adj_daily
from src.data.store import Store


def _seed_trade_calendar(store: Store, start: date, days: int) -> None:
    rows = []
    current = start
    for _ in range(days):
        rows.append({"date": current, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None})
        current += timedelta(days=1)
    cal = pd.DataFrame(rows)
    cal["prev_trade_day"] = cal["date"].shift(1)
    cal["next_trade_day"] = cal["date"].shift(-1)
    store.bulk_upsert("l1_trade_calendar", cal)


def test_cleaners_generate_l2_tables(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    store = Store(db)
    base = date(2026, 1, 1)
    _seed_trade_calendar(store, base, 80)

    info = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "industry": "银行",
                "market": "主板",
                "is_st": False,
                "list_date": date(2000, 1, 1),
                "effective_from": base,
            }
        ]
    )
    store.bulk_upsert("l1_stock_info", info)

    rows = []
    price = 10.0
    for i in range(80):
        d = base + timedelta(days=i)
        open_p = price
        close_p = price * 1.001
        rows.append(
            {
                "ts_code": "000001.SZ",
                "date": d,
                "open": open_p,
                "high": close_p * 1.01,
                "low": open_p * 0.99,
                "close": close_p,
                "pre_close": price,
                "volume": 1000 + i * 10,
                "amount": (1000 + i * 10) * close_p,
                "pct_chg": (close_p - price) / price,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": close_p * 1.1,
                "down_limit": close_p * 0.9,
                "total_mv": 1_000_000.0,
                "circ_mv": 900_000.0,
            }
        )
        price = close_p
    store.bulk_upsert("l1_stock_daily", pd.DataFrame(rows))

    start = base + timedelta(days=20)
    end = base + timedelta(days=79)
    assert clean_stock_adj_daily(store, start, end) > 0
    assert clean_industry_daily(store, start, end) > 0
    assert clean_market_snapshot(store, start, end) > 0

    l2_stock = store.read_df("SELECT * FROM l2_stock_adj_daily ORDER BY date")
    l2_industry = store.read_df("SELECT * FROM l2_industry_daily ORDER BY date")
    l2_market = store.read_df("SELECT * FROM l2_market_snapshot ORDER BY date")
    assert not l2_stock.empty
    assert not l2_industry.empty
    assert not l2_market.empty
    assert l2_stock.iloc[-1]["ma20"] is not None
    store.close()


def test_clean_industry_daily_prefers_sw_membership_and_skips_non_trade_day(tmp_path) -> None:
    db = tmp_path / "industry_sw.duckdb"
    store = Store(db)
    trade_day = date(2026, 1, 2)
    weekend = date(2026, 1, 3)
    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": trade_day, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None},
                {"date": weekend, "is_trade_day": False, "prev_trade_day": trade_day, "next_trade_day": None},
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "旧行业",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2000, 1, 1),
                    "effective_from": date(2000, 1, 1),
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l1_sw_industry_member",
        pd.DataFrame(
            [
                {
                    "industry_code": "801780.SI",
                    "industry_name": "银行",
                    "ts_code": "000001.SZ",
                    "in_date": date(1991, 4, 3),
                    "out_date": None,
                    "is_new": "Y",
                    "source_trade_date": trade_day,
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "date": trade_day,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.1,
                    "pre_close": 10.0,
                    "volume": 1000,
                    "amount": 10000,
                    "pct_chg": 0.01,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1_000_000,
                    "circ_mv": 900_000,
                },
                {
                    "ts_code": "000001.SZ",
                    "date": weekend,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.1,
                    "pre_close": 10.0,
                    "volume": 1000,
                    "amount": 10000,
                    "pct_chg": 0.01,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1_000_000,
                    "circ_mv": 900_000,
                },
            ]
        ),
    )

    assert clean_industry_daily(store, trade_day, weekend) == 1
    industry = store.read_df("SELECT industry, date FROM l2_industry_daily ORDER BY date")
    assert industry.to_dict(orient="records") == [{"industry": "银行", "date": pd.Timestamp(trade_day)}]
    assert clean_stock_adj_daily(store, trade_day, weekend) == 1
    dates = store.read_df("SELECT date FROM l2_stock_adj_daily ORDER BY date")
    assert dates["date"].dt.date.tolist() == [trade_day]
    store.close()


def test_clean_industry_daily_without_sw_mapping_falls_back_to_unknown(tmp_path) -> None:
    db = tmp_path / "industry_unknown.duckdb"
    store = Store(db)
    trade_day = date(2026, 1, 2)
    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [{"date": trade_day, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None}]
        ),
    )
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "旧行业",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2000, 1, 1),
                    "effective_from": date(2000, 1, 1),
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "date": trade_day,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.1,
                    "pre_close": 10.0,
                    "volume": 1000,
                    "amount": 10000,
                    "pct_chg": 0.01,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1_000_000,
                    "circ_mv": 900_000,
                }
            ]
        ),
    )

    assert clean_industry_daily(store, trade_day, trade_day) == 1
    industry = store.read_df("SELECT industry FROM l2_industry_daily")
    assert industry["industry"].tolist() == ["未知"]
    store.close()


def test_clean_stock_adj_daily_clears_stale_rows_in_target_range(tmp_path) -> None:
    db = tmp_path / "cleaner_stale_range.duckdb"
    store = Store(db)
    try:
        day_before = date(2026, 2, 9)
        target_day = date(2026, 2, 10)
        store.bulk_upsert(
            "l1_trade_calendar",
            pd.DataFrame(
                [
                    {"date": day_before, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": target_day},
                    {"date": target_day, "is_trade_day": True, "prev_trade_day": day_before, "next_trade_day": None},
                ]
            ),
        )
        store.bulk_upsert(
            "l1_stock_daily",
            pd.DataFrame(
                [
                    {
                        "ts_code": "000001.SZ",
                        "date": day_before,
                        "open": 10.0,
                        "high": 10.2,
                        "low": 9.8,
                        "close": 10.1,
                        "pre_close": 10.0,
                        "volume": 1000,
                        "amount": 10000,
                        "pct_chg": 0.01,
                        "adj_factor": 1.0,
                        "is_halt": False,
                        "up_limit": 11.0,
                        "down_limit": 9.0,
                        "total_mv": 1_000_000,
                        "circ_mv": 900_000,
                    }
                ]
            ),
        )
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(
                [
                    {
                        "code": "999999",
                        "date": target_day,
                        "adj_open": 1.0,
                        "adj_high": 1.0,
                        "adj_low": 1.0,
                        "adj_close": 1.0,
                        "volume": 1.0,
                        "amount": 1.0,
                        "pct_chg": 0.0,
                        "ma5": None,
                        "ma10": None,
                        "ma20": None,
                        "ma60": None,
                        "volume_ma5": None,
                        "volume_ma20": None,
                        "volume_ratio": None,
                    }
                ]
            ),
        )

        assert clean_stock_adj_daily(store, target_day, target_day) == 0
        out = store.read_df("SELECT * FROM l2_stock_adj_daily WHERE date = ?", (target_day,))
        assert out.empty
    finally:
        store.close()
