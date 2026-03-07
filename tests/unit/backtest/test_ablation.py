from __future__ import annotations

from src.backtest.ablation import build_selector_ablation_scenarios
from src.config import Settings


def test_build_selector_ablation_scenarios_returns_fixed_dtt_matrix() -> None:
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        MSS_VARIANT="zscore_weighted6",
        MSS_GATE_MODE="bearish_only",
        MSS_BULLISH_THRESHOLD=65.0,
        MSS_BEARISH_THRESHOLD=35.0,
        IRS_TOP_N=10,
    )

    scenarios = build_selector_ablation_scenarios(cfg)

    assert [item.label for item in scenarios] == [
        "legacy_bof_baseline",
        "v0_01_dtt_bof_only",
        "v0_01_dtt_bof_plus_irs_score",
        "v0_01_dtt_bof_plus_irs_mss_score",
    ]
    assert [item.pipeline_mode for item in scenarios] == ["legacy", "dtt", "dtt", "dtt"]
    assert [item.dtt_variant for item in scenarios] == [
        "legacy_bof_baseline",
        "v0_01_dtt_bof_only",
        "v0_01_dtt_bof_plus_irs_score",
        "v0_01_dtt_bof_plus_irs_mss_score",
    ]
    assert [(item.enable_mss_gate, item.enable_irs_filter) for item in scenarios] == [
        (True, True),
        (False, False),
        (False, False),
        (False, False),
    ]
