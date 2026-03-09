from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.store import Store


def _seed_trade_calendar(store: Store, start: date, days: int) -> list[date]:
    days_list = [start + timedelta(days=i) for i in range(days)]
    rows = []
    for i, trade_date in enumerate(days_list):
        rows.append(
            {
                "date": trade_date,
                "is_trade_day": True,
                "prev_trade_day": days_list[i - 1] if i > 0 else None,
                "next_trade_day": days_list[i + 1] if i < len(days_list) - 1 else None,
            }
        )
    store.bulk_upsert("l1_trade_calendar", pd.DataFrame(rows))
    return days_list


def _seed_single_stock(store: Store, days_list: list[date], signal_idx: int) -> None:
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "银行",
                    "market": "主板",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": days_list[0],
                }
            ]
        ),
    )

    l1_rows = []
    l2_rows = []
    for i, trade_date in enumerate(days_list):
        low = 9.95
        high = 10.20
        close = 10.00
        open_price = 10.00
        volume = 1_000.0
        if i == signal_idx:
            low = 9.80
            high = 10.10
            close = 10.00
            open_price = 9.90
            volume = 1_300.0

        l1_rows.append(
            {
                "ts_code": "000001.SZ",
                "date": trade_date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "pre_close": 10.00,
                "volume": volume,
                "amount": 100_000_000.0,
                "pct_chg": 0.0,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 11.00,
                "down_limit": 9.00,
                "total_mv": 1_000_000.0,
                "circ_mv": 800_000.0,
            }
        )
        l2_rows.append(
            {
                "code": "000001",
                "date": trade_date,
                "adj_open": open_price,
                "adj_high": high,
                "adj_low": low,
                "adj_close": close,
                "volume": volume,
                "amount": 100_000_000.0,
                "pct_chg": 0.0,
                "ma5": 10.0,
                "ma10": 10.0,
                "ma20": 10.0,
                "ma60": 10.0,
                "volume_ma5": 1_000.0,
                "volume_ma20": 1_000.0,
                "volume_ratio": volume / 1_000.0,
            }
        )

    store.bulk_upsert("l1_stock_daily", pd.DataFrame(l1_rows))
    store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(l2_rows))


def test_force_close_trace_origin_stays_queryable(tmp_path) -> None:
    db = tmp_path / "force_close_patch.duckdb"
    store = Store(db)
    days_list = _seed_trade_calendar(store, start=date(2026, 1, 1), days=30)
    _seed_single_stock(store, days_list, signal_idx=24)
    store.close()

    cfg = Settings(
        PIPELINE_MODE="legacy",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        ENABLE_GENE_FILTER=False,
        PAS_PATTERNS="bof",
        PAS_MIN_HISTORY_DAYS=21,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
        BACKTEST_INITIAL_CASH=1_000_000,
    )

    run_backtest(
        db_path=db,
        config=cfg,
        start=days_list[22],
        end=days_list[25],
        patterns=["bof"],
        initial_cash=1_000_000,
    )

    verify = Store(db)
    force_close_order_id = verify.read_scalar("SELECT order_id FROM l4_orders WHERE order_id LIKE 'FC_%' LIMIT 1")
    trace = verify.get_broker_lifecycle_trace("", str(force_close_order_id))

    assert force_close_order_id is not None
    assert not trace.empty
    assert "FORCE_CLOSE_FILLED" in trace["event_stage"].tolist()
    assert "FORCE_CLOSE" in trace["origin"].tolist()
    verify.close()
