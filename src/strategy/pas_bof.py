from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from src.config import Settings
from src.contracts import Signal, build_signal_id
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
        """
        BOF(Spring) v0.01 判定：
        1) Low < LowerBound * (1-break_pct)
        2) Close >= LowerBound
        3) 收盘位于当日振幅上 60%
        4) Volume >= SMA20(volume) * volume_mult
        """
        signal_id = build_signal_id(code, asof_date, self.name)
        trace: dict[str, object] = {
            "signal_id": signal_id,
            "pattern": self.name,
            "triggered": False,
            "skip_reason": None,
            "reason_code": "PAS_BOF",
            "history_days": int(len(df)),
            "min_history_days": 21,
            "lower_bound": None,
            "today_low": None,
            "today_close": None,
            "today_open": None,
            "today_high": None,
            "close_pos": None,
            "volume": None,
            "volume_ma20": None,
            "volume_ratio": None,
            "cond_break": None,
            "cond_recover": None,
            "cond_close_pos": None,
            "cond_volume": None,
            "strength": None,
            "bof_strength": None,
        }

        if df.empty or len(df) < 21:
            trace["skip_reason"] = "INSUFFICIENT_HISTORY"
            return None, trace

        data = df.sort_values("date").reset_index(drop=True)
        lookback = data.iloc[-21:-1]
        if len(lookback) < 20:
            trace["skip_reason"] = "INSUFFICIENT_HISTORY"
            return None, trace

        required_cols = {"adj_low", "adj_close", "adj_open", "adj_high", "volume", "volume_ma20"}
        if not required_cols.issubset(set(data.columns)):
            trace["skip_reason"] = "MISSING_REQUIRED_COLUMNS"
            return None, trace

        today = data.iloc[-1]
        lower_bound = float(lookback["adj_low"].min())
        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)

        trace.update(
            {
                "lower_bound": lower_bound,
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
            return None, trace

        cond_break = today_low < lower_bound * (1 - self.params.break_pct)
        cond_recover = today_close >= lower_bound
        close_pos = (today_close - today_low) / (today_high - today_low)
        cond_close_pos = close_pos >= 0.6
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        cond_volume = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "close_pos": float(close_pos),
                "volume_ratio": float(volume_ratio),
                "cond_break": bool(cond_break),
                "cond_recover": bool(cond_recover),
                "cond_close_pos": bool(cond_close_pos),
                "cond_volume": bool(cond_volume),
            }
        )

        if not cond_break:
            trace["skip_reason"] = "NO_BREAK"
            return None, trace
        if not cond_recover:
            trace["skip_reason"] = "NO_RECOVERY"
            return None, trace
        if not cond_close_pos:
            trace["skip_reason"] = "LOW_CLOSE_POSITION"
            return None, trace
        if not cond_volume:
            trace["skip_reason"] = "LOW_VOLUME"
            return None, trace

        body_ratio = abs(today_close - today_open) / (today_high - today_low)
        strength = float(np.clip(0.4 * close_pos + 0.3 * min(volume_ratio / 2, 1) + 0.3 * body_ratio, 0, 1))
        trace.update(
            {
                "triggered": True,
                "strength": strength,
                "bof_strength": strength,
            }
        )

        return (
            Signal(
                signal_id=signal_id,
                code=code,
                signal_date=asof_date,
                action="BUY",
                strength=strength,
                pattern=self.name,
                reason_code="PAS_BOF",
            ),
            trace,
        )

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
