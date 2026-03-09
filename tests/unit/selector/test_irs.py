from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.store import Store
from src.selector.irs import compute_irs


def test_compute_irs_writes_industry_trace_with_benchmark_fill(tmp_path) -> None:
    db = tmp_path / "irs_industry_trace.duckdb"
    store = Store(db)
    trade_date = date(2026, 1, 8)

    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {"industry": "电子", "date": trade_date, "pct_chg": 0.03, "amount": 120.0, "stock_count": 10},
                {"industry": "银行", "date": trade_date, "pct_chg": 0.01, "amount": 100.0, "stock_count": 10},
            ]
        ),
    )

    written = compute_irs(store, trade_date, trade_date, min_industries_per_day=2)

    trace_run_id = f"IRS_DAILY::{trade_date.isoformat()}::{trade_date.isoformat()}"
    trace = store.read_df(
        """
        SELECT industry, trace_scope, coverage_flag, benchmark_code, benchmark_pct, industry_score, industry_rank
        FROM irs_industry_trace_exp
        WHERE run_id = ?
        ORDER BY industry_rank ASC, industry ASC
        """,
        (trace_run_id,),
    )
    scored = store.read_df(
        """
        SELECT industry, score, rank
        FROM l3_irs_daily
        WHERE date = ?
        ORDER BY rank ASC
        """,
        (trade_date,),
    )

    assert written == 2
    assert trace["trace_scope"].tolist() == ["INDUSTRY_DAILY", "INDUSTRY_DAILY"]
    assert trace["coverage_flag"].tolist() == ["BENCHMARK_FILL", "BENCHMARK_FILL"]
    assert trace["benchmark_code"].tolist() == ["000001.SH", "000001.SH"]
    assert trace["benchmark_pct"].tolist() == [0.0, 0.0]
    assert trace["industry"].tolist() == scored["industry"].tolist()
    assert trace["industry_rank"].tolist() == scored["rank"].tolist()
    assert trace["industry_score"].tolist() == scored["score"].tolist()
    store.close()


def test_compute_irs_records_unknown_drop_and_min_industries_skip(tmp_path) -> None:
    db = tmp_path / "irs_skip_trace.duckdb"
    store = Store(db)
    trade_date = date(2026, 1, 9)

    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {"industry": "银行", "date": trade_date, "pct_chg": 0.01, "amount": 150.0, "stock_count": 8},
                {"industry": "未知", "date": trade_date, "pct_chg": 0.02, "amount": 80.0, "stock_count": 3},
            ]
        ),
    )
    store.bulk_upsert(
        "l1_index_daily",
        pd.DataFrame([{"ts_code": "000001.SH", "date": trade_date, "pct_chg": 0.005}]),
    )

    written = compute_irs(store, trade_date, trade_date, min_industries_per_day=2)

    trace_run_id = f"IRS_DAILY::{trade_date.isoformat()}::{trade_date.isoformat()}"
    trace = store.read_df(
        """
        SELECT industry, coverage_flag, industry_rank
        FROM irs_industry_trace_exp
        WHERE run_id = ?
        ORDER BY industry ASC
        """,
        (trace_run_id,),
    )

    assert written == 0
    assert trace["industry"].tolist() == ["未知", "银行"]
    assert trace["coverage_flag"].tolist() == ["UNKNOWN_DROPPED", "MIN_INDUSTRIES_SKIP"]
    assert pd.isna(trace.iloc[0]["industry_rank"])
    assert pd.isna(trace.iloc[1]["industry_rank"])
    assert store.read_df("SELECT * FROM l3_irs_daily WHERE date = ?", (trade_date,)).empty
    store.close()
