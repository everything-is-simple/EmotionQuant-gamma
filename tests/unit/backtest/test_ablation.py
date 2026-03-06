from __future__ import annotations

from src.backtest.ablation import build_selector_ablation_scenarios


def test_build_selector_ablation_scenarios_order_and_flags() -> None:
    scenarios = build_selector_ablation_scenarios(
        mss_thresholds=[65.0],
        gate_modes=["bearish_only", "soft_gate"],
        irs_top_ns=[10, 15],
        mss_variants=["zscore_weighted6", "percentile_weighted6"],
    )

    assert [item.label for item in scenarios] == [
        "bof_baseline",
        "bof_plus_mss_zscore_weighted6_bearish_only_t65",
        "bof_plus_mss_plus_irs_zscore_weighted6_bearish_only_t65_top10",
        "bof_plus_mss_plus_irs_zscore_weighted6_bearish_only_t65_top15",
        "bof_plus_mss_zscore_weighted6_soft_gate_t65",
        "bof_plus_mss_plus_irs_zscore_weighted6_soft_gate_t65_top10",
        "bof_plus_mss_plus_irs_zscore_weighted6_soft_gate_t65_top15",
        "bof_plus_mss_percentile_weighted6_bearish_only_t65",
        "bof_plus_mss_plus_irs_percentile_weighted6_bearish_only_t65_top10",
        "bof_plus_mss_plus_irs_percentile_weighted6_bearish_only_t65_top15",
        "bof_plus_mss_percentile_weighted6_soft_gate_t65",
        "bof_plus_mss_plus_irs_percentile_weighted6_soft_gate_t65_top10",
        "bof_plus_mss_plus_irs_percentile_weighted6_soft_gate_t65_top15",
    ]
    assert [(item.enable_mss_gate, item.enable_irs_filter) for item in scenarios] == [
        (False, False),
        (True, False),
        (True, True),
        (True, True),
        (True, False),
        (True, True),
        (True, True),
        (True, False),
        (True, True),
        (True, True),
        (True, False),
        (True, True),
        (True, True),
    ]
    assert [item.mss_bullish_threshold for item in scenarios] == [65.0] * 13
    assert [item.mss_variant for item in scenarios] == [
        "zscore_weighted6",
        "zscore_weighted6",
        "zscore_weighted6",
        "zscore_weighted6",
        "zscore_weighted6",
        "zscore_weighted6",
        "zscore_weighted6",
        "percentile_weighted6",
        "percentile_weighted6",
        "percentile_weighted6",
        "percentile_weighted6",
        "percentile_weighted6",
        "percentile_weighted6",
    ]
    assert [item.mss_gate_mode for item in scenarios] == [
        "disabled",
        "bearish_only",
        "bearish_only",
        "bearish_only",
        "soft_gate",
        "soft_gate",
        "soft_gate",
        "bearish_only",
        "bearish_only",
        "bearish_only",
        "soft_gate",
        "soft_gate",
        "soft_gate",
    ]
    assert [item.irs_top_n for item in scenarios] == [10, 10, 10, 15, 10, 10, 15, 10, 10, 15, 10, 10, 15]
