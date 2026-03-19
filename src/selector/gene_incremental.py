from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Iterable

import pandas as pd

from src.data.store import Store
from src.selector.gene import (
    GENE_LOOKBACK_TRADE_DAYS,
    _apply_cross_section_ranks,
    _build_distribution_eval_rows,
    _build_factor_eval_rows,
    _build_code_gene_payload,
    _build_stock_lifespan_surface_rows,
    _concat_sparse_frames,
    _lookback_trade_start,
    compute_gene_validation,
    FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS,
    compute_gene_mirror,
)


@dataclass(frozen=True)
class GeneDirtyWindow:
    code: str
    dirty_start: date
    dirty_end: date
    rebuild_start: date
    source_row_count: int
    existing_gene_max_calc_date: date | None


def _normalize_codes(codes: Iterable[str] | None) -> list[str]:
    if codes is None:
        return []
    normalized = sorted({str(code).strip() for code in codes if str(code).strip()})
    return normalized


def _register_code_filter(store: Store, codes: list[str], view_name: str) -> None:
    code_frame = pd.DataFrame({"code": codes})
    store.conn.register(view_name, code_frame)


def _register_date_filter(store: Store, dates: list[date], view_name: str) -> None:
    date_frame = pd.DataFrame({"calc_date": dates})
    store.conn.register(view_name, date_frame)


def scan_gene_dirty_windows(
    store: Store,
    *,
    start: date,
    end: date,
    codes: Iterable[str] | None = None,
) -> list[GeneDirtyWindow]:
    requested_codes = _normalize_codes(codes)
    params: list[object] = [start, end]
    query = """
        WITH source_window AS (
            SELECT
                code,
                MIN(date) AS dirty_start,
                MAX(date) AS dirty_end,
                COUNT(*) AS source_row_count
            FROM l2_stock_adj_daily
            WHERE date BETWEEN ? AND ?
            GROUP BY code
        ),
        gene_max AS (
            SELECT code, MAX(calc_date) AS existing_gene_max_calc_date
            FROM l3_stock_gene
            GROUP BY code
        )
        SELECT
            s.code,
            s.dirty_start,
            s.dirty_end,
            s.source_row_count,
            g.existing_gene_max_calc_date
        FROM source_window s
        LEFT JOIN gene_max g
          ON g.code = s.code
    """
    if requested_codes:
        placeholders = ", ".join("?" for _ in requested_codes)
        query += f" WHERE s.code IN ({placeholders})"
        params.extend(requested_codes)
    query += " ORDER BY s.code"

    frame = store.read_df(query, tuple(params))
    if frame.empty:
        return []

    windows: list[GeneDirtyWindow] = []
    for row in frame.itertuples(index=False):
        dirty_start = pd.Timestamp(row.dirty_start).date()
        dirty_end = pd.Timestamp(row.dirty_end).date()
        rebuild_start = _lookback_trade_start(store, dirty_start, GENE_LOOKBACK_TRADE_DAYS)
        existing_gene_max = (
            None
            if pd.isna(row.existing_gene_max_calc_date)
            else pd.Timestamp(row.existing_gene_max_calc_date).date()
        )
        windows.append(
            GeneDirtyWindow(
                code=str(row.code),
                dirty_start=dirty_start,
                dirty_end=dirty_end,
                rebuild_start=rebuild_start,
                source_row_count=int(row.source_row_count),
                existing_gene_max_calc_date=existing_gene_max,
            )
        )
    return windows


def _load_gene_input_for_codes(
    store: Store,
    *,
    codes: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame()
    view_name = "gene_incremental_codes"
    _register_code_filter(store, codes, view_name)
    try:
        frame = store.read_df(
            f"""
            SELECT d.code, d.date, d.adj_open, d.adj_high, d.adj_low, d.adj_close, d.volume, d.amount
            FROM l2_stock_adj_daily d
            JOIN {view_name} c
              ON c.code = d.code
            WHERE d.date BETWEEN ? AND ?
            ORDER BY d.code, d.date
            """,
            (start, end),
        )
    finally:
        store.conn.unregister(view_name)
    return frame


def _clear_gene_range_for_codes(
    store: Store,
    *,
    codes: list[str],
    start: date,
    end: date,
) -> None:
    if not codes:
        return
    view_name = "gene_incremental_codes"
    _register_code_filter(store, codes, view_name)
    try:
        store.conn.execute(
            f"""
            DELETE FROM l3_stock_gene
            WHERE calc_date BETWEEN ? AND ?
              AND code IN (SELECT code FROM {view_name})
            """,
            [start, end],
        )
        store.conn.execute(
            f"""
            DELETE FROM l3_stock_lifespan_surface
            WHERE calc_date BETWEEN ? AND ?
              AND code IN (SELECT code FROM {view_name})
            """,
            [start, end],
        )
        store.conn.execute(
            f"""
            DELETE FROM l3_gene_wave
            WHERE end_date BETWEEN ? AND ?
              AND code IN (SELECT code FROM {view_name})
            """,
            [start, end],
        )
        store.conn.execute(
            f"""
            DELETE FROM l3_gene_event
            WHERE event_date BETWEEN ? AND ?
              AND code IN (SELECT code FROM {view_name})
            """,
            [start, end],
        )
    finally:
        store.conn.unregister(view_name)


def refresh_gene_cross_section_ranks(store: Store, target_dates: Iterable[date]) -> int:
    normalized_dates = sorted({item for item in target_dates if item is not None})
    if not normalized_dates:
        return 0
    view_name = "gene_incremental_dates"
    _register_date_filter(store, normalized_dates, view_name)
    try:
        snapshot_df = store.read_df(
            f"""
            SELECT *
            FROM l3_stock_gene
            WHERE calc_date IN (SELECT calc_date FROM {view_name})
            ORDER BY calc_date, code
            """
        )
    finally:
        store.conn.unregister(view_name)
    if snapshot_df.empty:
        return 0
    ranked = _apply_cross_section_ranks(snapshot_df)
    if ranked.empty:
        return 0
    return store.bulk_upsert("l3_stock_gene", ranked)


def refresh_gene_market_surfaces(store: Store, *, calc_date: date) -> int:
    return compute_gene_mirror(store, calc_date)


def _load_persisted_factor_eval_samples(
    store: Store,
    *,
    sample_start: date,
    calc_date: date,
) -> pd.DataFrame:
    horizon = FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS
    frame = store.read_df(
        f"""
        WITH price_forward AS (
            SELECT
                code,
                date AS confirm_date,
                LEAD(adj_close, ?) OVER (PARTITION BY code ORDER BY date) AS future_terminal_close,
                MAX(adj_high) OVER (
                    PARTITION BY code
                    ORDER BY date
                    ROWS BETWEEN 1 FOLLOWING AND {horizon} FOLLOWING
                ) AS future_max_high,
                MIN(adj_low) OVER (
                    PARTITION BY code
                    ORDER BY date
                    ROWS BETWEEN 1 FOLLOWING AND {horizon} FOLLOWING
                ) AS future_min_low
            FROM l2_stock_adj_daily
            WHERE date BETWEEN ? AND ?
        ),
        wave_base AS (
            SELECT
                code,
                wave_id,
                direction,
                end_date,
                end_price,
                magnitude_pct,
                duration_trade_days,
                magnitude_band,
                duration_band,
                wave_age_band,
                magnitude_percentile,
                duration_percentile,
                extreme_density_percentile,
                COALESCE(
                    two_b_confirm_date,
                    turn_step3_date,
                    turn_step2_date,
                    turn_step1_date,
                    end_date
                ) AS confirm_date
            FROM l3_gene_wave
            WHERE end_date BETWEEN ? AND ?
        )
        SELECT
            w.code,
            w.wave_id,
            w.direction,
            w.end_date,
            CAST(w.magnitude_pct AS DOUBLE) AS magnitude_raw_pct,
            CAST(w.duration_trade_days AS DOUBLE) AS duration_raw_trade_days,
            w.magnitude_band,
            w.duration_band,
            w.wave_age_band,
            CAST(w.magnitude_percentile AS DOUBLE) AS magnitude,
            CAST(w.duration_percentile AS DOUBLE) AS duration,
            CAST(w.extreme_density_percentile AS DOUBLE) AS extreme_density,
            CASE
                WHEN w.direction = 'UP'
                    THEN ((p.future_terminal_close - w.end_price) / w.end_price) * 100.0
                ELSE ((w.end_price - p.future_terminal_close) / w.end_price) * 100.0
            END AS aligned_close_return_pct,
            CASE
                WHEN w.direction = 'UP'
                    THEN GREATEST(0.0, ((w.end_price - p.future_min_low) / w.end_price) * 100.0)
                ELSE GREATEST(0.0, ((p.future_max_high - w.end_price) / w.end_price) * 100.0)
            END AS adverse_excursion_pct,
            CASE
                WHEN w.direction = 'UP'
                    THEN GREATEST(0.0, ((p.future_max_high - w.end_price) / w.end_price) * 100.0)
                ELSE GREATEST(0.0, ((w.end_price - p.future_min_low) / w.end_price) * 100.0)
            END AS favorable_excursion_pct
        FROM wave_base w
        JOIN price_forward p
          ON p.code = w.code
         AND p.confirm_date = w.confirm_date
        WHERE w.end_price > 0
          AND w.direction IN ('UP', 'DOWN')
          AND p.future_terminal_close IS NOT NULL
        ORDER BY w.code, w.end_date, w.wave_id
        """,
        (horizon, sample_start, calc_date, sample_start, calc_date),
    )
    if frame.empty:
        return frame
    frame["continuation_flag"] = (
        (frame["favorable_excursion_pct"] > frame["adverse_excursion_pct"])
        & (frame["favorable_excursion_pct"] > 0.0)
    )
    frame["reversal_flag"] = (
        (frame["adverse_excursion_pct"] > frame["favorable_excursion_pct"])
        & (frame["adverse_excursion_pct"] > 0.0)
    )
    return frame


def refresh_gene_evals_for_dates(store: Store, target_dates: Iterable[date]) -> dict[str, int]:
    normalized_dates = sorted({item for item in target_dates if item is not None})
    if not normalized_dates:
        return {
            "factor_eval_rows": 0,
            "distribution_eval_rows": 0,
            "validation_eval_rows": 0,
        }

    factor_written = 0
    distribution_written = 0
    validation_written = 0
    for calc_date in normalized_dates:
        sample_start = _lookback_trade_start(store, calc_date, GENE_LOOKBACK_TRADE_DAYS)
        factor_samples_df = _load_persisted_factor_eval_samples(
            store,
            sample_start=sample_start,
            calc_date=calc_date,
        )

        store.conn.execute("DELETE FROM l3_gene_factor_eval WHERE calc_date = ?", [calc_date])
        if not factor_samples_df.empty:
            factor_eval_df = _build_factor_eval_rows(factor_samples_df, calc_date=calc_date)
            if not factor_eval_df.empty:
                factor_written += store.bulk_upsert("l3_gene_factor_eval", factor_eval_df)

        store.conn.execute("DELETE FROM l3_gene_distribution_eval WHERE calc_date = ?", [calc_date])
        final_snapshot_df = store.read_df(
            """
            SELECT *
            FROM l3_stock_gene
            WHERE calc_date = ?
            ORDER BY code
            """,
            (calc_date,),
        )
        if not factor_samples_df.empty and not final_snapshot_df.empty:
            distribution_eval_df = _build_distribution_eval_rows(
                samples_df=factor_samples_df,
                final_snapshot_df=final_snapshot_df,
                calc_date=calc_date,
            )
            if not distribution_eval_df.empty:
                distribution_written += store.bulk_upsert("l3_gene_distribution_eval", distribution_eval_df)

        validation_written += compute_gene_validation(store, calc_date)

    return {
        "factor_eval_rows": int(factor_written),
        "distribution_eval_rows": int(distribution_written),
        "validation_eval_rows": int(validation_written),
    }


def compute_gene_incremental_for_codes(
    store: Store,
    *,
    codes: Iterable[str],
    start: date,
    end: date,
    refresh_evals: bool = True,
    refresh_market: bool = False,
    market_calc_date: date | None = None,
) -> dict[str, object]:
    normalized_codes = _normalize_codes(codes)
    if not normalized_codes:
        return {
            "mode": "per_code_rebuild",
            "code_count": 0,
            "written_rows": 0,
            "rank_refresh_rows": 0,
            "factor_eval_rows": 0,
            "distribution_eval_rows": 0,
            "validation_eval_rows": 0,
            "market_rows": 0,
            "codes": [],
            "touched_dates": [],
        }

    rebuild_start = _lookback_trade_start(store, start, GENE_LOOKBACK_TRADE_DAYS)
    _clear_gene_range_for_codes(store, codes=normalized_codes, start=rebuild_start, end=end)
    df = _load_gene_input_for_codes(store, codes=normalized_codes, start=rebuild_start, end=end)
    if df.empty:
        return {
            "mode": "per_code_rebuild",
            "code_count": len(normalized_codes),
            "written_rows": 0,
            "rank_refresh_rows": 0,
            "factor_eval_rows": 0,
            "distribution_eval_rows": 0,
            "validation_eval_rows": 0,
            "market_rows": 0,
            "codes": normalized_codes,
            "touched_dates": [],
        }

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    snapshot_frames: list[pd.DataFrame] = []
    stock_surface_frames: list[pd.DataFrame] = []
    wave_frames: list[pd.DataFrame] = []
    event_frames: list[pd.DataFrame] = []

    for _, group in df.groupby("code", sort=True):
        snapshot_df, wave_df, event_df, _ = _build_code_gene_payload(group.reset_index(drop=True))
        if not snapshot_df.empty:
            snapshot_df = snapshot_df.loc[
                (snapshot_df["calc_date"] >= rebuild_start) & (snapshot_df["calc_date"] <= end)
            ].copy()
            if not snapshot_df.empty:
                snapshot_frames.append(snapshot_df)
                stock_surface_df = _build_stock_lifespan_surface_rows(snapshot_df=snapshot_df, wave_df=wave_df)
                if not stock_surface_df.empty:
                    stock_surface_frames.append(stock_surface_df)
        if not wave_df.empty:
            wave_df = wave_df.loc[(wave_df["end_date"] >= rebuild_start) & (wave_df["end_date"] <= end)].copy()
            if not wave_df.empty:
                wave_frames.append(wave_df)
        if not event_df.empty:
            event_df = event_df.loc[
                (event_df["event_date"] >= rebuild_start) & (event_df["event_date"] <= end)
            ].copy()
            if not event_df.empty:
                event_frames.append(event_df)

    written = 0
    touched_dates: list[date] = []
    if snapshot_frames:
        snapshot_df = _concat_sparse_frames(snapshot_frames)
        if not snapshot_df.empty:
            written += store.bulk_upsert("l3_stock_gene", snapshot_df)
            touched_dates = sorted(pd.to_datetime(snapshot_df["calc_date"], errors="coerce").dt.date.dropna().unique())
    if stock_surface_frames:
        stock_surface_df = _concat_sparse_frames(stock_surface_frames)
        if not stock_surface_df.empty:
            written += store.bulk_upsert("l3_stock_lifespan_surface", stock_surface_df)
    if wave_frames:
        wave_df = _concat_sparse_frames(wave_frames)
        if not wave_df.empty:
            written += store.bulk_upsert("l3_gene_wave", wave_df)
    if event_frames:
        event_df = _concat_sparse_frames(event_frames)
        if not event_df.empty:
            written += store.bulk_upsert("l3_gene_event", event_df)

    rank_refresh_rows = refresh_gene_cross_section_ranks(store, touched_dates)
    eval_rows = {
        "factor_eval_rows": 0,
        "distribution_eval_rows": 0,
        "validation_eval_rows": 0,
    }
    if refresh_evals:
        eval_rows = refresh_gene_evals_for_dates(store, [end])
    market_rows = 0
    if refresh_market:
        market_rows = refresh_gene_market_surfaces(store, calc_date=market_calc_date or end)

    return {
        "mode": "per_code_rebuild",
        "code_count": len(normalized_codes),
        "written_rows": int(written),
        "rank_refresh_rows": int(rank_refresh_rows),
        **eval_rows,
        "market_rows": int(market_rows),
        "codes": normalized_codes,
        "touched_dates": [item.isoformat() for item in touched_dates],
        "rebuild_start": rebuild_start.isoformat(),
        "rebuild_end": end.isoformat(),
    }


def run_gene_incremental_builder(
    store: Store,
    *,
    start: date,
    end: date,
    codes: Iterable[str] | None = None,
    refresh_evals: bool = True,
    refresh_market: bool = True,
) -> dict[str, object]:
    dirty_windows = scan_gene_dirty_windows(store, start=start, end=end, codes=codes)
    dirty_codes = [window.code for window in dirty_windows]
    summary = compute_gene_incremental_for_codes(
        store,
        codes=dirty_codes,
        start=start,
        end=end,
        refresh_evals=refresh_evals,
        refresh_market=refresh_market,
        market_calc_date=end,
    )
    summary["mode"] = "dirty_scan_incremental"
    summary["dirty_windows"] = [asdict(window) for window in dirty_windows]
    return summary
