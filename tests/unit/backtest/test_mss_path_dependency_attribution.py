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
        / "run_v001_plus_mss_path_dependency_attribution.py"
    )
    spec = importlib.util.spec_from_file_location("mss_path_dependency_attribution", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 会读取模块注册名；这里先挂到 sys.modules，避免动态加载时丢失类型归属。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_holdings_snapshots_uses_pre_trade_state() -> None:
    module = _load_module()
    trades = pd.DataFrame(
        [
            {"execute_date": "2026-01-30", "action": "BUY", "code": "000001", "quantity": 100},
            {"execute_date": "2026-02-02", "action": "BUY", "code": "000002", "quantity": 100},
            {"execute_date": "2026-02-06", "action": "SELL", "code": "000001", "quantity": 100},
        ]
    )

    snapshots = module._build_holdings_snapshots(
        trades,
        focus_dates=["2026-01-30", "2026-02-02", "2026-02-06", "2026-02-09"],
    )

    assert snapshots["2026-01-30"] == []
    assert snapshots["2026-02-02"] == ["000001"]
    assert snapshots["2026-02-06"] == ["000001", "000002"]
    assert snapshots["2026-02-09"] == ["000002"]


def test_find_delayed_entry_returns_first_later_buy_for_same_code() -> None:
    module = _load_module()
    buy_attr = pd.DataFrame(
        [
            {
                "signal_id": "000001_2026-01-30_bof",
                "execute_date": "2026-01-30",
                "code": "000001",
                "quantity": 100,
                "entry_pnl": 10.0,
                "entry_pnl_pct": 0.01,
            },
            {
                "signal_id": "000001_2026-02-06_bof",
                "execute_date": "2026-02-06",
                "code": "000001",
                "quantity": 200,
                "entry_pnl": -5.0,
                "entry_pnl_pct": -0.005,
            },
            {
                "signal_id": "000001_2026-02-09_bof",
                "execute_date": "2026-02-09",
                "code": "000001",
                "quantity": 300,
                "entry_pnl": 8.0,
                "entry_pnl_pct": 0.008,
            },
        ]
    )

    delayed = module._find_delayed_entry("000001", "2026-01-30", buy_attr)

    assert delayed is not None
    assert delayed["execute_date"] == "2026-02-06"
    assert delayed["signal_id"] == "000001_2026-02-06_bof"
    assert delayed["quantity"] == 200
