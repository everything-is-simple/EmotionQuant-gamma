from __future__ import annotations

from datetime import date

import pandas as pd

from src.broker.broker import Broker, Position
from src.config import Settings
from src.contracts import Order, Signal, build_signal_id
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


def test_broker_signal_competition_respects_strength_and_max_positions(tmp_path) -> None:
    db = tmp_path / "test_maxpos.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.2,
        MAX_POSITION_PCT=0.5,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=1,
    )
    broker = Broker(store, cfg)

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
            ]
        ),
    )
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
                    "code": "000002",
                    "date": signal_date,
                    "adj_open": 12.0,
                    "adj_high": 12.2,
                    "adj_low": 11.8,
                    "adj_close": 12.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
                    "ma5": 12.0,
                    "ma10": 12.0,
                    "ma20": 12.0,
                    "ma60": 12.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.0,
                },
            ]
        ),
    )

    low = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof_low"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.1,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    high = Signal(
        signal_id=build_signal_id("000002", signal_date, "bof_high"),
        code="000002",
        signal_date=signal_date,
        action="BUY",
        strength=0.9,
        pattern="bof",
        reason_code="PAS_BOF",
    )

    accepted = broker.process_signals([low, high])
    assert len(accepted) == 1
    assert accepted[0].code == "000002"

    rows = store.read_df(
        """
        SELECT signal_id, code, status, reject_reason
        FROM l4_orders
        ORDER BY signal_id
        """
    )
    assert len(rows) == 2
    reject = rows[rows["status"] == "REJECTED"].iloc[0]
    assert reject["code"] == "000001"
    assert reject["reject_reason"] == "MAX_POSITIONS_REACHED"
    store.close()


def test_broker_rejects_when_cash_insufficient_and_marks_reason(tmp_path) -> None:
    db = tmp_path / "test_cash.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=2_100,
        RISK_PER_TRADE_PCT=1.0,
        MAX_POSITION_PCT=1.0,
        STOP_LOSS_PCT=0.01,
        MAX_POSITIONS=10,
    )
    broker = Broker(store, cfg)

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
            ]
        ),
    )
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
                    "code": "000002",
                    "date": signal_date,
                    "adj_open": 11.0,
                    "adj_high": 11.2,
                    "adj_low": 10.8,
                    "adj_close": 11.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
                    "ma5": 11.0,
                    "ma10": 11.0,
                    "ma20": 11.0,
                    "ma60": 11.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.0,
                },
            ]
        ),
    )

    first = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof_first"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    second = Signal(
        signal_id=build_signal_id("000002", signal_date, "bof_second"),
        code="000002",
        signal_date=signal_date,
        action="BUY",
        strength=0.7,
        pattern="bof",
        reason_code="PAS_BOF",
    )

    accepted = broker.process_signals([first, second])
    assert len(accepted) == 1
    assert accepted[0].code == "000001"

    rejected = store.read_df(
        """
        SELECT code, status, reject_reason
        FROM l4_orders
        WHERE status = 'REJECTED'
        """
    )
    assert len(rejected) == 1
    assert rejected.iloc[0]["code"] == "000002"
    assert rejected.iloc[0]["reject_reason"] == "INSUFFICIENT_CASH"
    store.close()


def test_broker_rechecks_cash_at_execution_open(tmp_path) -> None:
    db = tmp_path / "test_exec_cash.duckdb"
    store = Store(db)
    cfg = Settings(BACKTEST_INITIAL_CASH=500, RISK_PER_TRADE_PCT=0.01, MAX_POSITION_PCT=0.1)
    broker = Broker(store, cfg, initial_cash=500)
    exec_date = date(2026, 3, 4)

    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": exec_date,
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
                    "date": exec_date,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.1,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.01,
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

    order = Order(
        order_id="000001_2026-03-03_bof",
        signal_id="000001_2026-03-03_bof",
        code="000001",
        action="BUY",
        quantity=100,
        execute_date=exec_date,
        pattern="bof",
        status="PENDING",
    )
    broker.add_pending_order(order)
    store.bulk_upsert("l4_orders", pd.DataFrame([order.model_dump()]))

    trades = broker.execute_pending_orders(exec_date)
    assert len(trades) == 0
    row = store.read_df(
        "SELECT status, reject_reason FROM l4_orders WHERE order_id = ?",
        (order.order_id,),
    ).iloc[0]
    assert row["status"] == "REJECTED"
    assert row["reject_reason"] == "INSUFFICIENT_CASH_AT_EXECUTION"
    store.close()


def test_broker_generates_stop_loss_exit_order_t_plus_1(tmp_path) -> None:
    db = tmp_path / "test_exit.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        STOP_LOSS_PCT=0.05,
        TRAILING_STOP_PCT=0.08,
    )
    broker = Broker(store, cfg)

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
            ]
        ),
    )
    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": signal_date,
                    "adj_open": 9.4,
                    "adj_high": 9.6,
                    "adj_low": 9.2,
                    "adj_close": 9.4,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": -0.06,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.0,
                }
            ]
        ),
    )

    # 手工放入一个持仓，模拟前序 BUY 已成交。
    broker.portfolio["000001"] = Position(
        code="000001",
        entry_date=date(2026, 3, 1),
        entry_price=10.0,
        quantity=100,
        current_price=10.0,
        max_price=10.0,
        pattern="bof",
        is_paper=False,
    )

    exits = broker.generate_exit_orders(signal_date)
    assert len(exits) == 1
    assert exits[0].action == "SELL"
    assert exits[0].execute_date == exec_date
    assert exits[0].quantity == 100
    assert exits[0].order_id.startswith("EXIT_")
    store.close()


def test_broker_exit_not_duplicated_when_pending_exists(tmp_path) -> None:
    db = tmp_path / "test_exit_dup.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(BACKTEST_INITIAL_CASH=1_000_000, STOP_LOSS_PCT=0.05, TRAILING_STOP_PCT=0.08)
    broker = Broker(store, cfg)

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
            ]
        ),
    )
    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": signal_date,
                    "adj_open": 9.4,
                    "adj_high": 9.6,
                    "adj_low": 9.2,
                    "adj_close": 9.4,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": -0.06,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 10000,
                    "volume_ma20": 10000,
                    "volume_ratio": 1.0,
                }
            ]
        ),
    )
    broker.portfolio["000001"] = Position(
        code="000001",
        entry_date=date(2026, 3, 1),
        entry_price=10.0,
        quantity=100,
        current_price=10.0,
        max_price=10.0,
        pattern="bof",
        is_paper=False,
    )
    pending = Order(
        order_id="EXIT_000001_2026-03-03_stop_loss",
        signal_id="000001_2026-03-03_stop_loss",
        code="000001",
        action="SELL",
        quantity=100,
        execute_date=exec_date,
        pattern="bof",
        status="PENDING",
    )
    broker.add_pending_order(pending)

    exits = broker.generate_exit_orders(signal_date)
    assert exits == []
    store.close()
