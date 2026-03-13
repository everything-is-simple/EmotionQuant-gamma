from __future__ import annotations

from src.backtest.positioning_null_control import (
    build_positioning_null_control_digest,
    build_positioning_null_control_scenarios,
)
from src.config import Settings


def test_build_positioning_null_control_scenarios_uses_default_fixed_notional_from_cash_cap() -> None:
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITION_PCT=0.10,
        FIXED_LOT_SIZE=200,
        FIXED_NOTIONAL_AMOUNT=0.0,
    )

    scenarios = build_positioning_null_control_scenarios(cfg)

    assert [scenario.label for scenario in scenarios] == [
        "SINGLE_LOT_CONTROL",
        "FIXED_NOTIONAL_CONTROL",
    ]
    assert scenarios[0].position_sizing_mode == "single_lot"
    assert scenarios[0].fixed_lot_size == 200
    assert scenarios[1].position_sizing_mode == "fixed_notional"
    assert scenarios[1].fixed_notional_amount == 100_000.0


def test_build_positioning_null_control_digest_keeps_single_lot_when_fixed_notional_cash_pressure_is_high() -> None:
    digest = build_positioning_null_control_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_control_baseline",
            "results": [
                {
                    "label": "SINGLE_LOT_CONTROL",
                    "trade_count": 100,
                    "buy_filled_count": 100,
                    "expected_value": 0.01,
                    "profit_factor": 2.0,
                    "max_drawdown": 0.10,
                    "avg_entry_notional": 2_000.0,
                    "exposure_rate": 0.30,
                    "cash_pressure_reject_rate": 0.0,
                },
                {
                    "label": "FIXED_NOTIONAL_CONTROL",
                    "trade_count": 60,
                    "buy_filled_count": 60,
                    "expected_value": 0.02,
                    "profit_factor": 2.2,
                    "max_drawdown": 0.11,
                    "avg_entry_notional": 100_000.0,
                    "exposure_rate": 0.55,
                    "cash_pressure_reject_rate": 0.35,
                    "fixed_notional_amount": 100_000.0,
                },
            ],
        }
    )

    assert digest["canonical_control_label"] == "SINGLE_LOT_CONTROL"
    assert digest["diagnosis"] == "single_lot_canonical_control"


def test_build_positioning_null_control_digest_promotes_fixed_notional_when_participation_holds() -> None:
    digest = build_positioning_null_control_digest(
        {
            "matrix_status": "completed",
            "research_parent": "positioning_control_baseline",
            "results": [
                {
                    "label": "SINGLE_LOT_CONTROL",
                    "trade_count": 100,
                    "buy_filled_count": 100,
                    "expected_value": 0.01,
                    "profit_factor": 1.8,
                    "max_drawdown": 0.12,
                    "avg_entry_notional": 2_000.0,
                    "exposure_rate": 0.25,
                    "cash_pressure_reject_rate": 0.0,
                },
                {
                    "label": "FIXED_NOTIONAL_CONTROL",
                    "trade_count": 92,
                    "buy_filled_count": 88,
                    "expected_value": 0.012,
                    "profit_factor": 1.9,
                    "max_drawdown": 0.13,
                    "avg_entry_notional": 100_000.0,
                    "exposure_rate": 0.48,
                    "cash_pressure_reject_rate": 0.10,
                    "fixed_notional_amount": 100_000.0,
                },
            ],
        }
    )

    assert digest["canonical_control_label"] == "FIXED_NOTIONAL_CONTROL"
    assert digest["diagnosis"] == "fixed_notional_canonical_control"
