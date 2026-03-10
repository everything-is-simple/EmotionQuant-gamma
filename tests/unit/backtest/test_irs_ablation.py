from __future__ import annotations

import pytest

from src.backtest.irs_ablation import build_irs_ablation_scenarios, run_irs_ablation
from src.config import Settings


def test_build_irs_ablation_scenarios_returns_fixed_phase2_matrix() -> None:
    scenarios = build_irs_ablation_scenarios()
    assert [(scenario.label, scenario.factor_mode) for scenario in scenarios] == [
        ("IRS_LITE", "lite"),
        ("IRS_RSRV", "rsrv"),
        ("IRS_RSRVRTBDGN", "rsrvrtbdgn"),
    ]


def test_run_irs_ablation_rejects_skip_rebuild_for_multi_scenario_matrix(tmp_path) -> None:
    db = tmp_path / "irs-ablation.duckdb"
    db.write_bytes(b"")

    with pytest.raises(ValueError, match="skip_rebuild_irs"):
        run_irs_ablation(
            db_path=db,
            config=Settings(),
            start=Settings().history_start,
            end=Settings().history_start,
            dtt_variant="v0_01_dtt_pattern_plus_irs_score",
            skip_rebuild_irs=True,
        )
