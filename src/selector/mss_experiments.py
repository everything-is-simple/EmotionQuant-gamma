from __future__ import annotations

"""MSS 实验工位。

这里专门承接“不同归一化 / 聚合方式会不会更好”的实验，
目的是把研究试验和正式主线隔离开：
- 正式主线在 mss.py
- 实验变体在这里
"""

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from src.data.store import Store
from src.selector.baseline import MSS_BASELINE
from src.selector.mss import (
    MSS_FACTOR_NAMES,
    build_mss_raw_frame,
    calibrate_mss_baseline,
    resolve_mss_state,
)
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


# 把实验标签解析成具体的归一化方式和聚合方式。
# 实验层允许用一个短标签同时表达“归一化方式 + 聚合方式”，
# 这样做批量回放时更容易比较不同实验版本。
def get_mss_variant_spec(label: str) -> MssVariantSpec:
    """把实验标签解析成具体配方。"""

    normalized = label.strip().lower()
    for variant in MSS_VARIANTS:
        if variant.label == normalized:
            return variant
    raise ValueError(f"Unsupported MSS variant: {label}")


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


# 用某个实验配方对原始 MSS 因子框架重新打分。
# 它不会改主线表的治理含义，只是把同一份原始观测换一套数学口径重算，
# 便于研究“主线为什么这样定，而不是那样定”。
def score_mss_variant(
    raw_df: pd.DataFrame,
    variant: MssVariantSpec,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
    reference_raw_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """按某个实验配方对原始 MSS 因子框架重新打分。"""

    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["date", "score", "signal"] + MSS_FACTOR_NAMES)

    base = baseline or calibrate_mss_baseline(raw_df) or MSS_BASELINE
    percentile_reference = _build_percentile_reference(reference_raw_df if reference_raw_df is not None else raw_df)
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


# 把某个实验版 MSS 落成正式表结构，便于和主线直接做并排对比。
def compute_mss_variant(
    store: Store,
    start: date,
    end: date,
    variant_label: str = "zscore_weighted6",
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> int:
    """把某个实验版 MSS 落成正式日表形状，便于并排对照。"""
    # MSS 支持按日期局部重建；先清分区，避免源数据收缩后保留旧结果。
    store.conn.execute("DELETE FROM l3_mss_daily WHERE date BETWEEN ? AND ?", [start, end])
    variant = get_mss_variant_spec(variant_label)
    score_df = store.read_df(
        """
        SELECT *
        FROM l2_market_snapshot
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if score_df.empty:
        return 0

    reference_df = score_df
    if variant.normalization == "percentile":
        reference_df = store.read_df(
            """
            SELECT *
            FROM l2_market_snapshot
            ORDER BY date
            """
        )
        if reference_df.empty:
            reference_df = score_df

    raw_df = build_mss_raw_frame(score_df)
    reference_raw_df = build_mss_raw_frame(reference_df)
    scored = score_mss_variant(
        raw_df,
        variant,
        baseline=baseline or MSS_BASELINE,
        bullish_threshold=bullish_threshold,
        bearish_threshold=bearish_threshold,
        reference_raw_df=reference_raw_df,
    )
    if scored.empty:
        return 0

    # build_l3 的正式入口走的是 compute_mss_variant，而 Broker 在 Phase 3 之后
    # 必须直接从 l3_mss_daily 读取 raw 因子和状态层字段。
    # 因此这里不能只写 score/signal/normalized components，必须把：
    # 1. raw 因子
    # 2. phase / phase_trend / phase_days / position_advice / risk_regime / trend_quality
    # 一次性回写到正式表，避免“单测纯函数有状态、真实 build_l3 却全是 NULL”。
    prior_df = store.read_df(
        """
        SELECT date, score, phase, phase_days
        FROM l3_mss_daily
        WHERE date < ?
        ORDER BY date DESC
        LIMIT 20
        """,
        (start,),
    )
    score_history: list[float] = []
    prev_phase: str | None = None
    prev_phase_days: int | None = None
    if not prior_df.empty:
        for _, prior_row in prior_df.sort_values("date").iterrows():
            prior_score = prior_row["score"]
            if prior_score is None or pd.isna(prior_score):
                continue
            score_history.append(float(prior_score))
            score_history = score_history[-20:]
            prior_phase_value = prior_row["phase"]
            prior_phase_days_value = prior_row["phase_days"]
            if prior_phase_value is not None and not pd.isna(prior_phase_value):
                prev_phase = str(prior_phase_value)
            if prior_phase_days_value is not None and not pd.isna(prior_phase_days_value):
                prev_phase_days = int(prior_phase_days_value)
            else:
                prior_state = resolve_mss_state(
                    score_history,
                    prev_phase=prev_phase,
                    prev_phase_days=prev_phase_days,
                )
                prev_phase = str(prior_state["phase"])
                prev_phase_days = int(prior_state["phase_days"])

    state_rows: list[dict[str, str | int | date]] = []
    for row in scored.sort_values("date").itertuples(index=False):
        score = float(row.score)
        state = resolve_mss_state(
            [*score_history, score],
            prev_phase=prev_phase,
            prev_phase_days=prev_phase_days,
        )
        state_rows.append({"date": row.date, **state})
        score_history.append(score)
        score_history = score_history[-20:]
        prev_phase = str(state["phase"])
        prev_phase_days = int(state["phase_days"])

    enriched = (
        raw_df.merge(scored, on="date", how="inner")
        .merge(pd.DataFrame(state_rows), on="date", how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )
    return store.bulk_upsert("l3_mss_daily", enriched)


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
            reference_raw_df=raw_df,
        )
        for variant in MSS_VARIANTS
    }
