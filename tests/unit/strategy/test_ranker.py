from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy import strategy as strategy_module
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


class _StubDetector:
    def __init__(self, strengths: dict[str, float]):
        self._strengths = strengths

    def detect(self, code: str, asof_date: date, history: pd.DataFrame) -> Signal | None:
        strength = self._strengths.get(code)
        if strength is None:
            return None
        return Signal(
            signal_id=f"{code}_{asof_date.isoformat()}_bof",
            code=code,
            signal_date=asof_date,
            action="BUY",
            strength=strength,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=strength,
        )


def test_generate_signals_dtt_only_writes_top_n_formal_signal(tmp_path, monkeypatch) -> None:
    db = tmp_path / "strategy_dtt.duckdb"
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

    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        DTT_TOP_N=1,
        DTT_BOF_WEIGHT=0.5,
        DTT_IRS_WEIGHT=0.5,
        DTT_MSS_WEIGHT=0.0,
        DTT_SCORE_FILL=50.0,
        PAS_MIN_HISTORY_DAYS=21,
        PAS_EVAL_BATCH_SIZE=1,
    )
    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
        StockCandidate(code="000002", industry="电子", score=9.0, preselect_score=9.0),
    ]

    # 直接 stub 掉批量历史与 detector，专门验证 DTT 主线的排序落库边界。
    loader_calls: list[list[str]] = []

    def _stub_history_loader(_store, codes, _asof_date, _lookback_days):
        loader_calls.append(list(codes))
        return pd.DataFrame(
            [
                {
                    "code": code,
                    "date": calc_date - timedelta(days=offset),
                    "adj_low": 1.0,
                    "adj_close": 1.0,
                    "adj_open": 1.0,
                    "adj_high": 1.1,
                    "volume": 1.0,
                    "volume_ma20": 1.0,
                }
                for code in codes
                for offset in range(cfg.pas_min_history_days)
            ]
        )

    monkeypatch.setattr(strategy_module, "_load_candidate_histories_batch", _stub_history_loader)
    monkeypatch.setattr(
        strategy_module,
        "get_active_detectors",
        lambda _cfg: [_StubDetector({"000001": 0.6, "000002": 0.9})],
    )

    signals = strategy_module.generate_signals(
        store=store,
        candidates=candidates,
        asof_date=calc_date,
        config=cfg,
        run_id="unit_dtt_top_n",
    )

    assert len(signals) == 1
    assert signals[0].code == "000001"
    assert signals[0].final_rank == 1

    formal = store.read_df("SELECT code, pattern FROM l3_signals ORDER BY code ASC")
    ranked = store.read_df(
        """
        SELECT code, final_rank, selected
        FROM l3_signal_rank_exp
        WHERE run_id = ?
        ORDER BY final_rank ASC
        """,
        ("unit_dtt_top_n",),
    )
    assert formal["code"].tolist() == ["000001"]
    assert ranked["code"].tolist() == ["000001", "000002"]
    assert ranked["selected"].tolist() == [True, False]
    assert loader_calls == [["000001"], ["000002"]]
    store.close()


def test_dtt_irs_mss_variant_keeps_mss_in_sidecar_but_not_in_final_score(tmp_path) -> None:
    db = tmp_path / "ranker_mss_overlay.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)

    store.bulk_upsert(
        "l3_irs_daily",
        pd.DataFrame(
            [
                {"date": calc_date, "industry": "银行", "score": 1.0, "rank": 1, "rs_score": 1.0, "cf_score": 1.0},
            ]
        ),
    )
    store.bulk_upsert(
        "l3_mss_daily",
        pd.DataFrame([{"date": calc_date, "score": 20.0, "signal": "BEARISH"}]),
    )

    cfg_irs_only = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        DTT_TOP_N=10,
        DTT_BOF_WEIGHT=0.5,
        DTT_IRS_WEIGHT=0.3,
        DTT_MSS_WEIGHT=0.2,
        DTT_SCORE_FILL=50.0,
    )
    cfg_irs_mss = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_mss_score",
        DTT_TOP_N=10,
        DTT_BOF_WEIGHT=0.5,
        DTT_IRS_WEIGHT=0.3,
        DTT_MSS_WEIGHT=0.2,
        DTT_SCORE_FILL=50.0,
    )
    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
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
    ]

    rank_irs_only = build_dtt_rank_frame(store, signals, candidates, calc_date, "run_irs", cfg_irs_only)
    rank_irs_mss = build_dtt_rank_frame(store, signals, candidates, calc_date, "run_irs_mss", cfg_irs_mss)

    assert rank_irs_only.iloc[0]["final_score"] == rank_irs_mss.iloc[0]["final_score"]
    assert rank_irs_only.iloc[0]["mss_score"] == 50.0
    assert rank_irs_mss.iloc[0]["mss_score"] == 20.0
    store.close()
