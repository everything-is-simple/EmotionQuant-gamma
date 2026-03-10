from __future__ import annotations

import pandas as pd

from src.backtest.pas_ablation import (
    build_pas_ablation_scenarios,
    compute_diff_days,
    compute_pattern_overlap_rate,
    summarize_introduced_rows,
    summarize_selected_pattern_distribution,
)
from src.config import Settings


def test_build_pas_ablation_scenarios_returns_fixed_phase1_registry_matrix() -> None:
    scenarios = build_pas_ablation_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF",
        "BPB",
        "PB",
        "TST",
        "CPB",
        "YTC5_ANY",
        "YTC5_ANY_PLUS_QUALITY",
    ]
    assert scenarios[0].single_pattern_mode == "bof"
    assert scenarios[-1].quality_enabled is True
    assert scenarios[-2].patterns == ("bof", "bpb", "pb", "tst", "cpb")


def test_compute_diff_days_counts_rank_or_execution_set_changes() -> None:
    left = pd.DataFrame(
        [
            {"signal_date": "2026-01-08", "signal_id": "a", "final_rank": 1},
            {"signal_date": "2026-01-09", "signal_id": "b", "final_rank": 1},
        ]
    )
    right = pd.DataFrame(
        [
            {"signal_date": "2026-01-08", "signal_id": "a", "final_rank": 2},
            {"signal_date": "2026-01-09", "signal_id": "b", "final_rank": 1},
            {"signal_date": "2026-01-10", "signal_id": "c", "final_rank": 1},
        ]
    )

    assert compute_diff_days(left, right, date_col="signal_date", key_cols=("signal_id", "final_rank")) == 2


def test_compute_pattern_overlap_rate_uses_detected_pattern_groups() -> None:
    frame = pd.DataFrame(
        [
            {"signal_date": "2026-01-08", "code": "000001", "pattern": "bof"},
            {"signal_date": "2026-01-08", "code": "000001", "pattern": "bpb"},
            {"signal_date": "2026-01-08", "code": "000002", "pattern": "pb"},
            {"signal_date": "2026-01-09", "code": "000003", "pattern": "tst"},
        ]
    )

    assert compute_pattern_overlap_rate(frame) == 1 / 3


def test_summarize_introduced_rows_reports_unique_samples() -> None:
    base = pd.DataFrame(
        [
            {"signal_date": "2026-01-08", "code": "000001", "signal_id": "a", "final_rank": 1},
        ]
    )
    target = pd.DataFrame(
        [
            {"signal_date": "2026-01-08", "code": "000001", "signal_id": "a", "final_rank": 1},
            {"signal_date": "2026-01-08", "code": "000002", "signal_id": "b", "final_rank": 2},
            {"signal_date": "2026-01-08", "code": "000002", "signal_id": "b", "final_rank": 2},
        ]
    )

    summary = summarize_introduced_rows(
        base,
        target,
        date_col="signal_date",
        columns=("code", "signal_id", "final_rank"),
    )
    assert summary["count"] == 1
    assert summary["sample"] == [
        {"signal_date": "2026-01-08", "code": "000002", "signal_id": "b", "final_rank": 2}
    ]


def test_summarize_selected_pattern_distribution_counts_selected_patterns() -> None:
    frame = pd.DataFrame(
        [
            {"pattern": "bof"},
            {"pattern": "bpb"},
            {"pattern": "bpb"},
        ]
    )

    assert summarize_selected_pattern_distribution(frame) == {"bof": 1, "bpb": 2}
