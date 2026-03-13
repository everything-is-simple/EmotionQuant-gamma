from __future__ import annotations

from src.backtest.positioning_sizing_family import (
    build_positioning_sizing_family_digest,
    build_positioning_sizing_family_scenarios,
)
from src.config import Settings


def test_build_positioning_sizing_family_scenarios_covers_control_and_first_batch_families() -> None:
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITION_PCT=0.10,
        FIXED_NOTIONAL_AMOUNT=0.0,
    )

    scenarios = build_positioning_sizing_family_scenarios(cfg)

    assert [scenario.label for scenario in scenarios] == [
        "FIXED_NOTIONAL_CONTROL",
        "FIXED_RISK",
        "FIXED_CAPITAL",
        "FIXED_RATIO",
        "FIXED_UNIT",
        "WILLIAMS_FIXED_RISK",
        "FIXED_PERCENTAGE",
        "FIXED_VOLATILITY",
    ]
    assert scenarios[0].runtime_overrides["fixed_notional_amount"] == 100_000.0


def test_build_positioning_sizing_family_digest_marks_provisional_retained_candidate() -> None:
    digest = build_positioning_sizing_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_sizing_family_replay",
            "results": [
                {
                    "label": "FIXED_NOTIONAL_CONTROL",
                    "family": "control",
                    "trade_count": 100,
                    "expected_value": 0.0100,
                    "profit_factor": 1.90,
                    "max_drawdown": 0.12,
                    "net_pnl": 100_000.0,
                    "cash_pressure_reject_rate": 0.10,
                    "trade_sequence_max_drawdown": 0.15,
                },
                {
                    "label": "FIXED_PERCENTAGE",
                    "family": "fixed-percentage",
                    "trade_count": 95,
                    "expected_value": 0.0115,
                    "profit_factor": 1.92,
                    "max_drawdown": 0.11,
                    "net_pnl": 120_000.0,
                    "cash_pressure_reject_rate": 0.12,
                    "trade_sequence_max_drawdown": 0.14,
                    "max_consecutive_loss_count": 3,
                    "runtime_overrides": {"position_sizing_mode": "fixed_percentage"},
                },
            ],
        }
    )

    assert digest["diagnosis"] == "provisional_retained_sizing_candidate_found"
    assert digest["decision"] == "advance_retained_candidate_to_single_lot_sanity_replay"
    assert digest["leader"]["label"] == "FIXED_PERCENTAGE"


def test_build_positioning_sizing_family_digest_keeps_watch_when_improvement_is_not_clean() -> None:
    digest = build_positioning_sizing_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_sizing_family_replay",
            "results": [
                {
                    "label": "FIXED_NOTIONAL_CONTROL",
                    "family": "control",
                    "trade_count": 100,
                    "expected_value": 0.0100,
                    "profit_factor": 1.90,
                    "max_drawdown": 0.12,
                    "net_pnl": 100_000.0,
                    "cash_pressure_reject_rate": 0.10,
                    "trade_sequence_max_drawdown": 0.15,
                },
                {
                    "label": "FIXED_RATIO",
                    "family": "fixed-ratio",
                    "trade_count": 92,
                    "expected_value": 0.0104,
                    "profit_factor": 1.88,
                    "max_drawdown": 0.15,
                    "net_pnl": 105_000.0,
                    "cash_pressure_reject_rate": 0.12,
                    "trade_sequence_max_drawdown": 0.18,
                    "max_consecutive_loss_count": 4,
                    "runtime_overrides": {"position_sizing_mode": "fixed_ratio"},
                },
            ],
        }
    )

    assert digest["diagnosis"] == "watch_only_no_retained_candidate_yet"
    assert digest["leader"]["label"] == "FIXED_RATIO"
    assert digest["scorecard"][0]["verdict"] == "watch_candidate"
