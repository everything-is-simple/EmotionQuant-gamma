from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


def _load_module():
    script_path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "backtest"
        / "run_v001_plus_mss_remediation_candidate_freeze.py"
    )
    spec = importlib.util.spec_from_file_location("mss_remediation_candidate_freeze", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 会读取模块注册名；这里先挂到 sys.modules，避免动态加载时类型归属丢失。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_summarize_side_only_trades_supports_merge_suffix_columns() -> None:
    module = _load_module()
    current_only = pd.DataFrame(
        [
            {
                "signal_id": "000001_2026-01-06_bof",
                "execute_date": "2026-01-06",
                "code": "000001",
                "pattern": "bof",
                "quantity_current": 100,
                "entry_pnl_current": 12.5,
                "entry_pnl_pct_current": 0.0125,
            }
        ]
    )
    candidate_only = pd.DataFrame(
        [
            {
                "signal_id": "000002_2026-01-07_bof",
                "execute_date": "2026-01-07",
                "code": "000002",
                "pattern": "bof",
                "quantity_candidate": 200,
                "entry_pnl_candidate": -8.0,
                "entry_pnl_pct_candidate": -0.008,
            }
        ]
    )
    signal_context = pd.DataFrame(
        [
            {
                "signal_id": "000001_2026-01-06_bof",
                "final_rank": 1,
                "final_score": 91.2,
                "risk_regime": "RISK_OFF",
                "overlay_reason": "STORED",
                "holdings_before": 5,
                "target_max_positions": 4,
                "effective_max_positions": 4,
                "decision_bucket": "CAPACITY",
                "decision_reason": "MAX_POSITIONS_REACHED",
            },
            {
                "signal_id": "000002_2026-01-07_bof",
                "final_rank": 2,
                "final_score": 88.6,
                "risk_regime": "RISK_OFF",
                "overlay_reason": "STORED",
                "holdings_before": 4,
                "target_max_positions": 4,
                "effective_max_positions": 5,
                "decision_bucket": "CAPACITY",
                "decision_reason": "ACCEPTED",
            },
        ]
    )

    current_summary = module._summarize_side_only_trades(
        "current",
        current_only,
        signal_context,
        quantity_col="quantity_current",
        entry_pnl_col="entry_pnl_current",
        entry_pnl_pct_col="entry_pnl_pct_current",
    )
    candidate_summary = module._summarize_side_only_trades(
        "candidate",
        candidate_only,
        signal_context,
        quantity_col="quantity_candidate",
        entry_pnl_col="entry_pnl_candidate",
        entry_pnl_pct_col="entry_pnl_pct_candidate",
    )

    assert current_summary["trade_count"] == 1
    assert current_summary["entry_pnl_total"] == 12.5
    assert current_summary["samples"][0]["quantity"] == 100
    assert current_summary["samples"][0]["effective_max_positions"] == 4

    assert candidate_summary["trade_count"] == 1
    assert candidate_summary["entry_pnl_total"] == -8.0
    assert candidate_summary["samples"][0]["quantity"] == 200
    assert candidate_summary["samples"][0]["effective_max_positions"] == 5
