from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.backtest.phase9_duration_percentile_validation import PHASE9B_BASELINE_CONTROL
from src.backtest.phase9_reversal_state_validation import (
    GENE_REVERSAL_PREP_EXIT_REASON,
    PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP,
    ReversalStateExitHook,
    build_phase9_reversal_candidate_label,
    build_phase9_reversal_state_validation_digest,
)


class _DummyStore:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def read_df(self, query: str, params: tuple[object, ...]):  # noqa: ARG002
        import pandas as pd

        return pd.DataFrame(self.rows)


@dataclass
class _DummyPosition:
    code: str
    position_id: str | None = None


class _DummyBroker:
    def __init__(self) -> None:
        self.portfolio = {
            "000001": _DummyPosition(code="000001", position_id="POS_1"),
            "000002": _DummyPosition(code="000002", position_id="POS_2"),
        }

    def schedule_custom_exit_order(self, code: str, signal_date: date, exit_reason: str, *, event_stage: str = "CUSTOM_EXIT_ORDER_CREATED"):
        _ = (signal_date, exit_reason, event_stage)
        if code == "000001":
            return "created", type("OrderStub", (), {"order_id": f"EXIT_{code}"})()
        return "pending_sell_exists", None


def _build_digest_payload(*, expected_value_delta: float, profit_factor_delta: float, max_drawdown_delta: float, created_count: int = 2, filled_exit_count: int = 2, trade_exit_count: int = 2) -> dict[str, object]:
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
        "reversal_exit_metrics": {},
    }
    candidate = {
        "scenario_label": PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP,
        "window_label": "full_window",
        "trade_count": 9,
        "buy_filled_count": 10,
        "signals_count": 20,
        "expected_value": baseline["expected_value"] + expected_value_delta,
        "profit_factor": baseline["profit_factor"] + profit_factor_delta,
        "max_drawdown": baseline["max_drawdown"] + max_drawdown_delta,
        "trade_days": 20,
        "trace_counts": {"pas_trigger_trace_count": 10, "broker_lifecycle_trace_count": 10},
        "reversal_exit_metrics": {"reversal_exit_filled_count": filled_exit_count, "reversal_exit_trade_count": trade_exit_count},
    }
    front = {"scenario_label": PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP, "window_label": "front_half_window", "trade_count": 4, "expected_value": 0.02, "trade_days": 10, "trace_counts": {"pas_trigger_trace_count": 5, "broker_lifecycle_trace_count": 5}}
    back = {"scenario_label": PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP, "window_label": "back_half_window", "trade_count": 5, "expected_value": 0.015, "trade_days": 10, "trace_counts": {"pas_trigger_trace_count": 5, "broker_lifecycle_trace_count": 5}}
    return {"matrix_status": "completed", "results": [baseline, candidate, front, back], "candidate_exit_rule": {"metrics": {"reversal_exit_matched_state_position_day_count": 3, "reversal_exit_created_count": created_count, "reversal_exit_target_state": "CONFIRMED_TURN_DOWN", "reversal_exit_reason_code": GENE_REVERSAL_PREP_EXIT_REASON, "reversal_exit_rule": "schedule T+1 SELL when reversal_state == CONFIRMED_TURN_DOWN"}}}


def test_reversal_state_exit_hook_creates_order_when_state_matches() -> None:
    hook = ReversalStateExitHook(target_state="CONFIRMED_TURN_DOWN", exit_reason_code=GENE_REVERSAL_PREP_EXIT_REASON)
    broker = _DummyBroker()
    store = _DummyStore(
        [
            {"code": "000001", "reversal_state": "CONFIRMED_TURN_DOWN", "latest_confirmed_turn_type": "CONFIRMED_TURN_DOWN"},
            {"code": "000002", "reversal_state": "CONFIRMED_TURN_DOWN", "latest_confirmed_turn_type": "CONFIRMED_TURN_DOWN"},
        ]
    )
    created = hook(date(2026, 2, 24), [], broker, store)
    assert len(created) == 1
    metrics = hook.build_metrics()
    assert metrics["reversal_exit_total_position_day_count"] == 2
    assert metrics["reversal_exit_matched_state_position_day_count"] == 2
    assert metrics["reversal_exit_created_count"] == 1
    assert metrics["reversal_exit_pending_sell_skip_count"] == 1


def test_build_phase9_reversal_state_validation_digest_promotes_when_candidate_cleanly_improves() -> None:
    digest = build_phase9_reversal_state_validation_digest(_build_digest_payload(expected_value_delta=0.005, profit_factor_delta=0.20, max_drawdown_delta=-0.02))
    assert digest["decision"] == "promote_reversal_state_exit_preparation"
    assert digest["diagnosis"] == "isolated_exit_preparation_improves_baseline"


def test_build_phase9_reversal_state_validation_digest_retains_when_rule_does_not_touch_runtime() -> None:
    digest = build_phase9_reversal_state_validation_digest(_build_digest_payload(expected_value_delta=0.003, profit_factor_delta=0.05, max_drawdown_delta=-0.01, created_count=0, filled_exit_count=0, trade_exit_count=0))
    assert digest["decision"] == "retain_sidecar_only"
    assert digest["diagnosis"] == "rule_did_not_truthfully_touch_runtime_exits"


def test_build_phase9_reversal_candidate_label_reflects_target_state() -> None:
    assert build_phase9_reversal_candidate_label("CONFIRMED_TURN_DOWN") == PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP
    assert build_phase9_reversal_candidate_label("two_b_watch") == "PHASE9B_REVERSAL_TWO_B_WATCH_EXIT_PREP"
