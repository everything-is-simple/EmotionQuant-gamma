from __future__ import annotations

from datetime import date

import pandas as pd

import src.data.builder as builder_mod
from src.config import Settings
from src.data.store import Store


def test_build_l3_still_rebuilds_irs_when_mss_is_already_up_to_date(tmp_path, monkeypatch) -> None:
    """回归用例：MSS 已追平时，不应再拿它的 max_date 把 IRS 的缺口一起跳过。"""
    db = tmp_path / "builder_window_regression.duckdb"
    store = Store(db)
    try:
        store.bulk_upsert(
            "l1_trade_calendar",
            pd.DataFrame(
                [
                    {
                        "date": date(2026, 1, 1),
                        "is_trade_day": True,
                        "prev_trade_day": None,
                        "next_trade_day": date(2026, 1, 2),
                    },
                    {
                        "date": date(2026, 1, 2),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 1),
                        "next_trade_day": date(2026, 1, 3),
                    },
                    {
                        "date": date(2026, 1, 3),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 2),
                        "next_trade_day": date(2026, 1, 6),
                    },
                    {
                        "date": date(2026, 1, 6),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 3),
                        "next_trade_day": None,
                    },
                ]
            ),
        )
        store.bulk_upsert(
            "l3_mss_daily",
            pd.DataFrame([{"date": date(2026, 1, 3), "score": 55.0, "signal": "NEUTRAL"}]),
        )
        store.bulk_upsert(
            "l3_irs_daily",
            pd.DataFrame([{"date": date(2026, 1, 1), "industry": "银行", "score": 60.0, "rank": 1}]),
        )

        store.bulk_upsert(
            "l3_stock_gene",
            pd.DataFrame([{"code": "000001", "calc_date": date(2026, 1, 3), "gene_score": 50.0}]),
        )

        calls: list[tuple[str, date, date]] = []

        def fake_compute_mss_variant(*args, **kwargs) -> int:
            _store, begin, finish = args[:3]
            calls.append(("mss", begin, finish))
            return 11

        def fake_compute_irs(*args, **kwargs) -> int:
            _store, begin, finish = args[:3]
            calls.append(("irs", begin, finish))
            return 7

        monkeypatch.setattr(builder_mod, "compute_mss_variant", fake_compute_mss_variant)
        monkeypatch.setattr(builder_mod, "compute_irs", fake_compute_irs)

        written = builder_mod.build_l3(
            store,
            Settings(),
            start=None,
            end=date(2026, 1, 3),
            force=False,
        )

        assert written == 7
        assert calls == [("irs", date(2026, 1, 2), date(2026, 1, 3))]
    finally:
        store.close()


def test_build_l3_still_rebuilds_gene_when_mss_and_irs_are_already_up_to_date(tmp_path, monkeypatch) -> None:
    db = tmp_path / "builder_gene_window_regression.duckdb"
    store = Store(db)
    try:
        store.bulk_upsert(
            "l1_trade_calendar",
            pd.DataFrame(
                [
                    {
                        "date": date(2026, 1, 1),
                        "is_trade_day": True,
                        "prev_trade_day": None,
                        "next_trade_day": date(2026, 1, 2),
                    },
                    {
                        "date": date(2026, 1, 2),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 1),
                        "next_trade_day": date(2026, 1, 3),
                    },
                    {
                        "date": date(2026, 1, 3),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 2),
                        "next_trade_day": date(2026, 1, 6),
                    },
                    {
                        "date": date(2026, 1, 6),
                        "is_trade_day": True,
                        "prev_trade_day": date(2026, 1, 3),
                        "next_trade_day": None,
                    },
                ]
            ),
        )
        store.bulk_upsert(
            "l3_mss_daily",
            pd.DataFrame([{"date": date(2026, 1, 3), "score": 55.0, "signal": "NEUTRAL"}]),
        )
        store.bulk_upsert(
            "l3_irs_daily",
            pd.DataFrame([{"date": date(2026, 1, 3), "industry": "银行", "score": 60.0, "rank": 1}]),
        )

        calls: list[tuple[str, date, date]] = []

        def fake_compute_mss_variant(*args, **kwargs) -> int:
            _store, begin, finish = args[:3]
            calls.append(("mss", begin, finish))
            return 11

        def fake_compute_irs(*args, **kwargs) -> int:
            _store, begin, finish = args[:3]
            calls.append(("irs", begin, finish))
            return 7

        def fake_compute_gene(*args, **kwargs) -> int:
            _store, begin, finish = args[:3]
            calls.append(("gene", begin, finish))
            return 5

        monkeypatch.setattr(builder_mod, "compute_mss_variant", fake_compute_mss_variant)
        monkeypatch.setattr(builder_mod, "compute_irs", fake_compute_irs)
        monkeypatch.setattr(builder_mod, "compute_gene", fake_compute_gene)

        written = builder_mod.build_l3(
            store,
            Settings(HISTORY_START=date(2026, 1, 1)),
            start=None,
            end=date(2026, 1, 3),
            force=False,
        )

        assert written == 5
        assert calls == [("gene", date(2026, 1, 1), date(2026, 1, 3))]
    finally:
        store.close()
