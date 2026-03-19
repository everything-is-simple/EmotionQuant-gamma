from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from src.config import Settings
from src.data.cleaner import clean_industry_daily, clean_industry_structure_daily, clean_market_snapshot, clean_stock_adj_daily
from src.data.store import Store
from src.logging_utils import logger
from src.selector.gene import compute_gene, compute_gene_conditioning, compute_gene_mirror
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


def _date_column_for_table(table: str) -> str:
    if table == "l3_stock_gene":
        return "calc_date"
    return "date"


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
        start = _next_trade_day_or_fallback(
            store,
            store.get_max_date(target_table, date_col=_date_column_for_table(target_table)),
            config.history_start,
        )
    if end is None:
        end = _today()
    if start > end:
        return None
    return start, end


def build_l2(store: Store, config: Settings, start: date | None, end: date | None, force: bool) -> int:
    if force:
        # Only clear L2 outputs on forced rebuild.
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
        store.conn.execute("DELETE FROM l3_stock_gene")
        store.conn.execute("DELETE FROM l3_stock_lifespan_surface")
        store.conn.execute("DELETE FROM l3_gene_wave")
        store.conn.execute("DELETE FROM l3_gene_event")
        store.conn.execute("DELETE FROM l3_gene_factor_eval")
        store.conn.execute("DELETE FROM l3_gene_distribution_eval")
        store.conn.execute("DELETE FROM l3_gene_validation_eval")
        store.conn.execute("DELETE FROM l3_gene_mirror")
        store.conn.execute("DELETE FROM l3_gene_market_lifespan_surface")
        store.conn.execute("DELETE FROM l3_gene_conditioning_eval")

    # Keep each L3 product on its own rebuild window.
    mss_window = _resolve_window(store, "l3_mss_daily", config, start, end, force)
    irs_window = _resolve_window(store, "l3_irs_daily", config, start, end, force)
    gene_window = _resolve_window(store, "l3_stock_gene", config, start, end, force)
    if mss_window is None and irs_window is None and gene_window is None:
        logger.info("L3 already up-to-date, skip.")
        return 0

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
            rt_lookback_days=config.irs_rt_lookback_days,
            top_rank_threshold=config.irs_top_rank_threshold,
            factor_mode=config.irs_factor_mode,
            factor_weight_rs=config.irs_factor_weight_rs,
            factor_weight_rv=config.irs_factor_weight_rv,
            factor_weight_rt=config.irs_factor_weight_rt,
            factor_weight_bd=config.irs_factor_weight_bd,
            factor_weight_gn=config.irs_factor_weight_gn,
        )

    n3 = 0
    if gene_window is not None:
        gene_begin, gene_finish = gene_window
        n3 = compute_gene(store, gene_begin, gene_finish)
        n3 += compute_gene_mirror(store, gene_finish)
        n3 += compute_gene_conditioning(store, gene_finish)
    return n1 + n2 + n3


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
