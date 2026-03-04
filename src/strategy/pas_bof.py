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

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        """
        BOF(Spring) v0.01 判定：
        1) Low < LowerBound * (1-break_pct)
        2) Close >= LowerBound
        3) 收盘位于当日振幅上 60%
        4) Volume >= SMA20(volume) * volume_mult
        """
        if df.empty or len(df) < 21:
            return None

        # 防止调用方未排序导致时序错读。
        data = df.sort_values("date").reset_index(drop=True)
        today = data.iloc[-1]
        lookback = data.iloc[-21:-1]
        if len(lookback) < 20:
            return None

        required_cols = {"adj_low", "adj_close", "adj_open", "adj_high", "volume", "volume_ma20"}
        if not required_cols.issubset(set(data.columns)):
            return None

        lower_bound = float(lookback["adj_low"].min())
        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)

        if today_high <= today_low:
            return None

        cond_break = today_low < lower_bound * (1 - self.params.break_pct)
        cond_recover = today_close >= lower_bound
        close_pos = (today_close - today_low) / (today_high - today_low)
        cond_close_pos = close_pos >= 0.6
        cond_volume = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        if not (cond_break and cond_recover and cond_close_pos and cond_volume):
            return None

        # 强度用于同日同股排序，不改变 T+1 交易语义。
        body_ratio = abs(today_close - today_open) / (today_high - today_low)
        volume_ratio = today_volume / volume_ma20 if volume_ma20 > 0 else 0.0
        strength = float(np.clip(0.4 * close_pos + 0.3 * min(volume_ratio / 2, 1) + 0.3 * body_ratio, 0, 1))

        signal_id = build_signal_id(code, asof_date, self.name)
        return Signal(
            signal_id=signal_id,
            code=code,
            signal_date=asof_date,
            action="BUY",
            strength=strength,
            pattern=self.name,
            reason_code="PAS_BOF",
        )

