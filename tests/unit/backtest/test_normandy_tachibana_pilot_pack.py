from __future__ import annotations

from datetime import date

from src.backtest.normandy_tachibana_pilot_pack import (
    FLOOR_CONTROL_LABEL,
    FLOOR_PROXY_LABEL,
    SameCodeCooldownSignalFilter,
    build_normandy_tachibana_pilot_pack_scenarios,
)
from src.config import Settings
from src.contracts import Signal, Trade


def _build_signal(code: str, signal_date: date) -> Signal:
    return Signal(
        signal_id=f"{code}_{signal_date.isoformat()}_bof",
        code=code,
        signal_date=signal_date,
        action="BUY",
        strength=1.0,
        pattern="bof",
        reason_code="BOF",
    )


def _build_full_exit_trade(code: str, execute_date: date) -> Trade:
    return Trade(
        trade_id=f"{code}_{execute_date.isoformat()}_sell",
        order_id=f"{code}_{execute_date.isoformat()}_sell",
        code=code,
        execute_date=execute_date,
        action="SELL",
        price=10.0,
        quantity=100,
        fee=5.0,
        pattern="trailing_stop",
        remaining_qty_after=0,
    )


def test_build_normandy_tachibana_pilot_pack_scenarios_respects_pilot_boundaries() -> None:
    scenarios = build_normandy_tachibana_pilot_pack_scenarios(Settings())
    by_label = {scenario.label: scenario for scenario in scenarios}

    assert by_label["FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0"].pilot_pack_component == (
        "E1_reduce_to_core_proxy_replay"
    )
    assert by_label["TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD2"].pilot_pack_component == (
        "E2_cooldown_overlay_family"
    )
    assert by_label[FLOOR_CONTROL_LABEL].pilot_pack_component == "E3_unit_regime_overlay"
    assert by_label[FLOOR_PROXY_LABEL].pilot_pack_component == "E3_unit_regime_overlay"


def test_same_code_cooldown_filter_blocks_reentry_until_window_expires() -> None:
    trade_day_index = {
        date(2026, 2, 3): 0,
        date(2026, 2, 4): 1,
        date(2026, 2, 5): 2,
        date(2026, 2, 6): 3,
    }
    filter_hook = SameCodeCooldownSignalFilter(trade_day_index=trade_day_index, cooldown_trade_days=2)

    day0_signal = _build_signal("000001", date(2026, 2, 3))
    assert filter_hook([day0_signal], date(2026, 2, 3), [], None, None) == [day0_signal]

    day1_signal = _build_signal("000001", date(2026, 2, 4))
    assert (
        filter_hook(
            [day1_signal],
            date(2026, 2, 4),
            [_build_full_exit_trade("000001", date(2026, 2, 4))],
            None,
            None,
        )
        == []
    )

    day2_signal = _build_signal("000001", date(2026, 2, 5))
    assert filter_hook([day2_signal], date(2026, 2, 5), [], None, None) == []

    day3_signal = _build_signal("000001", date(2026, 2, 6))
    assert filter_hook([day3_signal], date(2026, 2, 6), [], None, None) == [day3_signal]

    assert filter_hook.build_metrics() == {
        "entry_cooldown_trade_days": 2,
        "cooldown_scope": "same_code_after_full_exit",
        "cooldown_total_signal_count": 4,
        "cooldown_allowed_signal_count": 2,
        "cooldown_blocked_signal_count": 2,
        "cooldown_blocked_signal_share": 0.5,
        "cooldown_full_exit_event_count": 1,
    }
