from __future__ import annotations

from datetime import date

from src.backtest.phase9_context_trend_direction_validation import (
    PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD,
    ContextTrendDirectionNegativeSignalFilter,
    build_phase9_context_direction_candidate_label,
    build_phase9_context_direction_validation_digest,
)
from src.backtest.phase9_duration_percentile_validation import PHASE9B_BASELINE_CONTROL
from src.contracts import Signal


class _DummyStore:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def read_df(self, query: str, params: tuple[object, ...]):  # noqa: ARG002
        import pandas as pd

        return pd.DataFrame(self.rows)


def _signal(code: str, when: date, pattern: str = "bof") -> Signal:
    return Signal(
        signal_id=f"{code}_{when.isoformat()}_{pattern}",
        code=code,
        signal_date=when,
        action="BUY",
        strength=1.0,
        pattern=pattern,
        reason_code=f"PAS_{pattern.upper()}",
    )


def _build_digest_payload(
    *,
    expected_value_delta: float,
    profit_factor_delta: float,
    max_drawdown_delta: float,
    blocked_signal_count: int = 3,
    blocked_fill_count: int = 2,
) -> dict[str, object]:
    baseline = {
        "scenario_label": PHASE9B_BASELINE_CONTROL,
        "window_label": "full_window",
        "trade_count": 10,
        "buy_filled_count": 10,
        "signals_count": 20,
        "expected_value": 0.01,
        "profit_factor": 1.10,
        "max_drawdown": 0.15,
        "trade_days": 20,
        "trace_counts": {"pas_trigger_trace_count": 10, "broker_lifecycle_trace_count": 10},
    }
    candidate = {
        "scenario_label": PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD,
        "window_label": "full_window",
        "trade_count": 9,
        "buy_filled_count": 9,
        "signals_count": 20,
        "expected_value": baseline["expected_value"] + expected_value_delta,
        "profit_factor": baseline["profit_factor"] + profit_factor_delta,
        "max_drawdown": baseline["max_drawdown"] + max_drawdown_delta,
        "trade_days": 20,
        "trace_counts": {"pas_trigger_trace_count": 10, "broker_lifecycle_trace_count": 10},
    }
    front = {
        "scenario_label": PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD,
        "window_label": "front_half_window",
        "trade_count": 4,
        "expected_value": 0.02,
        "trade_days": 10,
        "trace_counts": {"pas_trigger_trace_count": 5, "broker_lifecycle_trace_count": 5},
    }
    back = {
        "scenario_label": PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD,
        "window_label": "back_half_window",
        "trade_count": 5,
        "expected_value": 0.015,
        "trade_days": 10,
        "trace_counts": {"pas_trigger_trace_count": 5, "broker_lifecycle_trace_count": 5},
    }
    return {
        "matrix_status": "completed",
        "results": [baseline, candidate, front, back],
        "candidate_filter": {
            "metrics": {
                "context_direction_filter_total_signal_count": 20,
                "context_direction_filter_blocked_signal_count": blocked_signal_count,
                "context_direction_filter_blocked_signal_share": blocked_signal_count / 20.0,
                "context_direction_filter_blocked_direction": "DOWN",
                "context_direction_filter_rule": "block when current_context_trend_direction == DOWN",
            }
        },
        "blocked_signal_truth": {
            "blocked_signals_present_in_baseline_signal_count": blocked_signal_count,
            "blocked_signals_with_baseline_buy_fill_count": blocked_fill_count,
            "blocked_signals_share_of_baseline_buy_fills": blocked_fill_count / 10.0,
        },
    }


def test_context_direction_filter_blocks_down_and_allows_missing_context() -> None:
    when = date(2026, 2, 24)
    signal_filter = ContextTrendDirectionNegativeSignalFilter(blocked_direction="DOWN")
    store = _DummyStore(
        [
            {
                "code": "000001",
                "current_context_trend_direction": "DOWN",
                "current_context_trend_level": "L2",
                "current_wave_role": "MAINSTREAM",
            },
            {
                "code": "000002",
                "current_context_trend_direction": "UP",
                "current_context_trend_level": "L2",
                "current_wave_role": "COUNTERTREND",
            },
        ]
    )

    kept = signal_filter(
        [_signal("000001", when), _signal("000002", when), _signal("000003", when)],
        when,
        [],
        None,
        store,
    )

    assert [signal.code for signal in kept] == ["000002", "000003"]
    metrics = signal_filter.build_metrics()
    assert metrics["context_direction_filter_total_signal_count"] == 3
    assert metrics["context_direction_filter_blocked_signal_count"] == 1
    assert metrics["context_direction_filter_missing_direction_signal_count"] == 1


def test_build_phase9_context_direction_validation_digest_promotes_when_candidate_cleanly_improves() -> None:
    digest = build_phase9_context_direction_validation_digest(
        _build_digest_payload(
            expected_value_delta=0.005,
            profit_factor_delta=0.20,
            max_drawdown_delta=-0.02,
        )
    )

    assert digest["decision"] == "promote_context_trend_direction_negative_guard"
    assert digest["diagnosis"] == "isolated_negative_guard_improves_baseline"


def test_build_phase9_context_direction_validation_digest_retains_sidecar_when_candidate_fails() -> None:
    digest = build_phase9_context_direction_validation_digest(
        _build_digest_payload(
            expected_value_delta=-0.002,
            profit_factor_delta=-0.05,
            max_drawdown_delta=0.01,
        )
    )

    assert digest["decision"] == "retain_sidecar_only"
    assert digest["diagnosis"] == "isolated_rule_not_better_than_baseline"


def test_build_phase9_context_direction_candidate_label_reflects_blocked_direction() -> None:
    assert build_phase9_context_direction_candidate_label("DOWN") == PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD
    assert build_phase9_context_direction_candidate_label("up") == "PHASE9B_CONTEXT_DIRECTION_UP_NEGATIVE_GUARD"
