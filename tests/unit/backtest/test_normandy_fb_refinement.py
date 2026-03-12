from __future__ import annotations

from src.backtest.normandy_fb_refinement import (
    build_normandy_fb_refinement_digest,
    build_normandy_fb_refinement_scenarios,
)
from src.config import Settings


def test_build_normandy_fb_refinement_scenarios_returns_cleaner_and_boundary() -> None:
    scenarios = build_normandy_fb_refinement_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF_CONTROL",
        "FB_CLEANER",
        "FB_BOUNDARY",
    ]
    assert scenarios[1].signal_pattern == "fb_cleaner"
    assert scenarios[2].detector_key == "fb_boundary"


def test_build_normandy_fb_refinement_digest_promotes_boundary_branch() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": "v0_01_dtt_pattern_only",
        "matrix_status": "completed",
        "results": [
            {
                "label": "BOF_CONTROL",
                "family": "BOF_CONTROL",
                "trade_count": 80,
                "expected_value": 0.02,
                "profit_factor": 1.40,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
            },
            {
                "label": "FB_CLEANER",
                "family": "FB_REFINED",
                "signal_pattern": "fb_cleaner",
                "trade_count": 16,
                "expected_value": -0.002,
                "profit_factor": 0.93,
                "max_drawdown": 0.11,
                "participation_rate": 0.06,
                "overlap_rate_vs_bof_control": 0.91,
                "incremental_buy_trades_vs_bof_control": 8,
                "best_environment_bucket": {"bucket": "NEUTRAL", "expected_value": -0.002},
            },
            {
                "label": "FB_BOUNDARY",
                "family": "FB_REFINED",
                "signal_pattern": "fb_boundary",
                "trade_count": 22,
                "expected_value": 0.031,
                "profit_factor": 1.32,
                "max_drawdown": 0.09,
                "participation_rate": 0.07,
                "overlap_rate_vs_bof_control": 0.74,
                "incremental_buy_trades_vs_bof_control": 21,
                "best_environment_bucket": {"bucket": "NEUTRAL", "expected_value": 0.031},
            },
        ],
    }

    digest = build_normandy_fb_refinement_digest(matrix_payload)

    assert digest["branch_leader"] == "FB_BOUNDARY"
    assert digest["refinement_verdict"] == "boundary_branch_promoted"
    assert digest["decision"] == "promote_fb_boundary_to_follow_up"
    assert digest["refined_second_alpha_candidates"] == ["FB_BOUNDARY"]
    assert "boundary_branch_carries_edge" in digest["risk_flags"]
