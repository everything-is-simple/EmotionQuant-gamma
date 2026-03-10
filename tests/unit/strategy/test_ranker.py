from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

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


def test_generate_signals_dtt_requires_run_id(tmp_path, monkeypatch) -> None:
    db = tmp_path / "strategy_requires_run_id.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        PAS_MIN_HISTORY_DAYS=21,
    )
    candidates = [StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0)]

    monkeypatch.setattr(
        strategy_module,
        "get_active_detectors",
        lambda _cfg: [_StubDetector({"000001": 0.6})],
    )
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

    with pytest.raises(ValueError, match="run_id"):
        strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id=None)
    store.close()


def test_pas_trigger_trace_persists_triggered_and_not_triggered_candidates(tmp_path, monkeypatch) -> None:
    db = tmp_path / "pas_trace.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_only",
        DTT_TOP_N=10,
        PAS_MIN_HISTORY_DAYS=21,
        PAS_EVAL_BATCH_SIZE=2,
    )
    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
        StockCandidate(code="000002", industry="电子", score=9.0, preselect_score=9.0),
    ]

    class _TraceableDetector:
        name = "bof"

        def evaluate(self, code: str, asof_date: date, history: pd.DataFrame):
            signal_id = f"{code}_{asof_date.isoformat()}_bof"
            if code == "000001":
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
            return None, {
                "signal_id": signal_id,
                "pattern": "bof",
                "triggered": False,
                "skip_reason": "NO_BREAK",
                "reason_code": "PAS_BOF",
            }

    monkeypatch.setattr(strategy_module, "get_active_detectors", lambda _cfg: [_TraceableDetector()])
    monkeypatch.setattr(
        strategy_module,
        "_load_candidate_histories_batch",
        lambda *_args, **_kwargs: pd.DataFrame(
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
                for code in ["000001", "000002"]
                for offset in range(cfg.pas_min_history_days)
            ]
        ),
    )

    strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id="pas_trace")
    trace = store.read_df(
        """
        SELECT code, candidate_rank, detected, detect_reason, selected_pattern, pattern_strength, skip_reason
        FROM pas_trigger_trace_exp
        WHERE run_id = ?
        ORDER BY code ASC
        """,
        ("pas_trace",),
    )

    assert trace["code"].tolist() == ["000001", "000002"]
    assert trace["candidate_rank"].tolist() == [1, 2]
    assert trace["detected"].tolist() == [True, False]
    assert trace.iloc[0]["selected_pattern"] == "bof"
    assert pd.isna(trace.iloc[1]["selected_pattern"])
    assert trace.iloc[0]["pattern_strength"] == 0.7
    assert pd.isna(trace.iloc[1]["pattern_strength"])
    assert pd.isna(trace.iloc[0]["detect_reason"])
    assert trace.iloc[1]["detect_reason"] == "NO_BREAK"
    assert pd.isna(trace.iloc[0]["skip_reason"])
    assert trace.iloc[1]["skip_reason"] == "NO_BREAK"
    store.close()


def test_irs_trace_marks_missing_industry_scores_as_fill(tmp_path) -> None:
    db = tmp_path / "irs_trace.duckdb"
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

    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_plus_irs_score",
        DTT_TOP_N=10,
        DTT_SCORE_FILL=50.0,
    )
    candidates = [
        StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0),
        StockCandidate(code="000002", industry="有色", score=9.0, preselect_score=9.0),
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
            strength=0.55,
            pattern="bof",
            reason_code="PAS_BOF",
            bof_strength=0.55,
        ),
    ]

    build_dtt_rank_frame(store, signals, candidates, calc_date, "irs_trace", cfg)
    trace = store.read_df(
        """
        SELECT code, trace_scope, status, signal_irs_score
        FROM irs_industry_trace_exp
        WHERE run_id = ?
        ORDER BY code ASC
        """,
        ("irs_trace",),
    )

    assert trace["code"].tolist() == ["000001", "000002"]
    assert trace["trace_scope"].tolist() == ["SIGNAL_ATTACH", "SIGNAL_ATTACH"]
    assert trace["status"].tolist() == ["NORMAL", "FILL_NO_DAILY_SCORE"]
    assert trace.iloc[0]["signal_irs_score"] == 100.0
    assert trace.iloc[1]["signal_irs_score"] == 50.0
    store.close()


def test_pas_trace_persists_quality_and_reference_sidecar_for_selected_pattern(tmp_path, monkeypatch) -> None:
    db = tmp_path / "pas_trace_sidecar.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_only",
        DTT_TOP_N=10,
        PAS_PATTERNS="bpb",
        PAS_PATTERN_PRIORITY="bpb,pb,tst,cpb,bof",
        PAS_MIN_HISTORY_DAYS=30,
        PAS_EVAL_BATCH_SIZE=1,
    )
    candidates = [StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0)]

    class _BpbTraceableDetector:
        name = "bpb"

        def evaluate(self, code: str, asof_date: date, history: pd.DataFrame):
            signal_id = f"{code}_{asof_date.isoformat()}_bpb"
            signal = Signal(
                signal_id=signal_id,
                code=code,
                signal_date=asof_date,
                action="BUY",
                strength=0.82,
                pattern="bpb",
                reason_code="PAS_BPB",
            )
            return signal, {
                "signal_id": signal_id,
                "pattern": "bpb",
                "triggered": True,
                "reason_code": "PAS_BPB",
                "history_days": 40,
                "required_window": 26,
                "required_mult": 1.2,
                "today_low": 10.2,
                "today_close": 10.6,
                "today_open": 10.3,
                "today_high": 10.8,
                "volume": 1400.0,
                "volume_ma20": 1000.0,
                "volume_ratio": 1.4,
                "breakout_ref": 10.0,
                "breakout_peak": 10.5,
                "pullback_low": 10.15,
                "confirm_strength": 0.6,
                "support_hold_score": 0.8,
                "depth_score": 0.9,
                "strength": 0.82,
            }

    monkeypatch.setattr(strategy_module, "get_active_detectors", lambda _cfg: [_BpbTraceableDetector()])
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

    strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id="pas_trace_sidecar")
    trace = store.read_df(
        """
        SELECT selected_pattern, pattern_quality_score, entry_ref, stop_ref, target_ref,
               risk_reward_ref, failure_handling_tag, pattern_group, registry_run_label,
               quality_status, reference_status
        FROM pas_trigger_trace_exp
        WHERE run_id = ? AND code = ? AND detector = ?
        """,
        ("pas_trace_sidecar", "000001", "bpb"),
    )

    assert trace.iloc[0]["selected_pattern"] == "bpb"
    assert trace.iloc[0]["pattern_quality_score"] > 0
    assert trace.iloc[0]["entry_ref"] == 10.6
    assert trace.iloc[0]["stop_ref"] > 0
    assert trace.iloc[0]["target_ref"] >= 10.6
    assert trace.iloc[0]["risk_reward_ref"] > 0
    assert trace.iloc[0]["failure_handling_tag"] is not None
    assert trace.iloc[0]["pattern_group"] == "BREAKOUT_PULLBACK"
    assert trace.iloc[0]["registry_run_label"] == "BPB + quality"
    assert trace.iloc[0]["quality_status"] == "OK"
    assert trace.iloc[0]["reference_status"] == "OK"
    store.close()


def test_pas_trace_bof_sidecar_keeps_reference_and_quality_queryable(tmp_path, monkeypatch) -> None:
    db = tmp_path / "pas_trace_bof_sidecar.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 8)
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT="v0_01_dtt_bof_only",
        DTT_TOP_N=10,
        PAS_PATTERNS="bof",
        PAS_MIN_HISTORY_DAYS=30,
        PAS_EVAL_BATCH_SIZE=1,
    )
    candidates = [StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0)]

    history_rows: list[dict[str, object]] = []
    start_date = calc_date - timedelta(days=29)
    for offset in range(29):
        history_rows.append(
            {
                "code": "000001",
                "date": start_date + timedelta(days=offset),
                "adj_low": 10.0 if offset >= 9 else 10.2,
                "adj_close": 10.4,
                "adj_open": 10.3,
                "adj_high": 12.0 if offset == 20 else 10.8,
                "volume": 900.0,
                "volume_ma20": 1000.0,
            }
        )
    history_rows.append(
        {
            "code": "000001",
            "date": calc_date,
            "adj_low": 9.7,
            "adj_close": 10.5,
            "adj_open": 9.9,
            "adj_high": 10.8,
            "volume": 1500.0,
            "volume_ma20": 1000.0,
        }
    )

    monkeypatch.setattr(
        strategy_module,
        "_load_candidate_histories_batch",
        lambda *_args, **_kwargs: pd.DataFrame(history_rows),
    )

    strategy_module.generate_signals(store, candidates, calc_date, cfg, run_id="pas_trace_bof_sidecar")
    trace = store.read_df(
        """
        SELECT selected_pattern, pattern_quality_score, entry_ref, stop_ref, target_ref,
               risk_reward_ref, quality_status, reference_status
        FROM pas_trigger_trace_exp
        WHERE run_id = ? AND code = ? AND detector = ?
        """,
        ("pas_trace_bof_sidecar", "000001", "bof"),
    )

    assert trace.iloc[0]["selected_pattern"] == "bof"
    assert trace.iloc[0]["pattern_quality_score"] > 0
    assert trace.iloc[0]["entry_ref"] == 10.5
    assert trace.iloc[0]["stop_ref"] > 0
    assert trace.iloc[0]["target_ref"] >= 12.0
    assert trace.iloc[0]["risk_reward_ref"] > 0
    assert trace.iloc[0]["quality_status"] == "OK"
    assert trace.iloc[0]["reference_status"] == "OK"
    store.close()
