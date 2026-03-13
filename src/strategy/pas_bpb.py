from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_common import EPSILON, base_trace, clip, missing_required_columns, sort_history
from src.strategy.pattern_base import PatternDetector


@dataclass
class BpbParams:
    breakout_window: int = 20
    pullback_min: float = 0.25
    pullback_max: float = 0.80
    volume_mult: float = 1.2


class BpbDetector(PatternDetector):
    name = "bpb"

    def __init__(self, config: Settings):
        self.params = BpbParams(
            breakout_window=config.pas_bpb_breakout_window,
            pullback_min=config.pas_bpb_pullback_min,
            pullback_max=config.pas_bpb_pullback_max,
            volume_mult=config.pas_bpb_volume_mult,
        )

    @property
    def required_history_days(self) -> int:
        return self.params.breakout_window + 6

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        reason_code = "PAS_BPB"
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

        setup_window = data.iloc[-(self.params.breakout_window + 6) : -6]
        pullback_window = data.iloc[-6:-1]
        today = data.iloc[-1]
        if setup_window.empty or pullback_window.empty:
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

        breakout_ref = float(setup_window["adj_high"].max())
        base_low = float(setup_window["adj_low"].min())
        breakout_peak = float(pullback_window["adj_high"].max())
        pullback_low = float(pullback_window["adj_low"].min())
        breakout_mask = (
            (pullback_window["adj_close"] > breakout_ref)
            & (pullback_window["volume"] / pullback_window["volume_ma20"].replace(0, pd.NA) >= 1.2)
        ).fillna(False)
        breakout_leg_exists = bool(breakout_mask.any())
        support_hold = pullback_low >= breakout_ref * (1 - 0.03)
        pullback_depth = (breakout_peak - pullback_low) / max(breakout_peak - breakout_ref, EPSILON)
        pullback_depth_valid = self.params.pullback_min <= pullback_depth <= self.params.pullback_max
        pullback_high = float(pullback_window["adj_high"].max())
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        confirmation = (
            today_close > pullback_high
            and today_close >= breakout_ref
            and today_volume >= volume_ma20 * self.params.volume_mult
        )
        not_overextended = today_close <= breakout_peak * 1.03
        body_ratio = abs(today_close - today_open) / (today_high - today_low)

        trace.update(
            {
                "base_low": base_low,
                "breakout_ref": breakout_ref,
                "breakout_peak": breakout_peak,
                "pullback_low": pullback_low,
                "pullback_depth": float(pullback_depth),
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "body_ratio": float(body_ratio),
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": float(volume_ratio),
            }
        )

        if not breakout_leg_exists:
            trace["skip_reason"] = "NO_BREAKOUT_LEG"
            trace["detect_reason"] = "NO_BREAKOUT_LEG"
            return None, trace
        if not support_hold:
            trace["skip_reason"] = "SUPPORT_LOST"
            trace["detect_reason"] = "SUPPORT_LOST"
            return None, trace
        if not pullback_depth_valid:
            trace["skip_reason"] = "PULLBACK_NOT_VALID"
            trace["detect_reason"] = "PULLBACK_NOT_VALID"
            return None, trace
        if not confirmation:
            trace["skip_reason"] = "NO_CONFIRMATION"
            trace["detect_reason"] = "NO_CONFIRMATION"
            return None, trace
        if not not_overextended:
            trace["skip_reason"] = "OVEREXTENDED_CONFIRM"
            trace["detect_reason"] = "OVEREXTENDED_CONFIRM"
            return None, trace

        confirm_strength = clip((today_close - breakout_ref) / max(0.10 * breakout_ref, EPSILON))
        volume_strength = clip(volume_ratio / 2.0)
        if 0.40 <= pullback_depth <= 0.60:
            depth_quality = 1.0
        elif self.params.pullback_min <= pullback_depth <= self.params.pullback_max:
            depth_quality = 0.7
        else:
            depth_quality = 0.0
        strength = clip(
            0.40 * confirm_strength
            + 0.25 * volume_strength
            + 0.20 * depth_quality
            + 0.15 * body_ratio
        )
        trace.update(
            {
                "triggered": True,
                "detect_reason": "TRIGGERED",
                "strength": strength,
                "pattern_strength": strength,
                "bof_strength": strength,
                "confirm_strength": confirm_strength,
                "support_hold_score": 1.0 - clip(max(breakout_ref - pullback_low, 0.0) / max(0.03 * breakout_ref, EPSILON)),
                "depth_score": depth_quality,
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
