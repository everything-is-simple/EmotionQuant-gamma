from __future__ import annotations

from src.backtest.phase6_integrated_validation import (
    PHASE6_UNIFIED_DEFAULT_CANDIDATE,
    RAW_LEGACY_BASELINE_CONTROL,
    build_phase6_integrated_scenarios,
    build_phase6_integrated_validation_digest,
)
from src.config import Settings


def test_build_phase6_integrated_scenarios_freezes_raw_legacy_and_candidate_boundaries() -> None:
    cfg = Settings(
        BACKTEST_INITIAL_CASH=1_000_000,
        MAX_POSITION_PCT=0.10,
        FIXED_NOTIONAL_AMOUNT=0.0,
    )

    scenarios = build_phase6_integrated_scenarios(cfg)

    assert [scenario.label for scenario in scenarios] == [
        RAW_LEGACY_BASELINE_CONTROL,
        PHASE6_UNIFIED_DEFAULT_CANDIDATE,
    ]
    assert scenarios[0].enable_irs_filter is True
    assert scenarios[0].enable_mss_gate is True
    assert scenarios[0].position_sizing_mode == "risk_budget"
    assert scenarios[1].enable_irs_filter is False
    assert scenarios[1].enable_mss_gate is False
    assert scenarios[1].position_sizing_mode == "fixed_notional"
    assert scenarios[1].fixed_notional_amount == 100_000.0


def test_build_phase6_integrated_validation_digest_goes_to_phase_6c_when_checks_pass() -> None:
    digest = build_phase6_integrated_validation_digest(
        {
            "matrix_status": "completed",
            "gene_sidecar": {
                "stock_gene_rows": 10_000,
                "gene_validation_rows": 4,
                "gene_mirror_rows": 32,
                "gene_conditioning_rows": 108,
            },
            "boundary_audit": {
                "audit_passed": True,
            },
            "results": [
                {
                    "scenario_label": RAW_LEGACY_BASELINE_CONTROL,
                    "window_label": "full_window",
                    "trade_count": 50,
                    "buy_filled_count": 50,
                    "exposure_rate": 0.20,
                    "expected_value": 0.01,
                    "profit_factor": 1.40,
                    "max_drawdown": 0.18,
                    "trace_counts": {
                        "selector_candidate_trace_count": 100,
                        "pas_trigger_trace_count": 60,
                        "broker_lifecycle_trace_count": 110,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "full_window",
                    "trade_count": 62,
                    "buy_filled_count": 62,
                    "exposure_rate": 0.34,
                    "expected_value": 0.012,
                    "profit_factor": 1.45,
                    "max_drawdown": 0.21,
                    "enable_irs_filter": False,
                    "enable_mss_gate": False,
                    "reject_rate": 0.22,
                    "trace_counts": {
                        "selector_candidate_trace_count": 120,
                        "pas_trigger_trace_count": 70,
                        "broker_lifecycle_trace_count": 140,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "front_half_window",
                    "trade_days": 20,
                    "trade_count": 28,
                    "expected_value": 0.011,
                    "trace_counts": {
                        "selector_candidate_trace_count": 55,
                        "pas_trigger_trace_count": 30,
                        "broker_lifecycle_trace_count": 62,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "back_half_window",
                    "trade_days": 19,
                    "trade_count": 34,
                    "expected_value": 0.013,
                    "trace_counts": {
                        "selector_candidate_trace_count": 65,
                        "pas_trigger_trace_count": 40,
                        "broker_lifecycle_trace_count": 78,
                    },
                },
            ],
        }
    )

    assert digest["decision"] == "go_to_phase_6c"
    assert digest["diagnosis"] == "candidate_boundary_and_runtime_validated"


def test_build_phase6_integrated_validation_digest_returns_no_go_when_boundary_fails() -> None:
    digest = build_phase6_integrated_validation_digest(
        {
            "matrix_status": "completed",
            "gene_sidecar": {
                "stock_gene_rows": 0,
                "gene_validation_rows": 0,
                "gene_mirror_rows": 0,
                "gene_conditioning_rows": 0,
            },
            "boundary_audit": {
                "audit_passed": False,
            },
            "results": [
                {
                    "scenario_label": RAW_LEGACY_BASELINE_CONTROL,
                    "window_label": "full_window",
                    "trade_count": 50,
                    "buy_filled_count": 50,
                    "exposure_rate": 0.20,
                    "expected_value": 0.01,
                    "profit_factor": 1.40,
                    "max_drawdown": 0.18,
                    "trace_counts": {
                        "selector_candidate_trace_count": 100,
                        "pas_trigger_trace_count": 60,
                        "broker_lifecycle_trace_count": 110,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "full_window",
                    "trade_count": 62,
                    "buy_filled_count": 62,
                    "exposure_rate": 0.34,
                    "expected_value": 0.012,
                    "profit_factor": 1.45,
                    "max_drawdown": 0.21,
                    "enable_irs_filter": False,
                    "enable_mss_gate": False,
                    "reject_rate": 0.22,
                    "trace_counts": {
                        "selector_candidate_trace_count": 120,
                        "pas_trigger_trace_count": 70,
                        "broker_lifecycle_trace_count": 140,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "front_half_window",
                    "trade_days": 20,
                    "trade_count": 28,
                    "expected_value": 0.011,
                    "trace_counts": {
                        "selector_candidate_trace_count": 55,
                        "pas_trigger_trace_count": 30,
                        "broker_lifecycle_trace_count": 62,
                    },
                },
                {
                    "scenario_label": PHASE6_UNIFIED_DEFAULT_CANDIDATE,
                    "window_label": "back_half_window",
                    "trade_days": 19,
                    "trade_count": 34,
                    "expected_value": 0.013,
                    "trace_counts": {
                        "selector_candidate_trace_count": 65,
                        "pas_trigger_trace_count": 40,
                        "broker_lifecycle_trace_count": 78,
                    },
                },
            ],
        }
    )

    assert digest["decision"] == "no_go"
    assert digest["diagnosis"] == "boundary_violation"
