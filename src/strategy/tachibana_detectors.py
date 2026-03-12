from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.config import Settings
from src.contracts import Signal
from src.strategy.pattern_base import PatternDetector
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


TACHIBANA_REQUIRED_COLUMNS = REQUIRED_COLUMNS | {"ma20"}


@dataclass
class TachiCrowdFailureParams:
    volume_mult: float = 1.15
    crowd_drawdown_min: float = 0.15
    crowd_down_ratio_min: float = 0.60
    stretch_close_pos_max: float = 0.35
    ma20_discount_min: float = 0.02
    washout_break_pct: float = 0.01
    reclaim_break_pct: float = 0.003
    close_pos_min: float = 0.65


class TachiCrowdFailureDetector(PatternDetector):
    """
    TACHI_CROWD_FAILURE:
    1. 先有一段明显的一致性下压
    2. 卖压把价格打到近期极端并压在 ma20 下方
    3. 当日继续下探失败，并出现强力 reclaim
    """

    name = "tachi_crowd_failure"
    required_window = 31

    def __init__(self, config: Settings):
        self.params = TachiCrowdFailureParams(
            volume_mult=max(1.05, float(config.pas_bof_volume_mult)),
        )

    def evaluate(self, code: str, asof_date: date, df) -> tuple[Signal | None, dict[str, object]]:
        trace = init_trace(code, asof_date, self.name, len(df))
        trace.update({"required_window": self.required_window, "required_mult": self.params.volume_mult})
        if df.empty or len(df) < self.required_window:
            return fail_trace(trace, "INSUFFICIENT_HISTORY")

        data = normalize_history(df)
        if not TACHIBANA_REQUIRED_COLUMNS.issubset(set(data.columns)):
            return fail_trace(trace, "MISSING_REQUIRED_COLUMNS")

        prior_window = data.iloc[-31:-11]
        selloff_window = data.iloc[-11:-1]
        today = data.iloc[-1]
        if len(prior_window) < 20 or len(selloff_window) < 10:
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

        prior_high = float(prior_window["adj_high"].max())
        crowd_low = float(selloff_window["adj_low"].min())
        selloff_high = float(selloff_window["adj_high"].max())
        recent_close = float(selloff_window["adj_close"].iloc[-1])
        ma20_ref = float(today["ma20"] or selloff_window["ma20"].iloc[-1] or 0.0)
        recent_reclaim_ref = float(selloff_window.tail(3)["adj_high"].max())
        crowd_drawdown = safe_ratio(prior_high - crowd_low, prior_high)
        selloff_down_ratio = float((selloff_window["adj_close"].diff().fillna(0.0) < 0).mean())
        stretch_close_pos = safe_ratio(recent_close - crowd_low, selloff_high - crowd_low)
        close_pos = safe_ratio(today_close - today_low, today_high - today_low)
        body_ratio = safe_ratio(abs(today_close - today_open), today_high - today_low)

        crowd_extreme = crowd_drawdown >= self.params.crowd_drawdown_min
        one_side_selling = selloff_down_ratio >= self.params.crowd_down_ratio_min
        crowd_stretched = stretch_close_pos <= self.params.stretch_close_pos_max
        below_ma20 = ma20_ref > 0 and recent_close <= ma20_ref * (1 - self.params.ma20_discount_min)
        washout_break = today_low < crowd_low * (1 - self.params.washout_break_pct)
        reclaim_confirm = (
            today_close > recent_reclaim_ref * (1 + self.params.reclaim_break_pct) and today_close > today_open
        )
        strong_close = close_pos >= self.params.close_pos_min
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
                "prior_high": prior_high,
                "crowd_low": crowd_low,
                "selloff_high": selloff_high,
                "recent_close": recent_close,
                "ma20_ref": ma20_ref,
                "recent_reclaim_ref": recent_reclaim_ref,
                "crowd_drawdown": crowd_drawdown,
                "selloff_down_ratio": selloff_down_ratio,
                "stretch_close_pos": stretch_close_pos,
                "close_pos": close_pos,
                "body_ratio": body_ratio,
            }
        )

        if not crowd_extreme:
            return fail_trace(trace, "NO_CROWD_EXTREME")
        if not one_side_selling:
            return fail_trace(trace, "NO_ONE_SIDE_SELLING")
        if not crowd_stretched:
            return fail_trace(trace, "SELLING_NOT_STRETCHED")
        if not below_ma20:
            return fail_trace(trace, "NOT_BELOW_MA20")
        if not washout_break:
            return fail_trace(trace, "NO_WASHOUT_BREAK")
        if not reclaim_confirm:
            return fail_trace(trace, "NO_RECLAIM_CONFIRM")
        if not strong_close:
            return fail_trace(trace, "WEAK_CLOSE")
        if not volume_confirm:
            return fail_trace(trace, "LOW_VOLUME")

        drawdown_quality = clip(crowd_drawdown / 0.25)
        reclaim_strength = clip((today_close - recent_reclaim_ref) / max(0.08 * recent_reclaim_ref, EPS))
        strength = clip(
            0.30 * drawdown_quality
            + 0.25 * reclaim_strength
            + 0.20 * close_pos
            + 0.15 * min(volume_ratio / 2.0, 1.0)
            + 0.10 * body_ratio
        )
        trace.update({"triggered": True, "strength": strength})
        return build_signal(code, asof_date, self.name, strength), trace

    def detect(self, code: str, asof_date: date, df) -> Signal | None:
        signal, _ = self.evaluate(code, asof_date, df)
        return signal
