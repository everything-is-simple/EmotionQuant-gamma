from __future__ import annotations

from datetime import date

import pandas as pd

from src.broker.broker import Broker
from src.config import Settings
from src.contracts import Signal, build_signal_id
from src.data.store import Store


def test_broker_reject_limit_up_and_fill_normal(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    store = Store(db)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.01,
        MAX_POSITION_PCT=0.1,
        STOP_LOSS_PCT=0.05,
    )
    broker = Broker(store, cfg)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)

    # 交易日历 + 估算价格
    cal = pd.DataFrame(
        [
            {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
            {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
        ]
    )
    store.bulk_upsert("l1_trade_calendar", cal)
    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": signal_date,
                    "adj_open": 10.0,
                    "adj_high": 10.2,
                    "adj_low": 9.8,
                    "adj_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.0,
                },
                {
                    "code": "000001",
                    "date": exec_date,
                    "adj_open": 10.1,
                    "adj_high": 10.4,
                    "adj_low": 10.0,
                    "adj_close": 10.2,
                    "volume": 12000,
                    "amount": 1.2e8,
                    "pct_chg": 0.02,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.2,
                },
            ]
        ),
    )

    # 先构造涨停拒单
    store.bulk_upsert(
        "l1_stock_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "date": exec_date,
                    "open": 11.0,
                    "high": 11.0,
                    "low": 11.0,
                    "close": 11.0,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.1,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1e6,
                    "circ_mv": 8e5,
                }
            ]
        ),
    )

    s1 = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    orders = broker.process_signals([s1])
    assert len(orders) == 1
    trades = broker.execute_pending_orders(exec_date)
    assert len(trades) == 0

    # 再改为可成交
    store.bulk_upsert(
        "l1_stock_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "date": exec_date,
                    "open": 10.1,
                    "high": 10.4,
                    "low": 10.0,
                    "close": 10.2,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.02,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1e6,
                    "circ_mv": 8e5,
                }
            ]
        ),
    )
    s2 = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof_retry"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    broker.process_signals([s2])
    trades = broker.execute_pending_orders(exec_date)
    assert len(trades) == 1
    assert trades[0].price > 0
    store.close()

