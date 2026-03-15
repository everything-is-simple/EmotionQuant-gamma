from __future__ import annotations

from datetime import date

from src.backtest.normandy_tachibana_pilot_pack import (
    FLOOR_CONTROL_LABEL,
    FLOOR_PROXY_LABEL,
    SameCodeCooldownSignalFilter,
    build_normandy_tachibana_pilot_pack_digest,
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


def _build_digest_result(
    label: str,
    *,
    position_sizing_mode: str = "fixed_notional",
    entry_cooldown_trade_days: int = 0,
    expected_value: float = 0.01,
    profit_factor: float = 2.0,
    max_drawdown: float = 0.1,
    net_pnl: float = 1000.0,
    trade_count: int = 100,
    buy_filled_count: int = 100,
    partial_exit_pair_count: int = 0,
    unit_regime_tag: str = "fixed_notional_control",
    experimental_segment_policy: str = "isolate_from_canonical_aggregate",
) -> dict[str, object]:
    return {
        "label": label,
        "position_sizing_mode": position_sizing_mode,
        "entry_cooldown_trade_days": entry_cooldown_trade_days,
        "expected_value": expected_value,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "net_pnl": net_pnl,
        "trade_count": trade_count,
        "buy_filled_count": buy_filled_count,
        "partial_exit_pair_count": partial_exit_pair_count,
        "partial_exit_pair_share": partial_exit_pair_count / trade_count if trade_count else 0.0,
        "trade_sequence_max_drawdown": max_drawdown,
        "avg_hold_days": 5.0,
        "unit_regime_tag": unit_regime_tag,
        "reduced_unit_scale": 1.0,
        "experimental_segment_policy": experimental_segment_policy,
    }


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


def test_build_normandy_tachibana_pilot_pack_digest_isolates_experimental_sidecar() -> None:
    matrix_payload = {
        "matrix_status": "completed",
        "research_parent": "tachibana_pilot_pack_runner",
        "baseline_runtime": {
            "experimental_segment_policy": "isolate_from_canonical_aggregate",
        },
        "results": [
            _build_digest_result(
                "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0",
                expected_value=0.01,
                profit_factor=2.0,
                max_drawdown=0.10,
                net_pnl=1000.0,
                trade_count=100,
                buy_filled_count=100,
            ),
            _build_digest_result(
                "TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0",
                expected_value=0.03,
                profit_factor=2.5,
                max_drawdown=0.09,
                net_pnl=1300.0,
                trade_count=120,
                buy_filled_count=98,
                partial_exit_pair_count=60,
            ),
            _build_digest_result(
                "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD5",
                entry_cooldown_trade_days=5,
                expected_value=0.02,
                profit_factor=2.1,
                max_drawdown=0.08,
                net_pnl=1100.0,
            ),
            _build_digest_result(
                FLOOR_CONTROL_LABEL,
                position_sizing_mode="single_lot",
                unit_regime_tag="single_lot_control",
                expected_value=0.005,
                profit_factor=1.8,
                max_drawdown=0.03,
                net_pnl=-200.0,
            ),
            _build_digest_result(
                "TRAIL_SCALE_OUT_33_67__FIXED_NOTIONAL_CONTROL__CD0",
                expected_value=0.05,
                profit_factor=3.0,
                max_drawdown=0.11,
                net_pnl=1500.0,
                trade_count=130,
                buy_filled_count=97,
                partial_exit_pair_count=70,
            ),
        ],
    }

    payload = build_normandy_tachibana_pilot_pack_digest(matrix_payload)

    isolation = payload["experimental_segment_isolation"]
    assert isolation["policy"] == "isolate_from_canonical_aggregate"
    assert isolation["canonical_aggregate_labels"] == [
        "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0",
        "TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0",
    ]
    assert isolation["experimental_sidecar_labels"] == [
        "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD5",
        FLOOR_CONTROL_LABEL,
        "TRAIL_SCALE_OUT_33_67__FIXED_NOTIONAL_CONTROL__CD0",
    ]
    assert isolation["cooldown_sidecar_labels"] == ["FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD5"]
    assert isolation["unit_regime_sidecar_labels"] == [FLOOR_CONTROL_LABEL]
    assert isolation["noncanonical_fixed_notional_reference_labels"] == [
        "TRAIL_SCALE_OUT_33_67__FIXED_NOTIONAL_CONTROL__CD0"
    ]
    assert payload["e1_formal_entry_digest"]["leader"]["label"] == "TRAIL_SCALE_OUT_25_75"
    assert payload["conclusion"].endswith("Experimental sidecar remains isolated from the canonical aggregate.")
