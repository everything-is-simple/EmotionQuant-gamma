from __future__ import annotations

from datetime import date
from typing import Literal

import numpy as np
import pandas as pd

from src.contracts import MarketScore
from src.data.store import Store
from src.selector.baseline import MSS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single

MSS_FACTOR_NAMES = [
    "market_coefficient",
    "profit_effect",
    "loss_effect",
    "continuity",
    "extreme",
    "volatility",
]


def _signal_from_score(
    score: float,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> Literal["BULLISH", "NEUTRAL", "BEARISH"]:
    if score >= bullish_threshold:
        return "BULLISH"
    if score <= bearish_threshold:
        return "BEARISH"
    return "NEUTRAL"


def _compute_mss_raw_components(row: pd.Series) -> dict[str, float]:
    total_stocks = row.get("total_stocks", 0) or 0
    limit_up_count = row.get("limit_up_count", 0) or 0
    new_high_count = row.get("new_100d_high_count", 0) or 0

    market_coefficient_raw = safe_ratio(row.get("rise_count", 0), total_stocks, default=0.0)

    limit_up_ratio = safe_ratio(limit_up_count, total_stocks, default=0.0)
    new_high_ratio = safe_ratio(new_high_count, total_stocks, default=0.0)
    strong_up_ratio = safe_ratio(row.get("strong_up_count", 0), total_stocks, default=0.0)
    profit_effect_raw = 0.4 * limit_up_ratio + 0.3 * new_high_ratio + 0.3 * strong_up_ratio

    broken_rate = safe_ratio(row.get("touched_limit_up_count", 0), limit_up_count, default=0.0)
    limit_down_ratio = safe_ratio(row.get("limit_down_count", 0), total_stocks, default=0.0)
    strong_down_ratio = safe_ratio(row.get("strong_down_count", 0), total_stocks, default=0.0)
    new_low_ratio = safe_ratio(row.get("new_100d_low_count", 0), total_stocks, default=0.0)
    loss_effect_raw = (
        0.3 * broken_rate
        + 0.2 * limit_down_ratio
        + 0.3 * strong_down_ratio
        + 0.2 * new_low_ratio
    )

    cont_limit_up_ratio = safe_ratio(
        row.get("continuous_limit_up_2d", 0) + row.get("continuous_limit_up_3d_plus", 0),
        limit_up_count,
        default=0.0,
    )
    cont_new_high_ratio = safe_ratio(row.get("continuous_new_high_2d_plus", 0), new_high_count, default=0.0)
    continuity_raw = 0.5 * cont_limit_up_ratio + 0.5 * cont_new_high_ratio

    panic_tail_ratio = safe_ratio(row.get("high_open_low_close_count", 0), total_stocks, default=0.0)
    squeeze_tail_ratio = safe_ratio(row.get("low_open_high_close_count", 0), total_stocks, default=0.0)
    extreme_raw = panic_tail_ratio + squeeze_tail_ratio

    pct_chg_std = float(row.get("pct_chg_std", 0.0) or 0.0)
    amount_vol = float(row.get("amount_volatility", 0.0) or 0.0)
    amount_vol_ratio = amount_vol / (amount_vol + 1e6) if amount_vol > 0 else 0.0
    volatility_raw = 0.5 * pct_chg_std + 0.5 * amount_vol_ratio

    return {
        "market_coefficient_raw": market_coefficient_raw,
        "profit_effect_raw": profit_effect_raw,
        "loss_effect_raw": loss_effect_raw,
        "continuity_raw": continuity_raw,
        "extreme_raw": extreme_raw,
        "volatility_raw": volatility_raw,
    }


def _normalize_mss_components(raw: dict[str, float], baseline: dict[str, float] | None = None) -> dict[str, float]:
    base = baseline or MSS_BASELINE
    # v0.01 主链仍以 z-score 为正式口径；percentile 对照只放在实验模块中。
    return {
        "market_coefficient": zscore_single(
            raw["market_coefficient_raw"],
            base["market_coefficient_mean"],
            base["market_coefficient_std"],
        ),
        "profit_effect": zscore_single(
            raw["profit_effect_raw"],
            base["profit_effect_mean"],
            base["profit_effect_std"],
        ),
        "loss_effect": zscore_single(
            raw["loss_effect_raw"],
            base["loss_effect_mean"],
            base["loss_effect_std"],
        ),
        "continuity": zscore_single(
            raw["continuity_raw"],
            base["continuity_mean"],
            base["continuity_std"],
        ),
        "extreme": zscore_single(
            raw["extreme_raw"],
            base["extreme_mean"],
            base["extreme_std"],
        ),
        "volatility": zscore_single(
            raw["volatility_raw"],
            base["volatility_mean"],
            base["volatility_std"],
        ),
    }


def _aggregate_mss_score(components: dict[str, float]) -> float:
    return float(
        np.clip(
            0.17 * components["market_coefficient"]
            + 0.34 * components["profit_effect"]
            + 0.34 * (100.0 - components["loss_effect"])
            + 0.05 * components["continuity"]
            + 0.05 * components["extreme"]
            + 0.05 * (100.0 - components["volatility"]),
            0.0,
            100.0,
        )
    )


def _compute_mss_components(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> tuple[
    date,
    float,
    Literal["BULLISH", "NEUTRAL", "BEARISH"],
    float,
    float,
    float,
    float,
    float,
    float,
]:
    raw = _compute_mss_raw_components(row)
    components = _normalize_mss_components(raw, baseline=baseline)
    score = _aggregate_mss_score(components)

    d = row["date"]
    if isinstance(d, pd.Timestamp):
        d = d.date()
    return (
        d,
        score,
        _signal_from_score(score, bullish_threshold=bullish_threshold, bearish_threshold=bearish_threshold),
        components["market_coefficient"],
        components["profit_effect"],
        components["loss_effect"],
        components["continuity"],
        components["extreme"],
        components["volatility"],
    )


def build_mss_raw_frame(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    if snapshot_df is None or snapshot_df.empty:
        return pd.DataFrame(columns=["date"] + [f"{name}_raw" for name in MSS_FACTOR_NAMES])
    records: list[dict[str, float | date]] = []
    for _, row in snapshot_df.iterrows():
        d = row["date"]
        if isinstance(d, pd.Timestamp):
            d = d.date()
        raw = _compute_mss_raw_components(row)
        records.append({"date": d, **raw})
    return pd.DataFrame(records)


def calibrate_mss_baseline(raw_df: pd.DataFrame) -> dict[str, float]:
    baseline: dict[str, float] = {}
    for factor in MSS_FACTOR_NAMES:
        values = pd.to_numeric(raw_df.get(f"{factor}_raw"), errors="coerce").dropna()
        mean = float(values.mean()) if not values.empty else 0.0
        std = float(values.std(ddof=0)) if not values.empty else 1.0
        baseline[f"{factor}_mean"] = mean
        baseline[f"{factor}_std"] = std if std > 0 else 1.0
    return baseline


def score_mss_raw_frame(
    raw_df: pd.DataFrame,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["date", "score", "signal"] + MSS_FACTOR_NAMES)

    base = baseline or MSS_BASELINE
    rows: list[dict[str, float | str | date]] = []
    for _, row in raw_df.iterrows():
        raw = {key: float(row[key]) for key in raw_df.columns if key.endswith("_raw")}
        components = _normalize_mss_components(raw, baseline=base)
        score = _aggregate_mss_score(components)
        if score >= bullish_threshold:
            signal = "BULLISH"
        elif score <= bearish_threshold:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        d = row["date"]
        if isinstance(d, pd.Timestamp):
            d = d.date()
        rows.append({"date": d, "score": score, "signal": signal, **components})
    return pd.DataFrame(rows)


def compute_mss_single(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> MarketScore:
    """
    MSS 单日纯函数：
    输入是一行 l2_market_snapshot，输出 MarketScore。
    """
    d, score, signal, *_ = _compute_mss_components(
        row,
        baseline=baseline,
        bullish_threshold=bullish_threshold,
        bearish_threshold=bearish_threshold,
    )
    return MarketScore(date=d, score=score, signal=signal)


def compute_mss(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> int:
    """
    批量计算 MSS 并写入 l3_mss_daily（幂等 upsert）。
    """
    df = store.read_df(
        """
        SELECT * FROM l2_market_snapshot
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if df.empty:
        return 0

    records = []
    for _, row in df.iterrows():
        (
            score_date,
            score,
            signal,
            market_coefficient,
            profit_effect,
            loss_effect,
            continuity,
            extreme,
            volatility,
        ) = _compute_mss_components(
            row,
            baseline=baseline,
            bullish_threshold=bullish_threshold,
            bearish_threshold=bearish_threshold,
        )
        records.append(
            {
                "date": score_date,
                "score": score,
                "signal": signal,
                "market_coefficient": market_coefficient,
                "profit_effect": profit_effect,
                "loss_effect": loss_effect,
                "continuity": continuity,
                "extreme": extreme,
                "volatility": volatility,
            }
        )
    return store.bulk_upsert("l3_mss_daily", pd.DataFrame(records))





