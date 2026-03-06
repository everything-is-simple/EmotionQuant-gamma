from __future__ import annotations

from datetime import date

import pandas as pd

from src.selector.mss import build_mss_raw_frame, calibrate_mss_baseline, score_mss_raw_frame


def test_mss_calibration_pipeline_builds_non_placeholder_baseline() -> None:
    snapshot = pd.DataFrame(
        [
            {
                "date": date(2026, 1, 2),
                "total_stocks": 100,
                "rise_count": 60,
                "strong_up_count": 10,
                "limit_up_count": 5,
                "touched_limit_up_count": 1,
                "new_100d_high_count": 8,
                "limit_down_count": 2,
                "strong_down_count": 3,
                "new_100d_low_count": 4,
                "continuous_limit_up_2d": 2,
                "continuous_limit_up_3d_plus": 1,
                "continuous_new_high_2d_plus": 3,
                "high_open_low_close_count": 2,
                "low_open_high_close_count": 1,
                "pct_chg_std": 0.02,
                "amount_volatility": 100000.0,
            },
            {
                "date": date(2026, 1, 3),
                "total_stocks": 100,
                "rise_count": 30,
                "strong_up_count": 2,
                "limit_up_count": 1,
                "touched_limit_up_count": 1,
                "new_100d_high_count": 1,
                "limit_down_count": 6,
                "strong_down_count": 8,
                "new_100d_low_count": 9,
                "continuous_limit_up_2d": 0,
                "continuous_limit_up_3d_plus": 0,
                "continuous_new_high_2d_plus": 0,
                "high_open_low_close_count": 6,
                "low_open_high_close_count": 1,
                "pct_chg_std": 0.05,
                "amount_volatility": 400000.0,
            },
        ]
    )

    raw_df = build_mss_raw_frame(snapshot)
    baseline = calibrate_mss_baseline(raw_df)
    scored = score_mss_raw_frame(raw_df, baseline=baseline, bullish_threshold=55.0, bearish_threshold=45.0)

    assert len(raw_df) == 2
    assert baseline["market_coefficient_std"] > 0
    assert baseline["profit_effect_mean"] != 0
    assert set(scored["signal"]) == {"BULLISH", "BEARISH"}
