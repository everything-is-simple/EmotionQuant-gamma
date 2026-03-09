from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

import src.strategy.strategy as strategy_module
from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.ranker import build_dtt_rank_frame


class _TraceableDetector:
    name = "bof"

    def evaluate(self, code: str, asof_date: date, history: pd.DataFrame):
        signal_id = f"{code}_{asof_date.isoformat()}_bof"
        signal = Signal(
            signal_id=signal_id,
            code=code,
            signal_date=asof_date,
            action="BUY",
            strength=0.7,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=0.7,
        )
        return signal, {
            "signal_id": signal_id,
            "pattern": "bof",
            "triggered": True,
            "skip_reason": None,
            "reason_code": "PAS_BOF",
            "strength": 0.7,
            "bof_strength": 0.7,
        }


def test_pas_trace_signal_id_stays_stable_across_runs(tmp_path, monkeypatch) -> None:
    db = tmp_path / "pas_trace_patch.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_only",
        DTT_TOP_N=10,
        PAS_MIN_HISTORY_DAYS=21,
        PAS_EVAL_BATCH_SIZE=1,
    )
    candidates = [StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0)]

    monkeypatch.setattr(strategy_module, "get_active_detectors", lambda _cfg: [_TraceableDetector()])
    monkeypatch.setattr(
        strategy_module,
        "_load_candidate_histories_batch",
        lambda *_args, **_kwargs: pd.DataFrame(
            [
                {
                    "code": "000001",
                    "date": calc_date - timedelta(days=offset),
                    "adj_low": 1.0,
                    "adj_close": 1.0,
                    "adj_open": 1.0,
                    "adj_high": 1.1,
                    "volume": 1.0,
                    "volume_ma20": 1.0,
                }
                for offset in range(cfg.pas_min_history_days)
            ]
        ),
    )

    strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id="run_a")
    strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id="run_b")

    trace_a = store.get_pas_trigger_trace("run_a", calc_date, "000001", "bof")
    trace_b = store.get_pas_trigger_trace("run_b", calc_date, "000001", "bof")

    assert trace_a is not None
    assert trace_b is not None
    assert trace_a["signal_id"] == trace_b["signal_id"] == "000001_2026-01-08_bof"
    assert trace_a["candidate_rank"] == trace_b["candidate_rank"] == 1
    assert trace_a["selected_pattern"] == trace_b["selected_pattern"] == "bof"
    assert trace_a["detected"] == trace_b["detected"] is True
    store.close()


def test_irs_trace_status_covers_disabled_unknown_missing_and_normal(tmp_path) -> None:
    db = tmp_path / "irs_trace_patch.duckdb"
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

    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
        StockCandidate(code="000002", industry="未知", score=9.0, preselect_score=9.0),
        StockCandidate(code="000003", industry="有色", score=8.0, preselect_score=8.0),
    ]
    signals = [
        Signal(
            signal_id=f"{code}_{calc_date.isoformat()}_bof",
            code=code,
            signal_date=calc_date,
            action="BUY",
            strength=0.60,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=0.60,
        )
        for code in ["000001", "000002", "000003"]
    ]

    enabled_cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        DTT_TOP_N=10,
        DTT_SCORE_FILL=50.0,
    )
    disabled_cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_only",
        DTT_TOP_N=10,
        DTT_SCORE_FILL=50.0,
    )

    build_dtt_rank_frame(store, signals, candidates, calc_date, "irs_enabled", enabled_cfg)
    build_dtt_rank_frame(store, signals, candidates, calc_date, "irs_disabled", disabled_cfg)

    enabled = store.read_df(
        "SELECT code, status FROM irs_industry_trace_exp WHERE run_id = ? ORDER BY code ASC",
        ("irs_enabled",),
    )
    sample = store.read_df("SELECT * FROM irs_industry_trace_exp WHERE run_id = ? LIMIT 1", ("irs_enabled",))
    disabled = store.get_irs_industry_trace("irs_disabled", f"000001_{calc_date.isoformat()}_bof")

    assert "status" in sample.columns
    assert "irs_status" not in sample.columns
    assert enabled["status"].tolist() == ["NORMAL", "FILL_UNKNOWN_INDUSTRY", "FILL_NO_DAILY_SCORE"]
    assert disabled is not None
    assert disabled["status"] == "DISABLED"
    store.close()
