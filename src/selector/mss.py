from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.contracts import MarketScore
from src.data.store import Store
from src.selector.baseline import MSS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single


def _signal_from_score(score: float) -> str:
    if score >= 65:
        return "BULLISH"
    if score <= 35:
        return "BEARISH"
    return "NEUTRAL"


def _compute_mss_components(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
) -> tuple[date, float, str, float, float, float, float, float, float]:
    base = baseline or MSS_BASELINE

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

    market_coefficient = zscore_single(
        market_coefficient_raw,
        base["market_coefficient_mean"],
        base["market_coefficient_std"],
    )
    profit_effect = zscore_single(profit_effect_raw, base["profit_effect_mean"], base["profit_effect_std"])
    loss_effect = zscore_single(loss_effect_raw, base["loss_effect_mean"], base["loss_effect_std"])
    continuity = zscore_single(continuity_raw, base["continuity_mean"], base["continuity_std"])
    extreme = zscore_single(extreme_raw, base["extreme_mean"], base["extreme_std"])
    volatility = zscore_single(volatility_raw, base["volatility_mean"], base["volatility_std"])

    score = float(
        np.clip(
            0.17 * market_coefficient
            + 0.34 * profit_effect
            + 0.34 * (100.0 - loss_effect)
            + 0.05 * continuity
            + 0.05 * extreme
            + 0.05 * (100.0 - volatility),
            0.0,
            100.0,
        )
    )

    d = row["date"]
    if isinstance(d, pd.Timestamp):
        d = d.date()
    return (
        d,
        score,
        _signal_from_score(score),
        market_coefficient,
        profit_effect,
        loss_effect,
        continuity,
        extreme,
        volatility,
    )


def compute_mss_single(row: pd.Series, baseline: dict[str, float] | None = None) -> MarketScore:
    """
    MSS 单日纯函数：
    输入是一行 l2_market_snapshot，输出 MarketScore。
    """
    d, score, signal, *_ = _compute_mss_components(row, baseline=baseline)
    return MarketScore(date=d, score=score, signal=signal)


def compute_mss(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
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
        ) = _compute_mss_components(row, baseline=baseline)
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
