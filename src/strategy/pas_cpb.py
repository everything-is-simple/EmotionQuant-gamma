from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_common import EPSILON, base_trace, clip, missing_required_columns, sort_history
from src.strategy.pattern_base import PatternDetector


@dataclass
class CpbParams:
    retest_min: int = 2
    neckline_break_pct: float = 0.01
    volume_mult: float = 1.2


class CpbDetector(PatternDetector):
    name = "cpb"

    def __init__(self, config: Settings):
        self.params = CpbParams(
            retest_min=config.pas_cpb_retest_min,
            neckline_break_pct=config.pas_cpb_neckline_break_pct,
            volume_mult=config.pas_cpb_volume_mult,
        )

    @property
    def required_history_days(self) -> int:
        return 41

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        reason_code = "PAS_CPB"
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

        base_window = data.iloc[-21:-1]
        today = data.iloc[-1]
        if base_window.empty:
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

        support_band_low = float(base_window["adj_low"].min())
        support_band_high = float(base_window["adj_low"].quantile(0.35))
        neckline_ref = float(base_window["adj_high"].max())
        retest_mask = (base_window["adj_low"] >= support_band_low) & (base_window["adj_low"] <= support_band_high)
        retest_count = int(retest_mask.sum())
        compression_width = (float(base_window["adj_high"].max()) - support_band_low) / max(support_band_low, EPSILON)
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        retest_enough = retest_count >= self.params.retest_min
        support_band_valid = support_band_high / max(support_band_low, EPSILON) <= 1.03
        compression_valid = compression_width <= 0.12
        neckline_break = today_close > neckline_ref * (1 + self.params.neckline_break_pct)
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "support_band_low": support_band_low,
                "support_band_high": support_band_high,
                "neckline_ref": neckline_ref,
                "retest_count": retest_count,
                "compression_width": float(compression_width),
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": float(volume_ratio),
            }
        )

        if not retest_enough:
            trace["skip_reason"] = "RETEST_NOT_ENOUGH"
            trace["detect_reason"] = "RETEST_NOT_ENOUGH"
            return None, trace
        if not support_band_valid:
            trace["skip_reason"] = "SUPPORT_BAND_TOO_WIDE"
            trace["detect_reason"] = "SUPPORT_BAND_TOO_WIDE"
            return None, trace
        if not compression_valid:
            trace["skip_reason"] = "COMPRESSION_TOO_WIDE"
            trace["detect_reason"] = "COMPRESSION_TOO_WIDE"
            return None, trace
        if not neckline_break:
            trace["skip_reason"] = "NO_NECKLINE_BREAK"
            trace["detect_reason"] = "NO_NECKLINE_BREAK"
            return None, trace
        if not volume_confirm:
            trace["skip_reason"] = "LOW_VOLUME"
            trace["detect_reason"] = "LOW_VOLUME"
            return None, trace

        neckline_strength = clip((today_close - neckline_ref) / max(0.10 * neckline_ref, EPSILON))
        retest_quality = clip(retest_count / 3.0)
        compression_quality = 1.0 - clip(compression_width / 0.12)
        volume_strength = clip(volume_ratio / 2.0)
        strength = clip(
            0.35 * neckline_strength
            + 0.25 * retest_quality
            + 0.20 * compression_quality
            + 0.20 * volume_strength
        )
        trace.update(
            {
                "triggered": True,
                "detect_reason": "TRIGGERED",
                "strength": strength,
                "pattern_strength": strength,
                "bof_strength": strength,
                "neckline_strength": neckline_strength,
                "retest_quality": retest_quality,
                "compression_quality": compression_quality,
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
