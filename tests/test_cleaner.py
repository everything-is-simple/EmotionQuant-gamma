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

