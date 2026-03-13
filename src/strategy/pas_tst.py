from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_common import EPSILON, base_trace, clip, missing_required_columns, sort_history
from src.strategy.pattern_base import PatternDetector


@dataclass
class TstParams:
    distance_max: float = 0.03
    volume_mult: float = 1.0


class TstDetector(PatternDetector):
    name = "tst"

    def __init__(self, config: Settings):
        self.params = TstParams(
            distance_max=config.pas_tst_distance_max,
            volume_mult=config.pas_tst_volume_mult,
        )

    @property
    def required_history_days(self) -> int:
        return 61

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        reason_code = "PAS_TST"
        trace = base_trace(
            code=code,
            asof_date=asof_date,
            pattern=self.name,
            reason_code=reason_code,
            history_days=len(df),
            min_history_days=self.required_history_days,
        )
        if df.empty or len(df) < self.required_history_days:
            trace["skip_reason"] = "INSUFFICIENT_HISTORY"
            trace["detect_reason"] = "INSUFFICIENT_HISTORY"
            return None, trace

        data = sort_history(df)
        if missing_required_columns(data):
            trace["skip_reason"] = "MISSING_REQUIRED_COLUMNS"
            trace["detect_reason"] = "MISSING_REQUIRED_COLUMNS"
            return None, trace

        structure_window = data.iloc[-61:-6]
        test_window = data.iloc[-6:-1]
        today = data.iloc[-1]
        if structure_window.empty or test_window.empty:
            trace["skip_reason"] = "INSUFFICIENT_HISTORY"
            trace["detect_reason"] = "INSUFFICIENT_HISTORY"
            return None, trace

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        if today_high <= today_low:
            trace["skip_reason"] = "INVALID_RANGE"
            trace["detect_reason"] = "INVALID_RANGE"
            return None, trace

        support_level = float(structure_window["adj_low"].min())
        structure_high = float(structure_window["adj_high"].max())
        test_low = float(test_window["adj_low"].min())
        test_high_ref = float(test_window["adj_high"].max())
        test_distance = abs(test_low - support_level) / max(support_level, EPSILON)
        lower_shadow_ratio = (min(today_open, today_close) - today_low) / max(today_high - today_low, EPSILON)
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        near_support = test_distance <= self.params.distance_max
        support_hold = today_close >= support_level
        bounce_confirm = today_close > test_high_ref or (
            today_close > today_open and today_close > support_level * 1.01
        )
        rejection_candle = lower_shadow_ratio >= 0.35
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "support_level": support_level,
                "structure_high": structure_high,
                "test_low": test_low,
                "test_high_ref": test_high_ref,
                "test_distance": float(test_distance),
                "lower_shadow_ratio": float(lower_shadow_ratio),
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": float(volume_ratio),
            }
        )

        if not near_support:
            trace["skip_reason"] = "SUPPORT_TOO_FAR"
            trace["detect_reason"] = "SUPPORT_TOO_FAR"
            return None, trace
        if not support_hold:
            trace["skip_reason"] = "SUPPORT_LOST"
            trace["detect_reason"] = "SUPPORT_LOST"
            return None, trace
        if not bounce_confirm:
            trace["skip_reason"] = "NO_BOUNCE_CONFIRM"
            trace["detect_reason"] = "NO_BOUNCE_CONFIRM"
            return None, trace
        if not rejection_candle:
            trace["skip_reason"] = "NO_REJECTION_CANDLE"
            trace["detect_reason"] = "NO_REJECTION_CANDLE"
            return None, trace
        if not volume_confirm:
            trace["skip_reason"] = "LOW_VOLUME"
            trace["detect_reason"] = "LOW_VOLUME"
            return None, trace

        support_closeness = 1.0 - clip(test_distance / max(self.params.distance_max, EPSILON))
        bounce_strength = clip((today_close - support_level) / max(0.05 * support_level, EPSILON))
        rejection_strength = clip(lower_shadow_ratio)
        volume_strength = clip(volume_ratio / 1.5)
        strength = clip(
            0.35 * support_closeness
            + 0.30 * bounce_strength
            + 0.20 * rejection_strength
            + 0.15 * volume_strength
        )
        trace.update(
            {
                "triggered": True,
                "detect_reason": "TRIGGERED",
                "strength": strength,
                "pattern_strength": strength,
                "bof_strength": strength,
                "support_closeness": support_closeness,
                "bounce_strength": bounce_strength,
                "rejection_strength": rejection_strength,
            }
        )
        return (
            Signal(
                signal_id=str(trace["signal_id"]),
                code=code,
                signal_date=asof_date,
                action="BUY",
                strength=strength,
                pattern=self.name,
                reason_code=reason_code,
                pattern_strength=strength,
            ),
            trace,
        )
