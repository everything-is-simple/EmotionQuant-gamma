from __future__ import annotations

from src.backtest.normandy_fb_boundary_stability import build_normandy_fb_boundary_stability_report


def _matrix_payload() -> dict[str, object]:
    return {
        "summary_run_id": "normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
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
                "label": "FB_BOUNDARY",
                "run_id": "fb_boundary_run_token",
                "trade_count": 17,
                "expected_value": 0.03143,
                "profit_factor": 3.24845,
                "max_drawdown": 0.02544,
                "participation_rate": 1.0,
            },
        ],
    }


def _digest_payload() -> dict[str, object]:
    return {
        "summary_run_id": "normandy_fb_refinement_digest_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000002",
        "scorecard": [
            {
                "label": "FB_BOUNDARY",
                "dominant_environment_share": 0.94118,
                "best_environment_bucket": {
                    "bucket": "NEUTRAL",
                    "expected_value": 0.04078,
                    "trade_count": 16,
                },
            }
        ],
        "leader_stability_flags": [
            "single_bucket_dependency",
            "negative_signal_year_slices",
        ],
    }


def test_build_normandy_fb_boundary_stability_report_marks_still_fragile() -> None:
    report = build_normandy_fb_boundary_stability_report(
        _matrix_payload(),
        _digest_payload(),
        {
            "snapshot_status": "available",
            "snapshot_db_path": "G:\\EmotionQuant-temp\\backtest\\example.duckdb",
            "boundary_run_id": "fb_boundary_run_token",
            "pairing_diagnostics": {
                "selected_entry_count": 17,
                "paired_trade_count": 17,
            },
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 5, "avg_gross_return": 0.0768, "win_rate": 0.4},
                {"signal_year": 2024, "trade_count": 2, "avg_gross_return": -0.0948, "win_rate": 0.0},
                {"signal_year": 2025, "trade_count": 7, "avg_gross_return": 0.0531, "win_rate": 0.4286},
                {"signal_year": 2026, "trade_count": 3, "avg_gross_return": -0.0011, "win_rate": 0.3333},
            ],
            "quarter_activity": [
                {"signal_quarter": "2023-Q1", "selected_count": 5},
                {"signal_quarter": "2024-Q4", "selected_count": 1},
                {"signal_quarter": "2025-Q3", "selected_count": 4},
                {"signal_quarter": "2026-Q1", "selected_count": 3},
            ],
            "negative_examples": [
                {"signal_date": "2023-03-13", "code": "000063", "gross_return": -0.0466},
                {"signal_date": "2024-10-28", "code": "300846", "gross_return": -0.1168},
                {"signal_date": "2025-08-25", "code": "601727", "gross_return": -0.0725},
                {"signal_date": "2026-01-26", "code": "603993", "gross_return": -0.1031},
            ],
        },
    )

    assert report["stability_status"] == "fragile_boundary_not_n2_ready"
    assert report["decision"] == "hold_n2_and_demote_boundary_to_watch_candidate"
    assert report["meaningful_negative_signal_years"] == [2024, 2026]
    assert "single_bucket_dependency" in report["stability_flags"]
    assert "negative_signal_year_slices" in report["stability_flags"]
    assert "losses_not_isolated" in report["stability_flags"]


def test_build_normandy_fb_boundary_stability_report_can_open_n2() -> None:
    report = build_normandy_fb_boundary_stability_report(
        {
            "summary_run_id": "matrix-token",
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
                    "label": "FB_BOUNDARY",
                    "run_id": "fb_boundary_run_token",
                    "trade_count": 24,
                    "expected_value": 0.041,
                    "profit_factor": 3.0,
                    "max_drawdown": 0.03,
                    "participation_rate": 1.0,
                },
            ],
        },
        {
            "summary_run_id": "digest-token",
            "scorecard": [
                {
                    "label": "FB_BOUNDARY",
                    "dominant_environment_share": 0.62,
                    "best_environment_bucket": {"bucket": "NEUTRAL", "expected_value": 0.04, "trade_count": 10},
                }
            ],
            "leader_stability_flags": [],
        },
        {
            "snapshot_status": "available",
            "boundary_run_id": "fb_boundary_run_token",
            "signal_year_slices": [
                {"signal_year": 2023, "trade_count": 6, "avg_gross_return": 0.02},
                {"signal_year": 2024, "trade_count": 6, "avg_gross_return": 0.01},
                {"signal_year": 2025, "trade_count": 7, "avg_gross_return": 0.03},
                {"signal_year": 2026, "trade_count": 5, "avg_gross_return": 0.02},
            ],
            "quarter_activity": [
                {"signal_quarter": "2023-Q1", "selected_count": 2},
                {"signal_quarter": "2023-Q3", "selected_count": 2},
                {"signal_quarter": "2024-Q1", "selected_count": 2},
                {"signal_quarter": "2024-Q3", "selected_count": 2},
                {"signal_quarter": "2025-Q1", "selected_count": 2},
                {"signal_quarter": "2025-Q3", "selected_count": 2},
            ],
            "negative_examples": [
                {"signal_date": "2023-03-13", "code": "000063", "gross_return": -0.01},
                {"signal_date": "2024-10-28", "code": "300846", "gross_return": -0.01},
            ],
        },
    )

    assert report["stability_status"] == "boundary_ready_for_n2"
    assert report["decision"] == "open_n2_for_bof_vs_fb_boundary"
