from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pattern_base import PatternDetector
from src.strategy.pas_support import REQUIRED_COLUMNS, EPS, build_signal, clip, fail_trace, init_trace, normalize_history, safe_ratio


@dataclass
class BpbParams:
    volume_mult: float = 1.2


class BpbDetector(PatternDetector):
    """
    BPB (Breakout-Pullback-Breakout) 形态检测器（Phase 1 核心）：
    
    形态定义：
    1. 前期突破（20日窗口）：有效突破 + 放量确认
    2. 回踩整理（5日窗口）：回踩不破突破位，深度 25-80%
    3. 二次突破（当日）：收盘突破回踩高点 + 放量 + 不过度延伸
    
    窗口要求：26 日（20日基准 + 5日回踩 + 当日）
    """
    name = "bpb"
    required_window = 26

    def __init__(self, config: Settings):
        self.params = BpbParams(volume_mult=config.pas_bpb_volume_mult)

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        today = data.iloc[-1]
        # BPB 拆成三段结构：突破腿 -> 回踩段 -> 当日确认。
        # 这样 trace 既能回答“有没有前置 breakout”，也能回答“回踩是否过深”。
        setup_window = data.iloc[-26:-6]
        pullback_window = data.iloc[-6:-1]
        if len(setup_window) < 20 or len(pullback_window) < 5:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        breakout_ref = float(setup_window["adj_high"].max())
        breakout_peak = float(pullback_window["adj_high"].max())
        pullback_low = float(pullback_window["adj_low"].min())
        volume_ratio = safe_ratio(today_volume, volume_ma20)
        # 先确认“此前真的发生过一次有效 breakout”，否则今天的上冲不算 BPB 的二次确认。
        breakout_leg_exists = bool(
            (
                (pullback_window["adj_close"] > breakout_ref)
                & (
                    pullback_window["volume"]
                    >= pullback_window["volume_ma20"].replace(0, float("inf")) * 1.2
                )
            ).any()
        )
        support_hold = pullback_low >= breakout_ref * (1 - 0.03)
        pullback_depth = (breakout_peak - pullback_low) / max(breakout_peak - breakout_ref, EPS)
        pullback_depth_valid = 0.25 <= pullback_depth <= 0.80
        confirmation = today_close > breakout_peak and today_close >= breakout_ref
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        not_overextended = today_close <= breakout_peak * 1.03
        body_ratio = abs(today_close - today_open) / max(today_high - today_low, EPS)
        confirm_strength = clip((today_close - breakout_ref) / max(0.10 * breakout_ref, EPS))
        depth_quality = 1.0 if 0.40 <= pullback_depth <= 0.60 else 0.7 if 0.25 <= pullback_depth <= 0.80 else 0.0
        support_hold_score = clip((pullback_low - breakout_ref * 0.97) / max(0.03 * breakout_ref, EPS))
        depth_score = float(depth_quality)

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "breakout_ref": breakout_ref,
                "breakout_peak": breakout_peak,
                "pullback_low": pullback_low,
                "pullback_depth": float(pullback_depth),
                "body_ratio": body_ratio,
                "confirm_strength": confirm_strength,
                "depth_quality": depth_quality,
                "support_hold_score": support_hold_score,
                "depth_score": depth_score,
            }
        )

        if not breakout_leg_exists:
            return fail_trace(trace, "NO_BREAKOUT_LEG")
        if not support_hold:
            return fail_trace(trace, "SUPPORT_LOST")
        if not pullback_depth_valid:
            return fail_trace(trace, "PULLBACK_TOO_DEEP")
        if not confirmation:
            return fail_trace(trace, "NO_CONFIRMATION")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")
        if not not_overextended:
            return fail_trace(trace, "OVEREXTENDED_CONFIRM")

        # strength 仍只表达“这次 BPB 触发有多干净”，不直接转成执行规则。
        strength = clip(
            0.40 * confirm_strength + 0.25 * min(volume_ratio / 2.0, 1.0) + 0.20 * depth_quality + 0.15 * body_ratio
        )
        trace.update({"triggered": True, "strength": strength})
        signal = build_signal(code, asof_date, self.name, strength)
        return signal, trace

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
