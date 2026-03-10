from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal
from src.strategy.pattern_base import PatternDetector
from src.strategy.pas_support import REQUIRED_COLUMNS, EPS, build_signal, clip, fail_trace, init_trace, normalize_history, safe_ratio


@dataclass
class CpbParams:
    retest_min: int = 2
    neckline_break_pct: float = 0.01
    volume_mult: float = 1.2


class CpbDetector(PatternDetector):
    """
    CPB (Complex Base) 复杂底部形态检测器（Phase 1 核心）：
    
    形态定义：
    1. 底部结构（20日窗口）：多次测试支撑带（≥2次），支撑带宽度 ≤3%
    2. 压缩整理：整体波动幅度 ≤12%
    3. 颈线突破（当日）：收盘突破结构高点 + 放量确认
    
    窗口要求：41 日（20日基准 + 当日，预留缓冲）
    """
    name = "cpb"
    required_window = 41

    def __init__(self, config: Settings):
        self.params = CpbParams(
            retest_min=config.pas_cpb_retest_min,
            neckline_break_pct=config.pas_cpb_neckline_break_pct,
            volume_mult=config.pas_cpb_volume_mult,
        )

    def evaluate(self, code: str, asof_date: date, df: pd.DataFrame) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        today = data.iloc[-1]
        # CPB 更看重“底部结构是否反复测试且逐步压缩”，因此先抽 base_window 再看今天是否颈线突破。
        base_window = data.iloc[-21:-1]
        if len(base_window) < 20:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        support_band_low = float(base_window["adj_low"].min())
        support_band_high = float(base_window["adj_low"].quantile(0.35))
        neckline_ref = float(base_window["adj_high"].max())
        retest_mask = (base_window["adj_low"] >= support_band_low) & (base_window["adj_low"] <= support_band_high)
        retest_count = int(retest_mask.sum())
        compression_width = (float(base_window["adj_high"].max()) - float(base_window["adj_low"].min())) / max(
            float(base_window["adj_low"].min()),
            EPS,
        )
        volume_ratio = safe_ratio(today_volume, volume_ma20)
        # 复杂底部不能只靠一次低点；至少要有多次 retest，且支撑带不能过宽。
        retest_enough = retest_count >= self.params.retest_min
        support_band_valid = support_band_high / max(support_band_low, EPS) <= 1.03
        compression_valid = compression_width <= 0.12
        neckline_break = today_close > neckline_ref * (1 + self.params.neckline_break_pct)
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        neckline_strength = clip((today_close - neckline_ref) / max(0.10 * neckline_ref, EPS))
        retest_quality = clip(retest_count / 3.0)
        compression_quality = 1.0 - clip(compression_width / 0.12)

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "support_band_low": support_band_low,
                "support_band_high": support_band_high,
                "neckline_ref": neckline_ref,
                "retest_count": retest_count,
                "compression_width": float(compression_width),
                "neckline_strength": neckline_strength,
                "retest_quality": retest_quality,
                "compression_quality": compression_quality,
            }
        )

        if not retest_enough:
            return fail_trace(trace, "RETEST_NOT_ENOUGH")
        if not support_band_valid:
            return fail_trace(trace, "SUPPORT_BAND_TOO_WIDE")
        if not compression_valid:
            return fail_trace(trace, "STRUCTURE_TOO_WIDE")
        if not neckline_break:
            return fail_trace(trace, "NO_NECKLINE_BREAK")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        # strength 同时考虑“突破力度 + retest 质量 + 压缩程度 + 量能确认”。
        strength = clip(
            0.35 * neckline_strength
            + 0.25 * retest_quality
            + 0.20 * compression_quality
            + 0.20 * min(volume_ratio / 2.0, 1.0)
        )
        trace.update({"triggered": True, "strength": strength})
        signal = build_signal(code, asof_date, self.name, strength)
        return signal, trace

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
