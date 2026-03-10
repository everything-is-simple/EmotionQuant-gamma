from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pattern_base import PatternDetector
from src.strategy.pas_support import REQUIRED_COLUMNS, EPS, build_signal, clip, fail_trace, init_trace, normalize_history, safe_ratio


@dataclass
class PbParams:
    volume_mult: float = 1.15


class PbDetector(PatternDetector):
    """
    PB (Pullback) 趋势回踩形态检测器（Phase 1 核心）：
    
    形态定义：
    1. 趋势确立（41日双窗口）：近期高点 > 远期高点，近期低点 > 远期低点
    2. 回踩整理（5日窗口）：回踩深度 20-50%，守住中期低点
    3. 反弹确认（当日）：收盘突破回踩高点 + 放量 + 不过度延伸
    
    窗口要求：41 日（20日远期 + 15日近期 + 5日回踩 + 当日）
    """
    name = "pb"
    required_window = 41

    def __init__(self, config: Settings):
        self.params = PbParams(volume_mult=config.pas_pb_volume_mult)

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        today = data.iloc[-1]
        # PB 先看趋势是否已经抬升，再看回踩是否健康，最后才看今天的反弹确认。
        trend_window_a = data.iloc[-41:-21]
        trend_window_b = data.iloc[-21:-6]
        pullback_window = data.iloc[-6:-1]
        if len(trend_window_a) < 20 or len(trend_window_b) < 15 or len(pullback_window) < 5:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        trend_peak = float(trend_window_b["adj_high"].max())
        trend_floor = float(trend_window_a["adj_low"].min())
        mid_floor = float(trend_window_b["adj_low"].min())
        pullback_low = float(pullback_window["adj_low"].min())
        rebound_ref = float(pullback_window["adj_high"].max())
        volume_ratio = safe_ratio(today_volume, volume_ma20)

        # PB 不是单纯“跌了又弹”，而是已经存在一段向上的结构抬升。
        trend_established = float(trend_window_b["adj_high"].max()) > float(trend_window_a["adj_high"].max()) and mid_floor > trend_floor
        pullback_depth = (trend_peak - pullback_low) / max(trend_peak - trend_floor, EPS)
        pullback_depth_valid = 0.20 <= pullback_depth <= 0.50
        support_hold = pullback_low >= mid_floor * 0.98
        rebound_confirm = today_close > rebound_ref and today_close <= trend_peak * 1.03
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        rebound_strength = clip((today_close - rebound_ref) / max(0.08 * rebound_ref, EPS))
        depth_quality = 1.0 if 0.25 <= pullback_depth <= 0.40 else 0.7 if 0.20 <= pullback_depth <= 0.50 else 0.0
        trend_quality = clip((mid_floor - trend_floor) / max(0.10 * trend_floor, EPS))

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "trend_peak": trend_peak,
                "trend_floor": trend_floor,
                "mid_floor": mid_floor,
                "pullback_low": pullback_low,
                "rebound_ref": rebound_ref,
                "pullback_depth": float(pullback_depth),
                "rebound_strength": rebound_strength,
                "depth_quality": depth_quality,
                "trend_quality": trend_quality,
            }
        )

        if not trend_established:
            return fail_trace(trace, "TREND_NOT_ESTABLISHED")
        if not pullback_depth_valid or not support_hold:
            return fail_trace(trace, "PULLBACK_NOT_VALID")
        if not rebound_confirm:
            return fail_trace(trace, "NO_REBOUND_CONFIRM")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        # 强度拆成“反弹质量 + 回踩质量 + 趋势质量 + 量能确认”，便于后续 ablation 解释。
        strength = clip(
            0.35 * rebound_strength + 0.25 * depth_quality + 0.20 * trend_quality + 0.20 * min(volume_ratio / 2.0, 1.0)
        )
        trace.update({"triggered": True, "strength": strength})
        signal = build_signal(code, asof_date, self.name, strength)
        return signal, trace

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
