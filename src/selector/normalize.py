from __future__ import annotations

"""Selector 家族共用的数值归一化工具。

MSS、IRS、Selector 诊断以及若干研究脚本，都需要同一套基础数值口径：
1. 安全除法：分母为 0、缺失、非有限值时不炸掉。
2. zscore 映射：统一投到 [0, 100] 的解释空间。

把这些原语集中在这里，是为了防止各模块各写各的，最后出现“都叫 score，
但口径完全不同”的隐性漂移。

冻结口径：
- `zscore_single` / `zscore_normalize` 都按 `[-3σ, +3σ] -> [0, 100]` 映射
- `std=0` 或不可用时，统一回退到 `50.0`，代表中性值
"""

import numpy as np
import pandas as pd


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    """单值安全除法。

    常用于市场快照、行业统计、流动性指标这类经常会碰到 0 / NaN 分母的场景。
    遇到异常分母时直接回退到 `default`，而不是返回 `inf / nan` 或抛异常。
    """

    # 这里故意不抛异常：Selector 相关模块大量面对真实市场脏数据，
    # “给出稳定默认值继续运行”比“中途炸掉整条链路”更符合主线要求。
    if denominator in (0, None) or np.isnan(denominator):
        return default
    if numerator is None or np.isnan(numerator):
        return default
    return float(numerator) / float(denominator)


def safe_ratio_vec(
    numerator: pd.Series | np.ndarray, denominator: pd.Series | np.ndarray, default: float = 0.0
) -> np.ndarray:
    """向量化安全除法。

    语义和 `safe_ratio` 完全一致，只是改成批量版本，供构造因子 DataFrame
    时使用，避免逐行循环。
    """

    num = np.asarray(numerator, dtype=float)
    den = np.asarray(denominator, dtype=float)
    mask = np.isfinite(den) & (den != 0) & np.isfinite(num)
    out = np.full_like(num, fill_value=default, dtype=float)
    out[mask] = num[mask] / den[mask]
    return out


def zscore_normalize(series: pd.Series, baseline_mean: float | None = None, baseline_std: float | None = None) -> pd.Series:
    """把一列数映射到共享的 `[0, 100]` 分数空间。

    规则：
    - 默认用序列自身的均值/标准差，适合探索分析。
    - 传入 `baseline_mean / baseline_std` 时，按冻结基线映射，适合正式链路。
    - 映射公式：`score = clip((z + 3) / 6 * 100, 0, 100)`。
    """

    # 先统一转成 float，保证上游即使传来 object 列，也会在这里一次性暴露问题，
    # 而不是在后续 clip / 减法里零散出错。
    values = series.astype(float)
    mean = float(values.mean()) if baseline_mean is None else float(baseline_mean)
    std = float(values.std(ddof=0)) if baseline_std is None else float(baseline_std)
    if std == 0 or np.isnan(std):
        return pd.Series(np.full(len(values), 50.0), index=series.index, dtype=float)
    z = (values - mean) / std
    return pd.Series(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0), index=series.index, dtype=float)


def zscore_single(value: float, mean: float, std: float) -> float:
    """单值版 zscore 映射。

    给 MSS / IRS 这类逐行评分器使用，保证它们和 `zscore_normalize`
    共用同一套数值口径。
    """

    # 50 代表“中性、不可区分”，不是好也不是坏；
    # 这比返回 0/100 更安全，因为后者会把不可判定误解释成极端状态。
    if std == 0 or np.isnan(std):
        return 50.0
    z = (value - mean) / std
    return float(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0))
