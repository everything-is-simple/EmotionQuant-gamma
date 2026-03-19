from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.data.store import Store
from src.selector.gene import compute_gene
from src.selector.gene_incremental import (
    compute_gene_incremental_for_codes,
    refresh_gene_evals_for_dates,
    run_gene_incremental_builder,
    scan_gene_dirty_windows,
)


def _trade_calendar(start: date, days: int) -> pd.DataFrame:
    rows = []
    for index in range(days):
        day = start + timedelta(days=index)
        rows.append(
            {
                "date": day,
                "is_trade_day": True,
                "prev_trade_day": start + timedelta(days=index - 1) if index > 0 else None,
                "next_trade_day": start + timedelta(days=index + 1) if index < days - 1 else None,
            }
        )
    return pd.DataFrame(rows)


def _adj_daily_rows(base: date, code: str, closes: list[float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, close in enumerate(closes):
        day = base + timedelta(days=index)
        rows.append(
            {
                "code": code,
                "date": day,
                "adj_open": close - 0.1,
                "adj_high": close + 0.2,
                "adj_low": close - 0.2,
                "adj_close": close,
                "volume": 1_000.0 + index * 10.0,
                "amount": close * 10_000.0,
                "pct_chg": 0.0,
            }
        )
    return rows


def test_gene_incremental_builder_rebuilds_only_dirty_codes(tmp_path) -> None:
    db = tmp_path / "gene_incremental.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes_a = [
            10.0,
            11.0,
            13.0,
            12.0,
            9.0,
            10.0,
            12.0,
            11.0,
            13.0,
            12.0,
            14.0,
            15.0,
            14.0,
            12.0,
            13.0,
            15.0,
            14.0,
            16.0,
            15.0,
            17.0,
            16.0,
            18.0,
            17.0,
            19.0,
            18.0,
            20.0,
        ]
        closes_b = [
            8.0,
            8.5,
            9.2,
            8.9,
            7.8,
            8.1,
            8.8,
            8.4,
            9.0,
            8.8,
            9.1,
            9.3,
            9.0,
            8.7,
            9.4,
            9.1,
            9.7,
            9.4,
            10.0,
            9.6,
            10.1,
            9.8,
            10.4,
            10.0,
            10.6,
            10.2,
        ]
        initial_end = base + timedelta(days=len(closes_a) - 1)

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes_a) + 2))
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(_adj_daily_rows(base, "AAA", closes_a) + _adj_daily_rows(base, "BBB", closes_b)),
        )
        compute_gene(store, base, initial_end)

        aaa_extension = [
            {
                "code": "AAA",
                "date": initial_end + timedelta(days=1),
                "adj_open": 14.9,
                "adj_high": 15.4,
                "adj_low": 14.7,
                "adj_close": 15.2,
                "volume": 1_200.0,
                "amount": 152_000.0,
                "pct_chg": 0.0,
            },
            {
                "code": "AAA",
                "date": initial_end + timedelta(days=2),
                "adj_open": 15.1,
                "adj_high": 15.8,
                "adj_low": 14.9,
                "adj_close": 15.6,
                "volume": 1_250.0,
                "amount": 156_000.0,
                "pct_chg": 0.0,
            },
        ]
        incremental_start = initial_end + timedelta(days=1)
        incremental_end = initial_end + timedelta(days=2)
        store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(aaa_extension))

        dirty_windows = scan_gene_dirty_windows(store, start=incremental_start, end=incremental_end)
        assert [window.code for window in dirty_windows] == ["AAA"]

        summary = run_gene_incremental_builder(store, start=incremental_start, end=incremental_end, refresh_market=False)
        assert summary["code_count"] == 1
        assert summary["codes"] == ["AAA"]
        assert summary["market_rows"] == 0
        assert incremental_end.isoformat() in summary["touched_dates"]
        assert summary["factor_eval_rows"] >= 0
        assert summary["distribution_eval_rows"] >= 0
        assert summary["validation_eval_rows"] >= 0

        latest_snapshots = store.read_df(
            """
            SELECT code, calc_date, cross_section_magnitude_rank
            FROM l3_stock_gene
            WHERE calc_date = ?
            ORDER BY code
            """,
            (incremental_end,),
        )
        assert latest_snapshots["code"].tolist() == ["AAA"]
        assert latest_snapshots["cross_section_magnitude_rank"].tolist() == [1]

        latest_stock_surface = store.read_df(
            """
            SELECT code, calc_date, surface_label
            FROM l3_stock_lifespan_surface
            WHERE calc_date = ?
            ORDER BY code, surface_label
            """,
            (incremental_end,),
        )
        assert len(latest_stock_surface) == 4
        assert latest_stock_surface["code"].eq("AAA").all()

        preserved_bbb = store.read_df(
            """
            SELECT code, calc_date
            FROM l3_stock_gene
            WHERE code = 'BBB' AND calc_date = ?
            """,
            (initial_end,),
        )
        assert len(preserved_bbb) == 1

        rerun = compute_gene_incremental_for_codes(
            store,
            codes=["AAA"],
            start=incremental_start,
            end=incremental_end,
            refresh_market=False,
        )
        assert rerun["code_count"] == 1
        assert store.read_scalar(
            "SELECT COUNT(*) FROM l3_stock_gene WHERE code = 'AAA' AND calc_date = ?",
            (incremental_end,),
        ) == 1
        assert store.read_scalar(
            "SELECT COUNT(*) FROM l3_stock_lifespan_surface WHERE code = 'AAA' AND calc_date = ?",
            (incremental_end,),
        ) == 4

        eval_counts = {
            "factor": store.read_scalar(
                "SELECT COUNT(*) FROM l3_gene_factor_eval WHERE calc_date = ?",
                (incremental_end,),
            ),
            "distribution": store.read_scalar(
                "SELECT COUNT(*) FROM l3_gene_distribution_eval WHERE calc_date = ?",
                (incremental_end,),
            ),
            "validation": store.read_scalar(
                "SELECT COUNT(*) FROM l3_gene_validation_eval WHERE calc_date = ?",
                (incremental_end,),
            ),
        }
        assert eval_counts["factor"] > 0
        assert eval_counts["distribution"] > 0
        assert eval_counts["validation"] == summary["validation_eval_rows"]
    finally:
        store.close()


def test_refresh_gene_evals_for_dates_rebuilds_target_calc_date_only(tmp_path) -> None:
    db = tmp_path / "gene_incremental_eval.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes_a = [
            10.0,
            11.0,
            13.0,
            12.0,
            9.0,
            10.0,
            12.0,
            11.0,
            13.0,
            12.0,
            14.0,
            15.0,
            14.0,
            12.0,
            13.0,
            15.0,
            14.0,
            16.0,
            15.0,
            17.0,
            16.0,
            18.0,
            17.0,
            19.0,
            18.0,
            20.0,
        ]
        closes_b = [
            8.0,
            8.5,
            9.2,
            8.9,
            7.8,
            8.1,
            8.8,
            8.4,
            9.0,
            8.8,
            9.1,
            9.3,
            9.0,
            8.7,
            9.4,
            9.1,
            9.7,
            9.4,
            10.0,
            9.6,
            10.1,
            9.8,
            10.4,
            10.0,
            10.6,
            10.2,
        ]
        calc_date = base + timedelta(days=len(closes_a) - 1)
        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes_a)))
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(_adj_daily_rows(base, "AAA", closes_a) + _adj_daily_rows(base, "BBB", closes_b)),
        )
        compute_gene(store, base, calc_date)

        store.conn.execute("DELETE FROM l3_gene_factor_eval WHERE calc_date = ?", [calc_date])
        store.conn.execute("DELETE FROM l3_gene_distribution_eval WHERE calc_date = ?", [calc_date])
        store.conn.execute("DELETE FROM l3_gene_validation_eval WHERE calc_date = ?", [calc_date])

        refreshed = refresh_gene_evals_for_dates(store, [calc_date])
        assert refreshed["factor_eval_rows"] > 0
        assert refreshed["distribution_eval_rows"] > 0
        assert refreshed["validation_eval_rows"] == store.read_scalar(
            "SELECT COUNT(*) FROM l3_gene_validation_eval WHERE calc_date = ?",
            (calc_date,),
        )
    finally:
        store.close()
