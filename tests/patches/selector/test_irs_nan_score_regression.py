from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.store import Store
from src.selector.irs import compute_irs


def test_compute_irs_handles_nan_score_without_crash(tmp_path) -> None:
    """回归用例：IRS 在分数出现 NaN 时应兜底为 0 并正常生成 rank。"""
    db = tmp_path / "test.duckdb"
    store = Store(db)

    day = date(2026, 3, 4)
    store.bulk_upsert(
        "l2_industry_daily",
        pd.DataFrame(
            [
                {
                    "industry": "银行",
                    "date": day,
                    "pct_chg": None,
                    "amount": None,
                    "stock_count": 10,
                    "rise_count": 0,
                    "fall_count": 0,
                }
            ]
        ),
    )
    store.bulk_upsert(
        "l1_index_daily",
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SH",
                    "date": day,
                    "open": 3000.0,
                    "high": 3010.0,
                    "low": 2990.0,
                    "close": 3005.0,
                    "pre_close": 3000.0,
                    "pct_chg": 0.001,
                    "volume": 1e8,
                    "amount": 2e11,
                }
            ]
        ),
    )

    written = compute_irs(store, day, day)
    assert written == 1

    out = store.read_df("SELECT score, rank FROM l3_irs_daily WHERE date = ?", (day,))
    assert len(out) == 1
    assert float(out.iloc[0]["score"]) == 0.0
    assert int(out.iloc[0]["rank"]) == 1
    store.close()
