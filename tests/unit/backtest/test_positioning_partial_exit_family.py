from __future__ import annotations

from src.backtest.positioning_partial_exit_family import (
    build_positioning_partial_exit_family_digest,
    build_positioning_partial_exit_family_scenarios,
)
from src.config import Settings


def test_build_positioning_partial_exit_family_scenarios_covers_control_and_first_batch_ratios() -> None:
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITION_PCT=0.10,
        FIXED_NOTIONAL_AMOUNT=0.0,
    )

    scenarios = build_positioning_partial_exit_family_scenarios(cfg)

    assert [scenario.label for scenario in scenarios] == [
        "FULL_EXIT_CONTROL",
        "TRAIL_SCALE_OUT_25_75",
        "TRAIL_SCALE_OUT_33_67",
        "TRAIL_SCALE_OUT_50_50",
        "TRAIL_SCALE_OUT_67_33",
        "TRAIL_SCALE_OUT_75_25",
    ]
    assert scenarios[0].fixed_notional_amount == 100_000.0
    assert scenarios[3].partial_exit_scale_out_ratio == 0.50


def test_build_positioning_partial_exit_family_digest_marks_retained_candidate() -> None:
    digest = build_positioning_partial_exit_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_partial_exit_family_replay",
            "results": [
                {
                    "label": "FULL_EXIT_CONTROL",
                    "family": "control",
                    "trade_count": 100,
                    "buy_filled_count": 100,
                    "expected_value": 0.0100,
                    "profit_factor": 2.00,
                    "max_drawdown": 0.12,
                    "net_pnl": 100_000.0,
                    "trade_sequence_max_drawdown": 0.18,
                    "avg_hold_days": 20.0,
                },
                {
                    "label": "TRAIL_SCALE_OUT_50_50",
                    "family": "naive-trailing-scale-out",
                    "partial_exit_scale_out_ratio": 0.50,
                    "trade_count": 130,
                    "buy_filled_count": 98,
                    "partial_exit_pair_count": 110,
                    "partial_exit_pair_share": 0.84,
                    "expected_value": 0.0132,
                    "profit_factor": 2.08,
                    "max_drawdown": 0.11,
                    "net_pnl": 122_000.0,
                    "trade_sequence_max_drawdown": 0.16,
                    "avg_hold_days": 24.0,
                },
            ],
        }
    )

    assert digest["diagnosis"] == "provisional_retained_partial_exit_candidate_found"
    assert digest["decision"] == "write_p8_record_with_retained_queue"
    assert digest["leader"]["label"] == "TRAIL_SCALE_OUT_50_50"


def test_build_positioning_partial_exit_family_digest_marks_watch_when_improvement_is_partial() -> None:
    digest = build_positioning_partial_exit_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_partial_exit_family_replay",
            "results": [
                {
                    "label": "FULL_EXIT_CONTROL",
                    "family": "control",
                    "trade_count": 100,
                    "buy_filled_count": 100,
                    "expected_value": 0.0100,
                    "profit_factor": 2.00,
                    "max_drawdown": 0.12,
                    "net_pnl": 100_000.0,
                    "trade_sequence_max_drawdown": 0.18,
                    "avg_hold_days": 20.0,
                },
                {
                    "label": "TRAIL_SCALE_OUT_67_33",
                    "family": "naive-trailing-scale-out",
                    "partial_exit_scale_out_ratio": 2.0 / 3.0,
                    "trade_count": 122,
                    "buy_filled_count": 94,
                    "partial_exit_pair_count": 60,
                    "partial_exit_pair_share": 0.49,
                    "expected_value": 0.0108,
                    "profit_factor": 1.98,
                    "max_drawdown": 0.125,
                    "net_pnl": 98_500.0,
                    "trade_sequence_max_drawdown": 0.185,
                    "avg_hold_days": 23.0,
                },
            ],
        }
    )

    assert digest["diagnosis"] == "watch_only_partial_exit_family"
    assert digest["leader"]["label"] == "TRAIL_SCALE_OUT_67_33"
    assert digest["scorecard"][0]["verdict"] == "watch_candidate"


def test_build_positioning_partial_exit_family_digest_marks_no_go_when_partial_exit_is_degenerate() -> None:
    digest = build_positioning_partial_exit_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_partial_exit_family_replay",
            "results": [
                {
                    "label": "FULL_EXIT_CONTROL",
                    "family": "control",
                    "trade_count": 100,
                    "buy_filled_count": 100,
                    "expected_value": 0.0100,
                    "profit_factor": 2.00,
                    "max_drawdown": 0.12,
                    "net_pnl": 100_000.0,
                    "trade_sequence_max_drawdown": 0.18,
                    "avg_hold_days": 20.0,
                },
                {
                    "label": "TRAIL_SCALE_OUT_25_75",
                    "family": "naive-trailing-scale-out",
                    "partial_exit_scale_out_ratio": 0.25,
                    "trade_count": 100,
                    "buy_filled_count": 86,
                    "partial_exit_pair_count": 0,
                    "partial_exit_pair_share": 0.0,
                    "expected_value": 0.0080,
                    "profit_factor": 1.70,
                    "max_drawdown": 0.14,
                    "net_pnl": 80_000.0,
                    "trade_sequence_max_drawdown": 0.23,
                    "avg_hold_days": 20.0,
                },
            ],
        }
    )

    assert digest["diagnosis"] == "no_retained_partial_exit_family_yet"
    assert digest["scorecard"][0]["verdict"] == "no_go"
