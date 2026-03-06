from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from src.selector.baseline import MSS_BASELINE
from src.selector.mss import MSS_FACTOR_NAMES, build_mss_raw_frame, calibrate_mss_baseline
from src.selector.normalize import zscore_single


@dataclass(frozen=True)
class MssVariantSpec:
    label: str
    normalization: str
    aggregation: str


MSS_VARIANTS = [
    MssVariantSpec(label="zscore_weighted6", normalization="zscore", aggregation="weighted6"),
    MssVariantSpec(label="percentile_weighted6", normalization="percentile", aggregation="weighted6"),
    MssVariantSpec(label="zscore_core3", normalization="zscore", aggregation="core3"),
    MssVariantSpec(label="percentile_core3", normalization="percentile", aggregation="core3"),
]


def _signal_from_score(score: float, bullish_threshold: float = 65.0, bearish_threshold: float = 35.0) -> str:
    if score >= bullish_threshold:
        return "BULLISH"
    if score <= bearish_threshold:
        return "BEARISH"
    return "NEUTRAL"


def _percentile_single(value: float, reference: np.ndarray) -> float:
    if reference.size <= 1:
        return 50.0
    left = int(np.searchsorted(reference, value, side="left"))
    right = int(np.searchsorted(reference, value, side="right"))
    midpoint = (left + right) / 2.0
    return float(np.clip(midpoint / len(reference) * 100.0, 0.0, 100.0))


def _build_percentile_reference(raw_df: pd.DataFrame) -> dict[str, np.ndarray]:
    reference: dict[str, np.ndarray] = {}
    for factor in MSS_FACTOR_NAMES:
        values = pd.to_numeric(raw_df.get(f"{factor}_raw"), errors="coerce").dropna().to_numpy(dtype=float)
        # percentile 实验使用经验分布本身做锚点，不引入额外参数。
        reference[factor] = np.sort(values)
    return reference


def _normalize_components(
    raw: dict[str, float],
    baseline: dict[str, float],
    percentile_reference: dict[str, np.ndarray],
    normalization: str,
) -> dict[str, float]:
    if normalization == "zscore":
        return {
            "market_coefficient": zscore_single(
                raw["market_coefficient_raw"],
                baseline["market_coefficient_mean"],
                baseline["market_coefficient_std"],
            ),
            "profit_effect": zscore_single(
                raw["profit_effect_raw"],
                baseline["profit_effect_mean"],
                baseline["profit_effect_std"],
            ),
            "loss_effect": zscore_single(
                raw["loss_effect_raw"],
                baseline["loss_effect_mean"],
                baseline["loss_effect_std"],
            ),
            "continuity": zscore_single(
                raw["continuity_raw"],
                baseline["continuity_mean"],
                baseline["continuity_std"],
            ),
            "extreme": zscore_single(
                raw["extreme_raw"],
                baseline["extreme_mean"],
                baseline["extreme_std"],
            ),
            "volatility": zscore_single(
                raw["volatility_raw"],
                baseline["volatility_mean"],
                baseline["volatility_std"],
            ),
        }
    if normalization == "percentile":
        return {
            factor: _percentile_single(raw[f"{factor}_raw"], percentile_reference[factor]) for factor in MSS_FACTOR_NAMES
        }
    raise ValueError(f"Unsupported MSS normalization: {normalization}")


def _aggregate_components(components: dict[str, float], aggregation: str) -> float:
    if aggregation == "weighted6":
        score = (
            0.17 * components["market_coefficient"]
            + 0.34 * components["profit_effect"]
            + 0.34 * (100.0 - components["loss_effect"])
            + 0.05 * components["continuity"]
            + 0.05 * components["extreme"]
            + 0.05 * (100.0 - components["volatility"])
        )
        return float(np.clip(score, 0.0, 100.0))
    if aggregation == "core3":
        # core3 只保留市场/赚钱效应/亏钱效应，检验尾部三因子是否在压缩动态范围。
        score = (
            0.20 * components["market_coefficient"]
            + 0.40 * components["profit_effect"]
            + 0.40 * (100.0 - components["loss_effect"])
        )
        return float(np.clip(score, 0.0, 100.0))
    raise ValueError(f"Unsupported MSS aggregation: {aggregation}")


def score_mss_variant(
    raw_df: pd.DataFrame,
    variant: MssVariantSpec,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["date", "score", "signal"] + MSS_FACTOR_NAMES)

    base = baseline or calibrate_mss_baseline(raw_df) or MSS_BASELINE
    percentile_reference = _build_percentile_reference(raw_df)
    rows: list[dict[str, float | str | date]] = []
    for _, row in raw_df.iterrows():
        raw = {key: float(row[key]) for key in raw_df.columns if key.endswith("_raw")}
        components = _normalize_components(raw, base, percentile_reference, normalization=variant.normalization)
        score = _aggregate_components(components, aggregation=variant.aggregation)
        d = row["date"]
        if isinstance(d, pd.Timestamp):
            d = d.date()
        rows.append(
            {
                "date": d,
                "score": score,
                "signal": _signal_from_score(score, bullish_threshold, bearish_threshold),
                **components,
            }
        )
    return pd.DataFrame(rows)


def score_mss_variants(
    snapshot_df: pd.DataFrame,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> dict[str, pd.DataFrame]:
    raw_df = build_mss_raw_frame(snapshot_df)
    if raw_df.empty:
        return {variant.label: pd.DataFrame() for variant in MSS_VARIANTS}
    base = baseline or calibrate_mss_baseline(raw_df)
    return {
        variant.label: score_mss_variant(
            raw_df,
            variant,
            baseline=base,
            bullish_threshold=bullish_threshold,
            bearish_threshold=bearish_threshold,
        )
        for variant in MSS_VARIANTS
    }
