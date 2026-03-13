from __future__ import annotations

from datetime import date

import pandas as pd

from src.broker.broker import Broker
from src.broker.risk import BrokerRiskState
from src.config import Settings
from src.contracts import Signal, build_signal_id
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


def _seed_price_history(store: Store, code: str, rows: list[dict[str, object]]) -> None:
    store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(rows))


def test_risk_manager_fixed_capital_uses_configured_notional(tmp_path) -> None:
    db = tmp_path / "fixed_capital.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_price_history(
        store,
        "000001",
        [
            {
                "code": "000001",
                "date": signal_date,
                "adj_open": 10.0,
                "adj_high": 10.0,
                "adj_low": 10.0,
                "adj_close": 10.0,
                "volume": 10_000,
                "amount": 1e8,
                "pct_chg": 0.0,
                "ma5": 10.0,
                "ma10": 10.0,
                "ma20": 10.0,
                "ma60": 10.0,
                "volume_ma5": 10_000,
                "volume_ma20": 10_000,
                "volume_ratio": 1.0,
            }
        ],
    )

    cfg = Settings(
        POSITION_SIZING_MODE="fixed_capital",
        FIXED_CAPITAL_AMOUNT=75_000,
        MAX_POSITION_PCT=0.20,
        BACKTEST_INITIAL_CASH=1_000_000,
    )
    risk = Broker(store, cfg).risk
    overlay = risk._load_mss_overlay(signal_date)
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "fixed_capital"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    quantity = risk._calculate_position_size(
        signal,
        est_price=10.0,
        state=BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set()),
        overlay=overlay,
    )

    assert quantity == 7_500
    store.close()


def test_risk_manager_fixed_ratio_steps_up_with_equity_growth(tmp_path) -> None:
    db = tmp_path / "fixed_ratio.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 3)
    exec_date = date(2026, 3, 4)
    _seed_trade_calendar(store, signal_date, exec_date)
    _seed_price_history(
        store,
        "000001",
        [
            {
                "code": "000001",
                "date": signal_date,
                "adj_open": 10.0,
                "adj_high": 10.0,
                "adj_low": 10.0,
                "adj_close": 10.0,
                "volume": 10_000,
                "amount": 1e8,
                "pct_chg": 0.0,
                "ma5": 10.0,
                "ma10": 10.0,
                "ma20": 10.0,
                "ma60": 10.0,
                "volume_ma5": 10_000,
                "volume_ma20": 10_000,
                "volume_ratio": 1.0,
            }
        ],
    )

    cfg = Settings(
        POSITION_SIZING_MODE="fixed_ratio",
        FIXED_RATIO_BASE_AMOUNT=50_000,
        FIXED_RATIO_DELTA_AMOUNT=250_000,
        MAX_POSITION_PCT=0.20,
        BACKTEST_INITIAL_CASH=1_000_000,
    )
    risk = Broker(store, cfg).risk
    overlay = risk._load_mss_overlay(signal_date)
    signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "fixed_ratio"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )

    base_quantity = risk._calculate_position_size(
        signal,
        est_price=10.0,
        state=BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set()),
        overlay=overlay,
    )
    grown_quantity = risk._calculate_position_size(
        signal,
        est_price=10.0,
        state=BrokerRiskState(cash=1_600_000, portfolio_market_value=0.0, holdings=set()),
        overlay=overlay,
    )

    assert base_quantity == 5_000
    assert grown_quantity == 15_000
    store.close()


def test_risk_manager_fixed_volatility_allocates_less_to_higher_volatility_code(tmp_path) -> None:
    db = tmp_path / "fixed_volatility.duckdb"
    store = Store(db)
    signal_date = date(2026, 3, 21)
    exec_date = date(2026, 3, 24)
    _seed_trade_calendar(store, signal_date, exec_date)

    calm_rows = []
    volatile_rows = []
    calm_prices = [
        10.00,
        10.10,
        10.00,
        10.12,
        10.04,
        10.15,
        10.08,
    ]
    volatile_prices = [
        10.00,
        10.80,
        9.70,
        10.90,
        9.50,
        10.70,
        9.60,
    ]
    for idx, value in enumerate(calm_prices, start=1):
        calm_rows.append(
            {
                "code": "000001",
                "date": date(2026, 3, idx),
                "adj_open": value,
                "adj_high": value,
                "adj_low": value,
                "adj_close": value,
                "volume": 10_000,
                "amount": 1e8,
                "pct_chg": 0.0,
                "ma5": value,
                "ma10": value,
                "ma20": value,
                "ma60": value,
                "volume_ma5": 10_000,
                "volume_ma20": 10_000,
                "volume_ratio": 1.0,
            }
        )
    for idx, value in enumerate(volatile_prices, start=1):
        volatile_rows.append(
            {
                "code": "000002",
                "date": date(2026, 3, idx),
                "adj_open": value,
                "adj_high": value,
                "adj_low": value,
                "adj_close": value,
                "volume": 10_000,
                "amount": 1e8,
                "pct_chg": 0.0,
                "ma5": value,
                "ma10": value,
                "ma20": value,
                "ma60": value,
                "volume_ma5": 10_000,
                "volume_ma20": 10_000,
                "volume_ratio": 1.0,
            }
        )
    _seed_price_history(store, "000001", calm_rows)
    _seed_price_history(store, "000002", volatile_rows)

    cfg = Settings(
        POSITION_SIZING_MODE="fixed_volatility",
        FIXED_VOLATILITY_LOOKBACK_DAYS=6,
        FIXED_VOLATILITY_TARGET_PCT=0.003,
        FIXED_VOLATILITY_MIN_POSITION_PCT=0.03,
        FIXED_VOLATILITY_MAX_POSITION_PCT=0.10,
        MAX_POSITION_PCT=0.10,
        BACKTEST_INITIAL_CASH=1_000_000,
    )
    risk = Broker(store, cfg).risk
    overlay = risk._load_mss_overlay(signal_date)

    calm_signal = Signal(
        signal_id=build_signal_id("000001", signal_date, "vol_low"),
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    volatile_signal = Signal(
        signal_id=build_signal_id("000002", signal_date, "vol_high"),
        code="000002",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    state = BrokerRiskState(cash=1_000_000, portfolio_market_value=0.0, holdings=set())

    calm_quantity = risk._calculate_position_size(calm_signal, 10.0, state, overlay)
    volatile_quantity = risk._calculate_position_size(volatile_signal, 10.0, state, overlay)

    assert calm_quantity > volatile_quantity
    store.close()
