from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.data.store import Store
from src.selector.irs import compute_irs
from src.selector.mss import compute_mss
from src.selector.selector import select_candidates
from src.strategy.pas_bof import BofDetector


def _seed_market_snapshot(store: Store, start: date, days: int) -> None:
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        rows.append(
            {
                "date": d,
                "total_stocks": 5000,
                "rise_count": 2800 + (i % 30),
                "fall_count": 2200 - (i % 30),
                "strong_up_count": 400,
                "strong_down_count": 200,
                "limit_up_count": 60,
                "limit_down_count": 20,
                "touched_limit_up_count": 30,
                "new_100d_high_count": 120,
                "new_100d_low_count": 60,
                "continuous_limit_up_2d": 12,
                "continuous_limit_up_3d_plus": 5,
                "continuous_new_high_2d_plus": 20,
                "high_open_low_close_count": 30,
                "low_open_high_close_count": 35,
                "pct_chg_std": 0.018,
                "amount_volatility": 1.5e10,
            }
        )
    store.bulk_upsert("l2_market_snapshot", pd.DataFrame(rows))


def test_mss_irs_and_selector_pipeline(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    store = Store(db)
    d0 = date(2026, 1, 1)

    # 交易日历
    cal = pd.DataFrame(
        [{"date": d0 + timedelta(days=i), "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None} for i in range(30)]
    )
    cal["prev_trade_day"] = cal["date"].shift(1)
    cal["next_trade_day"] = cal["date"].shift(-1)
    store.bulk_upsert("l1_trade_calendar", cal)

    # MSS 输入
    _seed_market_snapshot(store, d0, 10)
    assert compute_mss(store, d0, d0 + timedelta(days=9)) > 0

    # IRS 输入
    industry_rows = []
    index_rows = []
    for i in range(10):
        d = d0 + timedelta(days=i)
        index_rows.append(
            {
                "ts_code": "000001.SH",
                "date": d,
                "open": 3000.0,
                "high": 3020.0,
                "low": 2980.0,
                "close": 3010.0,
                "pre_close": 3000.0,
                "pct_chg": 0.003,
                "volume": 1e8,
                "amount": 2e11,
            }
        )
        industry_rows.extend(
            [
                {"industry": "银行", "date": d, "pct_chg": 0.01, "amount": 8e10, "stock_count": 30, "rise_count": 20, "fall_count": 10},
                {"industry": "电子", "date": d, "pct_chg": -0.002, "amount": 6e10, "stock_count": 40, "rise_count": 15, "fall_count": 25},
            ]
        )
    store.bulk_upsert("l1_index_daily", pd.DataFrame(index_rows))
    store.bulk_upsert("l2_industry_daily", pd.DataFrame(industry_rows))
    assert compute_irs(store, d0, d0 + timedelta(days=9)) > 0

    # 候选输入
    info = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "industry": "银行",
                "market": "主板",
                "list_status": "L",
                "is_st": False,
                "list_date": date(2010, 1, 1),
                "effective_from": d0,
            }
        ]
    )
    store.bulk_upsert("l1_stock_info", info)
    stock_l1 = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "date": d0 + timedelta(days=9),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.4,
                "pre_close": 10.0,
                "volume": 100000,
                "amount": 1e8,
                "pct_chg": 0.04,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 11.0,
                "down_limit": 9.0,
                "total_mv": 1e6,
                "circ_mv": 8e5,
            }
        ]
    )
    stock_l2 = pd.DataFrame(
        [
            {
                "code": "000001",
                "date": d0 + timedelta(days=9),
                "adj_open": 10.0,
                "adj_high": 10.5,
                "adj_low": 9.8,
                "adj_close": 10.4,
                "volume": 100000,
                "amount": 1e8,
                "pct_chg": 0.04,
                "ma5": 10.0,
                "ma10": 9.9,
                "ma20": 9.7,
                "ma60": 9.5,
                "volume_ma5": 90000,
                "volume_ma20": 85000,
                "volume_ratio": 1.2,
            }
        ]
    )
    store.bulk_upsert("l1_stock_daily", stock_l1)
    store.bulk_upsert("l2_stock_adj_daily", stock_l2)

    cfg = Settings(ENABLE_MSS_GATE=False, ENABLE_IRS_FILTER=False, MIN_AMOUNT=1)
    candidates = select_candidates(store, d0 + timedelta(days=9), cfg)
    assert len(candidates) == 1
    assert candidates[0].code == "000001"
    store.close()


def test_bof_detector_trigger() -> None:
    cfg = Settings(PAS_BOF_BREAK_PCT=0.01, PAS_BOF_VOLUME_MULT=1.2)
    detector = BofDetector(cfg)
    d0 = date(2026, 1, 1)
    rows = []
    for i in range(21):
        d = d0 + timedelta(days=i)
        rows.append(
            {
                "date": d,
                "adj_open": 10.0,
                "adj_high": 10.5,
                "adj_low": 9.9,
                "adj_close": 10.2,
                "volume": 1000.0,
                "volume_ma20": 900.0,
            }
        )
    # 最后一日构造假破位后收回 + 放量
    rows[-1]["adj_low"] = 9.6
    rows[-1]["adj_close"] = 10.15
    rows[-1]["adj_open"] = 9.8
    rows[-1]["adj_high"] = 10.2
    rows[-1]["volume"] = 1300.0

    signal = detector.detect("000001", d0 + timedelta(days=20), pd.DataFrame(rows))
    assert signal is not None
    assert signal.pattern == "bof"
    assert signal.action == "BUY"


def test_selector_asof_prefers_latest_status_snapshot(tmp_path) -> None:
    db = tmp_path / "selector_asof.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": calc_date,
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
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.1,
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
                    "date": calc_date,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.0,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
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
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "样本股",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2026, 1, 1),
                },
                {
                    "ts_code": "000001.SZ",
                    "name": "样本股",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "D",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2026, 1, 9),
                },
            ]
        ),
    )

    cfg = Settings(ENABLE_MSS_GATE=False, ENABLE_IRS_FILTER=False, MIN_AMOUNT=1, MIN_LIST_DAYS=1)
    cands = select_candidates(store, calc_date, cfg)
    assert cands == []
    store.close()


def test_selector_filters_out_non_live_status(tmp_path) -> None:
    db = tmp_path / "selector_delist.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    store.bulk_upsert(
        "l2_stock_adj_daily",
        pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": calc_date,
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
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.1,
                },
                {
                    "code": "000002",
                    "date": calc_date,
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
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.1,
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
                    "date": calc_date,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.0,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1e6,
                    "circ_mv": 8e5,
                },
                {
                    "ts_code": "000002.SZ",
                    "date": calc_date,
                    "open": 12.0,
                    "high": 12.2,
                    "low": 11.8,
                    "close": 12.0,
                    "pre_close": 12.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.0,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 13.2,
                    "down_limit": 10.8,
                    "total_mv": 1e6,
                    "circ_mv": 8e5,
                },
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "在市股",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2020, 1, 1),
                },
                {
                    "ts_code": "000002.SZ",
                    "name": "退市股",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "D",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2020, 1, 1),
                },
            ]
        ),
    )

    cfg = Settings(ENABLE_MSS_GATE=False, ENABLE_IRS_FILTER=False, MIN_AMOUNT=1, MIN_LIST_DAYS=1)
    cands = select_candidates(store, calc_date, cfg)
    assert len(cands) == 1
    assert cands[0].code == "000001"
    store.close()
