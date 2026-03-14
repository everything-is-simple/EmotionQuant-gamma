from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.store import Store
from src.report.reporter import _compute_environment_breakdown, _pair_trades


def test_compute_environment_breakdown_uses_prev_trade_day_mss(tmp_path) -> None:
    db = tmp_path / "report_env.duckdb"
    store = Store(db)
    store.bulk_upsert(
        "l1_trade_calendar",
        pd.DataFrame(
            [
                {"date": date(2026, 1, 1), "is_trade_day": True, "prev_trade_day": None, "next_trade_day": date(2026, 1, 2)},
                {"date": date(2026, 1, 2), "is_trade_day": True, "prev_trade_day": date(2026, 1, 1), "next_trade_day": date(2026, 1, 3)},
                {"date": date(2026, 1, 3), "is_trade_day": True, "prev_trade_day": date(2026, 1, 2), "next_trade_day": None},
            ]
        ),
    )
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame(
            [
                {"date": date(2026, 1, 1), "score": 72.0, "signal": "BULLISH"},
                {"date": date(2026, 1, 2), "score": 28.0, "signal": "BEARISH"},
            ]
        ),
    )

    paired = pd.DataFrame(
        [
            {"code": "000001", "entry_date": date(2026, 1, 2), "exit_date": date(2026, 1, 2), "pattern": "bof", "quantity": 100, "pnl": 1000.0, "pnl_pct": 0.10},
            {"code": "000002", "entry_date": date(2026, 1, 3), "exit_date": date(2026, 1, 3), "pattern": "bof", "quantity": 100, "pnl": -500.0, "pnl_pct": -0.05},
        ]
    )

    breakdown = _compute_environment_breakdown(store, paired)

    assert breakdown["BULLISH"]["trade_count"] == 1.0
    assert breakdown["BULLISH"]["median_pnl_pct"] == 0.10
    assert breakdown["BULLISH"]["win_rate"] == 1.0
    assert breakdown["BEARISH"]["trade_count"] == 1.0
    assert breakdown["BEARISH"]["median_pnl_pct"] == -0.05
    assert breakdown["BEARISH"]["expected_value"] == -0.05
    store.close()


def test_pair_trades_preserves_position_and_partial_exit_metadata() -> None:
    trades = pd.DataFrame(
        [
            {
                "trade_id": "BUY_1_T",
                "order_id": "BUY_1",
                "code": "000001",
                "execute_date": date(2026, 1, 2),
                "action": "BUY",
                "price": 10.0,
                "quantity": 200,
                "fee": 5.0,
                "pattern": "bof",
                "is_paper": False,
                "position_id": "BUY_1",
                "exit_plan_id": None,
                "exit_leg_id": None,
                "exit_leg_seq": None,
                "exit_reason_code": None,
                "is_partial_exit": False,
                "remaining_qty_after": 200,
            },
            {
                "trade_id": "EXIT_1_L01_T",
                "order_id": "EXIT_1_L01",
                "code": "000001",
                "execute_date": date(2026, 1, 5),
                "action": "SELL",
                "price": 11.0,
                "quantity": 100,
                "fee": 5.0,
                "pattern": "bof",
                "is_paper": False,
                "position_id": "BUY_1",
                "exit_plan_id": "BUY_1_2026-01-04_trailing_stop",
                "exit_leg_id": "BUY_1_2026-01-04_trailing_stop_L01",
                "exit_leg_seq": 1,
                "exit_reason_code": "TRAILING_STOP",
                "is_partial_exit": True,
                "remaining_qty_after": 100,
            },
        ]
    )

    paired = _pair_trades(trades)

    assert len(paired) == 1
    row = paired.iloc[0]
    assert row["position_id"] == "BUY_1"
    assert row["entry_leg_id"] == "BUY_1_T"
    assert row["exit_leg_id"] == "BUY_1_2026-01-04_trailing_stop_L01"
    assert row["exit_leg_seq"] == 1
    assert row["exit_reason"] == "TRAILING_STOP"
    assert bool(row["is_partial_exit"]) is True
