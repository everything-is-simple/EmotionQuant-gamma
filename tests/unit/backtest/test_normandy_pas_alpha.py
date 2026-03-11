from __future__ import annotations

from src.backtest.normandy_pas_alpha import (
    YTC5_ANY_PATTERNS,
    build_normandy_pas_alpha_digest,
    build_normandy_pas_alpha_scenarios,
)
from src.config import Settings


def test_build_normandy_pas_alpha_scenarios_returns_fixed_n1_matrix() -> None:
    scenarios = build_normandy_pas_alpha_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF",
        "BPB",
        "PB",
        "TST",
        "CPB",
        "YTC5_ANY",
    ]
    assert scenarios[0].single_pattern_mode == "bof"
    assert scenarios[1].patterns == ("bpb",)
    assert scenarios[-1].patterns == YTC5_ANY_PATTERNS
    assert all(scenario.quality_enabled is False for scenario in scenarios)


def test_build_normandy_pas_alpha_digest_marks_n2_candidates_and_family_votes() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_pas_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000000",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": "v0_01_dtt_pattern_only",
        "results": [
            {
                "label": "BOF",
                "patterns": ["bof"],
                "pattern_families": ["BOF"],
                "trade_count": 60,
                "expected_value": 0.04,
                "profit_factor": 1.10,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
            },
            {
                "label": "BPB",
                "patterns": ["bpb"],
                "pattern_families": ["BPB"],
                "trade_count": 34,
                "expected_value": 0.03,
                "profit_factor": 1.02,
                "max_drawdown": 0.26,
                "participation_rate": 0.11,
            },
            {
                "label": "PB",
                "patterns": ["pb"],
                "pattern_families": ["PB"],
                "trade_count": 42,
                "expected_value": 0.08,
                "profit_factor": 1.35,
                "max_drawdown": 0.22,
                "participation_rate": 0.19,
            },
            {
                "label": "TST",
                "patterns": ["tst"],
                "pattern_families": ["TST"],
                "trade_count": 29,
                "expected_value": 0.05,
                "profit_factor": 1.18,
                "max_drawdown": 0.17,
                "participation_rate": 0.13,
            },
            {
                "label": "CPB",
                "patterns": ["cpb"],
                "pattern_families": ["CPB"],
                "trade_count": 24,
                "expected_value": 0.09,
                "profit_factor": 1.40,
                "max_drawdown": 0.20,
                "participation_rate": 0.12,
            },
            {
                "label": "YTC5_ANY",
                "patterns": ["bpb", "pb", "tst", "cpb", "bof"],
                "pattern_families": ["BPB", "PB", "TST", "CPB", "BOF"],
                "trade_count": 75,
                "expected_value": 0.06,
                "profit_factor": 1.22,
                "max_drawdown": 0.23,
                "participation_rate": 0.33,
            },
        ],
    }

    digest = build_normandy_pas_alpha_digest(matrix_payload)

    assert digest["provenance_leader"] == "CPB"
    assert digest["n2_candidates"] == ["CPB", "PB", "YTC5_ANY", "TST"]
    assert digest["likely_raw_alpha_family_votes"][0] == {"family": "CPB", "vote_count": 2}
    assert "CPB, PB, YTC5_ANY, TST" in digest["conclusion"]
