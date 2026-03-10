from __future__ import annotations

from datetime import date
from datetime import timedelta

import pandas as pd

from src.data.store import Store
from src.selector.irs import IRS_FACTOR_MODE_FULL, IRS_FACTOR_MODE_LITE, IRS_FACTOR_MODE_RSRV, compute_irs


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

    trace_run_id = f"IRS_DAILY::{IRS_FACTOR_MODE_FULL}::{trade_date.isoformat()}::{trade_date.isoformat()}"
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

    trace_run_id = f"IRS_DAILY::{IRS_FACTOR_MODE_FULL}::{trade_date.isoformat()}::{trade_date.isoformat()}"
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


def test_compute_irs_writes_factor_scores_and_rotation_fields(tmp_path) -> None:
    db = tmp_path / "irs_factor_layers.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        cal = []
        for i in range(6):
            day = base + timedelta(days=i)
            cal.append({"date": day, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None})
        cal_df = pd.DataFrame(cal)
        cal_df["prev_trade_day"] = cal_df["date"].shift(1)
        cal_df["next_trade_day"] = cal_df["date"].shift(-1)
        store.bulk_upsert("l1_trade_calendar", cal_df)

        industry_rows = []
        structure_rows = []
        benchmark_rows = []
        for i in range(6):
            day = base + timedelta(days=i)
            benchmark_rows.append({"ts_code": "000001.SH", "date": day, "pct_chg": 0.005})
            industry_rows.extend(
                [
                    {
                        "industry": "电子",
                        "date": day,
                        "pct_chg": 0.03,
                        "amount": 200.0 + i * 10,
                        "stock_count": 10,
                        "rise_count": 8,
                        "fall_count": 2,
                        "amount_ma20": 150.0,
                        "return_5d": 0.12 if i >= 4 else None,
                        "return_20d": None,
                    },
                    {
                        "industry": "银行",
                        "date": day,
                        "pct_chg": 0.01,
                        "amount": 120.0 + i * 5,
                        "stock_count": 10,
                        "rise_count": 6,
                        "fall_count": 4,
                        "amount_ma20": 100.0,
                        "return_5d": 0.04 if i >= 4 else None,
                        "return_20d": None,
                    },
                ]
            )
            structure_rows.extend(
                [
                    {
                        "industry": "电子",
                        "date": day,
                        "strong_up_count": 4,
                        "new_high_count": 3,
                        "leader_count": 2,
                        "leader_strength": 0.8,
                        "strong_stock_ratio": 0.4,
                        "strong_stock_amount_share": 0.55,
                        "leader_follow_through": 0.7,
                        "bof_hit_density_5d": 0.05,
                    },
                    {
                        "industry": "银行",
                        "date": day,
                        "strong_up_count": 2,
                        "new_high_count": 1,
                        "leader_count": 1,
                        "leader_strength": 0.4,
                        "strong_stock_ratio": 0.2,
                        "strong_stock_amount_share": 0.35,
                        "leader_follow_through": 0.4,
                        "bof_hit_density_5d": 0.0,
                    },
                ]
            )
        store.bulk_upsert("l2_industry_daily", pd.DataFrame(industry_rows))
        store.bulk_upsert("l2_industry_structure_daily", pd.DataFrame(structure_rows))
        store.bulk_upsert("l1_index_daily", pd.DataFrame(benchmark_rows))

        target_day = base + timedelta(days=5)
        written = compute_irs(store, target_day, target_day, min_industries_per_day=2)

        scored = store.read_df(
            """
            SELECT industry, score, rank, rs_score, cf_score, rv_score, rt_score, bd_score, gn_score, rotation_status, rotation_slope
            FROM l3_irs_daily
            WHERE date = ?
            ORDER BY rank ASC
            """,
            (target_day,),
        )

        assert written == 2
        assert scored["industry"].tolist() == ["电子", "银行"]
        assert scored["rank"].tolist() == [1, 2]
        assert scored["rv_score"].notna().all()
        assert scored["rt_score"].notna().all()
        assert scored["bd_score"].notna().all()
        assert scored["gn_score"].notna().all()
        assert scored["rotation_status"].isin(["START", "CONTINUE", "EXHAUST", "FALLBACK", "NEUTRAL"]).all()
        assert (scored["cf_score"] - scored["rv_score"]).abs().max() > 0.01
    finally:
        store.close()


def test_compute_irs_factor_modes_produce_distinct_scores_and_trace_variants(tmp_path) -> None:
    db = tmp_path / "irs_factor_modes.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        cal = []
        for i in range(6):
            day = base + timedelta(days=i)
            cal.append({"date": day, "is_trade_day": True, "prev_trade_day": None, "next_trade_day": None})
        cal_df = pd.DataFrame(cal)
        cal_df["prev_trade_day"] = cal_df["date"].shift(1)
        cal_df["next_trade_day"] = cal_df["date"].shift(-1)
        store.bulk_upsert("l1_trade_calendar", cal_df)

        industry_rows = []
        structure_rows = []
        benchmark_rows = []
        for i in range(6):
            day = base + timedelta(days=i)
            benchmark_rows.append({"ts_code": "000001.SH", "date": day, "pct_chg": 0.004})
            industry_rows.extend(
                [
                    {
                        "industry": "电子",
                        "date": day,
                        "pct_chg": 0.03,
                        "amount": 220.0 + i * 10,
                        "stock_count": 10,
                        "rise_count": 8,
                        "fall_count": 2,
                        "amount_ma20": 150.0,
                        "return_5d": 0.10 if i >= 4 else None,
                        "return_20d": None,
                    },
                    {
                        "industry": "银行",
                        "date": day,
                        "pct_chg": 0.01,
                        "amount": 110.0 + i * 5,
                        "stock_count": 10,
                        "rise_count": 5,
                        "fall_count": 5,
                        "amount_ma20": 100.0,
                        "return_5d": 0.02 if i >= 4 else None,
                        "return_20d": None,
                    },
                ]
            )
            structure_rows.extend(
                [
                    {
                        "industry": "电子",
                        "date": day,
                        "strong_up_count": 4,
                        "new_high_count": 3,
                        "leader_count": 2,
                        "leader_strength": 0.9,
                        "strong_stock_ratio": 0.45,
                        "strong_stock_amount_share": 0.60,
                        "leader_follow_through": 0.75,
                        "bof_hit_density_5d": 0.05,
                    },
                    {
                        "industry": "银行",
                        "date": day,
                        "strong_up_count": 1,
                        "new_high_count": 0,
                        "leader_count": 1,
                        "leader_strength": 0.3,
                        "strong_stock_ratio": 0.10,
                        "strong_stock_amount_share": 0.25,
                        "leader_follow_through": 0.35,
                        "bof_hit_density_5d": 0.0,
                    },
                ]
            )
        store.bulk_upsert("l2_industry_daily", pd.DataFrame(industry_rows))
        store.bulk_upsert("l2_industry_structure_daily", pd.DataFrame(structure_rows))
        store.bulk_upsert("l1_index_daily", pd.DataFrame(benchmark_rows))

        target_day = base + timedelta(days=5)
        score_by_mode: dict[str, list[float]] = {}
        for mode in [IRS_FACTOR_MODE_LITE, IRS_FACTOR_MODE_RSRV, IRS_FACTOR_MODE_FULL]:
            written = compute_irs(store, target_day, target_day, min_industries_per_day=2, factor_mode=mode)
            scored = store.read_df(
                """
                SELECT industry, score
                FROM l3_irs_daily
                WHERE date = ?
                ORDER BY rank ASC
                """,
                (target_day,),
            )
            trace = store.read_df(
                """
                SELECT DISTINCT variant
                FROM irs_industry_trace_exp
                WHERE run_id = ?
                ORDER BY variant ASC
                """,
                (f"IRS_DAILY::{mode}::{target_day.isoformat()}::{target_day.isoformat()}",),
            )
            assert written == 2
            assert len(trace["variant"].tolist()) == 1
            score_by_mode[mode] = scored["score"].tolist()

        assert score_by_mode[IRS_FACTOR_MODE_LITE] != score_by_mode[IRS_FACTOR_MODE_RSRV]
        assert score_by_mode[IRS_FACTOR_MODE_RSRV] != score_by_mode[IRS_FACTOR_MODE_FULL]
    finally:
        store.close()
