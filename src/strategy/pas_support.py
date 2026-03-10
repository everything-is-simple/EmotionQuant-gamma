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
    return df.sort_values("date").reset_index(drop=True)


def init_trace(code: str, asof_date: date, pattern: str, history_days: int) -> dict[str, object]:
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
    trace["skip_reason"] = reason
    trace["detect_reason"] = reason
    return None, trace


def build_signal(code: str, asof_date: date, pattern: str, strength: float) -> Signal:
    return Signal(
        signal_id=build_signal_id(code, asof_date, pattern),
        code=code,
        signal_date=asof_date,
        action="BUY",
        strength=float(strength),
        pattern=pattern,
        reason_code=f"PAS_{pattern.upper()}",
    )
