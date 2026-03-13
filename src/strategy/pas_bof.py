from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_common import base_trace, clip, missing_required_columns, sort_history
from src.strategy.pattern_base import PatternDetector


@dataclass
class BofParams:
    break_pct: float = 0.01
    volume_mult: float = 1.2


class BofDetector(PatternDetector):
    name = "bof"

    def __init__(self, config: Settings):
        self.params = BofParams(
            break_pct=config.pas_bof_break_pct,
            volume_mult=config.pas_bof_volume_mult,
        )

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        reason_code = "PAS_BOF"
        trace = base_trace(
            code=code,
            asof_date=asof_date,
            pattern=self.name,
            reason_code=reason_code,
            history_days=len(df),
            min_history_days=21,
        )
        if df.empty or len(df) < 21:
            trace["skip_reason"] = "INSUFFICIENT_HISTORY"
            trace["detect_reason"] = "INSUFFICIENT_HISTORY"
            return None, trace

        data = sort_history(df)
        if missing_required_columns(data):
            trace["skip_reason"] = "MISSING_REQUIRED_COLUMNS"
            trace["detect_reason"] = "MISSING_REQUIRED_COLUMNS"
            return None, trace

        lookback = data.iloc[-21:-1]
        today = data.iloc[-1]
        lower_bound = float(lookback["adj_low"].min())
        lookback_high_20 = float(lookback["adj_high"].max())
        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        trace.update(
            {
                "lower_bound": lower_bound,
                "lookback_high_20": lookback_high_20,
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
            }
        )

        if today_high <= today_low:
            trace["skip_reason"] = "INVALID_RANGE"
            trace["detect_reason"] = "INVALID_RANGE"
            return None, trace

        cond_break = today_low < lower_bound * (1 - self.params.break_pct)
        cond_recover = today_close >= lower_bound
        close_pos = (today_close - today_low) / (today_high - today_low)
        body_ratio = abs(today_close - today_open) / (today_high - today_low)
        cond_close_pos = close_pos >= 0.6
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        cond_volume = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        trace.update(
            {
                "close_pos": float(close_pos),
                "body_ratio": float(body_ratio),
                "volume_ratio": float(volume_ratio),
                "cond_break": bool(cond_break),
                "cond_recover": bool(cond_recover),
                "cond_close_pos": bool(cond_close_pos),
                "cond_volume": bool(cond_volume),
            }
        )

        if not cond_break:
            trace["skip_reason"] = "NO_BREAK"
            trace["detect_reason"] = "NO_BREAK"
            return None, trace
        if not cond_recover:
            trace["skip_reason"] = "NO_RECOVERY"
            trace["detect_reason"] = "NO_RECOVERY"
            return None, trace
        if not cond_close_pos:
            trace["skip_reason"] = "LOW_CLOSE_POSITION"
            trace["detect_reason"] = "LOW_CLOSE_POSITION"
            return None, trace
        if not cond_volume:
            trace["skip_reason"] = "LOW_VOLUME"
            trace["detect_reason"] = "LOW_VOLUME"
            return None, trace

        strength = clip(0.4 * close_pos + 0.3 * min(volume_ratio / 2.0, 1.0) + 0.3 * body_ratio)
        trace.update(
            {
                "triggered": True,
                "detect_reason": "TRIGGERED",
                "strength": strength,
                "pattern_strength": strength,
                "bof_strength": strength,
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
