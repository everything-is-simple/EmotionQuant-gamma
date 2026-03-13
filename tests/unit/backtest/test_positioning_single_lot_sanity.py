from __future__ import annotations

from src.backtest.positioning_single_lot_sanity import (
    build_positioning_single_lot_sanity_digest,
    build_positioning_single_lot_sanity_scenarios,
)
from src.config import Settings


def test_build_positioning_single_lot_sanity_scenarios_keeps_floor_and_two_candidates() -> None:
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITION_PCT=0.10,
        FIXED_LOT_SIZE=100,
        FIXED_NOTIONAL_AMOUNT=0.0,
    )

    scenarios = build_positioning_single_lot_sanity_scenarios(cfg)

    assert [scenario.label for scenario in scenarios] == [
        "SINGLE_LOT_CONTROL",
        "WILLIAMS_FIXED_RISK",
        "FIXED_RATIO",
    ]
    assert scenarios[0].runtime_overrides["position_sizing_mode"] == "single_lot"
    assert scenarios[1].runtime_overrides["position_sizing_mode"] == "williams_fixed_risk"
    assert scenarios[2].runtime_overrides["position_sizing_mode"] == "fixed_ratio"


def test_build_positioning_single_lot_sanity_digest_marks_both_survivors() -> None:
    digest = build_positioning_single_lot_sanity_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_single_lot_sanity_replay",
            "results": [
                {
                    "label": "SINGLE_LOT_CONTROL",
                    "family": "control-floor",
                    "trade_count": 100,
                    "expected_value": 0.0060,
                    "profit_factor": 2.20,
                    "max_drawdown": 0.040,
                    "net_pnl": 60_000.0,
                    "cash_pressure_reject_rate": 0.0,
                    "trade_sequence_max_drawdown": 0.080,
                },
                {
                    "label": "WILLIAMS_FIXED_RISK",
                    "family": "williams-fixed-risk",
                    "trade_count": 97,
                    "expected_value": 0.0080,
                    "profit_factor": 2.35,
                    "max_drawdown": 0.035,
                    "net_pnl": 70_000.0,
                    "cash_pressure_reject_rate": 0.03,
                    "trade_sequence_max_drawdown": 0.090,
                    "runtime_overrides": {"position_sizing_mode": "williams_fixed_risk"},
                },
                {
                    "label": "FIXED_RATIO",
                    "family": "fixed-ratio",
                    "trade_count": 95,
                    "expected_value": 0.0078,
                    "profit_factor": 2.32,
                    "max_drawdown": 0.038,
                    "net_pnl": 68_000.0,
                    "cash_pressure_reject_rate": 0.04,
                    "trade_sequence_max_drawdown": 0.095,
                    "runtime_overrides": {"position_sizing_mode": "fixed_ratio"},
                },
            ],
        }
    )

    assert digest["diagnosis"] == "both_provisional_candidates_survive_single_lot_sanity"
    assert digest["decision"] == "advance_both_candidates_to_p4_retained_or_no_go"
    assert len(digest["survivors"]) == 2


def test_build_positioning_single_lot_sanity_digest_marks_single_survivor() -> None:
    digest = build_positioning_single_lot_sanity_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_single_lot_sanity_replay",
            "results": [
                {
                    "label": "SINGLE_LOT_CONTROL",
                    "family": "control-floor",
                    "trade_count": 100,
                    "expected_value": 0.0060,
                    "profit_factor": 2.20,
                    "max_drawdown": 0.040,
                    "net_pnl": 60_000.0,
                    "cash_pressure_reject_rate": 0.0,
                    "trade_sequence_max_drawdown": 0.080,
                },
                {
                    "label": "WILLIAMS_FIXED_RISK",
                    "family": "williams-fixed-risk",
                    "trade_count": 96,
                    "expected_value": 0.0081,
                    "profit_factor": 2.31,
                    "max_drawdown": 0.036,
                    "net_pnl": 69_000.0,
                    "cash_pressure_reject_rate": 0.02,
                    "trade_sequence_max_drawdown": 0.088,
                    "runtime_overrides": {"position_sizing_mode": "williams_fixed_risk"},
                },
                {
                    "label": "FIXED_RATIO",
                    "family": "fixed-ratio",
                    "trade_count": 92,
                    "expected_value": 0.0062,
                    "profit_factor": 2.20,
                    "max_drawdown": 0.060,
                    "net_pnl": 59_000.0,
                    "cash_pressure_reject_rate": 0.08,
                    "trade_sequence_max_drawdown": 0.140,
                    "runtime_overrides": {"position_sizing_mode": "fixed_ratio"},
                },
            ],
        }
    )

    assert digest["diagnosis"] == "only_one_candidate_survives_single_lot_sanity"
    assert digest["decision"] == "advance_single_survivor_to_p4_retained_or_no_go"
    assert [item["label"] for item in digest["survivors"]] == ["WILLIAMS_FIXED_RISK"]


def test_build_positioning_single_lot_sanity_digest_marks_no_survivor() -> None:
    digest = build_positioning_single_lot_sanity_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_single_lot_sanity_replay",
            "results": [
                {
                    "label": "SINGLE_LOT_CONTROL",
                    "family": "control-floor",
                    "trade_count": 100,
                    "expected_value": 0.0060,
                    "profit_factor": 2.20,
                    "max_drawdown": 0.040,
                    "net_pnl": 60_000.0,
                    "cash_pressure_reject_rate": 0.0,
                    "trade_sequence_max_drawdown": 0.080,
                },
                {
                    "label": "WILLIAMS_FIXED_RISK",
                    "family": "williams-fixed-risk",
                    "trade_count": 93,
                    "expected_value": 0.0058,
                    "profit_factor": 2.15,
                    "max_drawdown": 0.052,
                    "net_pnl": 55_000.0,
                    "cash_pressure_reject_rate": 0.06,
                    "trade_sequence_max_drawdown": 0.120,
                    "runtime_overrides": {"position_sizing_mode": "williams_fixed_risk"},
                },
                {
                    "label": "FIXED_RATIO",
                    "family": "fixed-ratio",
                    "trade_count": 94,
                    "expected_value": 0.0055,
                    "profit_factor": 2.10,
                    "max_drawdown": 0.058,
                    "net_pnl": 54_000.0,
                    "cash_pressure_reject_rate": 0.07,
                    "trade_sequence_max_drawdown": 0.130,
                    "runtime_overrides": {"position_sizing_mode": "fixed_ratio"},
                },
            ],
        }
    )

    assert digest["diagnosis"] == "no_candidate_survives_single_lot_sanity"
    assert digest["decision"] == "write_p3_record_and_prepare_p4_no_retained_case"
    assert digest["survivors"] == []
