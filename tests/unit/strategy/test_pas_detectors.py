from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_bpb import BpbDetector
from src.strategy.pas_cpb import CpbDetector
from src.strategy.pas_pb import PbDetector
from src.strategy.pas_tst import TstDetector
from src.strategy.registry import get_active_detectors
from src.strategy.strategy import _combine_signals


def _frame(rows: list[dict[str, float | date]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_bpb_detector_triggers_on_breakout_pullback_confirmation() -> None:
    cfg = Settings(PAS_PATTERNS="bpb", PAS_BPB_VOLUME_MULT=1.2)
    detector = BpbDetector(cfg)
    d0 = date(2026, 1, 1)
    rows: list[dict[str, float | date]] = []
    for i in range(20):
        rows.append(
            {
                "date": d0 + timedelta(days=i),
                "adj_open": 9.8,
                "adj_high": 10.0,
                "adj_low": 9.5,
                "adj_close": 9.9,
                "volume": 1000.0,
                "volume_ma20": 900.0,
            }
        )
    rows.extend(
        [
            {"date": d0 + timedelta(days=20), "adj_open": 10.0, "adj_high": 10.5, "adj_low": 10.2, "adj_close": 10.3, "volume": 1300.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=21), "adj_open": 10.3, "adj_high": 10.4, "adj_low": 10.18, "adj_close": 10.25, "volume": 1050.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=22), "adj_open": 10.2, "adj_high": 10.35, "adj_low": 10.15, "adj_close": 10.2, "volume": 1000.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=23), "adj_open": 10.18, "adj_high": 10.3, "adj_low": 10.12, "adj_close": 10.18, "volume": 980.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=24), "adj_open": 10.18, "adj_high": 10.28, "adj_low": 10.16, "adj_close": 10.22, "volume": 970.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=25), "adj_open": 10.28, "adj_high": 10.7, "adj_low": 10.25, "adj_close": 10.56, "volume": 1400.0, "volume_ma20": 1000.0},
        ]
    )

    signal, trace = detector.evaluate("000001", d0 + timedelta(days=25), _frame(rows))

    assert signal is not None
    assert signal.pattern == "bpb"
    assert signal.reason_code == "PAS_BPB"
    assert trace["triggered"] is True
    assert trace["breakout_ref"] == 10.0


def test_pb_detector_triggers_on_trend_pullback_rebound() -> None:
    cfg = Settings(PAS_PATTERNS="pb", PAS_PB_VOLUME_MULT=1.15)
    detector = PbDetector(cfg)
    d0 = date(2026, 1, 1)
    rows: list[dict[str, float | date]] = []
    for i in range(20):
        rows.append(
            {
                "date": d0 + timedelta(days=i),
                "adj_open": 9.2 + i * 0.03,
                "adj_high": 10.2 + i * 0.04,
                "adj_low": 9.0 + i * 0.03,
                "adj_close": 9.8 + i * 0.04,
                "volume": 1000.0,
                "volume_ma20": 900.0,
            }
        )
    for i in range(15):
        rows.append(
            {
                "date": d0 + timedelta(days=20 + i),
                "adj_open": 10.8 + i * 0.08,
                "adj_high": 12.0 + i * 0.14,
                "adj_low": 10.5 + i * 0.08,
                "adj_close": 11.4 + i * 0.12,
                "volume": 1100.0,
                "volume_ma20": 950.0,
            }
        )
    rows.extend(
        [
            {"date": d0 + timedelta(days=35), "adj_open": 12.8, "adj_high": 12.85, "adj_low": 12.1, "adj_close": 12.35, "volume": 980.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=36), "adj_open": 12.35, "adj_high": 12.5, "adj_low": 11.95, "adj_close": 12.05, "volume": 970.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=37), "adj_open": 12.05, "adj_high": 12.3, "adj_low": 11.85, "adj_close": 11.98, "volume": 960.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=38), "adj_open": 11.98, "adj_high": 12.2, "adj_low": 11.8, "adj_close": 11.92, "volume": 950.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=39), "adj_open": 11.92, "adj_high": 12.25, "adj_low": 11.88, "adj_close": 12.12, "volume": 980.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=40), "adj_open": 12.2, "adj_high": 13.1, "adj_low": 12.0, "adj_close": 12.9, "volume": 1300.0, "volume_ma20": 1000.0},
        ]
    )

    signal, trace = detector.evaluate("000001", d0 + timedelta(days=40), _frame(rows))

    assert signal is not None
    assert signal.pattern == "pb"
    assert trace["triggered"] is True
    assert trace["trend_peak"] > trace["trend_floor"]


def test_tst_detector_triggers_on_support_test_rejection() -> None:
    cfg = Settings(PAS_PATTERNS="tst", PAS_TST_DISTANCE_MAX=0.03, PAS_TST_VOLUME_MULT=1.1)
    detector = TstDetector(cfg)
    d0 = date(2026, 1, 1)
    rows: list[dict[str, float | date]] = []
    for i in range(55):
        rows.append(
            {
                "date": d0 + timedelta(days=i),
                "adj_open": 10.2,
                "adj_high": 11.8,
                "adj_low": 9.8 if i == 0 else 10.0,
                "adj_close": 10.8,
                "volume": 1000.0,
                "volume_ma20": 900.0,
            }
        )
    rows.extend(
        [
            {"date": d0 + timedelta(days=55), "adj_open": 10.1, "adj_high": 10.2, "adj_low": 9.85, "adj_close": 10.0, "volume": 980.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=56), "adj_open": 10.0, "adj_high": 10.15, "adj_low": 9.84, "adj_close": 9.98, "volume": 970.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=57), "adj_open": 9.98, "adj_high": 10.12, "adj_low": 9.83, "adj_close": 10.0, "volume": 960.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=58), "adj_open": 10.0, "adj_high": 10.18, "adj_low": 9.82, "adj_close": 10.05, "volume": 970.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=59), "adj_open": 10.05, "adj_high": 10.2, "adj_low": 9.84, "adj_close": 10.08, "volume": 980.0, "volume_ma20": 1000.0},
            {"date": d0 + timedelta(days=60), "adj_open": 10.0, "adj_high": 10.35, "adj_low": 9.75, "adj_close": 10.25, "volume": 1300.0, "volume_ma20": 1000.0},
        ]
    )

    signal, trace = detector.evaluate("000001", d0 + timedelta(days=60), _frame(rows))

    assert signal is not None
    assert signal.pattern == "tst"
    assert trace["triggered"] is True
    assert trace["support_closeness"] > 0.9


def test_cpb_detector_triggers_on_complex_pullback_breakout() -> None:
    cfg = Settings(PAS_PATTERNS="cpb", PAS_CPB_RETEST_MIN=2, PAS_CPB_NECKLINE_BREAK_PCT=0.01, PAS_CPB_VOLUME_MULT=1.2)
    detector = CpbDetector(cfg)
    d0 = date(2026, 1, 1)
    rows: list[dict[str, float | date]] = []
    for i in range(20):
        rows.append(
            {
                "date": d0 + timedelta(days=i),
                "adj_open": 10.25,
                "adj_high": 10.7,
                "adj_low": 10.1,
                "adj_close": 10.35,
                "volume": 930.0,
                "volume_ma20": 900.0,
            }
        )
    for i in range(20):
        rows.append(
            {
                "date": d0 + timedelta(days=20 + i),
                "adj_open": 10.3,
                "adj_high": 10.6 + (0.2 if i % 5 == 0 else 0.0),
                "adj_low": [10.02, 10.05, 10.08, 10.1, 10.04][i % 5],
                "adj_close": 10.35,
                "volume": 950.0,
                "volume_ma20": 900.0,
            }
        )
    rows.append(
        {"date": d0 + timedelta(days=40), "adj_open": 10.5, "adj_high": 11.3, "adj_low": 10.45, "adj_close": 11.1, "volume": 1300.0, "volume_ma20": 1000.0}
    )

    signal, trace = detector.evaluate("000001", d0 + timedelta(days=40), _frame(rows))

    assert signal is not None
    assert signal.pattern == "cpb"
    assert trace["triggered"] is True
    assert trace["retest_count"] >= 2


def test_registry_and_combination_support_phase1_patterns() -> None:
    cfg = Settings(PAS_PATTERNS="bof,bpb,pb,tst,cpb", PAS_PATTERN_PRIORITY="bpb,pb,tst,cpb,bof")
    detectors = get_active_detectors(cfg)
    assert [detector.name for detector in detectors] == ["bof", "bpb", "pb", "tst", "cpb"]

    signal_date = date(2026, 1, 8)
    s1 = Signal(signal_id="000001_2026-01-08_bof", code="000001", signal_date=signal_date, action="BUY", strength=0.8, pattern="bof", reason_code="PAS_BOF")
    s2 = Signal(signal_id="000001_2026-01-08_bpb", code="000001", signal_date=signal_date, action="BUY", strength=0.8, pattern="bpb", reason_code="PAS_BPB")
    assert _combine_signals([s1, s2], active_detector_count=5, mode="ANY", pattern_priority=cfg.pas_pattern_priority_list) == [s2]

