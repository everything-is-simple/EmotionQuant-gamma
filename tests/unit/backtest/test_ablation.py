from __future__ import annotations

from datetime import date

import pandas as pd

from src.backtest.ablation import build_selector_ablation_scenarios, clear_runtime_tables
from src.config import Settings
from src.data.store import Store


def test_build_selector_ablation_scenarios_returns_fixed_dtt_matrix() -> None:
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_score",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MSS_VARIANT="zscore_weighted6",
        MSS_GATE_MODE="bearish_only",
        MSS_BULLISH_THRESHOLD=65.0,
        MSS_BEARISH_THRESHOLD=35.0,
        IRS_TOP_N=10,
    )

    scenarios = build_selector_ablation_scenarios(cfg)

    assert [item.label for item in scenarios] == [
        "legacy_bof_baseline",
        "v0_01_dtt_pattern_only",
        "v0_01_dtt_pattern_plus_irs_score",
        "v0_01_dtt_pattern_plus_irs_mss_score",
    ]
    assert [item.pipeline_mode for item in scenarios] == ["legacy", "dtt", "dtt", "dtt"]
    assert [item.dtt_variant for item in scenarios] == [
        "legacy_bof_baseline",
        "v0_01_dtt_pattern_only",
        "v0_01_dtt_pattern_plus_irs_score",
        "v0_01_dtt_pattern_plus_irs_mss_score",
    ]
    assert [(item.enable_mss_gate, item.enable_irs_filter) for item in scenarios] == [
        (True, True),
        (False, False),
        (False, False),
        (False, False),
    ]


def test_clear_runtime_tables_only_removes_current_run_scoped_trace_rows(tmp_path) -> None:
    db = tmp_path / "ablation_clear_runtime.duckdb"
    store = Store(db)
    try:
        day = date(2026, 1, 8)
        store.bulk_upsert(
            "selector_candidate_trace_exp",
            pd.DataFrame(
                [
                    {
                        "run_id": "run_a",
                        "signal_date": day,
                        "code": "000001",
                        "pipeline_mode": "dtt",
                        "selected": True,
                    },
                    {
                        "run_id": "run_b",
                        "signal_date": day,
                        "code": "000002",
                        "pipeline_mode": "dtt",
                        "selected": True,
                    },
                ]
            ),
        )
        store.bulk_upsert(
            "l3_signal_rank_exp",
            pd.DataFrame(
                [
                    {
                        "run_id": "run_a",
                        "signal_id": "000001_2026-01-08_bof",
                        "signal_date": day,
                        "code": "000001",
                        "variant": "v0_01_dtt_pattern_only",
                        "pattern_strength": 0.8,
                        "irs_score": 50.0,
                        "mss_score": 50.0,
                        "final_score": 80.0,
                        "final_rank": 1,
                        "selected": True,
                    },
                    {
                        "run_id": "run_b",
                        "signal_id": "000002_2026-01-08_bof",
                        "signal_date": day,
                        "code": "000002",
                        "variant": "v0_01_dtt_pattern_only",
                        "pattern_strength": 0.7,
                        "irs_score": 50.0,
                        "mss_score": 50.0,
                        "final_score": 70.0,
                        "final_rank": 1,
                        "selected": True,
                    },
                ]
            ),
        )
        store.bulk_upsert(
            "l3_signals",
            pd.DataFrame(
                [
                    {
                        "signal_id": "000001_2026-01-08_bof",
                        "code": "000001",
                        "signal_date": day,
                        "action": "BUY",
                        "strength": 0.8,
                        "pattern": "bof",
                        "reason_code": "PAS_BOF",
                    }
                ]
            ),
        )
        store.bulk_upsert(
            "l4_orders",
            pd.DataFrame(
                [
                    {
                        "order_id": "000001_2026-01-08_bof",
                        "signal_id": "000001_2026-01-08_bof",
                        "code": "000001",
                        "action": "BUY",
                        "pattern": "bof",
                        "quantity": 100,
                        "execute_date": day,
                        "status": "PENDING",
                    }
                ]
            ),
        )

        clear_runtime_tables(store, run_id="run_a")

        remaining_trace_runs = store.read_df(
            "SELECT run_id, code FROM selector_candidate_trace_exp ORDER BY run_id ASC",
        )
        remaining_rank_runs = store.read_df(
            "SELECT run_id, code FROM l3_signal_rank_exp ORDER BY run_id ASC",
        )

        assert remaining_trace_runs["run_id"].tolist() == ["run_b"]
        assert remaining_trace_runs["code"].tolist() == ["000002"]
        assert remaining_rank_runs["run_id"].tolist() == ["run_b"]
        assert remaining_rank_runs["code"].tolist() == ["000002"]
        assert store.read_df("SELECT * FROM l3_signals").empty
        assert store.read_df("SELECT * FROM l4_orders").empty
    finally:
        store.close()
