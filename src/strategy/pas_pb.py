from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_common import EPSILON, base_trace, clip, missing_required_columns, sort_history
from src.strategy.pattern_base import PatternDetector


@dataclass
class PbParams:
    pullback_min: float = 0.20
    pullback_max: float = 0.50
    volume_mult: float = 1.1


class PbDetector(PatternDetector):
    name = "pb"

    def __init__(self, config: Settings):
        self.params = PbParams(
            pullback_min=config.pas_pb_pullback_min,
            pullback_max=config.pas_pb_pullback_max,
            volume_mult=config.pas_pb_volume_mult,
        )

    @property
    def required_history_days(self) -> int:
        return 41

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        reason_code = "PAS_PB"
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

        trend_window_a = data.iloc[-41:-21]
        trend_window_b = data.iloc[-21:-6]
        pullback_window = data.iloc[-6:-1]
        today = data.iloc[-1]
        if trend_window_a.empty or trend_window_b.empty or pullback_window.empty:
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

        trend_peak = float(trend_window_b["adj_high"].max())
        trend_floor = float(trend_window_a["adj_low"].min())
        mid_floor = float(trend_window_b["adj_low"].min())
        pullback_low = float(pullback_window["adj_low"].min())
        rebound_ref = float(pullback_window["adj_high"].max())
        trend_established = (
            float(trend_window_b["adj_high"].max()) > float(trend_window_a["adj_high"].max())
            and mid_floor > trend_floor
        )
        pullback_depth = (trend_peak - pullback_low) / max(trend_peak - trend_floor, EPSILON)
        pullback_depth_valid = self.params.pullback_min <= pullback_depth <= self.params.pullback_max
        support_hold = pullback_low >= mid_floor * 0.98
        rebound_confirm = today_close > rebound_ref and today_close <= trend_peak * 1.03
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "trend_peak": trend_peak,
                "trend_floor": trend_floor,
                "mid_floor": mid_floor,
                "pullback_low": pullback_low,
                "pullback_depth": float(pullback_depth),
                "rebound_ref": rebound_ref,
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": float(volume_ratio),
            }
        )

        if not trend_established:
            trace["skip_reason"] = "TREND_NOT_ESTABLISHED"
            trace["detect_reason"] = "TREND_NOT_ESTABLISHED"
            return None, trace
        if not pullback_depth_valid:
            trace["skip_reason"] = "PULLBACK_NOT_VALID"
            trace["detect_reason"] = "PULLBACK_NOT_VALID"
            return None, trace
        if not support_hold:
            trace["skip_reason"] = "SUPPORT_LOST"
            trace["detect_reason"] = "SUPPORT_LOST"
            return None, trace
        if not rebound_confirm:
            trace["skip_reason"] = "NO_REBOUND_CONFIRM"
            trace["detect_reason"] = "NO_REBOUND_CONFIRM"
            return None, trace
        if not volume_confirm:
            trace["skip_reason"] = "LOW_VOLUME"
            trace["detect_reason"] = "LOW_VOLUME"
            return None, trace

        rebound_strength = clip((today_close - rebound_ref) / max(0.08 * rebound_ref, EPSILON))
        if 0.25 <= pullback_depth <= 0.40:
            depth_quality = 1.0
        elif self.params.pullback_min <= pullback_depth <= self.params.pullback_max:
            depth_quality = 0.7
        else:
            depth_quality = 0.0
        trend_quality = clip((mid_floor - trend_floor) / max(0.10 * trend_floor, EPSILON))
        volume_strength = clip(volume_ratio / 2.0)
        strength = clip(
            0.35 * rebound_strength
            + 0.25 * depth_quality
            + 0.20 * trend_quality
            + 0.20 * volume_strength
        )
        trace.update(
            {
                "triggered": True,
                "detect_reason": "TRIGGERED",
                "strength": strength,
                "pattern_strength": strength,
                "bof_strength": strength,
                "rebound_strength": rebound_strength,
                "depth_quality": depth_quality,
                "trend_quality": trend_quality,
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
