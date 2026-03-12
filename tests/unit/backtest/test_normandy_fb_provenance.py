from __future__ import annotations

from src.backtest.normandy_fb_provenance import build_normandy_fb_candidate_report


def test_build_normandy_fb_candidate_report_marks_qualified_candidate_with_risk_flags() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000000",
        "results": [
            {
                "label": "BOF_CONTROL",
                "trade_count": 120,
                "expected_value": 0.02,
                "profit_factor": 2.5,
                "max_drawdown": 0.12,
                "participation_rate": 0.80,
            },
            {
                "label": "FB",
                "trade_count": 33,
                "expected_value": 0.014,
                "profit_factor": 3.4,
                "max_drawdown": 0.05,
                "participation_rate": 1.0,
                "overlap_rate_vs_bof_control": 0.0,
                "incremental_buy_trades_vs_bof_control": 33,
                "best_environment_bucket": {
                    "bucket": "NEUTRAL",
                    "expected_value": 0.022,
                    "profit_factor": 3.6,
                    "trade_count": 31,
                },
                "environment_breakdown": {
                    "BULLISH": {
                        "trade_count": 2,
                        "expected_value": -0.10,
                        "profit_factor": 0.0,
                        "win_rate": 0.0,
                    },
                    "NEUTRAL": {
                        "trade_count": 31,
                        "expected_value": 0.022,
                        "profit_factor": 3.6,
                        "win_rate": 0.29,
                    },
                },
            },
        ],
    }
    digest_payload = {
        "summary_run_id": "normandy_volman_alpha_digest_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000000",
        "second_alpha_candidates": ["FB"],
    }

    report = build_normandy_fb_candidate_report(matrix_payload, digest_payload)

    assert report["qualified_second_alpha_candidate"] is True
    assert report["qualification"] == "qualified_second_alpha_candidate_with_risk_flags"
    assert report["risk_flags"] == [
        "low_sample_count",
        "dominant_bucket_dependency",
        "bullish_failure_observed",
        "edge_below_bof_control",
    ]
    assert report["positive_buckets"] == ["NEUTRAL"]
    assert report["negative_buckets"] == ["BULLISH"]


def test_build_normandy_fb_candidate_report_without_digest_marks_unqualified() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "results": [
            {
                "label": "BOF_CONTROL",
                "trade_count": 100,
                "expected_value": 0.02,
                "profit_factor": 2.0,
                "max_drawdown": 0.15,
                "participation_rate": 0.70,
            },
            {
                "label": "FB",
                "trade_count": 12,
                "expected_value": -0.01,
                "profit_factor": 0.8,
                "max_drawdown": 0.16,
                "participation_rate": 1.0,
                "overlap_rate_vs_bof_control": 0.0,
                "incremental_buy_trades_vs_bof_control": 12,
                "environment_breakdown": {
                    "NEUTRAL": {
                        "trade_count": 12,
                        "expected_value": -0.01,
                        "profit_factor": 0.8,
                        "win_rate": 0.2,
                    },
                },
            },
        ],
    }

    report = build_normandy_fb_candidate_report(matrix_payload, None)

    assert report["qualified_second_alpha_candidate"] is False
    assert report["qualification"] == "candidate_not_qualified"
    assert "low_sample_count" in report["risk_flags"]
    assert "dominant_bucket_dependency" in report["risk_flags"]
