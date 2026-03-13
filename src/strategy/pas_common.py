from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.contracts import build_signal_id

EPSILON = 1e-9
PAS_REQUIRED_COLUMNS = {
    "date",
    "adj_low",
    "adj_close",
    "adj_open",
    "adj_high",
    "volume",
    "volume_ma20",
}
PATTERN_GROUP_YTC = "YTC"


def clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return float(np.clip(value, lower, upper))


def missing_required_columns(df: pd.DataFrame) -> set[str]:
    return PAS_REQUIRED_COLUMNS.difference(df.columns)


def sort_history(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("date").reset_index(drop=True)


def base_trace(
    *,
    code: str,
    asof_date: date,
    pattern: str,
    reason_code: str,
    history_days: int,
    min_history_days: int,
) -> dict[str, object]:
    return {
        "signal_id": build_signal_id(code, asof_date, pattern),
        "pattern": pattern,
        "triggered": False,
        "skip_reason": None,
        "detect_reason": None,
        "reason_code": reason_code,
        "history_days": int(history_days),
        "min_history_days": int(min_history_days),
        "strength": None,
        "bof_strength": None,
        "lower_bound": None,
        "lookback_high_20": None,
        "today_low": None,
        "today_close": None,
        "today_open": None,
        "today_high": None,
        "close_pos": None,
        "body_ratio": None,
        "volume": None,
        "volume_ma20": None,
        "volume_ratio": None,
        "cond_break": None,
        "cond_recover": None,
        "cond_close_pos": None,
        "cond_volume": None,
        "base_low": None,
        "breakout_ref": None,
        "breakout_peak": None,
        "pullback_low": None,
        "pullback_depth": None,
        "rebound_ref": None,
        "trend_peak": None,
        "trend_floor": None,
        "mid_floor": None,
        "support_level": None,
        "structure_high": None,
        "test_low": None,
        "test_high_ref": None,
        "test_distance": None,
        "lower_shadow_ratio": None,
        "support_band_low": None,
        "support_band_high": None,
        "neckline_ref": None,
        "retest_count": None,
        "compression_width": None,
        "entry_ref": None,
        "stop_ref": None,
        "target_ref": None,
        "risk_reward_ref": None,
        "failure_handling_tag": None,
        "pattern_quality_score": None,
        "quality_breakdown_json": None,
        "quality_status": None,
        "reference_status": None,
        "pattern_group": PATTERN_GROUP_YTC,
        "registry_run_label": None,
    }

