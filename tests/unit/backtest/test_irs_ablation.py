from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.backtest.irs_ablation import (
    _snapshot_runtime_metrics,
    build_irs_ablation_scenarios,
    run_irs_ablation,
)
from src.config import Settings
from src.data.store import Store


def test_build_irs_ablation_scenarios_returns_fixed_phase2_matrix() -> None:
    scenarios = build_irs_ablation_scenarios()
    assert [(scenario.label, scenario.factor_mode) for scenario in scenarios] == [
        ("IRS_LITE", "lite"),
        ("IRS_RSRV", "rsrv"),
        ("IRS_RSRVRTBDGN", "rsrvrtbdgn"),
    ]


def test_run_irs_ablation_rejects_skip_rebuild_for_multi_scenario_matrix(tmp_path) -> None:
    db = tmp_path / "irs-ablation.duckdb"
    db.write_bytes(b"")

    with pytest.raises(ValueError, match="skip_rebuild_irs"):
        run_irs_ablation(
            db_path=db,
            config=Settings(),
            start=Settings().history_start,
            end=Settings().history_start,
            dtt_variant="v0_01_dtt_pattern_plus_irs_score",
            skip_rebuild_irs=True,
        )


def test_snapshot_runtime_metrics_scopes_ranked_signal_count_by_run_id(tmp_path) -> None:
    db = tmp_path / "irs-ablation-metrics.duckdb"
    store = Store(db)
    try:
        start = date(2026, 1, 5)
        end = date(2026, 2, 24)
        store.bulk_upsert(
            "l3_signals",
            pd.DataFrame(
                [
                    {
                        "signal_id": "000001_2026-02-03_bof",
                        "code": "000001",
                        "signal_date": date(2026, 2, 3),
                        "action": "BUY",
                        "strength": 88.0,
                        "pattern": "bof",
                        "reason_code": None,
                    }
                ]
            ),
        )
        store.bulk_upsert(
            "l3_signal_rank_exp",
            pd.DataFrame(
                [
                    {
                        "run_id": "run-a",
                        "signal_id": "000001_2026-02-03_bof",
                        "signal_date": date(2026, 2, 3),
                        "code": "000001",
                        "industry": "银行",
                        "variant": "v0_01_dtt_pattern_plus_irs_score",
                        "pattern_strength": 88.0,
                        "irs_score": 60.0,
                        "mss_score": 50.0,
                        "final_score": 74.0,
                        "final_rank": 1,
                        "selected": True,
                    },
                    {
                        "run_id": "run-b",
                        "signal_id": "000001_2026-02-03_bof",
                        "signal_date": date(2026, 2, 3),
                        "code": "000001",
                        "industry": "银行",
                        "variant": "v0_01_dtt_pattern_plus_irs_score",
                        "pattern_strength": 88.0,
                        "irs_score": 59.0,
                        "mss_score": 50.0,
                        "final_score": 73.0,
                        "final_rank": 2,
                        "selected": True,
                    },
                ]
            ),
        )

        signals_count, ranked_signals_count, trades_count = _snapshot_runtime_metrics(
            store, start, end, "run-a"
        )

        assert signals_count == 1
        assert ranked_signals_count == 1
        assert trades_count == 0
    finally:
        store.close()
