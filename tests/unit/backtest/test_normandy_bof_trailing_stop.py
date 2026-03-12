from __future__ import annotations

from src.backtest.normandy_bof_trailing_stop import (
    _build_path_report,
    _classify_trailing_stop_case,
    build_normandy_bof_control_trailing_stop_digest,
)


def test_classify_trailing_stop_case_marks_legitimate_protection() -> None:
    category, rationale = _classify_trailing_stop_case(
        {
            "stop_only_pnl_delta_vs_control": -120.0,
            "loose_exit_pnl_delta_vs_control": -20.0,
            "stop_only_exit_reason": "STOP_LOSS",
        }
    )

    assert category == "legitimate_protection"
    assert "did not improve" in rationale


def test_classify_trailing_stop_case_marks_fat_tail_winner_cut() -> None:
    category, rationale = _classify_trailing_stop_case(
        {
            "stop_only_exit_reason": "FORCE_CLOSE",
            "stop_only_pnl_pct_delta_vs_control": 0.75,
            "stop_only_pnl_delta_vs_control": 9000.0,
            "stop_only_exit_timing_delta_trade_days": 55,
            "loose_exit_pnl_delta_vs_control": 4500.0,
            "loose_exit_exit_timing_delta_trade_days": 22,
            "trail_only_pnl_delta_vs_control": 0.0,
        }
    )

    assert category == "fat_tail_winner_cut"
    assert "fat-tail winner" in rationale


def test_build_path_report_aggregates_category_counts_and_extremes() -> None:
    case_rows = [
        {
            "signal_id": "a",
            "case_category": "fat_tail_winner_cut",
            "stop_only_pnl_delta_vs_control": 3000.0,
        },
        {
            "signal_id": "b",
            "case_category": "repeatable_trend_premature_exit",
            "stop_only_pnl_delta_vs_control": 800.0,
        },
        {
            "signal_id": "c",
            "case_category": "legitimate_protection",
            "stop_only_pnl_delta_vs_control": -500.0,
        },
    ]

    report = _build_path_report(case_rows)

    assert report["category_counts"] == {
        "fat_tail_winner_cut": 1,
        "repeatable_trend_premature_exit": 1,
        "legitimate_protection": 1,
    }
    assert report["positive_stop_only_case_count"] == 2
    assert report["negative_stop_only_case_count"] == 1
    assert report["top_positive_stop_only_cases"][0]["signal_id"] == "a"
    assert report["top_negative_stop_only_cases"][0]["signal_id"] == "c"


def test_build_normandy_bof_control_trailing_stop_digest_marks_outlier_cluster() -> None:
    followup_payload = {
        "followup_status": "completed",
        "research_parent": "BOF_CONTROL",
        "followup_focus": "targeted_trailing_stop_path_decomposition",
        "trailing_stop_case_table": [
            {"signal_id": f"fat_{idx}", "stop_only_pnl_delta_vs_control": 0.0, "case_category": "ambiguous_mixed"}
            for idx in range(55)
        ],
        "path_report": {
            "category_counts": {
                "fat_tail_winner_cut": 5,
                "repeatable_trend_premature_exit": 0,
                "legitimate_protection": 3,
                "ambiguous_mixed": 47,
            },
            "category_stop_only_pnl_delta_vs_control": {
                "fat_tail_winner_cut": 8500.0,
                "repeatable_trend_premature_exit": 0.0,
                "legitimate_protection": -600.0,
                "ambiguous_mixed": 1500.0,
            },
            "top_fat_tail_winner_cut_cases": [{"signal_id": "fat_0"}],
            "top_repeatable_trend_cases": [],
            "top_legitimate_protection_cases": [{"signal_id": "legit_0"}],
        },
    }
    followup_payload["trailing_stop_case_table"] = [
        {"signal_id": "fat_0", "stop_only_pnl_delta_vs_control": 3000.0, "case_category": "fat_tail_winner_cut"},
        {"signal_id": "fat_1", "stop_only_pnl_delta_vs_control": 2200.0, "case_category": "fat_tail_winner_cut"},
        {"signal_id": "fat_2", "stop_only_pnl_delta_vs_control": 1800.0, "case_category": "fat_tail_winner_cut"},
        {"signal_id": "fat_3", "stop_only_pnl_delta_vs_control": 900.0, "case_category": "fat_tail_winner_cut"},
        {"signal_id": "fat_4", "stop_only_pnl_delta_vs_control": 600.0, "case_category": "fat_tail_winner_cut"},
        {"signal_id": "legit_0", "stop_only_pnl_delta_vs_control": -300.0, "case_category": "legitimate_protection"},
    ] + [
        {"signal_id": f"mix_{idx}", "stop_only_pnl_delta_vs_control": value, "case_category": "ambiguous_mixed"}
        for idx, value in enumerate([450.0, 300.0, 250.0, 200.0, 180.0, 120.0, -120.0, -90.0])
    ]

    digest = build_normandy_bof_control_trailing_stop_digest(followup_payload)

    assert digest["diagnosis"] == "small_cluster_of_outlier_truncation"
    assert digest["decision"] == "investigate_fat_tail_preservation_before_global_change"


def test_build_normandy_bof_control_trailing_stop_digest_marks_repeatable_pattern() -> None:
    positive_repeatable = [
        {"signal_id": f"rep_{idx}", "stop_only_pnl_delta_vs_control": 120.0, "case_category": "repeatable_trend_premature_exit"}
        for idx in range(15)
    ]
    other_cases = [
        {"signal_id": f"mix_{idx}", "stop_only_pnl_delta_vs_control": 80.0, "case_category": "ambiguous_mixed"}
        for idx in range(10)
    ]
    followup_payload = {
        "followup_status": "completed",
        "research_parent": "BOF_CONTROL",
        "followup_focus": "targeted_trailing_stop_path_decomposition",
        "trailing_stop_case_table": positive_repeatable + other_cases,
        "path_report": {
            "category_counts": {
                "repeatable_trend_premature_exit": 15,
                "ambiguous_mixed": 10,
                "fat_tail_winner_cut": 0,
                "legitimate_protection": 0,
            },
            "category_stop_only_pnl_delta_vs_control": {
                "repeatable_trend_premature_exit": 1800.0,
                "ambiguous_mixed": 800.0,
                "fat_tail_winner_cut": 0.0,
                "legitimate_protection": 0.0,
            },
            "top_fat_tail_winner_cut_cases": [],
            "top_repeatable_trend_cases": [{"signal_id": "rep_0"}],
            "top_legitimate_protection_cases": [],
        },
    }

    digest = build_normandy_bof_control_trailing_stop_digest(followup_payload)

    assert digest["diagnosis"] == "repeatable_trend_premature_exit_pattern"
    assert digest["decision"] == "prioritize_targeted_trailing_semantics_follow_up"
