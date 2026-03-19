from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.data.store import Store
from src.selector.gene import compute_gene
from src.selector.gene_incremental import (
    compute_gene_incremental_for_codes,
    refresh_gene_conditioning_for_dates,
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


def _adj_daily_rows_from_specs(base: date, code: str, specs: list[dict[str, float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_close = float(specs[0]["close"])
    for index, spec in enumerate(specs):
        day = base + timedelta(days=index)
        close = float(spec["close"])
        open_price = float(spec.get("open", close if index == 0 else previous_close))
        high_price = float(spec.get("high", max(open_price, close) + 0.15))
        low_price = float(spec.get("low", min(open_price, close) - 0.15))
        volume = float(spec.get("volume", 1_000.0))
        volume_ma20 = float(spec.get("volume_ma20", 900.0))
        rows.append(
            {
                "code": code,
                "date": day,
                "adj_open": open_price,
                "adj_high": high_price,
                "adj_low": low_price,
                "adj_close": close,
                "volume": volume,
                "volume_ma20": volume_ma20,
                "amount": close * volume,
                "pct_chg": ((close - previous_close) / previous_close) * 100.0 if index > 0 else 0.0,
            }
        )
        previous_close = close
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
        assert summary["conditioning_sample_rows"] >= 0
        assert summary["conditioning_eval_rows"] >= 0

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


def test_refresh_gene_conditioning_for_dates_rebuilds_samples_and_eval(tmp_path) -> None:
    db = tmp_path / "gene_incremental_conditioning.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)

        def bof_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for _ in range(20):
                specs.append(
                    {
                        "open": 9.95,
                        "high": 10.4,
                        "low": 9.8,
                        "close": 10.0,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 9.7,
                    "high": 10.5,
                    "low": 9.5,
                    "close": 10.3,
                    "volume": 1_300.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.5, 10.7, 10.9, 11.1, 11.0, 11.3, 11.5, 11.7, 11.8, 12.0, 12.2, 12.1]:
                specs.append({"close": close, "volume": 1_100.0, "volume_ma20": 900.0})
            return specs

        def pb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for index in range(20):
                close = 10.0 + index * 0.25
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.18,
                        "low": close - 0.18,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for index in range(15):
                close = 15.2 + index * 0.32
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.2,
                        "low": close - 0.18,
                        "volume": 1_030.0,
                        "volume_ma20": 900.0,
                    }
                )
            for close in [19.0, 18.5, 18.0, 17.5, 18.8]:
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.18,
                        "low": close - 0.18,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 18.9,
                    "high": 19.8,
                    "low": 18.7,
                    "close": 19.6,
                    "volume": 1_200.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [19.8, 20.0, 20.2, 20.5, 20.3, 20.6, 20.8, 21.0, 21.2, 21.5, 21.3, 21.4]:
                specs.append({"close": close, "volume": 1_050.0, "volume_ma20": 900.0})
            return specs

        def bpb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for close in [
                10.0,
                10.05,
                10.1,
                10.15,
                10.2,
                10.25,
                10.2,
                10.15,
                10.1,
                10.05,
                10.0,
                10.08,
                10.12,
                10.16,
                10.2,
                10.24,
                10.18,
                10.12,
                10.08,
                10.14,
            ]:
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.12,
                        "low": close - 0.12,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.extend(
                [
                    {
                        "open": 10.48,
                        "high": 10.7,
                        "low": 10.56,
                        "close": 10.65,
                        "volume": 1_300.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.72,
                        "high": 10.88,
                        "low": 10.7,
                        "close": 10.82,
                        "volume": 1.280e3,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.78,
                        "high": 10.75,
                        "low": 10.55,
                        "close": 10.62,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.64,
                        "high": 10.7,
                        "low": 10.52,
                        "close": 10.58,
                        "volume": 970.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.6,
                        "high": 10.72,
                        "low": 10.56,
                        "close": 10.64,
                        "volume": 960.0,
                        "volume_ma20": 900.0,
                    },
                ]
            )
            specs.append(
                {
                    "open": 10.7,
                    "high": 11.05,
                    "low": 10.66,
                    "close": 11.0,
                    "volume": 1_250.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [11.05, 11.12, 11.2, 11.18, 11.26, 11.3, 11.36, 11.42, 11.48, 11.52, 11.58, 11.6]:
                specs.append({"close": close, "volume": 1_040.0, "volume_ma20": 900.0})
            return specs

        def tst_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for index in range(55):
                close = 10.35 + (index % 5) * 0.08 + (index // 20) * 0.03
                low = 10.0 if index in (3, 17, 31) else close - 0.18
                specs.append(
                    {
                        "open": close - 0.06,
                        "high": close + 0.18,
                        "low": low,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for close in [10.18, 10.12, 10.16, 10.1, 10.2]:
                specs.append(
                    {
                        "open": close + 0.02,
                        "high": close + 0.16,
                        "low": 10.05,
                        "close": close,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 10.22,
                    "high": 10.55,
                    "low": 10.0,
                    "close": 10.48,
                    "volume": 1_100.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.52, 10.56, 10.6, 10.64, 10.68, 10.72, 10.76, 10.8, 10.84, 10.88, 10.92, 10.96]:
                specs.append({"close": close, "volume": 1_020.0, "volume_ma20": 900.0})
            return specs

        def cpb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for close in [
                10.1,
                10.2,
                10.15,
                10.25,
                10.2,
                10.18,
                10.22,
                10.16,
                10.24,
                10.19,
                10.23,
                10.17,
                10.25,
                10.2,
                10.24,
                10.18,
                10.26,
                10.21,
                10.25,
                10.2,
            ]:
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.15,
                        "low": close - 0.15,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for index in range(20):
                close = 10.2 + (index % 3) * 0.03
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.12,
                        "low": close - 0.12,
                        "close": close,
                        "volume": 1_020.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 10.4,
                    "high": 10.8,
                    "low": 10.35,
                    "close": 10.75,
                    "volume": 1_300.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.82, 10.88, 10.95, 11.0, 10.98, 11.05, 11.12, 11.2, 11.18, 11.26, 11.3, 11.28]:
                specs.append({"close": close, "volume": 1_040.0, "volume_ma20": 900.0})
            return specs

        spec_map = {
            "BOF": bof_specs(),
            "BPB": bpb_specs(),
            "PB": pb_specs(),
            "TST": tst_specs(),
            "CPB": cpb_specs(),
        }
        max_len = max(len(specs) for specs in spec_map.values())
        for specs in spec_map.values():
            while len(specs) < max_len:
                specs.append(
                    {
                        "close": float(specs[-1]["close"]) + 0.05,
                        "volume": 1_040.0,
                        "volume_ma20": 900.0,
                    }
                )
        calc_date = base + timedelta(days=max_len - 1)

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, max_len))
        stock_rows: list[dict[str, object]] = []
        for code, specs in spec_map.items():
            stock_rows.extend(_adj_daily_rows_from_specs(base, code, specs))
        store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(stock_rows))

        compute_gene(store, base, calc_date)
        store.conn.execute("DELETE FROM l3_gene_conditioning_sample")
        store.conn.execute("DELETE FROM l3_gene_conditioning_eval WHERE calc_date = ?", [calc_date])

        summary = compute_gene_incremental_for_codes(
            store,
            codes=spec_map.keys(),
            start=calc_date,
            end=calc_date,
            refresh_evals=False,
            refresh_conditioning=True,
            refresh_market=False,
        )
        assert summary["conditioning_sample_rows"] > 0
        assert summary["conditioning_eval_rows"] > 0

        store.conn.execute("DELETE FROM l3_gene_conditioning_eval WHERE calc_date = ?", [calc_date])
        rebuilt = refresh_gene_conditioning_for_dates(store, [calc_date])
        assert rebuilt > 0
        assert store.read_scalar("SELECT COUNT(*) FROM l3_gene_conditioning_sample") > 0
        assert store.read_scalar(
            "SELECT COUNT(*) FROM l3_gene_conditioning_eval WHERE calc_date = ?",
            (calc_date,),
        ) == rebuilt
    finally:
        store.close()
