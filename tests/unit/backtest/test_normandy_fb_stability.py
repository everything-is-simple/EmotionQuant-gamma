from __future__ import annotations

from src.backtest.normandy_fb_stability import (
    build_normandy_fb_purity_audit,
    build_normandy_fb_stability_report,
)


def _matrix_payload() -> dict[str, object]:
    return {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000000",
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
                "label": "FB",
                "run_id": "fb_run_token",
                "trade_count": 33,
                "expected_value": 0.01450,
                "profit_factor": 3.4433,
                "max_drawdown": 0.05908,
                "participation_rate": 1.0,
            },
        ],
    }


def _candidate_report_payload() -> dict[str, object]:
    return {
        "candidate_label": "FB",
        "control_label": "BOF_CONTROL",
        "candidate_summary": {
            "trade_count": 33,
            "expected_value": 0.01450,
            "profit_factor": 3.4433,
            "max_drawdown": 0.05908,
            "participation_rate": 1.0,
        },
        "control_summary": {
            "trade_count": 277,
            "expected_value": 0.01609,
            "profit_factor": 2.6121,
            "max_drawdown": 0.13267,
            "participation_rate": 0.80523,
        },
        "bucket_breakdown": [
            {
                "bucket": "NEUTRAL",
                "trade_count": 31,
                "expected_value": 0.02201,
                "share_of_candidate_trades": 0.93939,
            },
            {
                "bucket": "BULLISH",
                "trade_count": 2,
                "expected_value": -0.10197,
                "share_of_candidate_trades": 0.06061,
            },
        ],
        "positive_buckets": ["NEUTRAL"],
        "negative_buckets": ["BULLISH"],
        "risk_flags": [
            "low_sample_count",
            "dominant_bucket_dependency",
            "bullish_failure_observed",
            "edge_below_bof_control",
        ],
    }


def test_build_normandy_fb_stability_report_marks_fragile_candidate() -> None:
    report = build_normandy_fb_stability_report(
        _matrix_payload(),
        _candidate_report_payload(),
        {
            "snapshot_status": "available",
            "snapshot_db_path": "G:\\EmotionQuant-temp\\backtest\\example.duckdb",
            "fb_run_id": "fb_run_token",
            "pairing_diagnostics": {
                "selected_entry_count": 33,
                "paired_trade_count": 33,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 10, "avg_gross_return": 0.01847, "win_rate": 0.30},
                {"signal_year": 2024, "trade_count": 8, "avg_gross_return": -0.04309, "win_rate": 0.125},
                {"signal_year": 2025, "trade_count": 11, "avg_gross_return": 0.07067, "win_rate": 0.364},
                {"signal_year": 2026, "trade_count": 4, "avg_gross_return": -0.03475, "win_rate": 0.25},
            ],
            "quarter_activity": [
                {"signal_quarter": "2023-Q1", "selected_count": 9, "avg_strength": 0.78},
                {"signal_quarter": "2025-Q3", "selected_count": 7, "avg_strength": 0.78},
            ],
        },
    )

    assert report["stability_status"] == "fragile_candidate_not_exit_ready"
    assert report["decision"] == "detector_refinement_before_n2"
    assert report["meaningful_negative_signal_years"] == [2024]
    assert "single_bucket_positive_edge" in report["stability_flags"]
    assert "negative_signal_year_slices" in report["stability_flags"]
    assert "sample_still_small" in report["stability_flags"]


def test_build_normandy_fb_purity_audit_marks_boundary_loaded_detector() -> None:
    audit = build_normandy_fb_purity_audit(
        _matrix_payload(),
        _candidate_report_payload(),
        {
            "snapshot_status": "available",
            "snapshot_db_path": "G:\\EmotionQuant-temp\\backtest\\example.duckdb",
            "fb_run_id": "fb_run_token",
            "selected_summary": {
                "selected_count": 33,
                "edge_touch_ratio": 0.51515,
                "edge_depth_ratio": 0.21212,
                "near_floor_trend_ratio": 0.09091,
                "strong_volume_ratio": 0.45454,
                "avg_strength": 0.80010,
            },
            "prior_ema_touches_distribution": [
                {"prior_ema_touches": 0, "count": 11, "share": 0.3333},
                {"prior_ema_touches": 1, "count": 5, "share": 0.1515},
                {"prior_ema_touches": 2, "count": 17, "share": 0.5151},
            ],
            "failure_reason_breakdown": [
                {"reason": "TREND_NOT_EXPLOSIVE", "count": 64894, "share": 0.87615},
                {"reason": "NOT_FIRST_PULLBACK", "count": 5202, "share": 0.07023},
            ],
            "performance_by_touch_bucket": [
                {
                    "touch_bucket": "touch_0_1_cleaner",
                    "trade_count": 16,
                    "avg_gross_return": -0.00186,
                    "win_rate": 0.1875,
                    "avg_strength": 0.85525,
                },
                {
                    "touch_bucket": "touch_2_boundary",
                    "trade_count": 17,
                    "avg_gross_return": 0.03311,
                    "win_rate": 0.35294,
                    "avg_strength": 0.74819,
                },
            ],
            "performance_by_depth_bucket": [
                {"depth_bucket": "core_depth_band", "trade_count": 26, "avg_gross_return": 0.00405},
                {"depth_bucket": "edge_depth_band", "trade_count": 7, "avg_gross_return": 0.06114},
            ],
            "performance_by_trend_bucket": [
                {"trend_bucket": "near_floor_trend", "trade_count": 3, "avg_gross_return": 0.04238},
                {"trend_bucket": "stronger_trend", "trade_count": 30, "avg_gross_return": 0.01353},
            ],
            "performance_by_volume_bucket": [
                {"volume_bucket": "base_volume", "trade_count": 18, "avg_gross_return": 0.01064},
                {"volume_bucket": "strong_volume", "trade_count": 15, "avg_gross_return": 0.02277},
            ],
            "boundary_examples": [
                {
                    "signal_date": "2023-02-21",
                    "code": "600118",
                    "prior_ema_touches": 2,
                    "trend_gain": 0.08453,
                    "pullback_depth": 0.41197,
                    "pattern_strength": 0.68661,
                }
            ],
        },
    )

    assert audit["purity_verdict"] == "boundary_loaded_detector_refinement_required"
    assert "boundary_touch_loaded" in audit["purity_flags"]
    assert "boundary_samples_carry_edge" in audit["purity_flags"]
    assert "late_pullback_guardrail_active" in audit["purity_flags"]
