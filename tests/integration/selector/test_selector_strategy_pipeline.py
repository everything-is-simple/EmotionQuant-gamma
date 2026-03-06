from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.data.store import Store
from src.selector.selector import select_candidates_frame
from src.strategy.strategy import generate_signals
from src.contracts import StockCandidate


def _seed_trade_calendar(store: Store, start: date, days: int) -> list[date]:
    rows = []
    dates = [start + timedelta(days=i) for i in range(days)]
    for i, trade_date in enumerate(dates):
        rows.append(
            {
                "date": trade_date,
                "is_trade_day": True,
                "prev_trade_day": dates[i - 1] if i > 0 else None,
                "next_trade_day": dates[i + 1] if i < len(dates) - 1 else None,
            }
        )
    store.bulk_upsert("l1_trade_calendar", pd.DataFrame(rows))
    return dates


def _seed_single_stock_history(store: Store, trade_days: list[date], signal_idx: int) -> None:
    store.bulk_upsert(
        "l1_stock_info",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "is_st": False,
                    "list_date": date(2010, 1, 1),
                    "effective_from": trade_days[0],
                }
            ]
        ),
    )

    l1_rows = []
    l2_rows = []
    for idx, trade_date in enumerate(trade_days):
        open_price = 10.0
        high = 10.2
        low = 9.95
        close = 10.0
        volume = 1_000.0

        if idx == signal_idx:
            open_price = 9.9
            high = 10.2
            low = 9.8
            close = 10.1
            volume = 1_300.0

        l1_rows.append(
            {
                "ts_code": "000001.SZ",
                "date": trade_date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "pre_close": 10.0,
                "volume": volume,
                "amount": 2e8,
                "pct_chg": 0.0,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 11.0,
                "down_limit": 9.0,
                "total_mv": 1e6,
                "circ_mv": 8e5,
            }
        )
        l2_rows.append(
            {
                "code": "000001",
                "date": trade_date,
                "adj_open": open_price,
                "adj_high": high,
                "adj_low": low,
                "adj_close": close,
                "volume": volume,
                "amount": 2e8,
                "pct_chg": 0.0,
                "ma5": 10.0,
                "ma10": 10.0,
                "ma20": 10.0,
                "ma60": 10.0,
                "volume_ma5": 1_000.0,
                "volume_ma20": 1_000.0,
                "volume_ratio": volume / 1_000.0,
            }
        )

    store.bulk_upsert("l1_stock_daily", pd.DataFrame(l1_rows))
    store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(l2_rows))


def test_select_candidates_to_generate_signals_pipeline(tmp_path) -> None:
    db = tmp_path / "selector_strategy_chain.duckdb"
    store = Store(db)
    trade_days = _seed_trade_calendar(store, date(2026, 1, 1), 30)
    signal_idx = 24
    _seed_single_stock_history(store, trade_days, signal_idx=signal_idx)

    cfg = Settings(
        ENABLE_MSS_GATE=False,
        ENABLE_IRS_FILTER=False,
        PAS_PATTERNS="bof",
        PAS_COMBINATION="ANY",
        PAS_MIN_HISTORY_DAYS=21,
        MIN_AMOUNT=1,
        MIN_LIST_DAYS=1,
    )

    calc_date = trade_days[signal_idx]
    candidates_df = select_candidates_frame(store, calc_date, cfg)
    candidates = [
        StockCandidate(code=str(row["code"]), industry=str(row["industry"]), score=float(row["score"]))
        for _, row in candidates_df.iterrows()
    ]
    signals = generate_signals(store, candidates, calc_date, cfg)

    assert len(candidates) == 1
    assert len(signals) == 1
    assert signals[0].pattern == "bof"
    assert signals[0].signal_date == calc_date

    stored = store.read_df("SELECT signal_id, code, pattern FROM l3_signals")
    assert len(stored) == 1
    assert stored.iloc[0]["code"] == "000001"
    assert stored.iloc[0]["pattern"] == "bof"
    store.close()
