from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src.config import Settings
from src.contracts import Signal
from src.data.store import Store
from src.selector.irs import compute_irs
from src.selector.mss import compute_mss, compute_mss_single
from src.selector.selector import select_candidates, select_candidates_frame
from src.strategy.pas_bof import BofDetector
from src.strategy.registry import get_active_detectors
from src.strategy.strategy import _combine_signals, generate_signals


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


def _seed_selector_universe(store: Store, calc_date: date, codes: list[str]) -> None:
    l2_rows = []
    l1_rows = []
    info_rows = []
    for idx, code in enumerate(codes, start=1):
        ts_code = f"{code}.SZ"
        amount = float((len(codes) - idx + 1) * 1e8)
        l2_rows.append(
            {
                "code": code,
                "date": calc_date,
                "adj_open": 10.0 + idx,
                "adj_high": 10.2 + idx,
                "adj_low": 9.8 + idx,
                "adj_close": 10.0 + idx,
                "volume": 10000,
                "amount": amount,
                "pct_chg": 0.01 * idx,
                "ma5": 10.0,
                "ma10": 10.0,
                "ma20": 10.0,
                "ma60": 10.0,
                "volume_ma5": 9000,
                "volume_ma20": 9000,
                "volume_ratio": 1.1 + idx * 0.1,
            }
        )
        l1_rows.append(
            {
                "ts_code": ts_code,
                "date": calc_date,
                "open": 10.0 + idx,
                "high": 10.2 + idx,
                "low": 9.8 + idx,
                "close": 10.0 + idx,
                "pre_close": 10.0 + idx,
                "volume": 10000,
                "amount": amount,
                "pct_chg": 0.01 * idx,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 11.0 + idx,
                "down_limit": 9.0 + idx,
                "total_mv": 1e6,
                "circ_mv": 8e5,
            }
        )
        info_rows.append(
            {
                "ts_code": ts_code,
                "name": f"样本股{idx}",
                "industry": "银行",
                "market": "主板",
                "list_status": "L",
                "is_st": False,
                "list_date": date(2010, 1, 1),
                "effective_from": date(2020, 1, 1),
            }
        )

    store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(l2_rows))
    store.bulk_upsert("l1_stock_daily", pd.DataFrame(l1_rows))
    store.bulk_upsert("l1_stock_info", pd.DataFrame(info_rows))


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

    cfg = Settings(PIPELINE_MODE="dtt", ENABLE_MSS_GATE=False, ENABLE_IRS_FILTER=False, MIN_AMOUNT=1)
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


def test_bof_detector_does_not_trigger_without_close_recovery() -> None:
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
    rows[-1]["adj_low"] = 9.6
    rows[-1]["adj_close"] = 9.7
    rows[-1]["adj_open"] = 9.8
    rows[-1]["adj_high"] = 10.2
    rows[-1]["volume"] = 1300.0

    signal = detector.detect("000001", d0 + timedelta(days=20), pd.DataFrame(rows))
    assert signal is None


def test_mss_single_all_zero_is_still_neutral_under_calibrated_baseline() -> None:
    score = compute_mss_single(
        pd.Series(
            {
                "date": date(2026, 1, 1),
                "total_stocks": 0,
                "rise_count": 0,
                "fall_count": 0,
                "strong_up_count": 0,
                "strong_down_count": 0,
                "limit_up_count": 0,
                "limit_down_count": 0,
                "touched_limit_up_count": 0,
                "new_100d_high_count": 0,
                "new_100d_low_count": 0,
                "continuous_limit_up_2d": 0,
                "continuous_limit_up_3d_plus": 0,
                "continuous_new_high_2d_plus": 0,
                "high_open_low_close_count": 0,
                "low_open_high_close_count": 0,
                "pct_chg_std": 0.0,
                "amount_volatility": 0.0,
            }
        )
    )
    assert score.score == pytest.approx(40.5409421919409, abs=1e-9)
    assert score.signal == "NEUTRAL"


def test_compute_irs_ranks_stronger_industry_first(tmp_path) -> None:
    db = tmp_path / "irs_rank.duckdb"
    store = Store(db)
    d0 = date(2026, 1, 1)

    store.bulk_upsert(
        "l1_index_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SH",
                    "date": d0,
                    "open": 3000.0,
                    "high": 3010.0,
                    "low": 2990.0,
                    "close": 3005.0,
                    "pre_close": 3000.0,
                    "pct_chg": 0.003,
                    "volume": 1e8,
                    "amount": 2e11,
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {
                    "industry": "银行",
                    "date": d0,
                    "pct_chg": 0.015,
                    "amount": 8e10,
                    "stock_count": 30,
                    "rise_count": 20,
                    "fall_count": 10,
                },
                {
                    "industry": "电子",
                    "date": d0,
                    "pct_chg": -0.004,
                    "amount": 3e10,
                    "stock_count": 40,
                    "rise_count": 15,
                    "fall_count": 25,
                },
            ]
        ),
    )

    assert compute_irs(store, d0, d0) == 2
    ranked = store.read_df("SELECT industry, rank FROM l3_irs_daily WHERE date = ? ORDER BY rank ASC", (d0,))
    assert ranked.iloc[0]["industry"] == "银行"
    assert ranked.iloc[0]["rank"] == 1
    assert ranked.iloc[1]["industry"] == "电子"
    assert ranked.iloc[1]["rank"] == 2
    store.close()


def test_compute_irs_assigns_unique_ranks_when_scores_tie(tmp_path) -> None:
    db = tmp_path / "irs_tie_rank.duckdb"
    store = Store(db)
    d0 = date(2026, 1, 1)

    store.bulk_upsert(
        "l1_index_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SH",
                    "date": d0,
                    "open": 3000.0,
                    "high": 3010.0,
                    "low": 2990.0,
                    "close": 3000.0,
                    "pre_close": 3000.0,
                    "pct_chg": 0.0,
                    "volume": 1e8,
                    "amount": 2e11,
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {
                    "industry": "电子",
                    "date": d0,
                    "pct_chg": 0.0,
                    "amount": 5e10,
                    "stock_count": 40,
                    "rise_count": 20,
                    "fall_count": 20,
                },
                {
                    "industry": "银行",
                    "date": d0,
                    "pct_chg": 0.0,
                    "amount": 5e10,
                    "stock_count": 30,
                    "rise_count": 15,
                    "fall_count": 15,
                },
            ]
        ),
    )

    assert compute_irs(store, d0, d0) == 2
    ranked = store.read_df("SELECT industry, rank FROM l3_irs_daily WHERE date = ? ORDER BY rank ASC", (d0,))
    assert ranked["rank"].tolist() == [1, 2]
    assert len(set(ranked["rank"].tolist())) == 2
    store.close()


def test_compute_irs_skips_days_below_min_industry_threshold(tmp_path) -> None:
    db = tmp_path / "irs_min_industries.duckdb"
    store = Store(db)
    d0 = date(2026, 1, 1)

    store.bulk_upsert(
        "l1_index_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SH",
                    "date": d0,
                    "open": 3000.0,
                    "high": 3010.0,
                    "low": 2990.0,
                    "close": 3000.0,
                    "pre_close": 3000.0,
                    "pct_chg": 0.0,
                    "volume": 1e8,
                    "amount": 2e11,
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {
                    "industry": "电子",
                    "date": d0,
                    "pct_chg": 0.0,
                    "amount": 5e10,
                    "stock_count": 40,
                    "rise_count": 20,
                    "fall_count": 20,
                },
                {
                    "industry": "银行",
                    "date": d0,
                    "pct_chg": 0.0,
                    "amount": 5e10,
                    "stock_count": 30,
                    "rise_count": 15,
                    "fall_count": 15,
                },
            ]
        ),
    )

    assert compute_irs(store, d0, d0, min_industries_per_day=3) == 0
    assert store.read_df("SELECT * FROM l3_irs_daily").empty
    store.close()


def test_strategy_combine_modes() -> None:
    signal_date = date(2026, 1, 8)
    s1 = Signal(
        signal_id="000001_2026-01-08_bof",
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.6,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    s2 = Signal(
        signal_id="000001_2026-01-08_bpb",
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.8,
        pattern="bpb",
        reason_code="PAS_BPB",
    )
    s3 = Signal(
        signal_id="000001_2026-01-08_pb",
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.7,
        pattern="pb",
        reason_code="PAS_PB",
    )

    assert _combine_signals([s1, s2], active_detector_count=3, mode="ANY") == [s2]
    assert _combine_signals([s1, s2], active_detector_count=3, mode="ALL") == []
    assert _combine_signals([s1, s2], active_detector_count=3, mode="VOTE") == [s2]
    assert _combine_signals([s1, s2, s3], active_detector_count=3, mode="ALL") == [s2]


def test_generate_signals_empty_candidates_returns_empty(tmp_path) -> None:
    db = tmp_path / "strategy_empty.duckdb"
    store = Store(db)
    cfg = Settings(PAS_PATTERNS="bof", PAS_COMBINATION="ANY")

    assert generate_signals(store, [], date(2026, 1, 8), cfg) == []
    store.close()


def test_registry_enforces_v001_single_bof_pattern() -> None:
    cfg = Settings(PAS_PATTERNS="bof,bpb")
    try:
        get_active_detectors(cfg)
    except ValueError as exc:
        assert "PAS_PATTERNS=bof" in str(exc)
    else:
        raise AssertionError("expected v0.01 single-pattern validation to fail")


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

    cfg = Settings(
        PIPELINE_MODE="dtt",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
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

    cfg = Settings(
        PIPELINE_MODE="dtt",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    cands = select_candidates(store, calc_date, cfg)
    assert len(cands) == 1
    assert cands[0].code == "000001"
    store.close()


def test_selector_returns_empty_when_mss_is_bearish(tmp_path) -> None:
    db = tmp_path / "selector_bearish.duckdb"
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
                    "amount": 2e8,
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
                    "amount": 2e8,
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
                    "effective_from": date(2020, 1, 1),
                }
            ]
        ),
    )
    store.bulk_upsert("l3_mss_daily", pd.DataFrame([{"date": calc_date, "score": 20.0, "signal": "BEARISH"}]))

    cfg = Settings(
        PIPELINE_MODE="legacy",
        ENABLE_MSS_GATE=True,
        ENABLE_IRS_FILTER=False,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    assert select_candidates(store, calc_date, cfg) == []
    store.close()


def test_selector_bullish_required_blocks_neutral_environment(tmp_path) -> None:
    db = tmp_path / "selector_bullish_required.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    _seed_selector_universe(store, calc_date, ["000001"])
    store.bulk_upsert("l3_mss_daily", pd.DataFrame([{"date": calc_date, "score": 50.0, "signal": "NEUTRAL"}]))

    cfg = Settings(
        PIPELINE_MODE="legacy",
        ENABLE_MSS_GATE=True,
        ENABLE_IRS_FILTER=False,
        MSS_GATE_MODE="bullish_required",
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    assert select_candidates(store, calc_date, cfg) == []
    store.close()


def test_selector_soft_gate_trims_neutral_candidate_count(tmp_path) -> None:
    db = tmp_path / "selector_soft_gate.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    _seed_selector_universe(store, calc_date, ["000001", "000002", "000003"])
    store.bulk_upsert("l3_mss_daily", pd.DataFrame([{"date": calc_date, "score": 52.0, "signal": "NEUTRAL"}]))

    cfg = Settings(
        PIPELINE_MODE="legacy",
        ENABLE_MSS_GATE=True,
        ENABLE_IRS_FILTER=False,
        MSS_GATE_MODE="soft_gate",
        MSS_SOFT_GATE_CANDIDATE_TOP_N=1,
        CANDIDATE_TOP_N=3,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    frame = select_candidates_frame(store, calc_date, cfg)
    assert len(frame) == 1
    assert frame.iloc[0]["code"] == "000001"
    store.close()


def test_selector_dtt_ignores_legacy_mss_and_irs_gate_flags(tmp_path) -> None:
    db = tmp_path / "selector_dtt_boundary.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    _seed_selector_universe(store, calc_date, ["000001"])
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame([{"date": calc_date, "score": 20.0, "signal": "BEARISH"}]),
    )
    store.bulk_upsert(
        "l3_irs_daily",
        pd.DataFrame([{"date": calc_date, "industry": "电子", "score": 90.0, "rank": 1}]),
    )

    cfg = Settings(
        PIPELINE_MODE="dtt",
        ENABLE_MSS_GATE=True,
        ENABLE_IRS_FILTER=True,
        MSS_GATE_MODE="bullish_required",
        IRS_TOP_N=1,
        CANDIDATE_TOP_N=5,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    frame = select_candidates_frame(store, calc_date, cfg)

    # DTT 主线只做基础过滤与算力调度，不能再被 legacy gate/filter 提前清空。
    assert len(frame) == 1
    assert frame.iloc[0]["code"] == "000001"
    assert frame.iloc[0]["preselect_score"] == frame.iloc[0]["score"]
    store.close()


def test_selector_frame_keeps_candidate_explainability_fields(tmp_path) -> None:
    db = tmp_path / "selector_trace.duckdb"
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
                    "amount": 2e8,
                    "pct_chg": 0.01,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.2,
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
                    "amount": 2e8,
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
                    "effective_from": date(2020, 1, 1),
                }
            ]
        ),
    )

    cfg = Settings(
        PIPELINE_MODE="dtt",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    frame = select_candidates_frame(store, calc_date, cfg)
    assert list(frame.columns) == [
        "code",
        "industry",
        "preselect_score",
        "score",
        "filters_passed",
        "reject_reason",
        "liquidity_tag",
    ]
    assert frame.iloc[0]["filters_passed"] == "LIST_STATUS;HALT;ST;LIST_DAYS;AMOUNT"
    assert frame.iloc[0]["reject_reason"] == ""
    assert frame.iloc[0]["liquidity_tag"] in {"MEDIUM", "HIGH"}
    assert frame.iloc[0]["preselect_score"] == frame.iloc[0]["score"]
    store.close()


def test_selector_dtt_preselect_score_mode_changes_sorting_basis(tmp_path) -> None:
    db = tmp_path / "selector_preselect_modes.duckdb"
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
                    "amount": 2e8,
                    "pct_chg": 0.01,
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
                    "adj_open": 10.0,
                    "adj_high": 10.2,
                    "adj_low": 9.8,
                    "adj_close": 10.0,
                    "volume": 10000,
                    "amount": 1e8,
                    "pct_chg": 0.01,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 5.0,
                },
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": f"{code}.SZ",
                    "date": calc_date,
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.8,
                    "close": 10.0,
                    "pre_close": 10.0,
                    "volume": 10000,
                    "amount": amount,
                    "pct_chg": 0.01,
                    "adj_factor": 1.0,
                    "is_halt": False,
                    "up_limit": 11.0,
                    "down_limit": 9.0,
                    "total_mv": 1e6,
                    "circ_mv": 8e5,
                }
                for code, amount in [("000001", 2e8), ("000002", 1e8)]
            ]
        ),
    )
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": f"{code}.SZ",
                    "name": f"样本股{code}",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2020, 1, 1),
                }
                for code in ["000001", "000002"]
            ]
        ),
    )

    cfg_amount = Settings(
        PIPELINE_MODE="dtt",
        PRESELECT_SCORE_MODE="amount_only",
        CANDIDATE_TOP_N=1,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    cfg_activity = Settings(
        PIPELINE_MODE="dtt",
        PRESELECT_SCORE_MODE="volume_ratio_only",
        CANDIDATE_TOP_N=1,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )

    frame_amount = select_candidates_frame(store, calc_date, cfg_amount)
    frame_activity = select_candidates_frame(store, calc_date, cfg_activity)

    assert frame_amount.iloc[0]["code"] == "000001"
    assert frame_activity.iloc[0]["code"] == "000002"
    store.close()


def test_selector_prefers_sw_industry_over_legacy_stock_basic_industry(tmp_path) -> None:
    db = tmp_path / "selector_sw_priority.duckdb"
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
                    "amount": 2e8,
                    "pct_chg": 0.01,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.2,
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
                    "amount": 2e8,
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
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "样本股",
                    "industry": "旧行业",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": date(2020, 1, 1),
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
                    "source_trade_date": calc_date,
                }
            ]
        ),
    )

    cfg = Settings(
        PIPELINE_MODE="dtt",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )
    frame = select_candidates_frame(store, calc_date, cfg)
    assert frame.iloc[0]["industry"] == "银行"
    store.close()
