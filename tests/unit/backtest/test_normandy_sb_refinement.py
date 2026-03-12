from __future__ import annotations

from src.backtest.normandy_sb_refinement import build_normandy_sb_refinement_report


def _matrix_payload() -> dict[str, object]:
    return {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "results": [
            {
                "label": "BOF_CONTROL",
                "trade_count": 277,
                "expected_value": 0.01609,
                "profit_factor": 2.6121,
                "max_drawdown": 0.13267,
                "participation_rate": 0.80523,
            },
            {
                "label": "SB",
                "run_id": "sb_run_token",
                "trade_count": 648,
                "expected_value": -0.01455,
                "profit_factor": 2.0909,
                "max_drawdown": 0.64103,
                "participation_rate": 0.15588,
                "overlap_rate_vs_bof_control": 0.0,
                "incremental_buy_trades_vs_bof_control": 648,
                "best_environment_bucket": {
                    "bucket": "BEARISH",
                    "expected_value": 0.02146,
                    "trade_count": 19,
                },
                "environment_breakdown": {
                    "BULLISH": {"trade_count": 12.0, "expected_value": -0.04722, "profit_factor": 0.24669},
                    "NEUTRAL": {"trade_count": 617.0, "expected_value": -0.01502, "profit_factor": 2.14976},
                    "BEARISH": {"trade_count": 19.0, "expected_value": 0.02146, "profit_factor": 1.55501},
                },
            },
        ],
    }


def test_build_normandy_sb_refinement_report_marks_full_detector_no_go() -> None:
    report = build_normandy_sb_refinement_report(
        _matrix_payload(),
        {
            "snapshot_status": "available",
            "snapshot_db_path": "G:\\EmotionQuant-temp\\backtest\\example.duckdb",
            "sb_run_id": "sb_run_token",
            "pairing_diagnostics": {
                "selected_entry_count": 4157,
                "buy_fill_count": 648,
                "executed_entry_count": 648,
                "exit_fill_count": 648,
                "paired_trade_count": 648,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 232, "avg_gross_return": -0.0125, "win_rate": 0.2543},
                {"signal_year": 2024, "trade_count": 208, "avg_gross_return": -0.0202, "win_rate": 0.2548},
                {"signal_year": 2025, "trade_count": 187, "avg_gross_return": -0.0081, "win_rate": 0.2513},
                {"signal_year": 2026, "trade_count": 21, "avg_gross_return": 0.0118, "win_rate": 0.3810},
            ],
            "selected_trace_summary": {
                "selected_count": 4157,
                "avg_trend_gain": 0.27467,
                "avg_retest_similarity": 0.01709,
                "avg_w_amplitude": 0.14236,
                "tight_retest_ratio": 0.64975,
                "large_w_ratio": 0.47847,
                "high_trend_ratio": 0.41905,
                "avg_strength": 0.79195,
            },
            "failure_reason_breakdown": [
                {"reason": "TREND_NOT_ESTABLISHED", "count": 100, "share": 0.5311},
                {"reason": "NOT_SECOND_TEST_SETUP", "count": 50, "share": 0.2486},
            ],
            "performance_by_strength_bucket": [
                {"strength_bucket": "low_strength", "trade_count": 126, "avg_gross_return": -0.0143},
                {"strength_bucket": "mid_strength", "trade_count": 271, "avg_gross_return": -0.0048},
                {"strength_bucket": "high_strength", "trade_count": 251, "avg_gross_return": -0.0211},
            ],
            "performance_by_retest_bucket": [
                {"retest_bucket": "tight_retest", "trade_count": 498, "avg_gross_return": -0.0127},
                {"retest_bucket": "mid_retest", "trade_count": 150, "avg_gross_return": -0.0138},
            ],
            "performance_by_trend_bucket": [
                {"trend_bucket": "low_trend", "trade_count": 115, "avg_gross_return": -0.0089},
                {"trend_bucket": "mid_trend", "trade_count": 296, "avg_gross_return": -0.0143},
                {"trend_bucket": "high_trend", "trade_count": 237, "avg_gross_return": -0.0131},
            ],
            "performance_by_w_bucket": [
                {"w_bucket": "small_w", "trade_count": 143, "avg_gross_return": 0.0017},
                {"w_bucket": "medium_w", "trade_count": 189, "avg_gross_return": -0.0248},
                {"w_bucket": "large_w", "trade_count": 316, "avg_gross_return": -0.0124},
            ],
            "branch_candidates": [
                {
                    "branch_label": "SB_SMALL_W_MID_STRENGTH",
                    "trade_count": 68,
                    "avg_gross_return": 0.0227,
                    "win_rate": 0.4118,
                    "avg_strength": 0.821,
                },
                {
                    "branch_label": "SB_LOW_TREND_MID_STRENGTH",
                    "trade_count": 46,
                    "avg_gross_return": 0.0155,
                    "win_rate": 0.3913,
                    "avg_strength": 0.802,
                },
                {
                    "branch_label": "SB_SMALL_W",
                    "trade_count": 143,
                    "avg_gross_return": 0.0017,
                    "win_rate": 0.3077,
                    "avg_strength": 0.774,
                },
            ],
            "positive_examples": [
                {
                    "signal_date": "2025-10-10",
                    "code": "603730",
                    "gross_return": 0.7540,
                    "w_amplitude": 0.0776,
                    "pattern_strength": 0.8156,
                }
            ],
            "negative_examples": [
                {
                    "signal_date": "2024-08-20",
                    "code": "300532",
                    "gross_return": -0.3338,
                    "w_amplitude": 0.0956,
                    "pattern_strength": 0.9395,
                }
            ],
        },
    )

    assert report["refinement_status"] == "full_detector_no_go_watch_branch_only"
    assert report["refinement_verdict"] == "current_sb_detector_no_go_narrow_watch_branch_only"
    assert report["decision"] == "freeze_full_sb_and_shift_main_queue"
    assert report["meaningful_negative_signal_years"] == [2023, 2024, 2025]
    assert report["meaningful_positive_signal_years"] == [2026]
    assert report["retained_watch_branch"]["branch_label"] == "SB_SMALL_W_MID_STRENGTH"
    assert "negative_full_detector_edge" in report["refinement_flags"]
    assert "extreme_drawdown_profile" in report["refinement_flags"]
    assert "detector_overwide_vs_execution" in report["refinement_flags"]
    assert report["next_main_queue_card"] == "N1.11 / Tachibana detector refinement or backlog retention"


def test_build_normandy_sb_refinement_report_without_watch_branch_closes_route() -> None:
    report = build_normandy_sb_refinement_report(
        _matrix_payload(),
        {
            "snapshot_status": "available",
            "sb_run_id": "sb_run_token",
            "pairing_diagnostics": {
                "selected_entry_count": 1000,
                "executed_entry_count": 400,
                "paired_trade_count": 400,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 80, "avg_gross_return": -0.01},
                {"signal_year": 2024, "trade_count": 90, "avg_gross_return": -0.02},
                {"signal_year": 2025, "trade_count": 100, "avg_gross_return": -0.01},
            ],
            "branch_candidates": [
                {
                    "branch_label": "SB_SMALL_W",
                    "trade_count": 120,
                    "avg_gross_return": 0.002,
                    "win_rate": 0.31,
                    "avg_strength": 0.78,
                }
            ],
        },
    )

    assert report["refinement_status"] == "full_detector_no_go"
    assert report["refinement_verdict"] == "current_sb_detector_no_go"
    assert report["decision"] == "close_sb_route_and_shift_main_queue"
    assert report["retained_watch_branch"] is None
