from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.config import Settings
from src.contracts import Signal
from src.strategy.pas_support import (
    EPS,
    REQUIRED_COLUMNS,
    build_signal,
    clip,
    fail_trace,
    init_trace,
    normalize_history,
    safe_ratio,
)
from src.strategy.pattern_base import PatternDetector

VOLMAN_REQUIRED_COLUMNS = REQUIRED_COLUMNS | {"ma20"}


@dataclass
class RbFakeParams:
    break_pct: float = 0.01
    volume_mult: float = 1.15
    range_width_min: float = 0.05
    range_width_max: float = 0.25
    boundary_tolerance: float = 0.02
    min_boundary_tests: int = 3


class RbFakeDetector(PatternDetector):
    """
    RB_FAKE:
    1. 先有可见区间边界
    2. 边界附近被反复测试
    3. 当日向下假跌破后收回区间
    """

    name = "rb_fake"
    required_window = 26

    def __init__(self, config: Settings):
        self.params = RbFakeParams(
            break_pct=config.pas_bof_break_pct,
            volume_mult=max(1.05, float(config.pas_bof_volume_mult)),
        )

    def evaluate(self, code: str, asof_date: date, df) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not VOLMAN_REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        range_window = data.iloc[-21:-1]
        today = data.iloc[-1]
        if len(range_window) < 20:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        range_low = float(range_window["adj_low"].min())
        range_high = float(range_window["adj_high"].max())
        range_width = safe_ratio(range_high - range_low, range_low)
        boundary_tests = int(
            (range_window["adj_low"] <= range_low * (1 + self.params.boundary_tolerance)).sum()
        )
        recent_window = range_window.tail(5).copy()
        recent_close_pos = float(
            (
                (recent_window["adj_close"] - range_low) / max(range_high - range_low, EPS)
            ).clip(lower=0.0, upper=1.0).mean()
        )
        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        volume_ratio = safe_ratio(today_volume, volume_ma20)
        close_pos = safe_ratio(today_close - today_low, today_high - today_low)
        body_ratio = safe_ratio(abs(today_close - today_open), today_high - today_low)
        fake_break_depth = safe_ratio(range_low - today_low, range_low)

        range_valid = self.params.range_width_min <= range_width <= self.params.range_width_max
        boundary_visible = boundary_tests >= self.params.min_boundary_tests
        not_teasing = recent_close_pos <= 0.65
        fake_break = today_low < range_low * (1 - self.params.break_pct)
        reclaim_in_range = today_close >= range_low
        strong_reclaim = close_pos >= 0.55
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "range_low": range_low,
                "range_high": range_high,
                "range_width": range_width,
                "boundary_tests": boundary_tests,
                "recent_close_pos": recent_close_pos,
                "close_pos": close_pos,
                "body_ratio": body_ratio,
                "fake_break_depth": fake_break_depth,
            }
        )

        if not range_valid:
            return fail_trace(trace, "NO_RANGE_BOUNDARY")
        if not boundary_visible:
            return fail_trace(trace, "NO_RANGE_BOUNDARY_TESTS")
        if not not_teasing:
            return fail_trace(trace, "TEASING_FROM_MIDRANGE")
        if not fake_break:
            return fail_trace(trace, "NO_FAKE_BREAK")
        if not reclaim_in_range:
            return fail_trace(trace, "NO_RANGE_RECLAIM")
        if not strong_reclaim:
            return fail_trace(trace, "WEAK_RECLAIM")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        reclaim_strength = clip((today_close - range_low) / max(0.06 * range_low, EPS))
        depth_quality = clip(fake_break_depth / 0.03)
        boundary_quality = clip(boundary_tests / 5.0)
        strength = clip(
            0.30 * reclaim_strength
            + 0.25 * boundary_quality
            + 0.20 * depth_quality
            + 0.15 * min(volume_ratio / 2.0, 1.0)
            + 0.10 * body_ratio
        )
        trace.update({"triggered": True, "strength": strength})
        return build_signal(code, asof_date, self.name, strength), trace

    def detect(self, code: str, asof_date: date, df) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal


@dataclass
class FbParams:
    volume_mult: float = 1.15
    trend_gain_min: float = 0.08
    pullback_min: float = 0.20
    pullback_max: float = 0.60
    ma20_distance_max: float = 0.04
    prior_ema_touches_min: int = 0
    prior_ema_touches_max: int = 2


class FbDetector(PatternDetector):
    """
    FB:
    1. 先有明显趋势爆发
    2. 再有第一次主要回撤，且回撤贴近 ma20
    3. 当日做顺势恢复确认
    """

    name = "fb"
    required_window = 31

    def __init__(
        self,
        config: Settings,
        *,
        prior_ema_touches_min: int = 0,
        prior_ema_touches_max: int = 2,
    ):
        min_touches = max(0, int(prior_ema_touches_min))
        max_touches = max(0, int(prior_ema_touches_max))
        if min_touches > max_touches:
            raise ValueError("FB prior_ema_touches_min must be <= prior_ema_touches_max")
        self.params = FbParams(
            volume_mult=max(1.05, float(config.pas_pb_volume_mult)),
            prior_ema_touches_min=min_touches,
            prior_ema_touches_max=max_touches,
        )

    def evaluate(self, code: str, asof_date: date, df) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update(
            {
                "required_window": self.required_window,
                "required_mult": self.params.volume_mult,
                "prior_ema_touches_min": self.params.prior_ema_touches_min,
                "prior_ema_touches_max": self.params.prior_ema_touches_max,
            }
        )
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not VOLMAN_REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        pre_window = data.iloc[-31:-21]
        trend_window = data.iloc[-21:-6]
        pullback_window = data.iloc[-6:-1]
        today = data.iloc[-1]
        if len(pre_window) < 10 or len(trend_window) < 15 or len(pullback_window) < 5:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        volume_ratio = safe_ratio(today_volume, volume_ma20)

        pre_high = float(pre_window["adj_high"].max())
        trend_peak = float(trend_window["adj_high"].max())
        trend_floor = float(pre_window["adj_low"].min())
        trend_gain = safe_ratio(trend_peak - pre_high, pre_high)
        trend_up_ratio = float((trend_window["adj_close"].diff().fillna(0.0) > 0).mean())
        prior_ema_touches = int((trend_window["adj_low"] <= trend_window["ma20"] * 1.02).sum())

        pullback_low = float(pullback_window["adj_low"].min())
        rebound_ref = float(pullback_window["adj_high"].max())
        pullback_depth = safe_ratio(trend_peak - pullback_low, trend_peak - trend_floor)
        pullback_down_ratio = float((pullback_window["adj_close"].diff().fillna(0.0) < 0).mean())
        ma20_ref = float(pullback_window["ma20"].iloc[-1] or today["ma20"] or 0.0)

        trend_ok = (
            trend_gain >= self.params.trend_gain_min
            and trend_up_ratio >= 0.55
            and float(trend_window["adj_close"].iloc[-1]) > float(trend_window["ma20"].iloc[-1])
        )
        first_pullback = self.params.prior_ema_touches_min <= prior_ema_touches <= self.params.prior_ema_touches_max
        pullback_valid = self.params.pullback_min <= pullback_depth <= self.params.pullback_max
        orderly_pullback = pullback_down_ratio >= 0.40 and float(pullback_window["adj_close"].iloc[-1]) <= float(
            pullback_window["adj_close"].iloc[0]
        )
        ma20_retest = ma20_ref > 0 and abs(pullback_low - ma20_ref) / ma20_ref <= self.params.ma20_distance_max
        rebound_confirm = today_close > rebound_ref and today_close > float(today["ma20"]) and today_close > today_open
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult
        not_overextended = today_close <= trend_peak * 1.08

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "pre_high": pre_high,
                "trend_peak": trend_peak,
                "trend_floor": trend_floor,
                "trend_gain": trend_gain,
                "trend_up_ratio": trend_up_ratio,
                "prior_ema_touches": prior_ema_touches,
                "pullback_low": pullback_low,
                "rebound_ref": rebound_ref,
                "pullback_depth": pullback_depth,
                "pullback_down_ratio": pullback_down_ratio,
                "ma20_ref": ma20_ref,
            }
        )

        if not trend_ok:
            return fail_trace(trace, "TREND_NOT_EXPLOSIVE")
        if not first_pullback:
            return fail_trace(trace, "NOT_FIRST_PULLBACK")
        if not pullback_valid or not orderly_pullback:
            return fail_trace(trace, "PULLBACK_NOT_ORDERLY")
        if not ma20_retest:
            return fail_trace(trace, "MA20_NOT_RETESTED")
        if not rebound_confirm:
            return fail_trace(trace, "NO_FB_CONFIRM")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")
        if not not_overextended:
            return fail_trace(trace, "OVEREXTENDED_CONFIRM")

        trend_quality = clip(trend_gain / 0.15)
        depth_quality = 1.0 if 0.25 <= pullback_depth <= 0.50 else 0.7
        rebound_strength = clip((today_close - rebound_ref) / max(0.06 * rebound_ref, EPS))
        first_pullback_quality = clip(1.0 - prior_ema_touches / 4.0)
        strength = clip(
            0.30 * trend_quality
            + 0.25 * depth_quality
            + 0.20 * rebound_strength
            + 0.15 * first_pullback_quality
            + 0.10 * min(volume_ratio / 2.0, 1.0)
        )
        trace.update({"triggered": True, "strength": strength})
        return build_signal(code, asof_date, self.name, strength), trace

    def detect(self, code: str, asof_date: date, df) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal


class FbCleanerDetector(FbDetector):
    """Cleaner FB branch: only keep 0/1-touch first-pullback samples."""

    name = "fb_cleaner"

    def __init__(self, config: Settings):
        super().__init__(config, prior_ema_touches_min=0, prior_ema_touches_max=1)


class FbBoundaryDetector(FbDetector):
    """Boundary FB branch: isolate the 2-touch edge bucket for refinement replay."""

    name = "fb_boundary"

    def __init__(self, config: Settings):
        super().__init__(config, prior_ema_touches_min=2, prior_ema_touches_max=2)


@dataclass
class SbParams:
    volume_mult: float = 1.10
    trend_gain_min: float = 0.10
    ma20_distance_max: float = 0.04
    retest_similarity_max: float = 0.05


class SbDetector(PatternDetector):
    """
    SB:
    1. 趋势背景仍在
    2. 第一次恢复没有走出来
    3. 第二次回到 ma20 区域后，当日完成第二次恢复突破
    """

    name = "sb"
    required_window = 41

    def __init__(self, config: Settings):
        self.params = SbParams(volume_mult=max(1.05, float(config.pas_tst_volume_mult)))

    def evaluate(self, code: str, asof_date: date, df) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not VOLMAN_REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        trend_window = data.iloc[-41:-11]
        structure_window = data.iloc[-11:-1]
        first_leg = structure_window.iloc[:5]
        second_leg = structure_window.iloc[5:]
        today = data.iloc[-1]
        if len(trend_window) < 30 or len(first_leg) < 5 or len(second_leg) < 5:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        today_low = float(today["adj_low"])
        today_close = float(today["adj_close"])
        today_open = float(today["adj_open"])
        today_high = float(today["adj_high"])
        if today_high <= today_low:
            return fail_trace(trace, "INVALID_RANGE")

        today_volume = float(today["volume"] or 0.0)
        volume_ma20 = float(today["volume_ma20"] or 0.0)
        volume_ratio = safe_ratio(today_volume, volume_ma20)

        trend_floor = float(trend_window["adj_low"].min())
        trend_peak = float(trend_window["adj_high"].max())
        trend_gain = safe_ratio(trend_peak - trend_floor, trend_floor)
        trend_ok = (
            trend_gain >= self.params.trend_gain_min
            and float(trend_window["adj_close"].iloc[-1]) > float(trend_window["ma20"].iloc[-1])
        )

        first_test_low = float(first_leg["adj_low"].min())
        second_test_low = float(second_leg["adj_low"].min())
        first_rebound_high = float(first_leg["adj_high"].max())
        second_break_ref = float(second_leg["adj_high"].max())
        first_ma20 = float(first_leg["ma20"].iloc[-1] or 0.0)
        second_ma20 = float(second_leg["ma20"].iloc[-1] or 0.0)
        first_near_ma20 = first_ma20 > 0 and abs(first_test_low - first_ma20) / first_ma20 <= self.params.ma20_distance_max
        second_near_ma20 = second_ma20 > 0 and abs(second_test_low - second_ma20) / second_ma20 <= self.params.ma20_distance_max
        first_break_failed = first_rebound_high < trend_peak * 0.995
        retest_similarity = abs(second_test_low - first_test_low) / max(first_test_low, EPS)
        retest_pair_valid = retest_similarity <= self.params.retest_similarity_max
        w_amplitude = safe_ratio(
            max(first_rebound_high, second_break_ref) - min(first_test_low, second_test_low),
            min(first_test_low, second_test_low),
        )
        second_break_confirm = (
            today_close > second_break_ref and today_close > float(today["ma20"]) and today_close > today_open
        )
        volume_confirm = volume_ma20 > 0 and today_volume >= volume_ma20 * self.params.volume_mult

        trace.update(
            {
                "today_low": today_low,
                "today_close": today_close,
                "today_open": today_open,
                "today_high": today_high,
                "volume": today_volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
                "trend_floor": trend_floor,
                "trend_peak": trend_peak,
                "trend_gain": trend_gain,
                "first_test_low": first_test_low,
                "second_test_low": second_test_low,
                "first_rebound_high": first_rebound_high,
                "second_break_ref": second_break_ref,
                "first_ma20": first_ma20,
                "second_ma20": second_ma20,
                "retest_similarity": retest_similarity,
                "w_amplitude": w_amplitude,
            }
        )

        if not trend_ok:
            return fail_trace(trace, "TREND_NOT_ESTABLISHED")
        if not first_near_ma20 or not second_near_ma20:
            return fail_trace(trace, "NOT_SECOND_TEST_SETUP")
        if not first_break_failed:
            return fail_trace(trace, "FIRST_BREAK_NOT_FAILED")
        if not retest_pair_valid:
            return fail_trace(trace, "SECOND_TEST_NOT_DISTINCT")
        if w_amplitude < 0.05:
            return fail_trace(trace, "NO_W_STRUCTURE")
        if not second_break_confirm:
            return fail_trace(trace, "NO_SB_CONFIRM")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        trend_quality = clip(trend_gain / 0.18)
        second_test_quality = clip(1.0 - retest_similarity / max(self.params.retest_similarity_max, EPS))
        breakout_strength = clip((today_close - second_break_ref) / max(0.06 * second_break_ref, EPS))
        structure_quality = clip(w_amplitude / 0.12)
        strength = clip(
            0.25 * trend_quality
            + 0.25 * second_test_quality
            + 0.25 * breakout_strength
            + 0.15 * structure_quality
            + 0.10 * min(volume_ratio / 2.0, 1.0)
        )
        trace.update({"triggered": True, "strength": strength})
        return build_signal(code, asof_date, self.name, strength), trace

    def detect(self, code: str, asof_date: date, df) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
