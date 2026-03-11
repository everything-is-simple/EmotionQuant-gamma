from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.broker.broker import Broker, Position
from src.broker.risk import BrokerRiskState
from src.config import Settings
from src.contracts import Order, Signal, build_signal_id
from src.data.store import Store


def _seed_trade_calendar(store: Store, signal_date: date, exec_date: date) -> None:
    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": None},
            ]
        ),
    )


def _seed_adj_daily(store: Store, rows: list[dict]) -> None:
    store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(rows))


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


def test_broker_mss_overlay_reduces_position_size_under_bearish_regime(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_size.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.20,
        MAX_POSITION_PCT=0.50,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=10,
        MSS_BULLISH_RISK_PER_TRADE_MULT=1.0,
        MSS_NEUTRAL_RISK_PER_TRADE_MULT=0.7,
        MSS_BEARISH_RISK_PER_TRADE_MULT=0.4,
        MSS_BULLISH_MAX_POSITION_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITION_MULT=0.7,
        MSS_BEARISH_MAX_POSITION_MULT=0.4,
    )
    risk = Broker(store, cfg).risk

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set())

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": "ACCELERATION",
                    "phase_trend": "UP",
                    "phase_days": 2,
                    "position_advice": "50%-70%",
                    "risk_regime": "RISK_ON",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    bullish = risk.assess_signal(signal, state)
    assert bullish.order is not None

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    risk._mss_overlay_cache.clear()
    bearish = risk.assess_signal(signal, state)
    assert bearish.order is not None

    # 这里故意制造“signal 看起来更强，但 regime 更保守”的场景，
    # 锁定 Broker 真正按 risk_regime 缩仓，而不是继续按 signal 选倍率。
    assert bullish.order.quantity == 50000
    assert bearish.order.quantity == 20000
    assert bearish.order.quantity < bullish.order.quantity
    assert bullish.overlay is not None and bullish.overlay.risk_regime == "RISK_ON"
    assert bearish.overlay is not None and bearish.overlay.risk_regime == "RISK_OFF"
    assert bearish.overlay.signal == "BULLISH"
    store.close()


def test_broker_mss_overlay_reduces_effective_max_positions_under_bearish_regime(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_maxpos.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.01,
        MAX_POSITION_PCT=0.10,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=3,
        MSS_BULLISH_MAX_POSITIONS_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITIONS_MULT=0.7,
        MSS_BEARISH_MAX_POSITIONS_MULT=0.4,
    )
    risk = Broker(store, cfg).risk

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
        [
            {
                "code": "000003",
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000003", signal_date, "bof"),
        code="000003",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    state = BrokerRiskState(
        cash=1_000_000,
        portfolio_market_value=100_000.0,
        holdings={"000001", "000002"},
    )

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": "ACCELERATION",
                    "phase_trend": "UP",
                    "phase_days": 2,
                    "position_advice": "50%-70%",
                    "risk_regime": "RISK_ON",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    bullish = risk.assess_signal(signal, state)
    assert bullish.order is not None

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    risk._mss_overlay_cache.clear()
    bearish = risk.assess_signal(signal, state)

    assert bearish.order is None
    assert bearish.reject_reason == "MAX_POSITIONS_REACHED"
    assert bearish.overlay is not None and bearish.overlay.risk_regime == "RISK_OFF"
    store.close()


def test_broker_overlay_only_max_positions_changes_capacity_without_resizing_quantity(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_only_maxpos.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.20,
        MAX_POSITION_PCT=0.50,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=3,
        MSS_BULLISH_MAX_POSITIONS_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITIONS_MULT=0.7,
        MSS_BEARISH_MAX_POSITIONS_MULT=0.4,
        MSS_BULLISH_RISK_PER_TRADE_MULT=1.0,
        MSS_NEUTRAL_RISK_PER_TRADE_MULT=1.0,
        MSS_BEARISH_RISK_PER_TRADE_MULT=1.0,
        MSS_BULLISH_MAX_POSITION_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITION_MULT=1.0,
        MSS_BEARISH_MAX_POSITION_MULT=1.0,
    )
    risk = Broker(store, cfg).risk

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
        [
            {
                "code": "000004",
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000004", signal_date, "bof"),
        code="000004",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    open_state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set())
    crowded_state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings={"000099"})

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": "ACCELERATION",
                    "phase_trend": "UP",
                    "phase_days": 2,
                    "position_advice": "50%-70%",
                    "risk_regime": "RISK_ON",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    bullish_open = risk.assess_signal(signal, open_state)
    assert bullish_open.order is not None

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    risk._mss_overlay_cache.clear()
    bearish_open = risk.assess_signal(signal, open_state)
    assert bearish_open.order is not None

    risk._mss_overlay_cache.clear()
    bearish_crowded = risk.assess_signal(signal, crowded_state)

    # 这个用例锁定“只有 max_positions 在动”的语义：
    # 空仓情况下，仓位数量不能被 max_positions 连带压缩；
    # 只有当持仓数触顶时，才应该体现为 MAX_POSITIONS_REACHED 拒绝。
    assert bullish_open.overlay is not None
    assert bearish_open.overlay is not None
    assert bullish_open.overlay.max_positions == 3
    assert bearish_open.overlay.max_positions == 1
    assert bullish_open.order.quantity == 50000
    assert bearish_open.order.quantity == bullish_open.order.quantity
    assert bearish_crowded.order is None
    assert bearish_crowded.reject_reason == "MAX_POSITIONS_REACHED"
    assert bearish_crowded.overlay is not None
    assert bearish_crowded.overlay.max_positions == 1
    store.close()


def test_broker_carryover_buffer_reserves_only_one_fresh_slot_per_day(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_carryover_buffer.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.20,
        MAX_POSITION_PCT=0.50,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=10,
        MSS_BULLISH_MAX_POSITIONS_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITIONS_MULT=1.0,
        MSS_BEARISH_MAX_POSITIONS_MULT=0.4,
        MSS_MAX_POSITIONS_MODE="carryover_buffer",
        MSS_MAX_POSITIONS_BUFFER_SLOTS=1,
        MSS_BULLISH_RISK_PER_TRADE_MULT=1.0,
        MSS_NEUTRAL_RISK_PER_TRADE_MULT=1.0,
        MSS_BEARISH_RISK_PER_TRADE_MULT=1.0,
        MSS_BULLISH_MAX_POSITION_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITION_MULT=1.0,
        MSS_BEARISH_MAX_POSITION_MULT=1.0,
    )
    broker = Broker(store, cfg, run_id="carryover_buffer")

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
        [
            {
                "code": "000010",
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
                "code": "000011",
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
        ],
    )
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )

    for code in ["600001", "600002", "600003", "600004", "600005"]:
        broker.portfolio[code] = Position(
            code=code,
            entry_date=date(2026, 3, 1),
            entry_price=10.0,
            quantity=100,
            current_price=10.0,
            max_price=10.0,
            pattern="bof",
            is_paper=False,
        )

    first = Signal(
        signal_id=build_signal_id("000010", signal_date, "bof_first"),
        code="000010",
        signal_date=signal_date,
        action="BUY",
        strength=0.9,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=95.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    second = Signal(
        signal_id=build_signal_id("000011", signal_date, "bof_second"),
        code="000011",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )

    accepted = broker.process_signals([second, first])
    assert len(accepted) == 1
    assert accepted[0].code == "000010"
    assert accepted[0].quantity == 50200

    orders = store.read_df(
        """
        SELECT code, status, reject_reason
        FROM l4_orders
        ORDER BY code ASC
        """
    )
    assert orders["status"].tolist() == ["PENDING", "REJECTED"]
    assert orders.iloc[1]["reject_reason"] == "MAX_POSITIONS_REACHED"

    trace = store.read_df(
        """
        SELECT code, target_max_positions, effective_max_positions, max_positions_mode,
               max_positions_buffer_slots, holdings_before, decision_status
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ?
        ORDER BY code ASC
        """,
        ("carryover_buffer",),
    )

    # 这个用例锁定 P4.1-C 候选语义：
    # shrink 目标仍然是 4，但在日初已 5 仓的 carryover 场景里，只额外保留 1 个 fresh slot，
    # 因此第一笔 rank 更高的信号能进，第二笔继续被挡下，不会把 shrink 直接放回 base=10。
    assert trace["target_max_positions"].tolist() == [4, 4]
    assert trace["effective_max_positions"].tolist() == [6, 6]
    assert trace["max_positions_mode"].tolist() == ["carryover_buffer", "carryover_buffer"]
    assert trace["max_positions_buffer_slots"].tolist() == [1, 1]
    assert trace["holdings_before"].tolist() == [5, 6]
    assert trace["decision_status"].tolist() == ["ACCEPTED", "REJECTED"]
    store.close()


def test_broker_no_maxpos_shrink_keeps_base_slot_cap_but_preserves_sizing_overlay(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_no_maxpos_shrink.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score_size_only_overlay",
        MSS_RISK_OVERLAY_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score_size_only_overlay",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.20,
        MAX_POSITION_PCT=0.50,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=10,
        MSS_MAX_POSITIONS_MODE="no_maxpos_shrink",
        MSS_MAX_POSITIONS_BUFFER_SLOTS=0,
        MSS_BULLISH_MAX_POSITIONS_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITIONS_MULT=1.0,
        MSS_BEARISH_MAX_POSITIONS_MULT=0.4,
        MSS_BULLISH_RISK_PER_TRADE_MULT=1.0,
        MSS_NEUTRAL_RISK_PER_TRADE_MULT=1.0,
        MSS_BEARISH_RISK_PER_TRADE_MULT=0.4,
        MSS_BULLISH_MAX_POSITION_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITION_MULT=1.0,
        MSS_BEARISH_MAX_POSITION_MULT=0.4,
    )
    broker = Broker(store, cfg, run_id="no_maxpos_shrink")

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
        [
            {
                "code": "000020",
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
                "code": "000021",
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
        ],
    )
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )

    for code in ["600001", "600002", "600003", "600004", "600005"]:
        broker.portfolio[code] = Position(
            code=code,
            entry_date=date(2026, 3, 1),
            entry_price=10.0,
            quantity=100,
            current_price=10.0,
            max_price=10.0,
            pattern="bof",
            is_paper=False,
        )

    first = Signal(
        signal_id=build_signal_id("000020", signal_date, "bof_first"),
        code="000020",
        signal_date=signal_date,
        action="BUY",
        strength=0.9,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=95.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score_size_only_overlay",
    )
    second = Signal(
        signal_id=build_signal_id("000021", signal_date, "bof_second"),
        code="000021",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score_size_only_overlay",
    )

    accepted = broker.process_signals([second, first])
    assert len(accepted) == 2
    assert accepted[0].quantity == 20100
    assert accepted[1].quantity == 16000

    orders = store.read_df(
        """
        SELECT code, status, reject_reason
        FROM l4_orders
        ORDER BY code ASC
        """
    )
    assert orders["status"].tolist() == ["PENDING", "PENDING"]
    assert orders["reject_reason"].isna().all()

    trace = store.read_df(
        """
        SELECT code, target_max_positions, effective_max_positions, max_positions_mode,
               max_positions_buffer_slots, holdings_before, decision_status,
               effective_risk_per_trade_pct, effective_max_position_pct
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ?
        ORDER BY code ASC
        """,
        ("no_maxpos_shrink",),
    )

    # P4.1-E 锁定的 size_only_overlay 语义：
    # shrink target 仍然记录为 4，但 Broker 实际 slot cap 回到 base=10；
    # 同时 sizing 仍按 RISK_OFF 倍率收缩，而不是把 overlay 整体关闭。
    assert trace["target_max_positions"].tolist() == [4, 4]
    assert trace["effective_max_positions"].tolist() == [10, 10]
    assert trace["max_positions_mode"].tolist() == ["no_maxpos_shrink", "no_maxpos_shrink"]
    assert trace["max_positions_buffer_slots"].tolist() == [0, 0]
    assert trace["holdings_before"].tolist() == [5, 6]
    assert trace["decision_status"].tolist() == ["ACCEPTED", "ACCEPTED"]
    assert trace["effective_risk_per_trade_pct"].tolist() == pytest.approx([0.08, 0.08])
    assert trace["effective_max_position_pct"].tolist() == pytest.approx([0.2, 0.2])
    store.close()


@pytest.mark.parametrize(
    ("settings_overrides", "bullish_qty", "bearish_qty"),
    [
        (
            {
                "RISK_PER_TRADE_PCT": 0.04,
                "MAX_POSITION_PCT": 1.0,
                "MSS_BULLISH_RISK_PER_TRADE_MULT": 1.0,
                "MSS_NEUTRAL_RISK_PER_TRADE_MULT": 1.0,
                "MSS_BEARISH_RISK_PER_TRADE_MULT": 0.4,
                "MSS_BULLISH_MAX_POSITION_MULT": 1.0,
                "MSS_NEUTRAL_MAX_POSITION_MULT": 1.0,
                "MSS_BEARISH_MAX_POSITION_MULT": 1.0,
            },
            80000,
            32000,
        ),
        (
            {
                "RISK_PER_TRADE_PCT": 1.0,
                "MAX_POSITION_PCT": 0.50,
                "MSS_BULLISH_RISK_PER_TRADE_MULT": 1.0,
                "MSS_NEUTRAL_RISK_PER_TRADE_MULT": 1.0,
                "MSS_BEARISH_RISK_PER_TRADE_MULT": 1.0,
                "MSS_BULLISH_MAX_POSITION_MULT": 1.0,
                "MSS_NEUTRAL_MAX_POSITION_MULT": 1.0,
                "MSS_BEARISH_MAX_POSITION_MULT": 0.4,
            },
            50000,
            20000,
        ),
    ],
    ids=["risk_per_trade_only", "max_position_pct_only"],
)
def test_broker_overlay_single_sizing_knob_resizes_quantity_without_changing_slots(
    tmp_path,
    settings_overrides: dict[str, float],
    bullish_qty: int,
    bearish_qty: int,
) -> None:
    db = tmp_path / "test_mss_overlay_only_size.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=10,
        MSS_BULLISH_MAX_POSITIONS_MULT=1.0,
        MSS_NEUTRAL_MAX_POSITIONS_MULT=1.0,
        MSS_BEARISH_MAX_POSITIONS_MULT=1.0,
        **settings_overrides,
    )
    risk = Broker(store, cfg).risk

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
        [
            {
                "code": "000005",
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000005", signal_date, "bof"),
        code="000005",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set())

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": "ACCELERATION",
                    "phase_trend": "UP",
                    "phase_days": 2,
                    "position_advice": "50%-70%",
                    "risk_regime": "RISK_ON",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    bullish = risk.assess_signal(signal, state)
    assert bullish.order is not None

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    risk._mss_overlay_cache.clear()
    bearish = risk.assess_signal(signal, state)
    assert bearish.order is not None

    # 这个用例锁定 sizing 旋钮的职责：它们只能改 quantity，
    # 不能把 slot 上限偷偷联动成 MAX_POSITIONS 缩容。
    assert bullish.overlay is not None
    assert bearish.overlay is not None
    assert bullish.overlay.max_positions == 10
    assert bearish.overlay.max_positions == 10
    assert bullish.order.quantity == bullish_qty
    assert bearish.order.quantity == bearish_qty
    assert bearish.order.quantity < bullish.order.quantity
    store.close()


def test_broker_mss_overlay_derives_risk_regime_from_phase_when_row_is_legacy(tmp_path) -> None:
    db = tmp_path / "test_mss_overlay_phase_fallback.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.20,
        MAX_POSITION_PCT=0.50,
        STOP_LOSS_PCT=0.05,
        MAX_POSITIONS=10,
    )
    risk = Broker(store, cfg).risk

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set())

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )

    decision = risk.assess_signal(signal, state)

    # 旧库行没有 risk_regime 时，Broker 允许按 phase + phase_trend 回退解析，
    # 但结果仍必须是 CLIMAX -> RISK_OFF，而不是被 BULLISH signal 误导。
    assert decision.order is not None
    assert decision.overlay is not None
    assert decision.overlay.risk_regime == "RISK_OFF"
    assert decision.overlay.regime_source == "PHASE_STATE"
    assert decision.overlay.signal == "BULLISH"
    assert decision.order.quantity == 20000
    store.close()


def test_broker_dtt_mainline_prioritizes_final_score_over_strength(tmp_path) -> None:
    db = tmp_path / "test_final_score_priority.duckdb"
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
            ]
        ),
    )

    low_strength_high_final = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof_low_strength"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.2,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=95.0,
    )
    high_strength_low_final = Signal(
        signal_id=build_signal_id("000002", signal_date, "bof_high_strength"),
        code="000002",
        signal_date=signal_date,
        action="BUY",
        strength=0.9,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=10.0,
    )

    accepted = broker.process_signals([high_strength_low_final, low_strength_high_final])
    assert len(accepted) == 1
    assert accepted[0].code == "000001"

    rows = store.read_df(
        """
        SELECT code, status, reject_reason
        FROM l4_orders
        ORDER BY code
        """
    )
    assert len(rows) == 2
    accepted_row = rows[rows["status"] == "PENDING"].iloc[0]
    rejected_row = rows[rows["status"] == "REJECTED"].iloc[0]
    assert accepted_row["code"] == "000001"
    assert rejected_row["code"] == "000002"
    assert rejected_row["reject_reason"] == "MAX_POSITIONS_REACHED"
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
    lifecycle = store.read_df(
        """
        SELECT event_stage, origin, reason_code
        FROM broker_order_lifecycle_trace_exp
        WHERE order_id = ?
        """,
        (exits[0].order_id,),
    )
    assert lifecycle.iloc[0]["event_stage"] == "EXIT_ORDER_CREATED"
    assert lifecycle.iloc[0]["origin"] == "EXIT_STOP_LOSS"
    assert lifecycle.iloc[0]["reason_code"] == "STOP_LOSS"
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


def test_broker_writes_mss_overlay_trace_for_disabled_missing_and_normal(tmp_path) -> None:
    db = tmp_path / "test_mss_trace.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
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
        ],
    )
    store.bulk_upsert(
        "l2_market_snapshot",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "total_stocks": 100,
                    "rise_count": 60,
                    "fall_count": 40,
                    "strong_up_count": 10,
                    "strong_down_count": 5,
                    "limit_up_count": 4,
                    "limit_down_count": 2,
                    "touched_limit_up_count": 1,
                    "new_100d_high_count": 6,
                    "new_100d_low_count": 3,
                    "continuous_limit_up_2d": 2,
                    "continuous_limit_up_3d_plus": 1,
                    "continuous_new_high_2d_plus": 2,
                    "high_open_low_close_count": 2,
                    "low_open_high_close_count": 1,
                    "pct_chg_std": 0.02,
                    "amount_volatility": 100000.0,
                }
            ]
        ),
    )

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

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 20.0,
                    "signal": "BEARISH",
                    "phase": "RECESSION",
                    "phase_trend": "DOWN",
                    "phase_days": 2,
                    "position_advice": "0%-20%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
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

    trace = store.read_df(
        """
        SELECT run_id, overlay_enabled, overlay_state, coverage_flag, overlay_reason, market_signal,
               risk_regime, ranker_mss_score, market_coefficient_raw, market_coefficient, decision_bucket
        FROM mss_risk_overlay_trace_exp
        WHERE signal_id = ?
        ORDER BY run_id ASC
        """,
        (signal.signal_id,),
    )
    assert trace["run_id"].tolist() == ["mss_disabled", "mss_missing", "mss_normal"]
    assert trace["overlay_enabled"].tolist() == [False, True, True]
    assert trace["overlay_state"].tolist() == ["DISABLED", "MISSING", "NORMAL"]
    assert trace["coverage_flag"].tolist() == ["OVERLAY_DISABLED", "SNAPSHOT_MISSING", "NORMAL"]
    assert trace["overlay_reason"].tolist() == ["OVERLAY_DISABLED", "SNAPSHOT_MISSING", "NORMAL"]
    assert trace.iloc[2]["market_signal"] == "BEARISH"
    assert trace["risk_regime"].tolist() == ["RISK_NEUTRAL", "RISK_NEUTRAL", "RISK_OFF"]
    assert trace.iloc[2]["ranker_mss_score"] == 20.0
    assert pd.notna(trace.iloc[2]["market_coefficient_raw"])
    assert trace.iloc[2]["market_coefficient"] == 40.0
    assert trace["decision_bucket"].tolist() == ["ACCEPTED", "ACCEPTED", "ACCEPTED"]
    store.close()


def test_broker_writes_mss_overlay_trace_for_score_fill_and_signal_normalized(tmp_path) -> None:
    db = tmp_path / "test_mss_trace_fallbacks.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
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
        ],
    )
    store.bulk_upsert(
        "l2_market_snapshot",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "total_stocks": 100,
                    "rise_count": 60,
                    "fall_count": 40,
                    "strong_up_count": 10,
                    "strong_down_count": 5,
                    "limit_up_count": 4,
                    "limit_down_count": 2,
                    "touched_limit_up_count": 1,
                    "new_100d_high_count": 6,
                    "new_100d_low_count": 3,
                    "continuous_limit_up_2d": 2,
                    "continuous_limit_up_3d_plus": 1,
                    "continuous_new_high_2d_plus": 2,
                    "high_open_low_close_count": 2,
                    "low_open_high_close_count": 1,
                    "pct_chg_std": 0.02,
                    "amount_volatility": 100000.0,
                }
            ]
        ),
    )

    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        mss_score=50.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.2,
        MAX_POSITION_PCT=0.5,
        STOP_LOSS_PCT=0.05,
    )

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": None,
                    "signal": "BEARISH",
                    "phase": "RECESSION",
                    "phase_trend": "DOWN",
                    "phase_days": 1,
                    "position_advice": "0%-20%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    Broker(store, cfg, run_id="mss_score_fill").process_signals([signal])

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "INVALID",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )
    Broker(store, cfg, run_id="mss_signal_normalized").process_signals([signal])

    trace = store.read_df(
        """
        SELECT run_id, coverage_flag, overlay_reason, market_signal, market_score, risk_regime
        FROM mss_risk_overlay_trace_exp
        WHERE signal_id = ?
        ORDER BY run_id ASC
        """,
        (signal.signal_id,),
    )

    assert trace["run_id"].tolist() == ["mss_score_fill", "mss_signal_normalized"]
    assert trace["coverage_flag"].tolist() == ["SCORE_FILL", "SIGNAL_NORMALIZED"]
    assert trace["overlay_reason"].tolist() == ["FACTOR_FILL_NEUTRAL", "NORMAL"]
    assert trace.iloc[0]["market_score"] == 50.0
    assert trace.iloc[1]["market_signal"] == "NEUTRAL"
    assert trace["risk_regime"].tolist() == ["RISK_OFF", "RISK_OFF"]
    store.close()


def test_broker_overlay_trace_marks_cold_start_and_overlay_missing_reasons(tmp_path) -> None:
    db = tmp_path / "test_mss_trace_phase3_reasons.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)

    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_adj_daily(
        store,
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
        ],
    )
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.2,
        MAX_POSITION_PCT=0.5,
        STOP_LOSS_PCT=0.05,
    )

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": "ACCELERATION",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "50%-70%",
                    "trend_quality": "COLD_START",
                }
            ]
        ),
    )
    Broker(store, cfg, run_id="mss_cold_start").process_signals([signal])

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 55.0,
                    "signal": "NEUTRAL",
                    "phase": None,
                    "phase_trend": None,
                    "phase_days": None,
                    "position_advice": None,
                    "risk_regime": None,
                    "trend_quality": None,
                }
            ]
        ),
    )
    Broker(store, cfg, run_id="mss_overlay_missing").process_signals([signal])

    trace = store.read_df(
        """
        SELECT run_id, overlay_reason, risk_regime, regime_source
        FROM mss_risk_overlay_trace_exp
        WHERE signal_id = ?
        ORDER BY run_id ASC
        """,
        (signal.signal_id,),
    )

    # cold start 与 overlay missing 都是 Phase 3 要单独追溯的原因位，
    # 不能继续混在一个 generic fallback 标签里。
    assert trace["run_id"].tolist() == ["mss_cold_start", "mss_overlay_missing"]
    assert trace["overlay_reason"].tolist() == ["TREND_COLD_START", "OVERLAY_MISSING"]
    assert trace.iloc[0]["risk_regime"] == "RISK_ON"
    assert trace.iloc[0]["regime_source"] == "PHASE_STATE"
    assert trace.iloc[1]["risk_regime"] == "RISK_NEUTRAL"
    assert trace.iloc[1]["regime_source"] == "DEFAULT_NEUTRAL"
    store.close()


def test_broker_overlay_trace_marks_capacity_reject_bucket(tmp_path) -> None:
    db = tmp_path / "test_mss_trace_capacity_reject.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)

    _seed_trade_calendar(store, signal_date, exec_date)
    signal = Signal(
        signal_id=build_signal_id("000009", signal_date, "bof"),
        code="000009",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
        final_score=90.0,
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
    )
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_mss_score",
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITIONS=3,
    )
    broker = Broker(store, cfg, run_id="mss_capacity_reject")
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
    broker.portfolio["000002"] = Position(
        code="000002",
        entry_date=date(2026, 3, 1),
        entry_price=10.0,
        quantity=100,
        current_price=10.0,
        max_price=10.0,
        pattern="bof",
        is_paper=False,
    )

    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {
                    "date": signal_date,
                    "score": 80.0,
                    "signal": "BULLISH",
                    "phase": "CLIMAX",
                    "phase_trend": "UP",
                    "phase_days": 1,
                    "position_advice": "20%-40%",
                    "risk_regime": "RISK_OFF",
                    "trend_quality": "NORMAL",
                }
            ]
        ),
    )

    broker.process_signals([signal])

    trace = store.read_df(
        """
        SELECT decision_bucket, decision_reason, risk_regime
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ? AND signal_id = ?
        """,
        ("mss_capacity_reject", signal.signal_id),
    )

    # MAX_POSITIONS_REACHED 在 Phase 3 里必须归并到高层容量拒绝桶，
    # 方便后续 evidence 判断“拒绝来自真实 regime 缩容还是别的失败路径”。
    assert trace.iloc[0]["decision_bucket"] == "BROKER_CAPACITY_REJECT"
    assert trace.iloc[0]["decision_reason"] == "MAX_POSITIONS_REACHED"
    assert trace.iloc[0]["risk_regime"] == "RISK_OFF"
    store.close()


def test_broker_records_lifecycle_trace_for_reject_fill_and_expire(tmp_path) -> None:
    db = tmp_path / "test_lifecycle_trace.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    hold_date = date(2026, 3, 5)
    expire_date = date(2026, 3, 6)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        RISK_PER_TRADE_PCT=0.01,
        MAX_POSITION_PCT=0.1,
        STOP_LOSS_PCT=0.05,
        MAX_PENDING_TRADE_DAYS=1,
    )
    broker = Broker(store, cfg, run_id="broker_trace")

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": hold_date},
                {"date": hold_date, "is_trade_day": True, "prev_trade_day": exec_date, "next_trade_day": expire_date},
                {"date": expire_date, "is_trade_day": True, "prev_trade_day": hold_date, "next_trade_day": None},
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
    retry_signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "bof_retry"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    broker.process_signals([retry_signal])
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

    lifecycle = store.read_df(
        """
        SELECT order_id, event_stage, reason_code, origin
        FROM broker_order_lifecycle_trace_exp
        WHERE run_id = ?
        ORDER BY order_id ASC, event_stage ASC
        """,
        ("broker_trace",),
    )

    assert "RISK_ACCEPTED" in lifecycle["event_stage"].tolist()
    assert "MATCH_REJECTED" in lifecycle["event_stage"].tolist()
    assert "MATCH_FILLED" in lifecycle["event_stage"].tolist()
    assert "ORDER_EXPIRED" in lifecycle["event_stage"].tolist()
    expired = lifecycle[lifecycle["event_stage"] == "ORDER_EXPIRED"].iloc[0]
    assert expired["reason_code"] == "ORDER_TIMEOUT"
    assert expired["origin"] == "UPSTREAM_SIGNAL"
    store.close()


def test_broker_expires_pending_order_on_next_trade_day_when_max_pending_is_one(tmp_path) -> None:
    db = tmp_path / "test_expire_next_trade_day.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    next_trade_date = date(2026, 3, 5)
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_PENDING_TRADE_DAYS=1,
    )
    broker = Broker(store, cfg, run_id="expire_next_trade_day")

    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": signal_date, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": exec_date},
                {"date": exec_date, "is_trade_day": True, "prev_trade_day": signal_date, "next_trade_day": next_trade_date},
                {"date": next_trade_date, "is_trade_day": True, "prev_trade_day": exec_date, "next_trade_day": None},
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

    expired = broker.expire_orders(next_trade_date)
    assert expired == 1

    lifecycle = store.get_broker_lifecycle_trace("expire_next_trade_day", order.order_id)
    assert len(lifecycle) == 1
    assert lifecycle.iloc[0]["event_stage"] == "ORDER_EXPIRED"
    assert lifecycle.iloc[0]["origin"] == "UPSTREAM_SIGNAL"
    store.close()
