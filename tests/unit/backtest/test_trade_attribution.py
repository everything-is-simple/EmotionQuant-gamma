from __future__ import annotations

import pandas as pd

from scripts.backtest.run_v001_plus_trade_attribution import _build_date_payload


def test_build_date_payload_tolerates_empty_reject_frames_with_mixed_date_dtypes() -> None:
    execute_date = "2026-02-04"
    left_attr = pd.DataFrame(
        {
            "signal_id": ["002517_2026-02-03_bof"],
            "execute_date": [execute_date],
            "code": ["002517"],
            "pattern": ["bof"],
            "quantity": [1600],
            "price": [0.0],
            "fee": [0.0],
            "entry_pnl": [371.5763],
            "entry_pnl_pct": [0.010178],
        }
    )
    right_attr = pd.DataFrame(
        columns=["signal_id", "execute_date", "code", "pattern", "quantity", "price", "fee", "entry_pnl", "entry_pnl_pct"]
    )
    left_rejects = pd.DataFrame(columns=["signal_id", "execute_date", "code", "reject_reason"])
    right_rejects = pd.DataFrame(
        {
            "signal_id": pd.Series([], dtype="object"),
            "execute_date": pd.to_datetime(pd.Series([], dtype="datetime64[ns]")),
            "code": pd.Series([], dtype="object"),
            "reject_reason": pd.Series([], dtype="object"),
        }
    )

    payload = _build_date_payload(
        execute_date=execute_date,
        left_variant="legacy_bof_baseline",
        right_variant="v0_01_dtt_pattern_plus_irs_mss_score_carryover_buffer1",
        left_attr=left_attr,
        right_attr=right_attr,
        left_rejects=left_rejects,
        right_rejects=right_rejects,
    )

    assert payload["execute_date"] == execute_date
    assert len(payload["trade_set_swaps"]) == 1
    assert payload["maxpos_reject_swaps"] == []
