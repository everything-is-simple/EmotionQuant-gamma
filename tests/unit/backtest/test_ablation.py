from __future__ import annotations

from src.backtest.ablation import build_selector_ablation_scenarios


def test_build_selector_ablation_scenarios_order_and_flags() -> None:
    scenarios = build_selector_ablation_scenarios()

    assert [item.label for item in scenarios] == [
        "bof_baseline",
        "bof_plus_mss",
        "bof_plus_mss_plus_irs",
    ]
    assert [(item.enable_mss_gate, item.enable_irs_filter) for item in scenarios] == [
        (False, False),
        (True, False),
        (True, True),
    ]
