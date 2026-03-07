from __future__ import annotations

from scripts.backtest.run_v001_plus_execution_sensitivity import (
    _conclude_scenario,
    _parse_scenarios,
)


def test_parse_scenarios_uses_default_matrix() -> None:
    scenarios = _parse_scenarios(None)

    assert [item.label for item in scenarios] == [
        "top1_pos1",
        "top1_pos2",
        "top2_pos1",
        "top2_pos2",
        "top50_pos10",
    ]
    assert scenarios[0].dtt_top_n == 1
    assert scenarios[0].max_positions == 1
    assert scenarios[-1].dtt_top_n == 50
    assert scenarios[-1].max_positions == 10


def test_conclude_scenario_detects_execution_constraint() -> None:
    conclusion = _conclude_scenario(
        {
            "rank_impact": {"rank_changed_count": 3, "selected_changed_count": 0},
            "buy_trade_impact": {"trade_set_changed_count": 1, "quantity_changed_count": 0},
            "maxpos_reject_impact": {"reject_set_changed_count": 0},
        }
    )

    assert conclusion.entered_execution_constraint is True
    assert "实际 BUY 成交集合" in conclusion.summary


def test_conclude_scenario_detects_rank_only_change() -> None:
    conclusion = _conclude_scenario(
        {
            "rank_impact": {"rank_changed_count": 4, "selected_changed_count": 0},
            "buy_trade_impact": {"trade_set_changed_count": 0, "quantity_changed_count": 0},
            "maxpos_reject_impact": {"reject_set_changed_count": 0},
        }
    )

    assert conclusion.entered_execution_constraint is False
    assert "只改变了名次" in conclusion.summary
