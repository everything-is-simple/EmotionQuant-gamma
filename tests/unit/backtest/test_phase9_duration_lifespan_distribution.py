from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest

from src.backtest import phase9_duration_lifespan_distribution as module
from src.backtest.phase9_duration_lifespan_distribution import (
    PHASE9E_DURATION_LIFESPAN_SCOPE,
    _build_roundtrip_ledger,
    build_phase9_duration_lifespan_digest,
    build_phase9_duration_lifespan_variant,
    build_phase9_duration_lifespan_window_summary,
)


def _entry_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_signal_date": "2026-01-10",
                "entry_duration_band": "FIRST_QUARTER",
                "entry_magnitude_band": "SECOND_QUARTER",
                "entry_lifespan_joint_band": "FIRST_QUARTER",
            },
            {
                "entry_signal_date": "2026-01-11",
                "entry_duration_band": "FOURTH_QUARTER",
                "entry_magnitude_band": "FOURTH_QUARTER",
                "entry_lifespan_joint_band": "FOURTH_QUARTER",
            },
            {
                "entry_signal_date": "2026-01-12",
                "entry_duration_band": "FOURTH_QUARTER",
                "entry_magnitude_band": "THIRD_QUARTER",
                "entry_lifespan_joint_band": "FOURTH_QUARTER",
            },
        ]
    )


def _roundtrip_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_signal_date": "2026-01-10",
                "entry_duration_band": "FIRST_QUARTER",
                "entry_magnitude_band": "SECOND_QUARTER",
                "entry_lifespan_joint_band": "FIRST_QUARTER",
                "entry_duration_percentile": 20.0,
                "entry_magnitude_percentile": 35.0,
                "entry_lifespan_joint_percentile": 22.0,
                "entry_average_aged_prob": 0.20,
                "entry_remaining_vs_aged_odds": 4.0,
                "pnl_pct": 0.09,
                "holding_days": 8,
            },
            {
                "entry_signal_date": "2026-01-11",
                "entry_duration_band": "FOURTH_QUARTER",
                "entry_magnitude_band": "FOURTH_QUARTER",
                "entry_lifespan_joint_band": "FOURTH_QUARTER",
                "entry_duration_percentile": 85.0,
                "entry_magnitude_percentile": 90.0,
                "entry_lifespan_joint_percentile": 88.0,
                "entry_average_aged_prob": 0.82,
                "entry_remaining_vs_aged_odds": 0.22,
                "pnl_pct": -0.04,
                "holding_days": 3,
            },
            {
                "entry_signal_date": "2026-01-12",
                "entry_duration_band": "FOURTH_QUARTER",
                "entry_magnitude_band": "THIRD_QUARTER",
                "entry_lifespan_joint_band": "FOURTH_QUARTER",
                "entry_duration_percentile": 92.0,
                "entry_magnitude_percentile": 74.0,
                "entry_lifespan_joint_percentile": 91.0,
                "entry_average_aged_prob": 0.88,
                "entry_remaining_vs_aged_odds": 0.14,
                "pnl_pct": -0.02,
                "holding_days": 4,
            },
        ]
    )


def test_build_phase9_duration_lifespan_variant_is_descriptive() -> None:
    assert build_phase9_duration_lifespan_variant() == "book_aligned_quartile_and_average_lifespan_odds"
    assert PHASE9E_DURATION_LIFESPAN_SCOPE == "phase9e_duration_lifespan_distribution"


def test_build_phase9_duration_lifespan_window_summary_includes_quartiles_and_odds() -> None:
    summary = build_phase9_duration_lifespan_window_summary(
        window_label="full_window",
        window_start=pd.Timestamp("2026-01-01").date(),
        window_end=pd.Timestamp("2026-01-31").date(),
        backtest_metrics={
            "trade_count": 3,
            "win_rate": 1 / 3,
            "expected_value": 0.01,
            "profit_factor": 0.5,
            "max_drawdown": 0.12,
            "filled_count": 3,
            "participation_rate": 0.4,
        },
        entry_df=_entry_frame(),
        roundtrip_df=_roundtrip_frame(),
    )

    duration_counts = {row["band_label"]: row["entry_count"] for row in summary["duration_quartile_counts"]}
    assert duration_counts["FIRST_QUARTER"] == 1
    assert duration_counts["FOURTH_QUARTER"] == 2

    fourth_row = next(row for row in summary["duration_quartile_payoff"] if row["band_label"] == "FOURTH_QUARTER")
    assert fourth_row["paired_trade_count"] == 2
    assert math.isclose(fourth_row["avg_average_aged_prob"], 0.85)
    assert summary["continuous_relationships"]["average_aged_prob_vs_pnl_pct_spearman"] < 0


def test_build_phase9_duration_lifespan_digest_supports_runtime_when_fourth_quarter_is_worse() -> None:
    full_window = build_phase9_duration_lifespan_window_summary(
        window_label="full_window",
        window_start=pd.Timestamp("2026-01-01").date(),
        window_end=pd.Timestamp("2026-01-31").date(),
        backtest_metrics={
            "trade_count": 12,
            "win_rate": 0.5,
            "expected_value": 0.01,
            "profit_factor": 1.1,
            "max_drawdown": 0.10,
            "filled_count": 12,
            "participation_rate": 0.5,
        },
        entry_df=pd.concat([_entry_frame()] * 4, ignore_index=True),
        roundtrip_df=pd.concat([_roundtrip_frame()] * 4, ignore_index=True),
    )
    digest = build_phase9_duration_lifespan_digest({"windows": [full_window]})

    assert digest["decision"] == "duration_runtime_candidate_survives_quartile_surface"
    assert digest["phase9f_duration_operand_recommendation"] == (
        "use_duration_band_fourth_quarter_only_if_duration_is_carried_forward"
    )


def test_build_phase9_duration_lifespan_digest_returns_sidecar_only_on_mixed_surface() -> None:
    mixed = _roundtrip_frame().copy()
    mixed.loc[mixed["entry_duration_band"] == "FOURTH_QUARTER", "pnl_pct"] = 0.03
    mixed.loc[mixed["entry_lifespan_joint_band"] == "FOURTH_QUARTER", "pnl_pct"] = 0.03
    full_window = build_phase9_duration_lifespan_window_summary(
        window_label="full_window",
        window_start=pd.Timestamp("2026-01-01").date(),
        window_end=pd.Timestamp("2026-01-31").date(),
        backtest_metrics={
            "trade_count": 3,
            "win_rate": 0.66,
            "expected_value": 0.02,
            "profit_factor": 1.5,
            "max_drawdown": 0.05,
            "filled_count": 3,
            "participation_rate": 0.5,
        },
        entry_df=_entry_frame(),
        roundtrip_df=mixed,
    )
    digest = build_phase9_duration_lifespan_digest({"windows": [full_window]})

    assert digest["decision"] == "duration_should_return_to_sidecar_only_distribution_reading"


def test_build_roundtrip_ledger_preserves_code_column_after_entry_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    trades = pd.DataFrame(
        [
            {
                "trade_id": 1,
                "order_id": "O1",
                "code": "AAA",
                "execute_date": date(2026, 1, 10),
                "action": "BUY",
                "price": 10.0,
                "quantity": 100,
                "fee": 1.0,
                "pattern": "bof",
                "is_paper": False,
                "position_id": "P1",
                "exit_plan_id": None,
                "exit_leg_id": None,
                "exit_leg_seq": None,
                "exit_reason_code": None,
                "is_partial_exit": False,
                "remaining_qty_after": 100,
            },
            {
                "trade_id": 2,
                "order_id": "O2",
                "code": "AAA",
                "execute_date": date(2026, 1, 14),
                "action": "SELL",
                "price": 11.0,
                "quantity": 100,
                "fee": 1.0,
                "pattern": "bof",
                "is_paper": False,
                "position_id": "P1",
                "exit_plan_id": None,
                "exit_leg_id": "L1",
                "exit_leg_seq": 1,
                "exit_reason_code": "FULL_EXIT_CONTROL",
                "is_partial_exit": False,
                "remaining_qty_after": 0,
            },
        ]
    )
    entry_context = pd.DataFrame(
        [
            {
                "entry_trade_id": 1,
                "code": "AAA",
                "entry_signal_date": date(2026, 1, 10),
                "entry_duration_band": "FOURTH_QUARTER",
            }
        ]
    )

    monkeypatch.setattr(module, "_load_trades", lambda store, start, end: trades)

    ledger = _build_roundtrip_ledger(object(), date(2026, 1, 10), date(2026, 1, 14), entry_context)

    assert ledger["code"].tolist() == ["AAA"]
    assert ledger["entry_signal_date"].tolist() == [date(2026, 1, 10)]
    assert ledger["holding_days"].tolist() == [4]
