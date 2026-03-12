from __future__ import annotations

from datetime import date

from src.backtest.normandy_bof_exit import NormandyBofExitVariant, _simulate_counterfactual_exit
from src.backtest.normandy_bof_fat_tail_preservation import (
    build_normandy_bof_control_fat_tail_preservation_digest,
    build_normandy_bof_control_fat_tail_preservation_variants,
)
from src.broker.matcher import Matcher
from src.config import Settings


def _make_bar(
    adj_open: float,
    adj_close: float,
    *,
    raw_open: float | None = None,
    up_limit: float = 999.0,
    down_limit: float = 0.0,
    is_halt: bool = False,
) -> dict[str, object]:
    return {
        "adj_open": adj_open,
        "adj_close": adj_close,
        "raw_open": adj_open if raw_open is None else raw_open,
        "up_limit": up_limit,
        "down_limit": down_limit,
        "is_halt": is_halt,
    }


def test_simulate_counterfactual_exit_respects_trailing_activation_delay() -> None:
    matcher = Matcher(Settings(SLIPPAGE_BPS=0.0))
    trade_days = [date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)]
    next_trade_day = {
        date(2026, 1, 2): date(2026, 1, 5),
        date(2026, 1, 5): date(2026, 1, 6),
        date(2026, 1, 6): date(2026, 1, 7),
        date(2026, 1, 7): None,
    }
    trade_day_index = {day: index for index, day in enumerate(trade_days)}
    entry = {
        "signal_id": "000001_2026-01-02_bof",
        "code": "000001",
        "entry_date": "2026-01-02",
        "entry_price": 10.0,
        "quantity": 100,
    }
    bars = {
        date(2026, 1, 2): _make_bar(10.0, 10.6),
        date(2026, 1, 5): _make_bar(10.2, 10.0),
        date(2026, 1, 6): _make_bar(9.9, 9.8),
        date(2026, 1, 7): _make_bar(9.7, 9.7),
    }
    variant = NormandyBofExitVariant(
        label="DELAYED_TRAIL_TEST",
        stop_loss_pct=1.00,
        trailing_stop_pct=0.05,
        notes="",
        trailing_activation_delay_trade_days=3,
    )

    result = _simulate_counterfactual_exit(
        entry=entry,
        bars_by_date=bars,
        trade_days=trade_days,
        next_trade_day=next_trade_day,
        trade_day_index=trade_day_index,
        matcher=matcher,
        variant=variant,
        end=date(2026, 1, 7),
    )

    assert result["exit_reason"] == "FORCE_CLOSE"
    assert result["exit_date"] == "2026-01-07"


def test_simulate_counterfactual_exit_respects_profit_gated_trailing() -> None:
    matcher = Matcher(Settings(SLIPPAGE_BPS=0.0))
    trade_days = [date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)]
    next_trade_day = {
        date(2026, 1, 2): date(2026, 1, 5),
        date(2026, 1, 5): date(2026, 1, 6),
        date(2026, 1, 6): date(2026, 1, 7),
        date(2026, 1, 7): None,
    }
    trade_day_index = {day: index for index, day in enumerate(trade_days)}
    entry = {
        "signal_id": "000001_2026-01-02_bof",
        "code": "000001",
        "entry_date": "2026-01-02",
        "entry_price": 10.0,
        "quantity": 100,
    }
    bars = {
        date(2026, 1, 2): _make_bar(10.0, 10.6),
        date(2026, 1, 5): _make_bar(10.2, 10.0),
        date(2026, 1, 6): _make_bar(9.9, 9.8),
        date(2026, 1, 7): _make_bar(9.7, 9.7),
    }
    variant = NormandyBofExitVariant(
        label="PROFIT_GATE_TEST",
        stop_loss_pct=1.00,
        trailing_stop_pct=0.05,
        notes="",
        trailing_activation_profit_pct=0.20,
    )

    result = _simulate_counterfactual_exit(
        entry=entry,
        bars_by_date=bars,
        trade_days=trade_days,
        next_trade_day=next_trade_day,
        trade_day_index=trade_day_index,
        matcher=matcher,
        variant=variant,
        end=date(2026, 1, 7),
    )

    assert result["exit_reason"] == "FORCE_CLOSE"
    assert result["exit_date"] == "2026-01-07"


def test_build_normandy_bof_control_fat_tail_preservation_variants_returns_profit_gate_sweep() -> None:
    variants = build_normandy_bof_control_fat_tail_preservation_variants(Settings())

    assert [variant.label for variant in variants] == [
        "PROFIT_GATED_TRAIL_22_5P",
        "PROFIT_GATED_TRAIL_25P",
        "PROFIT_GATED_TRAIL_27_5P",
        "PROFIT_GATED_TRAIL_30P",
    ]


def test_build_normandy_bof_control_fat_tail_preservation_digest_marks_candidate_found() -> None:
    payload = {
        "preservation_status": "completed",
        "research_parent": "BOF_CONTROL",
        "preservation_focus": "fat_tail_preservation_mechanism_research",
        "variants": [
            {
                "label": "PROFIT_GATED_TRAIL_25P",
                "overall_capture_share_vs_stop_only": 0.22,
                "category_tradeoff": {
                    "fat_tail_winner_cut": {"capture_share_vs_stop_only": 0.48},
                    "legitimate_protection": {"protection_damage_share_vs_stop_only": 0.30},
                    "all_trailing_stop_rows": {"candidate_total_pnl_delta_vs_control": 400000.0},
                },
            },
            {
                "label": "PROFIT_GATED_TRAIL_30P",
                "overall_capture_share_vs_stop_only": 0.05,
                "category_tradeoff": {
                    "fat_tail_winner_cut": {"capture_share_vs_stop_only": 0.12},
                    "legitimate_protection": {"protection_damage_share_vs_stop_only": 0.80},
                    "all_trailing_stop_rows": {"candidate_total_pnl_delta_vs_control": 10000.0},
                },
            },
        ],
    }

    digest = build_normandy_bof_control_fat_tail_preservation_digest(payload)

    assert digest["diagnosis"] == "targeted_preservation_candidate_found"
    assert digest["decision"] == "continue_mechanism_specific_follow_up"
    assert digest["best_candidate_label"] == "PROFIT_GATED_TRAIL_25P"
