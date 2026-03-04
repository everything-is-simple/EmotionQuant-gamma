from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.contracts import MarketScore
from src.data.store import Store
from src.selector.baseline import MSS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single


def _signal_from_score(score: float) -> str:
    if score >= 60:
        return "BULLISH"
    if score <= 40:
        return "BEARISH"
    return "NEUTRAL"


def compute_mss_single(row: pd.Series, baseline: dict[str, float] | None = None) -> MarketScore:
    """
    MSS 单日纯函数：
    输入是一行 l2_market_snapshot，输出 MarketScore。
    """
    base = baseline or MSS_BASELINE

    market_coefficient_raw = safe_ratio(row.get("rise_count", 0), row.get("fall_count", 0), default=1.0)
    profit_effect_raw = safe_ratio(row.get("strong_up_count", 0), row.get("total_stocks", 0), default=0.0)
    loss_effect_raw = safe_ratio(row.get("strong_down_count", 0), row.get("total_stocks", 0), default=0.0)
    continuity_raw = safe_ratio(
        row.get("continuous_limit_up_2d", 0) + row.get("continuous_limit_up_3d_plus", 0),
        row.get("limit_up_count", 0),
        default=0.0,
    )
    extreme_raw = safe_ratio(
        row.get("limit_up_count", 0) - row.get("limit_down_count", 0),
        row.get("total_stocks", 0),
        default=0.0,
    )
    volatility_raw = float(row.get("pct_chg_std", 0.0) or 0.0)

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

    # 线性合成温度：loss/volatility 作为负向因子，先乘 -1 再入权重。
    score_z = (
        0.20 * market_coefficient
        + 0.20 * profit_effect
        - 0.20 * loss_effect
        + 0.15 * continuity
        + 0.15 * extreme
        - 0.10 * volatility
    )
    score = float(np.clip(50 + score_z * 10, 0, 100))

    d = row["date"]
    if isinstance(d, pd.Timestamp):
        d = d.date()
    return MarketScore(date=d, score=score, signal=_signal_from_score(score))


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
        result = compute_mss_single(row, baseline=baseline)
        records.append(
            {
                "date": result.date,
                "score": result.score,
                "signal": result.signal,
                # v0.01 先写基础分，后续可追加入库每个分项。
                "market_coefficient": None,
                "profit_effect": None,
                "loss_effect": None,
                "continuity": None,
                "extreme": None,
                "volatility": None,
            }
        )
    return store.bulk_upsert("l3_mss_daily", pd.DataFrame(records))

