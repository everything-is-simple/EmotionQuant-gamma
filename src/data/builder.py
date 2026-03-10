from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from src.config import Settings
from src.data.cleaner import clean_industry_daily, clean_industry_structure_daily, clean_market_snapshot, clean_stock_adj_daily
from src.data.store import Store
from src.logging_utils import logger
from src.selector.irs import compute_irs
from src.selector.mss_experiments import compute_mss_variant


def _today() -> date:
    return date.today()


def _next_trade_day_or_fallback(store: Store, last: date | None, fallback_start: date) -> date:
    if last is None:
        return fallback_start
    nxt = store.next_trade_date(last)
    if nxt is not None:
        return nxt
    return last


def _resolve_window(
    store: Store,
    target_table: str,
    config: Settings,
    start: date | None,
    end: date | None,
    force: bool,
) -> tuple[date, date] | None:
    if force and start is None:
        start = config.history_start
    if start is None:
        start = _next_trade_day_or_fallback(store, store.get_max_date(target_table), config.history_start)
    if end is None:
        end = _today()
    if start > end:
        return None
    return start, end


def build_l2(store: Store, config: Settings, start: date | None, end: date | None, force: bool) -> int:
    if force:
        store.conn.execute("DELETE FROM l2_stock_adj_daily")
        store.conn.execute("DELETE FROM l2_industry_daily")
        store.conn.execute("DELETE FROM l2_industry_structure_daily")
        store.conn.execute("DELETE FROM l2_market_snapshot")

    window = _resolve_window(store, "l2_stock_adj_daily", config, start, end, force)
    if window is None:
        logger.info("L2 already up-to-date, skip.")
        return 0
    begin, finish = window
    n1 = clean_stock_adj_daily(store, begin, finish)
    n2 = clean_industry_daily(store, begin, finish)
    n3 = clean_industry_structure_daily(store, begin, finish)
    n4 = clean_market_snapshot(store, begin, finish)
    return n1 + n2 + n3 + n4


def build_l3(store: Store, config: Settings, start: date | None, end: date | None, force: bool) -> int:
    if force:
        store.conn.execute("DELETE FROM l3_mss_daily")
        store.conn.execute("DELETE FROM l3_irs_daily")

    # MSS / IRS 进度锚必须各自独立推进，避免其中一层已追平时把另一层的缺口静默跳过。
    mss_window = _resolve_window(store, "l3_mss_daily", config, start, end, force)
    irs_window = _resolve_window(store, "l3_irs_daily", config, start, end, force)
    if mss_window is None and irs_window is None:
        logger.info("L3 already up-to-date, skip.")
        return 0

    # L3 在 v0.01 只构建 MSS/IRS；signal 仍由 Strategy 运行时写入。
    n1 = 0
    if mss_window is not None:
        mss_begin, mss_finish = mss_window
        n1 = compute_mss_variant(
            store,
            mss_begin,
            mss_finish,
            variant_label=config.mss_variant,
            bullish_threshold=config.mss_bullish_threshold,
            bearish_threshold=config.mss_bearish_threshold,
        )

    n2 = 0
    if irs_window is not None:
        irs_begin, irs_finish = irs_window
        n2 = compute_irs(
            store,
            irs_begin,
            irs_finish,
            min_industries_per_day=config.irs_min_industries_per_day,
        )
    return n1 + n2


def build_layers(
    store: Store,
    config: Settings,
    layers: Iterable[str],
    start: date | None = None,
    end: date | None = None,
    force: bool = False,
) -> int:
    total = 0
    layer_set = {layer.strip().lower() for layer in layers}
    if "all" in layer_set:
        layer_set = {"l2", "l3"}
    if "l2" in layer_set:
        total += build_l2(store, config, start, end, force)
    if "l3" in layer_set:
        total += build_l3(store, config, start, end, force)
    return total
