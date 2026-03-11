from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.store import Store
from src.selector.mss import (
    build_mss_raw_frame,
    calibrate_mss_baseline,
    compute_mss,
    compute_mss_raw_components,
    compute_mss_single,
    materialize_mss_trace_snapshot,
    resolve_mss_phase,
    resolve_mss_position_advice,
    resolve_mss_risk_regime,
    resolve_mss_state,
    score_mss_raw_frame,
)
from src.selector.mss_experiments import MssVariantSpec, compute_mss_variant, score_mss_variant


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


def test_materialize_mss_trace_snapshot_exposes_raw_and_normalized_components() -> None:
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

    raw = compute_mss_raw_components(row)
    snapshot = materialize_mss_trace_snapshot(row, baseline=baseline, bullish_threshold=50.0, bearish_threshold=35.0)

    assert raw["market_coefficient_raw"] == 0.6
    assert snapshot["market_coefficient_raw"] == raw["market_coefficient_raw"]
    assert snapshot["market_coefficient"] >= 0.0
    assert snapshot["profit_effect"] >= 0.0
    assert snapshot["signal"] == "BULLISH"


def test_resolve_mss_state_detects_normal_uptrend_and_risk_on() -> None:
    # 8 日以上历史走正常趋势窗，ACCELERATION + UP 必须进入 RISK_ON。
    state = resolve_mss_state([20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0])

    assert state["phase_trend"] == "UP"
    assert state["trend_quality"] == "NORMAL"
    assert state["phase"] == "ACCELERATION"
    assert state["phase_days"] == 1
    assert state["position_advice"] == "50%-70%"
    assert state["risk_regime"] == "RISK_ON"


def test_resolve_mss_state_uses_cold_start_and_phase_days_increment_reset() -> None:
    # 历史不足 8 日时，状态层必须走 cold start，并且只按上一交易日 phase 连续计数。
    continued = resolve_mss_state([40.0, 45.0, 50.0], prev_phase="ACCELERATION", prev_phase_days=2)
    reset = resolve_mss_state([50.0, 45.0, 40.0], prev_phase="ACCELERATION", prev_phase_days=2)

    assert continued["phase_trend"] == "UP"
    assert continued["trend_quality"] == "COLD_START"
    assert continued["phase"] == "ACCELERATION"
    assert continued["phase_days"] == 3
    assert reset["phase_trend"] == "DOWN"
    assert reset["trend_quality"] == "COLD_START"
    assert reset["phase"] == "RECESSION"
    assert reset["phase_days"] == 1


def test_resolve_mss_phase_and_regime_distinguish_climax_diffusion_and_unknown() -> None:
    # Phase 3 的关键约束：高分不一定 risk_on，CLIMAX 必须允许直接打到 RISK_OFF。
    assert resolve_mss_phase(82.0, "UP") == "CLIMAX"
    assert resolve_mss_risk_regime("CLIMAX", "UP") == "RISK_OFF"
    assert resolve_mss_phase(65.0, "DOWN") == "DIFFUSION"
    assert resolve_mss_position_advice("DIFFUSION") == "30%-50%"
    assert resolve_mss_risk_regime("DIFFUSION", "DOWN") == "RISK_NEUTRAL"
    assert resolve_mss_phase(float("nan"), "UP") == "UNKNOWN"


def test_compute_mss_persists_raw_and_normalized_components_to_l3(tmp_path) -> None:
    db = tmp_path / "mss_l3_trace.duckdb"
    store = Store(db)
    snapshot_date = date(2026, 1, 2)
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
    store.bulk_upsert(
        "l2_market_snapshot",
        pd.DataFrame(
            [
                {
                    "date": snapshot_date,
                    "total_stocks": 100,
                    "rise_count": 60,
                    "fall_count": 40,
                    "strong_up_count": 10,
                    "strong_down_count": 3,
                    "limit_up_count": 5,
                    "limit_down_count": 2,
                    "touched_limit_up_count": 1,
                    "new_100d_high_count": 8,
                    "new_100d_low_count": 4,
                    "continuous_limit_up_2d": 2,
                    "continuous_limit_up_3d_plus": 1,
                    "continuous_new_high_2d_plus": 3,
                    "high_open_low_close_count": 2,
                    "low_open_high_close_count": 1,
                    "pct_chg_std": 0.02,
                    "amount_volatility": 100000.0,
                }
            ]
        ),
    )

    written = compute_mss(store, snapshot_date, snapshot_date, baseline=baseline, bullish_threshold=50.0, bearish_threshold=35.0)
    row = store.read_df(
        """
        SELECT market_coefficient_raw, profit_effect_raw, loss_effect_raw,
               market_coefficient, profit_effect, loss_effect, signal,
               phase, phase_trend, phase_days, position_advice, risk_regime, trend_quality, score
        FROM l3_mss_daily
        WHERE date = ?
        """,
        (snapshot_date,),
    )

    assert written == 1
    assert row.iloc[0]["market_coefficient_raw"] == 0.6
    assert row.iloc[0]["profit_effect_raw"] > 0.0
    assert row.iloc[0]["loss_effect_raw"] > 0.0
    assert row.iloc[0]["market_coefficient"] >= 0.0
    assert row.iloc[0]["profit_effect"] >= 0.0
    assert row.iloc[0]["loss_effect"] >= 0.0
    assert row.iloc[0]["signal"] == "BULLISH"
    # l3_mss_daily 现在不仅要保存市场分，还要成为 Broker 可直接消费的状态层真相源。
    expected_state = resolve_mss_state([float(row.iloc[0]["score"])])
    assert row.iloc[0]["phase"] == expected_state["phase"]
    assert row.iloc[0]["phase_trend"] == expected_state["phase_trend"]
    assert row.iloc[0]["phase_days"] == expected_state["phase_days"]
    assert row.iloc[0]["position_advice"] == expected_state["position_advice"]
    assert row.iloc[0]["risk_regime"] == expected_state["risk_regime"]
    assert row.iloc[0]["trend_quality"] == expected_state["trend_quality"]
    store.close()


def test_compute_mss_variant_persists_state_layer_to_l3(tmp_path) -> None:
    db = tmp_path / "mss_variant_l3_trace.duckdb"
    store = Store(db)
    snapshot_date = date(2026, 1, 2)
    store.bulk_upsert(
        "l2_market_snapshot",
        pd.DataFrame(
            [
                {
                    "date": snapshot_date,
                    "total_stocks": 100,
                    "rise_count": 60,
                    "fall_count": 40,
                    "strong_up_count": 10,
                    "strong_down_count": 3,
                    "limit_up_count": 5,
                    "limit_down_count": 2,
                    "touched_limit_up_count": 1,
                    "new_100d_high_count": 8,
                    "new_100d_low_count": 4,
                    "continuous_limit_up_2d": 2,
                    "continuous_limit_up_3d_plus": 1,
                    "continuous_new_high_2d_plus": 3,
                    "high_open_low_close_count": 2,
                    "low_open_high_close_count": 1,
                    "pct_chg_std": 0.02,
                    "amount_volatility": 100000.0,
                }
            ]
        ),
    )

    written = compute_mss_variant(store, snapshot_date, snapshot_date, variant_label="zscore_weighted6")
    row = store.read_df(
        """
        SELECT market_coefficient_raw, profit_effect_raw, loss_effect_raw,
               market_coefficient, profit_effect, loss_effect, signal,
               phase, phase_trend, phase_days, position_advice, risk_regime, trend_quality, score
        FROM l3_mss_daily
        WHERE date = ?
        """,
        (snapshot_date,),
    )

    assert written == 1
    assert row.iloc[0]["market_coefficient_raw"] is not None
    assert row.iloc[0]["profit_effect_raw"] is not None
    assert row.iloc[0]["loss_effect_raw"] is not None
    assert row.iloc[0]["phase"] is not None
    assert row.iloc[0]["phase_trend"] is not None
    assert row.iloc[0]["phase_days"] == 1
    assert row.iloc[0]["position_advice"] is not None
    assert row.iloc[0]["risk_regime"] is not None
    assert row.iloc[0]["trend_quality"] is not None
    expected_state = resolve_mss_state([float(row.iloc[0]["score"])])
    assert row.iloc[0]["phase"] == expected_state["phase"]
    assert row.iloc[0]["phase_trend"] == expected_state["phase_trend"]
    assert row.iloc[0]["risk_regime"] == expected_state["risk_regime"]
    store.close()
