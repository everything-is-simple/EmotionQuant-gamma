from __future__ import annotations

from src.backtest.ablation import build_selector_ablation_scenarios


def test_build_selector_ablation_scenarios_order_and_flags() -> None:
    scenarios = build_selector_ablation_scenarios(mss_thresholds=[65.0])

    assert [item.label for item in scenarios] == [
        "bof_baseline",
        "bof_plus_mss_t65",
        "bof_plus_mss_plus_irs_t65",
    ]
    assert [(item.enable_mss_gate, item.enable_irs_filter) for item in scenarios] == [
        (False, False),
        (True, False),
        (True, True),
    ]
    assert [item.mss_bullish_threshold for item in scenarios] == [65.0, 65.0, 65.0]
