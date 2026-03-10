from __future__ import annotations

# ---------------------------------------------------------------------------
# normalize.py — 因子标准化工具函数
# ---------------------------------------------------------------------------
# 职责：提供跨模块共享的安全数值运算原语。
# 所有因子（MSS / IRS / Selector）的 zscore 标准化都必须通过这里，
# 禁止各模块自行实现，避免口径漂移。
#
# 核心口径（Frozen）：
#   zscore_single / zscore_normalize 的映射规则：[-3σ, +3σ] -> [0, 100]
#   std=0 时统一回退到 50.0（中性值），不抛异常。
# ---------------------------------------------------------------------------

import numpy as np
import pandas as pd


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    """单值安全除法：分母为 0 或 NaN 时返回默认值，避免 ZeroDivisionError 扩散。"""
    if denominator in (0, None) or np.isnan(denominator):
        return default
    if numerator is None or np.isnan(numerator):
        return default
    return float(numerator) / float(denominator)


def safe_ratio_vec(
    numerator: pd.Series | np.ndarray, denominator: pd.Series | np.ndarray, default: float = 0.0
) -> np.ndarray:
    """向量化安全除法：批量计算因子时使用，比逐行调用 safe_ratio 效率高一个量级。"""
    num = np.asarray(numerator, dtype=float)
    den = np.asarray(denominator, dtype=float)
    mask = np.isfinite(den) & (den != 0) & np.isfinite(num)
    out = np.full_like(num, fill_value=default, dtype=float)
    out[mask] = num[mask] / den[mask]
    return out


def zscore_normalize(series: pd.Series, baseline_mean: float | None = None, baseline_std: float | None = None) -> pd.Series:
    """
    序列标准化到 [0, 100]：
    - 默认用序列自身的均值/标准差（适合探索性分析）
    - 注入 baseline_mean / baseline_std 时使用预标定基线（适合生产主链）

    映射公式：score = clip((z + 3) / 6 * 100, 0, 100)
    其中 z = (value - mean) / std
    """
    values = series.astype(float)
    mean = float(values.mean()) if baseline_mean is None else float(baseline_mean)
    std = float(values.std(ddof=0)) if baseline_std is None else float(baseline_std)
    if std == 0 or np.isnan(std):
        return pd.Series(np.full(len(values), 50.0), index=series.index, dtype=float)
    z = (values - mean) / std
    return pd.Series(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0), index=series.index, dtype=float)


def zscore_single(value: float, mean: float, std: float) -> float:
    """
    单值标准化到 [0, 100]，与 zscore_normalize 保持同一口径。

    专为逐行纯函数（如 MSS / IRS 的逐日计算循环）设计，
    避免在热路径上重复实现 NaN 判断和 clip 逻辑。

    std=0 或 NaN 时回退到 50.0（中性值）。
    """
    if std == 0 or np.isnan(std):
        return 50.0
    z = (value - mean) / std
    return float(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0))
