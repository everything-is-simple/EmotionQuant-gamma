from __future__ import annotations

from datetime import date

from src.backtest.normandy_bof_exit import (
    NormandyBofExitVariant,
    _simulate_counterfactual_exit,
    build_normandy_bof_control_exit_digest,
    build_normandy_bof_control_exit_variants,
)
from src.backtest.normandy_bof_quality import resolve_normandy_bof_quality_scenarios
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


def test_build_normandy_bof_control_exit_variants_returns_fixed_presets() -> None:
    variants = build_normandy_bof_control_exit_variants()
    assert [variant.label for variant in variants] == [
        "TIGHT_EXIT",
        "LOOSE_EXIT",
        "STOP_ONLY",
        "TRAIL_ONLY",
    ]


def test_resolve_normandy_bof_quality_scenarios_keeps_control_when_filtered() -> None:
    scenarios = resolve_normandy_bof_quality_scenarios(Settings(), ["BOF_KEYLEVEL_STRICT"])
    assert [scenario.label for scenario in scenarios] == ["BOF_CONTROL", "BOF_KEYLEVEL_STRICT"]


def test_simulate_counterfactual_exit_hits_stop_loss_on_next_open() -> None:
    matcher = Matcher(Settings(SLIPPAGE_BPS=0.0))
    trade_days = [date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)]
    next_trade_day = {
        date(2026, 1, 2): date(2026, 1, 5),
        date(2026, 1, 5): date(2026, 1, 6),
        date(2026, 1, 6): None,
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
        date(2026, 1, 2): _make_bar(10.0, 9.4),
        date(2026, 1, 5): _make_bar(9.3, 9.2),
        date(2026, 1, 6): _make_bar(9.1, 9.0),
    }
    variant = NormandyBofExitVariant(label="TEST_STOP", stop_loss_pct=0.05, trailing_stop_pct=0.50, notes="")

    result = _simulate_counterfactual_exit(
        entry=entry,
        bars_by_date=bars,
        trade_days=trade_days,
        next_trade_day=next_trade_day,
        trade_day_index=trade_day_index,
        matcher=matcher,
        variant=variant,
        end=date(2026, 1, 6),
    )

    assert result["exit_reason"] == "STOP_LOSS"
    assert result["exit_date"] == "2026-01-05"
    assert result["exit_stage"] == "MATCH_FILLED"


def test_simulate_counterfactual_exit_hits_trailing_stop_after_peak() -> None:
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
    variant = NormandyBofExitVariant(label="TEST_TRAIL", stop_loss_pct=1.00, trailing_stop_pct=0.05, notes="")

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

    assert result["exit_reason"] == "TRAILING_STOP"
    assert result["exit_date"] == "2026-01-06"
    assert result["exit_stage"] == "MATCH_FILLED"


def test_simulate_counterfactual_exit_force_closes_at_window_end() -> None:
    matcher = Matcher(Settings(SLIPPAGE_BPS=0.0))
    trade_days = [date(2026, 1, 2), date(2026, 1, 5)]
    next_trade_day = {
        date(2026, 1, 2): date(2026, 1, 5),
        date(2026, 1, 5): None,
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
        date(2026, 1, 2): _make_bar(10.0, 10.1),
        date(2026, 1, 5): _make_bar(10.2, 10.2),
    }
    variant = NormandyBofExitVariant(label="TEST_FORCE", stop_loss_pct=0.50, trailing_stop_pct=0.50, notes="")

    result = _simulate_counterfactual_exit(
        entry=entry,
        bars_by_date=bars,
        trade_days=trade_days,
        next_trade_day=next_trade_day,
        trade_day_index=trade_day_index,
        matcher=matcher,
        variant=variant,
        end=date(2026, 1, 5),
    )

    assert result["exit_reason"] == "FORCE_CLOSE"
    assert result["exit_date"] == "2026-01-05"
    assert result["exit_stage"] == "FORCE_CLOSE_FILLED"


def test_simulate_counterfactual_exit_can_loosen_trailing_after_profit_switch() -> None:
    matcher = Matcher(Settings(SLIPPAGE_BPS=0.0))
    trade_days = [date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8)]
    next_trade_day = {
        date(2026, 1, 2): date(2026, 1, 5),
        date(2026, 1, 5): date(2026, 1, 6),
        date(2026, 1, 6): date(2026, 1, 7),
        date(2026, 1, 7): date(2026, 1, 8),
        date(2026, 1, 8): None,
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
        date(2026, 1, 2): _make_bar(10.0, 12.0),
        date(2026, 1, 5): _make_bar(11.8, 11.0),
        date(2026, 1, 6): _make_bar(10.3, 10.1),
        date(2026, 1, 7): _make_bar(10.0, 10.0),
        date(2026, 1, 8): _make_bar(10.0, 10.0),
    }
    variant = NormandyBofExitVariant(
        label="TEST_TWO_STAGE_TRAIL",
        stop_loss_pct=1.00,
        trailing_stop_pct=0.05,
        notes="",
        trailing_loosen_profit_pct=0.20,
        trailing_stop_pct_after_loosen=0.15,
    )

    result = _simulate_counterfactual_exit(
        entry=entry,
        bars_by_date=bars,
        trade_days=trade_days,
        next_trade_day=next_trade_day,
        trade_day_index=trade_day_index,
        matcher=matcher,
        variant=variant,
        end=date(2026, 1, 8),
    )

    assert result["exit_reason"] == "TRAILING_STOP"
    assert result["exit_date"] == "2026-01-07"
    assert result["exit_stage"] == "MATCH_FILLED"


def test_simulate_counterfactual_exit_keeps_early_trailing_before_profit_switch() -> None:
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
        label="TEST_TWO_STAGE_TRAIL_EARLY",
        stop_loss_pct=1.00,
        trailing_stop_pct=0.05,
        notes="",
        trailing_loosen_profit_pct=0.20,
        trailing_stop_pct_after_loosen=0.15,
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

    assert result["exit_reason"] == "TRAILING_STOP"
    assert result["exit_date"] == "2026-01-06"
    assert result["exit_stage"] == "MATCH_FILLED"


def test_build_normandy_bof_control_exit_digest_marks_material_exit_damage() -> None:
    digest = build_normandy_bof_control_exit_digest(
        {
            "matrix_status": "completed",
            "results": [
                {
                    "label": "CONTROL_REALIZED",
                    "kind": "control_realized",
                    "trade_count": 100,
                    "expected_value": 0.010,
                    "profit_factor": 1.40,
                    "total_pnl": 10000.0,
                    "exit_reason_breakdown": {"STOP_LOSS": 30, "TRAILING_STOP": 60, "FORCE_CLOSE": 10},
                },
                {
                    "label": "LOOSE_EXIT",
                    "kind": "counterfactual_exit_variant",
                    "expected_value": 0.0135,
                    "profit_factor": 1.60,
                    "total_pnl": 12500.0,
                    "comparison_vs_control": {
                        "total_pnl_delta_vs_control": 2500.0,
                        "improved_trade_count_vs_control": 60,
                        "worsened_trade_count_vs_control": 35,
                        "top_improved_examples": [{"signal_id": "a"}],
                        "top_worsened_examples": [{"signal_id": "b"}],
                    },
                },
            ],
        }
    )

    assert digest["diagnosis"] == "exit_damage_material"
    assert digest["decision"] == "prioritize_exit_semantics_follow_up"
    assert digest["best_counterfactual_label"] == "LOOSE_EXIT"
