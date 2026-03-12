from __future__ import annotations

from src.backtest.normandy_bof_quality import (
    build_normandy_bof_quality_digest,
    build_normandy_bof_quality_scenarios,
    build_normandy_bof_quality_stability_report,
    compute_normandy_bof_branch_context,
)
from src.config import Settings


def test_build_normandy_bof_quality_scenarios_returns_fixed_family() -> None:
    scenarios = build_normandy_bof_quality_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF_CONTROL",
        "BOF_KEYLEVEL_STRICT",
        "BOF_PINBAR_EXPRESSION",
        "BOF_KEYLEVEL_PINBAR",
    ]
    assert all(scenario.signal_pattern == "bof" for scenario in scenarios)


def test_compute_normandy_bof_branch_context_marks_keylevel_and_pinbar() -> None:
    payload = {
        "triggered": True,
        "reference_status": "OK",
        "quality_status": "OK",
        "failure_handling_tag": "BOF_NO_FOLLOW_THROUGH",
        "lower_bound": 10.0,
        "today_low": 9.75,
        "today_open": 10.02,
        "today_close": 10.18,
        "today_high": 10.24,
        "close_pos": 0.877551,
        "body_ratio": 0.326531,
        "risk_reward_ref": 2.0,
        "entry_ref": 10.18,
        "stop_ref": 9.70,
        "pattern_quality_score": 72.0,
    }

    context = compute_normandy_bof_branch_context(payload)

    assert context["bof_keylevel_strict"] is True
    assert context["bof_pinbar_expression"] is True
    assert context["bof_keylevel_pinbar"] is True
    assert context["bof_keylevel_proxy_score"] >= 65.0
    assert context["bof_pinbar_proxy_score"] >= 68.0


def test_build_normandy_bof_quality_digest_promotes_intersection_branch() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_bof_quality_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": "v0_01_dtt_pattern_only",
        "matrix_status": "completed",
        "results": [
            {
                "label": "BOF_CONTROL",
                "family": "BOF_CONTROL",
                "signal_pattern": "bof",
                "trade_count": 100,
                "expected_value": 0.020,
                "profit_factor": 1.40,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
            },
            {
                "label": "BOF_KEYLEVEL_STRICT",
                "family": "BOF_QUALITY",
                "signal_pattern": "bof",
                "trade_count": 34,
                "expected_value": 0.021,
                "profit_factor": 1.45,
                "max_drawdown": 0.16,
                "participation_rate": 0.09,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
            {
                "label": "BOF_PINBAR_EXPRESSION",
                "family": "BOF_QUALITY",
                "signal_pattern": "bof",
                "trade_count": 26,
                "expected_value": 0.018,
                "profit_factor": 1.37,
                "max_drawdown": 0.17,
                "participation_rate": 0.07,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
            {
                "label": "BOF_KEYLEVEL_PINBAR",
                "family": "BOF_QUALITY",
                "signal_pattern": "bof",
                "trade_count": 28,
                "expected_value": 0.029,
                "profit_factor": 1.62,
                "max_drawdown": 0.11,
                "participation_rate": 0.08,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
        ],
    }

    digest = build_normandy_bof_quality_digest(matrix_payload)

    assert digest["retained_branch"] == "BOF_KEYLEVEL_PINBAR"
    assert digest["family_verdict"] == "retained_branch_selected"
    assert digest["decision"] == "advance_retained_branch_to_n1_12"
    assert digest["retained_branches"] == ["BOF_KEYLEVEL_PINBAR", "BOF_KEYLEVEL_STRICT"]


def test_build_normandy_bof_quality_stability_report_marks_branch_no_go() -> None:
    report = build_normandy_bof_quality_stability_report(
        {
            "summary_run_id": "matrix-token",
            "results": [
                {
                    "label": "BOF_CONTROL",
                    "trade_count": 140,
                    "expected_value": 0.02,
                    "profit_factor": 1.40,
                    "max_drawdown": 0.18,
                    "participation_rate": 0.30,
                },
                {
                    "label": "BOF_KEYLEVEL_PINBAR",
                    "run_id": "retained-run-token",
                    "trade_count": 18,
                    "expected_value": 0.031,
                    "profit_factor": 1.60,
                    "max_drawdown": 0.10,
                    "participation_rate": 0.04,
                    "overlap_rate_vs_bof_control": 1.0,
                    "incremental_buy_trades_vs_bof_control": 0,
                    "best_environment_bucket": {"bucket": "NEUTRAL", "expected_value": 0.031},
                    "environment_breakdown": {
                        "NEUTRAL": {"trade_count": 17.0, "expected_value": 0.034},
                        "BULLISH": {"trade_count": 1.0, "expected_value": -0.020},
                    },
                },
            ],
        },
        {
            "summary_run_id": "digest-token",
            "retained_branch": "BOF_KEYLEVEL_PINBAR",
        },
        {
            "snapshot_status": "available",
            "retained_branch_label": "BOF_KEYLEVEL_PINBAR",
            "retained_branch_run_id": "retained-run-token",
            "pairing_diagnostics": {
                "selected_entry_count": 120,
                "paired_trade_count": 18,
            },
            "selected_trace_summary": {
                "selected_count": 120,
                "avg_pattern_quality_score": 71.0,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 6, "avg_gross_return": 0.03},
                {"signal_year": 2024, "trade_count": 5, "avg_gross_return": -0.02},
                {"signal_year": 2025, "trade_count": 4, "avg_gross_return": 0.01},
                {"signal_year": 2026, "trade_count": 3, "avg_gross_return": 0.02},
            ],
            "quarter_activity": [
                {"signal_quarter": "2023-Q1", "selected_count": 8},
                {"signal_quarter": "2024-Q2", "selected_count": 4},
            ],
            "positive_examples": [
                {"signal_date": "2025-08-25", "code": "601727", "gross_return": 0.10},
            ],
            "negative_examples": [
                {"signal_date": "2024-10-28", "code": "300846", "gross_return": -0.12},
            ],
        },
    )

    assert report["stability_status"] == "branch_no_go"
    assert report["decision"] == "branch_no_go_keep_bof_control"
    assert "sample_still_small" in report["stability_flags"]
    assert "negative_signal_year_slices" in report["stability_flags"]
    assert "single_bucket_dependency" in report["stability_flags"]
    assert "selected_executed_gap_too_wide" in report["stability_flags"]
    assert "tiny_subset_only" in report["stability_flags"]


def test_build_normandy_bof_quality_stability_report_can_open_n2() -> None:
    report = build_normandy_bof_quality_stability_report(
        {
            "summary_run_id": "matrix-token",
            "results": [
                {
                    "label": "BOF_CONTROL",
                    "trade_count": 160,
                    "expected_value": 0.02,
                    "profit_factor": 1.40,
                    "max_drawdown": 0.18,
                    "participation_rate": 0.32,
                },
                {
                    "label": "BOF_KEYLEVEL_PINBAR",
                    "run_id": "retained-run-token",
                    "trade_count": 48,
                    "expected_value": 0.034,
                    "profit_factor": 1.72,
                    "max_drawdown": 0.09,
                    "participation_rate": 0.10,
                    "overlap_rate_vs_bof_control": 1.0,
                    "incremental_buy_trades_vs_bof_control": 0,
                    "best_environment_bucket": {"bucket": "NEUTRAL", "expected_value": 0.034},
                    "environment_breakdown": {
                        "NEUTRAL": {"trade_count": 22.0, "expected_value": 0.033},
                        "BULLISH": {"trade_count": 15.0, "expected_value": 0.038},
                        "BEARISH": {"trade_count": 11.0, "expected_value": 0.024},
                    },
                },
            ],
        },
        {
            "summary_run_id": "digest-token",
            "retained_branch": "BOF_KEYLEVEL_PINBAR",
        },
        {
            "snapshot_status": "available",
            "retained_branch_label": "BOF_KEYLEVEL_PINBAR",
            "retained_branch_run_id": "retained-run-token",
            "pairing_diagnostics": {
                "selected_entry_count": 72,
                "paired_trade_count": 48,
            },
            "selected_trace_summary": {
                "selected_count": 72,
                "avg_pattern_quality_score": 74.0,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 10, "avg_gross_return": 0.03},
                {"signal_year": 2024, "trade_count": 12, "avg_gross_return": 0.02},
                {"signal_year": 2025, "trade_count": 14, "avg_gross_return": 0.04},
                {"signal_year": 2026, "trade_count": 12, "avg_gross_return": 0.03},
            ],
            "quarter_activity": [
                {"signal_quarter": "2023-Q1", "selected_count": 6},
                {"signal_quarter": "2023-Q3", "selected_count": 6},
                {"signal_quarter": "2024-Q1", "selected_count": 6},
                {"signal_quarter": "2024-Q3", "selected_count": 6},
            ],
            "positive_examples": [
                {"signal_date": "2025-08-25", "code": "601727", "gross_return": 0.10},
            ],
            "negative_examples": [
                {"signal_date": "2024-10-28", "code": "300846", "gross_return": -0.03},
            ],
        },
    )

    assert report["stability_status"] == "eligible_for_n2_exit_decomposition"
    assert report["decision"] == "open_n2_for_bof_control_vs_retained_branch"
