from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.config import Settings
from src.strategy.volman_detectors import (
    FbBoundaryDetector,
    FbCleanerDetector,
    FbDetector,
    RbFakeDetector,
    SbDetector,
)


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
                "volume_ratio": row.get("volume_ratio", 1.0),
            }
        )
    return pd.DataFrame(payload)


def _build_fb_frame(prior_touch_count: int) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for idx in range(10):
        close = 100.0 + idx * 0.2
        rows.append(
            {
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "ma20": 99.8 + idx * 0.05,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )

    for idx in range(15):
        ma20 = 102.0 + idx * 0.55
        close = 106.0 + idx * 1.1
        low = ma20 * 1.01 if idx < prior_touch_count else ma20 * 1.06
        rows.append(
            {
                "open": close - 0.4,
                "high": close + 0.8,
                "low": min(low, close - 0.6),
                "close": close,
                "ma20": ma20,
                "volume": 110.0,
                "volume_ma20": 100.0,
            }
        )

    rows.extend(
        [
            {"open": 120.0, "high": 120.8, "low": 118.0, "close": 119.0, "ma20": 114.2, "volume": 95.0, "volume_ma20": 100.0},
            {"open": 118.8, "high": 119.2, "low": 116.8, "close": 117.6, "ma20": 114.5, "volume": 95.0, "volume_ma20": 100.0},
            {"open": 117.4, "high": 117.7, "low": 115.8, "close": 116.5, "ma20": 114.8, "volume": 95.0, "volume_ma20": 100.0},
            {"open": 116.2, "high": 116.4, "low": 114.8, "close": 115.6, "ma20": 115.0, "volume": 95.0, "volume_ma20": 100.0},
            {"open": 115.5, "high": 115.9, "low": 114.6, "close": 115.0, "ma20": 115.1, "volume": 95.0, "volume_ma20": 100.0},
            {"open": 116.0, "high": 122.5, "low": 115.3, "close": 121.5, "ma20": 115.2, "volume": 150.0, "volume_ma20": 100.0},
        ]
    )
    return _frame_from_rows(rows[-31:])


def test_rb_fake_detector_triggers_on_range_fake_break() -> None:
    rows: list[dict[str, float]] = []
    closes = [
        103.4,
        103.0, 104.0, 103.5, 104.2, 103.8,
        102.8, 103.2, 102.5, 103.1, 102.4,
        102.0, 101.8, 102.2, 101.6, 102.0,
        101.5, 101.8, 101.3, 101.6, 101.2,
    ]
    for close in closes:
        rows.append(
            {
                "open": close - 0.3,
                "high": 110.0 if close > 103 else close + 1.2,
                "low": 100.0 if close <= 102.2 else close - 1.0,
                "close": close,
                "ma20": 103.5,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )
    rows.extend(
        [
            {"open": 101.0, "high": 102.0, "low": 100.0, "close": 101.5, "ma20": 103.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 101.2, "high": 102.2, "low": 100.2, "close": 101.6, "ma20": 103.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 101.0, "high": 102.0, "low": 100.0, "close": 101.4, "ma20": 103.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 101.0, "high": 102.0, "low": 100.0, "close": 101.3, "ma20": 103.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 100.5, "high": 102.5, "low": 98.0, "close": 101.8, "ma20": 103.0, "volume": 150.0, "volume_ma20": 100.0},
        ]
    )
    frame = _frame_from_rows(rows[-26:])

    signal, trace = RbFakeDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert signal is not None
    assert signal.pattern == "rb_fake"
    assert trace["triggered"] is True


def test_fb_detector_triggers_on_first_pullback_recovery() -> None:
    rows: list[dict[str, float]] = []
    for close in [99.5, 100.0, 100.5, 100.8, 101.0, 100.9, 101.2, 101.5, 101.8, 102.0]:
        rows.append(
            {
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "ma20": 100.0,
                "volume": 100.0,
                "volume_ma20": 100.0,
            }
        )
    trend_closes = [103.0, 104.5, 106.0, 108.0, 109.5, 111.0, 113.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0, 121.0, 122.0]
    for idx, close in enumerate(trend_closes):
        rows.append(
            {
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "ma20": 101.0 + idx * 0.9,
                "volume": 110.0,
                "volume_ma20": 100.0,
            }
        )
    pullback_rows = [
        {"open": 121.0, "high": 121.5, "low": 118.5, "close": 120.0, "ma20": 114.0, "volume": 95.0, "volume_ma20": 100.0},
        {"open": 119.5, "high": 120.0, "low": 117.0, "close": 118.0, "ma20": 114.2, "volume": 95.0, "volume_ma20": 100.0},
        {"open": 118.0, "high": 118.5, "low": 116.0, "close": 117.0, "ma20": 114.4, "volume": 95.0, "volume_ma20": 100.0},
        {"open": 117.0, "high": 117.2, "low": 115.0, "close": 116.0, "ma20": 114.6, "volume": 95.0, "volume_ma20": 100.0},
        {"open": 116.0, "high": 116.5, "low": 114.2, "close": 115.0, "ma20": 114.8, "volume": 95.0, "volume_ma20": 100.0},
    ]
    rows.extend(pullback_rows)
    rows.append(
        {"open": 116.0, "high": 123.0, "low": 115.0, "close": 122.0, "ma20": 115.0, "volume": 150.0, "volume_ma20": 100.0}
    )
    frame = _frame_from_rows(rows[-31:])

    signal, trace = FbDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert signal is not None
    assert signal.pattern == "fb"
    assert trace["triggered"] is True


def test_fb_cleaner_detector_keeps_zero_or_one_touch_branch() -> None:
    frame = _build_fb_frame(prior_touch_count=1)

    cleaner_signal, cleaner_trace = FbCleanerDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)
    boundary_signal, boundary_trace = FbBoundaryDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert cleaner_signal is not None
    assert cleaner_trace["prior_ema_touches"] == 1
    assert boundary_signal is None
    assert boundary_trace["detect_reason"] == "NOT_FIRST_PULLBACK"


def test_fb_boundary_detector_isolates_two_touch_branch() -> None:
    frame = _build_fb_frame(prior_touch_count=2)

    default_signal, default_trace = FbDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)
    cleaner_signal, cleaner_trace = FbCleanerDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)
    boundary_signal, boundary_trace = FbBoundaryDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert default_signal is not None
    assert default_trace["prior_ema_touches"] == 2
    assert cleaner_signal is None
    assert cleaner_trace["detect_reason"] == "NOT_FIRST_PULLBACK"
    assert boundary_signal is not None
    assert boundary_trace["triggered"] is True


def test_sb_detector_triggers_on_second_break_recovery() -> None:
    rows: list[dict[str, float]] = []
    for idx, close in enumerate(range(100, 130)):
        rows.append(
            {
                "open": close - 0.3,
                "high": close + 1.2,
                "low": close - 1.0,
                "close": float(close),
                "ma20": 98.0 + idx * 0.9,
                "volume": 105.0,
                "volume_ma20": 100.0,
            }
        )
    rows.extend(
        [
            {"open": 129.0, "high": 129.0, "low": 126.0, "close": 127.0, "ma20": 126.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 127.0, "high": 128.0, "low": 124.0, "close": 125.0, "ma20": 124.8, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 125.5, "high": 129.0, "low": 123.0, "close": 128.0, "ma20": 124.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 128.0, "high": 129.0, "low": 126.5, "close": 127.5, "ma20": 124.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 127.5, "high": 128.0, "low": 125.0, "close": 126.0, "ma20": 124.0, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 126.0, "high": 128.0, "low": 124.2, "close": 125.0, "ma20": 124.5, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 125.0, "high": 127.0, "low": 124.0, "close": 126.0, "ma20": 124.5, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 126.0, "high": 128.0, "low": 124.5, "close": 127.0, "ma20": 124.5, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 127.0, "high": 129.0, "low": 125.5, "close": 128.0, "ma20": 124.5, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 128.0, "high": 129.5, "low": 126.8, "close": 128.5, "ma20": 124.5, "volume": 100.0, "volume_ma20": 100.0},
            {"open": 128.8, "high": 131.0, "low": 127.8, "close": 130.2, "ma20": 125.0, "volume": 150.0, "volume_ma20": 100.0},
        ]
    )
    frame = _frame_from_rows(rows[-41:])

    signal, trace = SbDetector(Settings()).evaluate("600000", date(2024, 2, 1), frame)

    assert signal is not None
    assert signal.pattern == "sb"
    assert trace["triggered"] is True
