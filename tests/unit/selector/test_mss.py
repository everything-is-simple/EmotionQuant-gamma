from __future__ import annotations

from datetime import date

import pandas as pd

from src.selector.mss import build_mss_raw_frame, calibrate_mss_baseline, compute_mss_single, score_mss_raw_frame
from src.selector.mss_experiments import MssVariantSpec, score_mss_variant


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


def test_compute_mss_single_respects_threshold_overrides() -> None:
    row = pd.Series(
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
        }
    )
    baseline = {
        "market_coefficient_mean": 0.0,
        "market_coefficient_std": 1.0,
        "profit_effect_mean": 0.0,
        "profit_effect_std": 1.0,
        "loss_effect_mean": 0.0,
        "loss_effect_std": 1.0,
        "continuity_mean": 0.0,
        "continuity_std": 1.0,
        "extreme_mean": 0.0,
        "extreme_std": 1.0,
        "volatility_mean": 0.0,
        "volatility_std": 1.0,
    }

    loose = compute_mss_single(row, baseline=baseline, bullish_threshold=50.0, bearish_threshold=35.0)
    tight = compute_mss_single(row, baseline=baseline, bullish_threshold=95.0, bearish_threshold=35.0)

    assert loose.score == tight.score
    assert loose.signal == "BULLISH"
    assert tight.signal == "NEUTRAL"


def test_mss_percentile_variant_preserves_ordering() -> None:
    raw_df = pd.DataFrame(
        [
            {
                "date": date(2026, 1, 2),
                "market_coefficient_raw": 0.20,
                "profit_effect_raw": 0.01,
                "loss_effect_raw": 0.08,
                "continuity_raw": 0.05,
                "extreme_raw": 0.10,
                "volatility_raw": 0.30,
            },
            {
                "date": date(2026, 1, 3),
                "market_coefficient_raw": 0.45,
                "profit_effect_raw": 0.03,
                "loss_effect_raw": 0.04,
                "continuity_raw": 0.10,
                "extreme_raw": 0.20,
                "volatility_raw": 0.20,
            },
            {
                "date": date(2026, 1, 4),
                "market_coefficient_raw": 0.70,
                "profit_effect_raw": 0.06,
                "loss_effect_raw": 0.01,
                "continuity_raw": 0.20,
                "extreme_raw": 0.35,
                "volatility_raw": 0.10,
            },
        ]
    )
    baseline = calibrate_mss_baseline(raw_df)

    scored = score_mss_variant(
        raw_df,
        MssVariantSpec(label="percentile_weighted6", normalization="percentile", aggregation="weighted6"),
        baseline=baseline,
    )

    assert scored["score"].is_monotonic_increasing
    assert scored.iloc[-1]["signal"] in {"BULLISH", "NEUTRAL"}


def test_mss_core3_variant_differs_from_weighted6() -> None:
    raw_df = pd.DataFrame(
        [
            {
                "date": date(2026, 1, 2),
                "market_coefficient_raw": 0.30,
                "profit_effect_raw": 0.04,
                "loss_effect_raw": 0.03,
                "continuity_raw": 0.01,
                "extreme_raw": 0.02,
                "volatility_raw": 0.40,
            },
            {
                "date": date(2026, 1, 3),
                "market_coefficient_raw": 0.45,
                "profit_effect_raw": 0.04,
                "loss_effect_raw": 0.03,
                "continuity_raw": 0.30,
                "extreme_raw": 0.35,
                "volatility_raw": 0.05,
            },
            {
                "date": date(2026, 1, 4),
                "market_coefficient_raw": 0.60,
                "profit_effect_raw": 0.05,
                "loss_effect_raw": 0.02,
                "continuity_raw": 0.12,
                "extreme_raw": 0.18,
                "volatility_raw": 0.12,
            },
        ]
    )
    baseline = calibrate_mss_baseline(raw_df)

    weighted = score_mss_variant(
        raw_df,
        MssVariantSpec(label="zscore_weighted6", normalization="zscore", aggregation="weighted6"),
        baseline=baseline,
    )
    core3 = score_mss_variant(
        raw_df,
        MssVariantSpec(label="zscore_core3", normalization="zscore", aggregation="core3"),
        baseline=baseline,
    )

    assert weighted["score"].tolist() != core3["score"].tolist()
