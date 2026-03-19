from __future__ import annotations

from datetime import date

from src.config import Settings
from src.data.builder import build_l3
from src.data.store import Store


def test_build_l3_uses_gene_incremental_builder_on_non_force(monkeypatch, tmp_path) -> None:
    store = Store(tmp_path / "builder_incremental.duckdb")
    try:
        base = date(2026, 2, 24)
        store.conn.execute("DELETE FROM l1_trade_calendar")
        store.conn.execute(
            """
            INSERT INTO l1_trade_calendar (date, is_trade_day, prev_trade_day, next_trade_day)
            VALUES (?, TRUE, NULL, NULL)
            """,
            [base],
        )

        calls: dict[str, object] = {}

        def fake_mss(*args, **kwargs) -> int:
            return 0

        def fake_irs(*args, **kwargs) -> int:
            return 0

        def fake_incremental_builder(store_arg, *, start, end, codes=None, refresh_evals=True, refresh_market=True):
            calls["start"] = start
            calls["end"] = end
            calls["refresh_evals"] = refresh_evals
            calls["refresh_market"] = refresh_market
            return {
                "written_rows": 11,
                "rank_refresh_rows": 7,
                "factor_eval_rows": 5,
                "distribution_eval_rows": 3,
                "validation_eval_rows": 2,
                "market_rows": 13,
            }

        def fake_conditioning(*args, **kwargs) -> int:
            return 17

        monkeypatch.setattr("src.data.builder.compute_mss_variant", fake_mss)
        monkeypatch.setattr("src.data.builder.compute_irs", fake_irs)
        monkeypatch.setattr("src.data.builder.run_gene_incremental_builder", fake_incremental_builder)
        monkeypatch.setattr("src.data.builder.compute_gene_conditioning", fake_conditioning)

        total = build_l3(
            store,
            Settings(history_start=base),
            start=base,
            end=base,
            force=False,
        )

        assert calls == {
            "start": base,
            "end": base,
            "refresh_evals": True,
            "refresh_market": True,
        }
        assert total == 58
    finally:
        store.close()
