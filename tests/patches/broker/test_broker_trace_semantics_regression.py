from __future__ import annotations

from datetime import date

import pandas as pd

from src.broker.broker import Broker
from src.config import Settings
from src.contracts import Order, Signal, build_signal_id
from src.data.store import Store


def _seed_trade_calendar(store: Store, signal_date: date, exec_date: date, expire_date: date) -> None:
    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": expire_date},
                {"date": expire_date, "is_trade_day": True, "prev_trade_day": exec_date, "next_trade_day": None},
            ]
        ),
    )


def _seed_adj_daily(store: Store, signal_date: date) -> None:
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
                }
            ]
        ),
    )


def test_mss_overlay_trace_helper_exposes_disabled_missing_and_normal_states(tmp_path) -> None:
    db = tmp_path / "mss_trace_patch.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    expire_date = date(2026, 3, 5)
    _seed_trade_calendar(store, signal_date, exec_date, expire_date)
    _seed_adj_daily(store, signal_date)

    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        mss_score=20.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )

    cfg_disabled = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.2,
        MAX_POSITION_PCT=0.5,
        STOP_LOSS_PCT=0.05,
    )
    cfg_enabled = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.2,
        MAX_POSITION_PCT=0.5,
        STOP_LOSS_PCT=0.05,
    )

    Broker(store, cfg_disabled, run_id="mss_disabled").process_signals([signal])
    Broker(store, cfg_enabled, run_id="mss_missing").process_signals([signal])
    # 删除快照后再跑 NORMAL 分支，确保 Broker 只依赖 l3_mss_daily，不回头重算 MSS 内部细节。
    store.conn.execute("DELETE FROM l2_market_snapshot WHERE date = ?", (signal_date,))
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 20.0,
                    "signal": "BEARISH",
                    "market_coefficient_raw": 0.60,
                    "profit_effect_raw": 0.20,
                    "loss_effect_raw": 0.10,
                    "continuity_raw": 0.05,
                    "extreme_raw": 0.01,
                    "volatility_raw": 0.02,
                    "market_coefficient": 40.0,
                    "profit_effect": 30.0,
                    "loss_effect": 70.0,
                    "continuity": 45.0,
                    "extreme": 35.0,
                    "volatility": 55.0,
                }
            ]
        ),
    )
    Broker(store, cfg_enabled, run_id="mss_normal").process_signals([signal])

    disabled = store.get_mss_risk_overlay_trace("mss_disabled", signal.signal_id)
    missing = store.get_mss_risk_overlay_trace("mss_missing", signal.signal_id)
    normal = store.get_mss_risk_overlay_trace("mss_normal", signal.signal_id)

    assert disabled is not None
    assert missing is not None
    assert normal is not None
    assert disabled["overlay_state"] == "DISABLED"
    assert disabled["coverage_flag"] == "OVERLAY_DISABLED"
    assert missing["overlay_state"] == "MISSING"
    assert missing["coverage_flag"] == "SNAPSHOT_MISSING"
    assert normal["overlay_state"] == "NORMAL"
    assert normal["coverage_flag"] == "NORMAL"
    assert normal["market_signal"] == "BEARISH"
    assert normal["market_coefficient_raw"] == 0.60
    store.close()


def test_broker_lifecycle_trace_helper_exposes_risk_and_expiry_origins(tmp_path) -> None:
    db = tmp_path / "broker_lifecycle_patch.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    expire_date = date(2026, 3, 5)
    _seed_trade_calendar(store, signal_date, exec_date, expire_date)
    _seed_adj_daily(store, signal_date)
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

    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.01,
        MAX_POSITION_PCT=0.1,
        STOP_LOSS_PCT=0.05,
        MAX_PENDING_TRADE_DAYS=1,
    )
    broker = Broker(store, cfg, run_id="broker_trace")
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    broker.process_signals([signal])
    broker.execute_pending_orders(exec_date)

    expiring_order = Order(
        order_id="000002_2026-03-03_bof",
        signal_id="000002_2026-03-03_bof",
        code="000002",
        action="BUY",
        quantity=100,
        execute_date=exec_date,
        pattern="bof",
        status="PENDING",
    )
    broker.add_pending_order(expiring_order)
    store.bulk_upsert("l4_orders", pd.DataFrame([expiring_order.model_dump()]))
    broker.expire_orders(expire_date)

    order_trace = store.get_broker_lifecycle_trace("broker_trace", signal.signal_id)
    expiry_trace = store.get_broker_lifecycle_trace("broker_trace", expiring_order.order_id)

    assert set(order_trace["origin"].tolist()) == {"UPSTREAM_SIGNAL"}
    assert expiry_trace.iloc[0]["origin"] == "UPSTREAM_SIGNAL"
    assert expiry_trace.iloc[0]["reason_code"] == "ORDER_TIMEOUT"
    store.close()
