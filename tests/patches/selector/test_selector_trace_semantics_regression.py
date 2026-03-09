from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings
from src.data.store import Store
from src.selector.selector import select_candidates


def test_selector_trace_keeps_reject_reason_on_rejected_rows_only(tmp_path) -> None:
    db = tmp_path / "selector_trace_patch.duckdb"
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
                    "amount": 3e8,
                    "pct_chg": 0.01,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.2,
                },
                {
                    "code": "000002",
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
                    "code": "000003",
                    "date": calc_date,
                    "adj_open": 10.0,
                    "adj_high": 10.2,
                    "adj_low": 9.8,
                    "adj_close": 10.0,
                    "volume": 10000,
                    "amount": 10.0,
                    "pct_chg": 0.01,
                    "ma5": 10.0,
                    "ma10": 10.0,
                    "ma20": 10.0,
                    "ma60": 10.0,
                    "volume_ma5": 9000,
                    "volume_ma20": 9000,
                    "volume_ratio": 1.0,
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
                for code, amount in [("000001", 3e8), ("000002", 2e8), ("000003", 10.0)]
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
                for code in ["000001", "000002", "000003"]
            ]
        ),
    )

    cfg = Settings(
        PIPELINE_MODE="dtt",
        CANDIDATE_TOP_N=1,
        PRESELECT_SCORE_MODE="amount_only",
        MIN_AMOUNT=1_000,
        MIN_LIST_DAYS=1,
    )

    candidates = select_candidates(store, calc_date, cfg, run_id="selector_trace")

    assert len(candidates) == 1
    selected = store.get_selector_candidate_trace("selector_trace", calc_date, "000001")
    truncated = store.get_selector_candidate_trace("selector_trace", calc_date, "000002")
    rejected = store.get_selector_candidate_trace("selector_trace", calc_date, "000003")

    assert selected is not None
    assert truncated is not None
    assert rejected is not None
    assert bool(selected["selected"]) is True
    assert pd.isna(selected["reject_reason"])
    assert bool(truncated["selected"]) is False
    assert pd.isna(truncated["reject_reason"])
    assert rejected["reject_reason"] == "LOW_LIQUIDITY"
    assert float(selected["preselect_score"]) == float(selected["final_score"])
    store.close()
