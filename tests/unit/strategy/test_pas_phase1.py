from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.pas_bpb import BpbDetector
from src.strategy.pas_cpb import CpbDetector
from src.strategy.pas_pb import PbDetector
from src.strategy.pas_tst import TstDetector
from src.strategy.strategy import _combine_signals, generate_signals


def _frame(rows: list[dict[str, float]], start: date) -> pd.DataFrame:
    payload = []
    for offset, row in enumerate(rows):
        payload.append(
            {
                "date": start + timedelta(days=offset),
                "adj_open": row["adj_open"],
                "adj_high": row["adj_high"],
                "adj_low": row["adj_low"],
                "adj_close": row["adj_close"],
                "volume": row.get("volume", 1000.0),
                "volume_ma20": row.get("volume_ma20", 1000.0),
            }
        )
    return pd.DataFrame(payload)


def _bpb_history() -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    rows.extend(
        [
            {
                "adj_open": 9.5,
                "adj_high": 10.0,
                "adj_low": 9.0,
                "adj_close": 9.5,
            }
            for _ in range(20)
        ]
    )
    rows.extend(
        [
            {"adj_open": 10.15, "adj_high": 10.25, "adj_low": 10.12, "adj_close": 10.20, "volume": 1300.0},
            {"adj_open": 10.20, "adj_high": 10.30, "adj_low": 10.18, "adj_close": 10.25},
            {"adj_open": 10.22, "adj_high": 10.35, "adj_low": 10.20, "adj_close": 10.18},
            {"adj_open": 10.18, "adj_high": 10.28, "adj_low": 10.16, "adj_close": 10.18},
            {"adj_open": 10.17, "adj_high": 10.22, "adj_low": 10.15, "adj_close": 10.16},
            {"adj_open": 10.25, "adj_high": 10.50, "adj_low": 10.20, "adj_close": 10.40, "volume": 1500.0},
        ]
    )
    return _frame(rows, date(2026, 1, 1))


def _pb_history() -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    rows.extend(
        [
            {
                "adj_open": 9.5,
                "adj_high": 10.0,
                "adj_low": 9.0,
                "adj_close": 9.4,
            }
            for _ in range(20)
        ]
    )
    rows.extend(
        [
            {
                "adj_open": 10.1,
                "adj_high": 10.8,
                "adj_low": 9.8,
                "adj_close": 10.4,
            }
            for _ in range(15)
        ]
    )
    rows.extend(
        [
            {"adj_open": 10.30, "adj_high": 10.55, "adj_low": 10.10, "adj_close": 10.35},
            {"adj_open": 10.28, "adj_high": 10.60, "adj_low": 10.15, "adj_close": 10.32},
            {"adj_open": 10.25, "adj_high": 10.58, "adj_low": 10.20, "adj_close": 10.30},
            {"adj_open": 10.24, "adj_high": 10.52, "adj_low": 10.25, "adj_close": 10.28},
            {"adj_open": 10.22, "adj_high": 10.50, "adj_low": 10.30, "adj_close": 10.26},
            {"adj_open": 10.40, "adj_high": 10.80, "adj_low": 10.35, "adj_close": 10.65, "volume": 1350.0},
        ]
    )
    return _frame(rows, date(2026, 1, 1))


def _tst_history() -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    rows.extend(
        [
            {
                "adj_open": 10.20,
                "adj_high": 10.80,
                "adj_low": 9.80,
                "adj_close": 10.30,
            }
            for _ in range(55)
        ]
    )
    rows.extend(
        [
            {"adj_open": 10.00, "adj_high": 10.05, "adj_low": 9.95, "adj_close": 10.00},
            {"adj_open": 9.98, "adj_high": 10.04, "adj_low": 9.96, "adj_close": 9.99},
            {"adj_open": 9.99, "adj_high": 10.03, "adj_low": 9.97, "adj_close": 10.00},
            {"adj_open": 10.00, "adj_high": 10.05, "adj_low": 9.98, "adj_close": 10.02},
            {"adj_open": 10.01, "adj_high": 10.02, "adj_low": 9.96, "adj_close": 10.00},
            {"adj_open": 10.00, "adj_high": 10.25, "adj_low": 9.84, "adj_close": 10.20, "volume": 1250.0},
        ]
    )
    return _frame(rows, date(2026, 1, 1))


def _cpb_history() -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    rows.extend(
        [
            {
                "adj_open": 10.10,
                "adj_high": 10.50,
                "adj_low": 9.80,
                "adj_close": 10.10,
            }
            for _ in range(20)
        ]
    )
    lows = [9.90, 9.92, 9.94, 9.96, 9.98, 10.00, 9.91, 9.93, 9.95, 9.97] * 2
    for low in lows:
        rows.append(
            {
                "adj_open": 10.15,
                "adj_high": 10.60,
                "adj_low": low,
                "adj_close": 10.20,
            }
        )
    rows.append({"adj_open": 10.35, "adj_high": 10.85, "adj_low": 10.30, "adj_close": 10.75, "volume": 1500.0})
    return _frame(rows, date(2026, 1, 1))


def test_phase1_detectors_trigger_expected_patterns() -> None:
    cfg = Settings()
    start = date(2026, 1, 1)

    bpb_signal, _ = BpbDetector(cfg).evaluate("000001", start + timedelta(days=25), _bpb_history())
    pb_signal, _ = PbDetector(cfg).evaluate("000001", start + timedelta(days=40), _pb_history())
    tst_signal, _ = TstDetector(cfg).evaluate("000001", start + timedelta(days=60), _tst_history())
    cpb_signal, _ = CpbDetector(cfg).evaluate("000001", start + timedelta(days=40), _cpb_history())

    assert bpb_signal is not None
    assert bpb_signal.pattern == "bpb"
    assert pb_signal is not None
    assert pb_signal.pattern == "pb"
    assert tst_signal is not None
    assert tst_signal.pattern == "tst"
    assert cpb_signal is not None
    assert cpb_signal.pattern == "cpb"


def test_combine_signals_breaks_strength_ties_by_pattern_priority() -> None:
    signal_date = date(2026, 1, 8)
    bpb = Signal(
        signal_id="000001_2026-01-08_bpb",
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.80,
        pattern="bpb",
        reason_code="PAS_BPB",
        pattern_strength=0.80,
    )
    tst = Signal(
        signal_id="000001_2026-01-08_tst",
        code="000001",
        signal_date=signal_date,
        action="BUY",
        strength=0.80,
        pattern="tst",
        reason_code="PAS_TST",
        pattern_strength=0.80,
    )

    merged = _combine_signals(
        [tst, bpb],
        active_detector_count=2,
        mode="ANY",
        pattern_priority=["bpb", "pb", "tst", "cpb", "bof"],
    )

    assert [signal.pattern for signal in merged] == ["bpb"]


def test_generate_signals_writes_quality_and_reference_into_pas_trace(tmp_path) -> None:
    db = tmp_path / "pas_phase1_trace.duckdb"
    store = Store(db)
    try:
        history = _bpb_history().copy()
        history.insert(0, "code", "000001")
        history["amount"] = 1.0
        history["pct_chg"] = 0.0
        history["ma5"] = 10.0
        history["ma10"] = 10.0
        history["ma20"] = 10.0
        history["ma60"] = 10.0
        history["volume_ma5"] = 1000.0
        history["volume_ratio"] = history["volume"] / history["volume_ma20"]
        store.bulk_upsert("l2_stock_adj_daily", history)

        calc_date = date(2026, 1, 26)
        cfg = Settings(
            PIPELINE_MODE="dtt",
            DTT_VARIANT="v0_01_dtt_pattern_only",
            DTT_TOP_N=10,
            PAS_PATTERNS="bpb",
            PAS_QUALITY_ENABLED=True,
            PAS_REFERENCE_ENABLED=True,
            PAS_EVAL_BATCH_SIZE=1,
        )
        candidates = [StockCandidate(code="000001", industry="银行", score=10.0, preselect_score=10.0)]

        signals = generate_signals(store, candidates, calc_date, cfg, run_id="pas_phase1_trace")
        trace = store.get_pas_trigger_trace("pas_phase1_trace", calc_date, "000001", "bpb")

        assert len(signals) == 1
        assert signals[0].pattern == "bpb"
        assert trace is not None
        assert trace["selected_pattern"] == "bpb"
        assert trace["pattern_quality_score"] is not None
        assert trace["entry_ref"] is not None
        assert trace["stop_ref"] is not None
        assert trace["target_ref"] is not None
        assert trace["risk_reward_ref"] is not None
        assert trace["registry_run_label"] == "BPB + quality"
    finally:
        store.close()
