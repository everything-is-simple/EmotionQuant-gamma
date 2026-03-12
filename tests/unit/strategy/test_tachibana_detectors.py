from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.strategy.tachibana_detectors import TachiCrowdFailureDetector


def _frame_from_rows(rows: list[dict[str, float]]) -> pd.DataFrame:
    start = date(2024, 1, 1)
    payload: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        payload.append(
            {
                "code": "600000",
                "date": start + timedelta(days=index),
                "adj_open": row["open"],
                "adj_high": row["high"],
                "adj_low": row["low"],
                "adj_close": row["close"],
                "volume": row.get("volume", 100.0),
                "volume_ma20": row.get("volume_ma20", 100.0),
                "ma20": row.get("ma20", row["close"]),
            }
        )
    return pd.DataFrame(payload)


def test_tachi_crowd_failure_detector_triggers_on_washout_reclaim() -> None:
    rows: list[dict[str, float]] = []
    for close in [
        100.0,
        100.5,
        101.0,
        101.5,
        102.0,
        102.5,
        103.0,
        103.5,
        104.0,
        104.5,
        105.0,
        105.5,
        106.0,
        106.5,
        107.0,
        107.5,
        108.0,
        108.5,
        109.0,
        109.5,
    ]:
        rows.append(
            {
                "open": close - 0.3,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "ma20": 100.0,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )
    for close in [104.0, 102.0, 100.0, 98.0, 96.0, 94.0, 92.0, 91.0, 90.5, 90.0]:
        rows.append(
            {
                "open": close + 0.4,
                "high": close + 0.8,
                "low": close - 1.0,
                "close": close,
                "ma20": 96.0,
                "volume": 105.0,
                "volume_ma20": 100.0,
            }
        )
    rows.append(
        {
            "open": 90.2,
            "high": 96.0,
            "low": 88.0,
            "close": 95.0,
            "ma20": 96.0,
            "volume": 140.0,
            "volume_ma20": 100.0,
        }
    )
    frame = _frame_from_rows(rows)

    signal, trace = TachiCrowdFailureDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert signal is not None
    assert signal.pattern == "tachi_crowd_failure"
    assert trace["triggered"] is True


def test_tachi_crowd_failure_detector_rejects_without_crowd_extreme() -> None:
    rows: list[dict[str, float]] = []
    for close in [
        100.0,
        100.2,
        100.4,
        100.1,
        100.5,
        100.3,
        100.6,
        100.4,
        100.7,
        100.5,
        100.3,
        100.6,
        100.4,
        100.7,
        100.5,
        100.4,
        100.6,
        100.5,
        100.7,
        100.6,
    ]:
        rows.append(
            {
                "open": close - 0.1,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "ma20": 100.0,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )
    for close in [100.4, 100.1, 99.9, 100.2, 99.8, 100.0, 99.9, 100.1, 99.8, 100.0]:
        rows.append(
            {
                "open": close + 0.1,
                "high": close + 0.4,
                "low": close - 0.4,
                "close": close,
                "ma20": 100.0,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )
    rows.append(
        {
            "open": 99.8,
            "high": 100.8,
            "low": 99.0,
            "close": 100.6,
            "ma20": 100.0,
            "volume": 140.0,
            "volume_ma20": 100.0,
        }
    )
    frame = _frame_from_rows(rows)

    signal, trace = TachiCrowdFailureDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert signal is None
    assert trace["skip_reason"] == "NO_CROWD_EXTREME"
