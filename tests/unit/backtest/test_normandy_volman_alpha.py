from __future__ import annotations

from datetime import date

from src.backtest.normandy_volman_alpha import (
    NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
    build_normandy_volman_alpha_digest,
    build_normandy_volman_alpha_scaffold_payload,
    build_normandy_volman_alpha_scenarios,
)
from src.config import Settings


def test_build_normandy_volman_alpha_scenarios_returns_fixed_first_batch() -> None:
    scenarios = build_normandy_volman_alpha_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF_CONTROL",
        "RB_FAKE",
        "SB",
        "FB",
    ]
    assert scenarios[0].detector_ready is True
    assert scenarios[1].detector_ready is True
    assert scenarios[2].notes.startswith("Volman second-break")


def test_build_normandy_volman_alpha_scaffold_payload_lists_ready_detectors() -> None:
    payload = build_normandy_volman_alpha_scaffold_payload(
        db_path="g:/EmotionQuant_data/emotionquant.duckdb",
        config=Settings(),
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        dtt_variant=NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
    )
    assert payload["matrix_status"] == "detector_contract_only"
    assert payload["pending_detectors"] == []
    assert payload["ready_detectors"] == ["BOF_CONTROL", "RB_FAKE", "SB", "FB"]
    assert payload["execution_mode"]["control_label"] == "BOF_CONTROL"


def test_build_normandy_volman_alpha_digest_handles_scaffold_matrix() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000000",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
        "matrix_status": "detector_contract_only",
        "pending_detectors": [],
        "results": [],
    }

    digest = build_normandy_volman_alpha_digest(matrix_payload)

    assert digest["matrix_status"] == "detector_contract_only"
    assert digest["pending_detectors"] == []
    assert digest["second_alpha_candidates"] == []
    assert "scaffold" in digest["conclusion"]


def test_build_normandy_volman_alpha_digest_marks_second_alpha_candidates() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": NORMANDY_VOLMAN_ALPHA_DTT_VARIANT,
        "matrix_status": "completed",
        "results": [
            {
                "label": "BOF_CONTROL",
                "family": "BOF_CONTROL",
                "trade_count": 80,
                "expected_value": 0.02,
                "profit_factor": 1.40,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
            {
                "label": "RB_FAKE",
                "family": "RB_FAKE",
                "trade_count": 46,
                "expected_value": 0.05,
                "profit_factor": 1.30,
                "max_drawdown": 0.22,
                "participation_rate": 0.14,
                "overlap_rate_vs_bof_control": 0.52,
                "incremental_buy_trades_vs_bof_control": 24,
            },
            {
                "label": "SB",
                "family": "SB",
                "trade_count": 33,
                "expected_value": 0.03,
                "profit_factor": 1.18,
                "max_drawdown": 0.20,
                "participation_rate": 0.08,
                "overlap_rate_vs_bof_control": 0.81,
                "incremental_buy_trades_vs_bof_control": 21,
            },
            {
                "label": "FB",
                "family": "FB",
                "trade_count": 18,
                "expected_value": -0.01,
                "profit_factor": 0.92,
                "max_drawdown": 0.16,
                "participation_rate": 0.03,
                "overlap_rate_vs_bof_control": 0.90,
                "incremental_buy_trades_vs_bof_control": 6,
            },
        ],
    }

    digest = build_normandy_volman_alpha_digest(matrix_payload)

    assert digest["provenance_leader"] == "RB_FAKE"
    assert digest["second_alpha_candidates"] == ["RB_FAKE", "SB"]
    assert digest["scorecard"][0]["label"] == "RB_FAKE"
    assert "RB_FAKE, SB" in digest["conclusion"]
