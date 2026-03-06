from __future__ import annotations

import numpy as np
import pandas as pd


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    """单值安全除法：分母为 0 或空值时返回默认值。"""
    if denominator in (0, None) or np.isnan(denominator):
        return default
    if numerator is None or np.isnan(numerator):
        return default
    return float(numerator) / float(denominator)


def safe_ratio_vec(
    numerator: pd.Series | np.ndarray, denominator: pd.Series | np.ndarray, default: float = 0.0
) -> np.ndarray:
    """向量化安全除法，用于批量计算因子。"""
    num = np.asarray(numerator, dtype=float)
    den = np.asarray(denominator, dtype=float)
    mask = np.isfinite(den) & (den != 0) & np.isfinite(num)
    out = np.full_like(num, fill_value=default, dtype=float)
    out[mask] = num[mask] / den[mask]
    return out


def zscore_normalize(series: pd.Series, baseline_mean: float | None = None, baseline_std: float | None = None) -> pd.Series:
    """标准化到 0-100：默认用样本均值/标准差，也可注入基线参数。"""
    values = series.astype(float)
    mean = float(values.mean()) if baseline_mean is None else float(baseline_mean)
    std = float(values.std(ddof=0)) if baseline_std is None else float(baseline_std)
    if std == 0 or np.isnan(std):
        return pd.Series(np.full(len(values), 50.0), index=series.index, dtype=float)
    z = (values - mean) / std
    return pd.Series(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0), index=series.index, dtype=float)


def zscore_single(value: float, mean: float, std: float) -> float:
    """单值标准化到 0-100，避免在逐行纯函数里重复判断。"""
    if std == 0 or np.isnan(std):
        return 50.0
    z = (value - mean) / std
    return float(np.clip((z + 3.0) / 6.0 * 100.0, 0.0, 100.0))
