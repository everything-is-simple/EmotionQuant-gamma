from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pattern_base import PatternDetector
from src.strategy.pas_support import REQUIRED_COLUMNS, EPS, build_signal, clip, fail_trace, init_trace, normalize_history, safe_ratio


@dataclass
class TstParams:
    distance_max: float = 0.03
    volume_mult: float = 1.1


class TstDetector(PatternDetector):
    name = "tst"
    required_window = 61

    def __init__(self, config: Settings):
        self.params = TstParams(
            distance_max=config.pas_tst_distance_max,
            volume_mult=config.pas_tst_volume_mult,
        )

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update(
            {
                "required_window": self.required_window,
                "required_mult": self.params.volume_mult,
            }
        )
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        today = data.iloc[-1]
        structure_window = data.iloc[-61:-6]
        test_window = data.iloc[-6:-1]
        if len(structure_window) < 55 or len(test_window) < 5:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        support_level = float(structure_window["adj_low"].min())
        structure_high = float(structure_window["adj_high"].max())
        test_low = float(test_window["adj_low"].min())
        test_high_ref = float(test_window["adj_high"].max())
        test_distance = abs(test_low - support_level) / max(support_level, EPS)
        lower_shadow_ratio = (min(today_open, today_close) - today_low) / max(today_high - today_low, EPS)
        volume_ratio = safe_ratio(today_volume, volume_ma20)

        near_support = test_distance <= self.params.distance_max
        support_hold = today_close >= support_level
        bounce_confirm = today_close > test_high_ref or (today_close > today_open and today_close > support_level * 1.01)
        rejection_candle = lower_shadow_ratio >= 0.35
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        support_closeness = 1.0 - clip(test_distance / max(self.params.distance_max, EPS))
        bounce_strength = clip((today_close - support_level) / max(0.05 * support_level, EPS))
        rejection_strength = clip(lower_shadow_ratio)

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "support_level": support_level,
                "structure_high": structure_high,
                "test_distance": float(test_distance),
                "lower_shadow_ratio": float(lower_shadow_ratio),
                "support_closeness": support_closeness,
                "bounce_strength": bounce_strength,
                "rejection_strength": rejection_strength,
            }
        )

        if not near_support:
            return fail_trace(trace, "SUPPORT_TOO_FAR")
        if not support_hold:
            return fail_trace(trace, "SUPPORT_LOST")
        if not bounce_confirm:
            return fail_trace(trace, "NO_BOUNCE_CONFIRM")
        if not rejection_candle:
            return fail_trace(trace, "NO_REJECTION_CANDLE")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        strength = clip(
            0.35 * support_closeness
            + 0.30 * bounce_strength
            + 0.20 * rejection_strength
            + 0.15 * min(volume_ratio / 1.5, 1.0)
        )
        trace.update({"triggered": True, "strength": strength})
        signal = build_signal(code, asof_date, self.name, strength)
        return signal, trace

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
