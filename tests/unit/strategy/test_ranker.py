from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.ranker import build_dtt_rank_frame, materialize_ranked_signals


def test_dtt_ranker_orders_by_final_score_and_marks_selected(tmp_path) -> None:
    db = tmp_path / "ranker.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)

    store.bulk_upsert(
        "l3_irs_daily",
        pd.DataFrame(
            [
                {"date": calc_date, "industry": "银行", "score": 1.0, "rank": 1, "rs_score": 1.0, "cf_score": 1.0},
                {"date": calc_date, "industry": "电子", "score": 0.5, "rank": 2, "rs_score": 0.5, "cf_score": 0.5},
            ]
        ),
    )
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame([{"date": calc_date, "score": 80.0, "signal": "BULLISH"}]),
    )

    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        DTT_TOP_N=1,
        DTT_BOF_WEIGHT=0.5,
        DTT_IRS_WEIGHT=0.3,
        DTT_MSS_WEIGHT=0.2,
        DTT_SCORE_FILL=50.0,
    )
    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
        StockCandidate(code="000002", industry="电子", score=9.0, preselect_score=9.0),
    ]
    signals = [
        Signal(
            signal_id="000001_2026-01-08_bof",
            code="000001",
            signal_date=calc_date,
            action="BUY",
            strength=0.60,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=0.60,
        ),
        Signal(
            signal_id="000002_2026-01-08_bof",
            code="000002",
            signal_date=calc_date,
            action="BUY",
            strength=0.90,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=0.90,
        ),
    ]

    rank_frame = build_dtt_rank_frame(store, signals, candidates, calc_date, "test_run", cfg)
    ranked_signals = materialize_ranked_signals(signals, rank_frame)

    assert rank_frame["signal_id"].tolist() == [
        "000001_2026-01-08_bof",
        "000002_2026-01-08_bof",
    ]
    assert rank_frame["selected"].tolist() == [True, False]
    assert len(ranked_signals) == 1
    assert ranked_signals[0].code == "000001"
    assert ranked_signals[0].final_rank == 1
    store.close()
