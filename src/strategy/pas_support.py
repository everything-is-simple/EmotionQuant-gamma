from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.contracts import Signal, build_signal_id

EPS = 1e-9
REQUIRED_COLUMNS = {"adj_low", "adj_close", "adj_open", "adj_high", "volume", "volume_ma20"}


def clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return float(np.clip(value, lower, upper))


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / denominator)


def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    # detector 一律基于升序时间序列工作，避免每个形态都自己重复处理排序细节。
    return df.sort_values("date").reset_index(drop=True)


def init_trace(code: str, asof_date: date, pattern: str, history_days: int) -> dict[str, object]:
    # 所有 detector 的 trace 先从统一骨架起步，再追加各自形态观测值。
    return {
        "signal_id": build_signal_id(code, asof_date, pattern),
        "pattern": pattern,
        "triggered": False,
        "skip_reason": None,
        "detect_reason": None,
        "reason_code": f"PAS_{pattern.upper()}",
        "history_days": int(history_days),
        "strength": None,
        "bof_strength": None,
    }


def fail_trace(trace: dict[str, object], reason: str) -> tuple[Signal | None, dict[str, object]]:
    # fail_trace 不抛异常，直接把失败原因落进 trace；
    # 这样 Strategy 可以把“没触发”和“触发成功”都统一写进真相源。
    trace["skip_reason"] = reason
    trace["detect_reason"] = reason
    return None, trace


def build_signal(code: str, asof_date: date, pattern: str, strength: float) -> Signal:
    # formal Signal 仍保持最小字段集，形态特有解释信息通过 trace / sidecar 落地。
    return Signal(
        signal_id=build_signal_id(code, asof_date, pattern),
        code=code,
        signal_date=asof_date,
        action="BUY",
        strength=float(strength),
        pattern=pattern,
        reason_code=f"PAS_{pattern.upper()}",
    )
