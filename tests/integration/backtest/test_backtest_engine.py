from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.store import Store


def _seed_trade_calendar(store: Store, start: date, days: int) -> list[date]:
    days_list = [start + timedelta(days=i) for i in range(days)]
    rows = []
    for i, d in enumerate(days_list):
        rows.append(
            {
                "date": d,
                "is_trade_day": True,
                "prev_trade_day": days_list[i - 1] if i > 0 else None,
                "next_trade_day": days_list[i + 1] if i < len(days_list) - 1 else None,
            }
        )
    store.bulk_upsert("l1_trade_calendar", pd.DataFrame(rows))
    return days_list


def _seed_single_stock(store: Store, days_list: list[date], signal_idx: int) -> None:
    stock_info = pd.DataFrame(
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
    )
    store.bulk_upsert("l1_stock_info", stock_info)

    l1_rows = []
    l2_rows = []
    for i, d in enumerate(days_list):
        low = 9.95
        high = 10.20
        close = 10.00
        open_price = 10.00
        volume = 1_000.0

        # 仅在 signal_idx 构造 BOF 触发：假破位后收回 + 收盘位于振幅上部 + 放量。
        if i == signal_idx:
            low = 9.80
            high = 10.10
            close = 10.00
            open_price = 9.90
            volume = 1_300.0

        l1_rows.append(
            {
                "ts_code": "000001.SZ",
                "date": d,
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
                "date": d,
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


def _seed_partial_exit_path(store: Store, days_list: list[date], signal_idx: int) -> None:
    stock_info = pd.DataFrame(
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
    )
    store.bulk_upsert("l1_stock_info", stock_info)

    signal_day = days_list[signal_idx]
    buy_day = days_list[signal_idx + 1]
    rally_day = days_list[signal_idx + 2]
    trailing_trigger_day = days_list[signal_idx + 3]
    first_exit_day = days_list[signal_idx + 4]
    final_day = days_list[signal_idx + 5]

    l1_rows = []
    l2_rows = []
    for d in days_list:
        open_price = 10.0
        high = 10.2
        low = 9.95
        close = 10.0
        volume = 1_000.0

        if d == signal_day:
            low = 9.80
            high = 10.10
            close = 10.00
            open_price = 9.90
            volume = 1_300.0
        elif d == buy_day:
            open_price = 10.0
            high = 10.2
            low = 9.9
            close = 10.1
        elif d == rally_day:
            open_price = 10.1
            high = 12.2
            low = 10.0
            close = 12.0
        elif d == trailing_trigger_day:
            open_price = 11.6
            high = 11.8
            low = 10.7
            close = 10.8
        elif d == first_exit_day:
            open_price = 10.7
            high = 10.9
            low = 10.6
            close = 10.7
        elif d == final_day:
            open_price = 10.6
            high = 10.7
            low = 10.5
            close = 10.6

        l1_rows.append(
            {
                "ts_code": "000001.SZ",
                "date": d,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "pre_close": 10.0,
                "volume": volume,
                "amount": 100_000_000.0,
                "pct_chg": 0.0,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 20.0,
                "down_limit": 5.0,
                "total_mv": 1_000_000.0,
                "circ_mv": 800_000.0,
            }
        )
        l2_rows.append(
            {
                "code": "000001",
                "date": d,
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


def test_backtest_t_plus_1_and_idempotency(tmp_path) -> None:
    db = tmp_path / "bt.duckdb"
    store = Store(db)
    days_list = _seed_trade_calendar(store, start=date(2026, 1, 1), days=30)
    signal_idx = 24
    _seed_single_stock(store, days_list, signal_idx=signal_idx)
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

    start = days_list[22]
    end = days_list[25]

    first = run_backtest(db_path=db, config=cfg, start=start, end=end, patterns=["bof"], initial_cash=1_000_000)

    verify = Store(db)
    buy_orders = verify.read_df(
        "SELECT order_id, execute_date FROM l4_orders WHERE action='BUY' ORDER BY order_id"
    )
    buy_trades = verify.read_df(
        "SELECT trade_id, execute_date, action FROM l4_trades WHERE action='BUY' ORDER BY trade_id"
    )
    force_close_orders = verify.read_df(
        "SELECT order_id FROM l4_orders WHERE order_id LIKE 'FC_%' ORDER BY order_id"
    )
    force_close_trace = verify.read_df(
        """
        SELECT event_stage, origin
        FROM broker_order_lifecycle_trace_exp
        WHERE event_stage = 'FORCE_CLOSE_FILLED'
        """
    )

    assert not buy_orders.empty
    assert not buy_trades.empty
    assert not force_close_orders.empty
    assert force_close_trace.iloc[0]["origin"] == "FORCE_CLOSE"

    expected_exec_date = days_list[signal_idx + 1]
    assert buy_orders.iloc[0]["execute_date"].date() == expected_exec_date
    assert buy_trades.iloc[0]["execute_date"].date() == expected_exec_date

    order_ids_1 = set(verify.read_df("SELECT order_id FROM l4_orders")["order_id"].tolist())
    trade_ids_1 = set(verify.read_df("SELECT trade_id FROM l4_trades")["trade_id"].tolist())
    verify.close()

    second = run_backtest(db_path=db, config=cfg, start=start, end=end, patterns=["bof"], initial_cash=1_000_000)

    verify2 = Store(db)
    order_ids_2 = set(verify2.read_df("SELECT order_id FROM l4_orders")["order_id"].tolist())
    trade_ids_2 = set(verify2.read_df("SELECT trade_id FROM l4_trades")["trade_id"].tolist())
    verify2.close()

    # 幂等要求：同输入重跑，主键集合不应变化。
    assert order_ids_1 == order_ids_2
    assert trade_ids_1 == trade_ids_2

    assert first.trade_count >= 1
    assert second.trade_count == first.trade_count


def test_backtest_partial_exit_control_variants_persist_position_aware_exit_fields(tmp_path) -> None:
    signal_idx = 24

    def _prepare_db(path) -> list[date]:
        store = Store(path)
        days = _seed_trade_calendar(store, start=date(2026, 1, 1), days=35)
        _seed_partial_exit_path(store, days, signal_idx=signal_idx)
        store.close()
        return days

    full_db = tmp_path / "bt_full_exit.duckdb"
    naive_db = tmp_path / "bt_naive_exit.duckdb"
    full_days = _prepare_db(full_db)
    naive_days = _prepare_db(naive_db)

    full_cfg = Settings(
        PIPELINE_MODE="legacy",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        ENABLE_GENE_FILTER=False,
        PAS_PATTERNS="bof",
        PAS_MIN_HISTORY_DAYS=21,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
        BACKTEST_INITIAL_CASH=1_000_000,
        EXIT_CONTROL_MODE="full_exit_control",
        POSITION_SIZING_MODE="single_lot",
        FIXED_LOT_SIZE=200,
        TRAILING_STOP_PCT=0.10,
    )
    naive_cfg = full_cfg.model_copy(update={"exit_control_mode": "naive_trail_scale_out_50_50_control"})

    start = full_days[22]
    end = full_days[29]

    run_backtest(db_path=full_db, config=full_cfg, start=start, end=end, patterns=["bof"], initial_cash=1_000_000)
    run_backtest(db_path=naive_db, config=naive_cfg, start=naive_days[22], end=naive_days[29], patterns=["bof"], initial_cash=1_000_000)

    full_store = Store(full_db)
    naive_store = Store(naive_db)
    try:
        full_sells = full_store.read_df(
            """
            SELECT position_id, exit_reason_code, is_partial_exit, remaining_qty_after
            FROM l4_trades
            WHERE action = 'SELL'
            ORDER BY execute_date, trade_id
            """
        )
        naive_sells = naive_store.read_df(
            """
            SELECT position_id, exit_reason_code, is_partial_exit, remaining_qty_after
            FROM l4_trades
            WHERE action = 'SELL'
            ORDER BY execute_date, trade_id
            """
        )

        assert len(full_sells) == 1
        assert full_sells.iloc[0]["position_id"] is not None
        assert bool(full_sells.iloc[0]["is_partial_exit"]) is False
        assert int(full_sells.iloc[0]["remaining_qty_after"]) == 0

        assert len(naive_sells) >= 2
        assert naive_sells.iloc[0]["position_id"] is not None
        assert bool(naive_sells.iloc[0]["is_partial_exit"]) is True
        assert naive_sells.iloc[0]["exit_reason_code"] == "TRAILING_STOP"
        assert int(naive_sells.iloc[0]["remaining_qty_after"]) == 100
        assert int(naive_sells.iloc[-1]["remaining_qty_after"]) == 0
        assert set(naive_sells["exit_reason_code"].tolist()).issubset({"TRAILING_STOP", "FORCE_CLOSE"})
    finally:
        full_store.close()
        naive_store.close()
