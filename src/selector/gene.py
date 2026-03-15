from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd

from src.data.store import Store

PivotKind = Literal["HIGH", "LOW"]
WaveDirection = Literal["UP", "DOWN"]

PIVOT_NEIGHBOR_BARS = 2
PIVOT_CONFIRMATION_BARS = 2
TWO_B_CONFIRMATION_BARS = 3
GENE_LOOKBACK_TRADE_DAYS = 260


@dataclass(frozen=True)
class PivotPoint:
    index: int
    confirm_index: int
    pivot_date: date
    confirm_date: date
    kind: PivotKind
    price: float


@dataclass(frozen=True)
class ExtremeCandidate:
    index: int
    event_date: date
    price: float
    previous_extreme_price: float
    failure_index: int | None
    failure_date: date | None


@dataclass
class ActiveWaveState:
    start_index: int
    start_date: date
    reference_price: float
    direction: WaveDirection
    event_candidates: list[ExtremeCandidate]
    next_event_ptr: int = 0
    failure_schedule: list[int] = field(default_factory=list)
    failure_ptr: int = 0
    extreme_count: int = 0
    last_extreme_seq: int | None = None
    last_extreme_date: date | None = None
    last_extreme_price: float | None = None
    two_b_failure_count: int = 0


def _lookback_trade_start(store: Store, start: date, days: int) -> date:
    current = start
    for _ in range(max(0, days)):
        prev = store.prev_trade_date(current)
        if prev is None:
            return current
        current = prev
    return current


def _clear_gene_range(store: Store, start: date, end: date) -> None:
    store.conn.execute("DELETE FROM l3_stock_gene WHERE calc_date BETWEEN ? AND ?", [start, end])
    store.conn.execute("DELETE FROM l3_gene_wave WHERE end_date BETWEEN ? AND ?", [start, end])
    store.conn.execute("DELETE FROM l3_gene_event WHERE event_date BETWEEN ? AND ?", [start, end])


def _load_gene_input(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT code, date, adj_open, adj_high, adj_low, adj_close, volume, amount
        FROM l2_stock_adj_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY code, date
        """,
        (start, end),
    )


def _build_extreme_candidates(frame: pd.DataFrame, direction: WaveDirection) -> list[ExtremeCandidate]:
    dates = pd.to_datetime(frame["date"]).dt.date.to_list()
    highs = pd.to_numeric(frame["adj_high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(frame["adj_low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(frame["adj_close"], errors="coerce").to_numpy(dtype=float)

    candidates: list[ExtremeCandidate] = []
    running_extreme = np.nan
    for idx in range(len(frame)):
        price = highs[idx] if direction == "UP" else lows[idx]
        if not np.isfinite(price):
            continue
        if idx == 0:
            running_extreme = price
            continue
        previous_extreme = float(running_extreme)
        is_breakout = price > previous_extreme if direction == "UP" else price < previous_extreme
        if is_breakout:
            failure_index: int | None = None
            for probe in range(idx + 1, min(len(frame), idx + TWO_B_CONFIRMATION_BARS + 1)):
                close_value = closes[probe]
                if not np.isfinite(close_value):
                    continue
                if direction == "UP" and close_value < previous_extreme:
                    failure_index = probe
                    break
                if direction == "DOWN" and close_value > previous_extreme:
                    failure_index = probe
                    break
            candidates.append(
                ExtremeCandidate(
                    index=idx,
                    event_date=dates[idx],
                    price=float(price),
                    previous_extreme_price=previous_extreme,
                    failure_index=failure_index,
                    failure_date=dates[failure_index] if failure_index is not None else None,
                )
            )
            running_extreme = price
            continue
        if direction == "UP":
            running_extreme = max(running_extreme, price)
        else:
            running_extreme = min(running_extreme, price)
    return candidates


def _is_swing_high(highs: np.ndarray, idx: int) -> bool:
    left = highs[idx - PIVOT_NEIGHBOR_BARS : idx]
    right = highs[idx + 1 : idx + PIVOT_NEIGHBOR_BARS + 1]
    if len(left) < PIVOT_NEIGHBOR_BARS or len(right) < PIVOT_NEIGHBOR_BARS:
        return False
    current = highs[idx]
    return bool(current >= float(np.nanmax(left)) and current > float(np.nanmax(right)))


def _is_swing_low(lows: np.ndarray, idx: int) -> bool:
    left = lows[idx - PIVOT_NEIGHBOR_BARS : idx]
    right = lows[idx + 1 : idx + PIVOT_NEIGHBOR_BARS + 1]
    if len(left) < PIVOT_NEIGHBOR_BARS or len(right) < PIVOT_NEIGHBOR_BARS:
        return False
    current = lows[idx]
    return bool(current <= float(np.nanmin(left)) and current < float(np.nanmin(right)))


def _seed_initial_pivot(frame: pd.DataFrame, first_pivot: PivotPoint | None) -> PivotPoint:
    dates = pd.to_datetime(frame["date"]).dt.date.to_list()
    highs = pd.to_numeric(frame["adj_high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(frame["adj_low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(frame["adj_close"], errors="coerce").to_numpy(dtype=float)

    if first_pivot is None:
        kind: PivotKind = "LOW" if closes[-1] >= closes[0] else "HIGH"
        price = float(lows[0] if kind == "LOW" else highs[0])
        return PivotPoint(0, 0, dates[0], dates[0], kind, price)

    if first_pivot.kind == "HIGH":
        seed_index = int(np.nanargmin(lows[: first_pivot.index + 1]))
        kind = "LOW"
        price = float(lows[seed_index])
    else:
        seed_index = int(np.nanargmax(highs[: first_pivot.index + 1]))
        kind = "HIGH"
        price = float(highs[seed_index])

    if seed_index >= first_pivot.index:
        seed_index = 0
        price = float(lows[0] if kind == "LOW" else highs[0])

    return PivotPoint(
        index=seed_index,
        confirm_index=seed_index,
        pivot_date=dates[seed_index],
        confirm_date=dates[seed_index],
        kind=kind,
        price=price,
    )


def _build_confirmed_pivots(frame: pd.DataFrame) -> list[PivotPoint]:
    if len(frame) == 0:
        return []

    dates = pd.to_datetime(frame["date"]).dt.date.to_list()
    highs = pd.to_numeric(frame["adj_high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(frame["adj_low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(frame["adj_close"], errors="coerce").to_numpy(dtype=float)

    candidates: list[PivotPoint] = []
    for idx in range(PIVOT_NEIGHBOR_BARS, len(frame) - PIVOT_NEIGHBOR_BARS):
        current_high = highs[idx]
        current_low = lows[idx]
        if not np.isfinite(current_high) or not np.isfinite(current_low):
            continue

        is_high = _is_swing_high(highs, idx)
        is_low = _is_swing_low(lows, idx)
        if not is_high and not is_low:
            continue

        if is_high and is_low:
            # 十字星或极短噪声区优先尊重当日收盘偏向，避免同一根 K 线同时落双 pivot。
            prev_close = closes[idx - 1]
            next_close = closes[idx + 1]
            is_high = closes[idx] >= np.nanmean([prev_close, next_close])
            is_low = not is_high

        kind: PivotKind = "HIGH" if is_high else "LOW"
        price = float(current_high if is_high else current_low)
        confirm_index = min(idx + PIVOT_CONFIRMATION_BARS, len(frame) - 1)
        candidates.append(
            PivotPoint(
                index=idx,
                confirm_index=confirm_index,
                pivot_date=dates[idx],
                confirm_date=dates[confirm_index],
                kind=kind,
                price=price,
            )
        )

    normalized: list[PivotPoint] = []
    for pivot in candidates:
        if not normalized:
            normalized.append(pivot)
            continue
        previous = normalized[-1]
        if pivot.kind == previous.kind:
            replace = (pivot.kind == "HIGH" and pivot.price >= previous.price) or (
                pivot.kind == "LOW" and pivot.price <= previous.price
            )
            if replace:
                normalized[-1] = pivot
            continue
        normalized.append(pivot)

    seed = _seed_initial_pivot(frame, normalized[0] if normalized else None)
    pivots = [seed]
    for pivot in normalized:
        if pivot.index <= pivots[-1].index:
            continue
        if pivot.kind == pivots[-1].kind:
            replace = (pivot.kind == "HIGH" and pivot.price >= pivots[-1].price) or (
                pivot.kind == "LOW" and pivot.price <= pivots[-1].price
            )
            if replace:
                pivots[-1] = pivot
            continue
        pivots.append(pivot)
    return pivots


def _relative_strength_stats(history: list[float], value: float) -> dict[str, float | int]:
    if not history:
        return {"rank": 1, "percentile": 50.0, "zscore": 0.0, "sample_size": 0}
    arr = np.asarray(history, dtype=float)
    rank = 1 + int(np.sum(arr > value))
    percentile = 100.0 * float(np.mean(arr <= value))
    std = float(arr.std(ddof=0))
    zscore = 0.0 if std <= 1e-12 else float((value - float(arr.mean())) / std)
    return {
        "rank": rank,
        "percentile": percentile,
        "zscore": zscore,
        "sample_size": int(len(history)),
    }


def _extract_wave_events(
    code: str,
    wave_id: str,
    direction: WaveDirection,
    start_index: int,
    end_index: int,
    candidates: list[ExtremeCandidate],
) -> tuple[list[dict[str, object]], int, date | None, float | None]:
    rows: list[dict[str, object]] = []
    selected = [item for item in candidates if start_index <= item.index <= end_index]
    if not selected:
        return rows, 0, None, None

    for seq, event in enumerate(selected, start=1):
        active_days = max(event.index - start_index + 1, 1)
        spacing = event.index - (selected[seq - 2].index if seq > 1 else start_index)
        rows.append(
            {
                "code": code,
                "wave_id": wave_id,
                "event_date": event.event_date,
                "event_seq": seq,
                "direction": direction,
                "event_type": "NEW_HIGH" if direction == "UP" else "NEW_LOW",
                "event_price": float(event.price),
                "previous_extreme_price": float(event.previous_extreme_price),
                "spacing_trade_days": int(spacing),
                "density_after_event": float(seq / active_days),
                "is_two_b_failure": bool(
                    event.failure_index is not None and event.failure_index <= end_index
                ),
                "failure_date": event.failure_date,
            }
        )
    last = selected[-1]
    failure_count = sum(
        1 for item in selected if item.failure_index is not None and item.failure_index <= end_index
    )
    return rows, failure_count, last.event_date, float(last.price)


def _build_wave_rows(
    code: str,
    pivots: list[PivotPoint],
    up_candidates: list[ExtremeCandidate],
    down_candidates: list[ExtremeCandidate],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    waves: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    for start_pivot, end_pivot in zip(pivots, pivots[1:]):
        if start_pivot.index >= end_pivot.index or start_pivot.kind == end_pivot.kind:
            continue
        direction: WaveDirection = "UP" if start_pivot.kind == "LOW" else "DOWN"
        start_price = float(start_pivot.price)
        end_price = float(end_pivot.price)
        if start_price <= 0:
            continue
        signed_return_pct = ((end_price - start_price) / start_price) * 100.0
        magnitude_pct = abs(signed_return_pct)
        duration_trade_days = int(end_pivot.index - start_pivot.index)
        wave_id = (
            f"{code}::{start_pivot.pivot_date.isoformat()}::{end_pivot.pivot_date.isoformat()}::{direction}"
        )
        candidates = up_candidates if direction == "UP" else down_candidates
        event_rows, two_b_count, last_extreme_date, last_extreme_price = _extract_wave_events(
            code=code,
            wave_id=wave_id,
            direction=direction,
            start_index=start_pivot.index,
            end_index=end_pivot.index,
            candidates=candidates,
        )
        events.extend(event_rows)
        extreme_count = len(event_rows)
        extreme_density = float(extreme_count / max(duration_trade_days, 1))
        waves.append(
            {
                "code": code,
                "wave_id": wave_id,
                "direction": direction,
                "start_date": start_pivot.pivot_date,
                "end_date": end_pivot.pivot_date,
                "start_price": start_price,
                "end_price": end_price,
                "signed_return_pct": float(signed_return_pct),
                "magnitude_pct": float(magnitude_pct),
                "duration_trade_days": duration_trade_days,
                "extreme_count": extreme_count,
                "extreme_density": extreme_density,
                "last_extreme_date": last_extreme_date,
                "last_extreme_price": last_extreme_price,
                "two_b_failure_count": two_b_count,
                "end_confirm_index": int(end_pivot.confirm_index),
                "trend_direction_before": "UNSET",
                "trend_direction_after": "UNSET",
                "wave_role": "MAINSTREAM",
                "reversal_tag": "NONE",
            }
        )
    return waves, events


def _assign_wave_trend_context(waves: list[dict[str, object]]) -> None:
    major_trend = "UNSET"
    highest_up_end: float | None = None
    lowest_down_end: float | None = None
    for wave in waves:
        direction = str(wave["direction"])
        before = major_trend
        role = "MAINSTREAM" if major_trend in {"UNSET", direction} else "COUNTERTREND"
        reversal_tag = "NONE"
        if direction == "UP":
            end_price = float(wave["end_price"])
            if highest_up_end is None or end_price > highest_up_end:
                highest_up_end = end_price
                if major_trend == "DOWN":
                    reversal_tag = "ONE_TWO_THREE_UP"
                elif major_trend == "UNSET":
                    reversal_tag = "INITIAL_TREND_UP"
                major_trend = "UP"
                role = "MAINSTREAM"
        else:
            end_price = float(wave["end_price"])
            if lowest_down_end is None or end_price < lowest_down_end:
                lowest_down_end = end_price
                if major_trend == "UP":
                    reversal_tag = "ONE_TWO_THREE_DOWN"
                elif major_trend == "UNSET":
                    reversal_tag = "INITIAL_TREND_DOWN"
                major_trend = "DOWN"
                role = "MAINSTREAM"
        if reversal_tag == "NONE" and int(wave["two_b_failure_count"]) > 0:
            reversal_tag = "TWO_B_WATCH"
        wave["trend_direction_before"] = before
        wave["trend_direction_after"] = major_trend if major_trend != "UNSET" else direction
        wave["wave_role"] = role
        wave["reversal_tag"] = reversal_tag


def _apply_wave_history_scores(waves: list[dict[str, object]]) -> None:
    history_by_direction: dict[str, list[dict[str, object]]] = {"UP": [], "DOWN": []}
    for wave in waves:
        history = history_by_direction[str(wave["direction"])]
        magnitude_stats = _relative_strength_stats(
            [float(item["magnitude_pct"]) for item in history],
            float(wave["magnitude_pct"]),
        )
        duration_stats = _relative_strength_stats(
            [float(item["duration_trade_days"]) for item in history],
            float(wave["duration_trade_days"]),
        )
        density_stats = _relative_strength_stats(
            [float(item["extreme_density"]) for item in history],
            float(wave["extreme_density"]),
        )
        wave["history_sample_size"] = int(magnitude_stats["sample_size"])
        wave["magnitude_rank"] = int(magnitude_stats["rank"])
        wave["duration_rank"] = int(duration_stats["rank"])
        wave["extreme_density_rank"] = int(density_stats["rank"])
        wave["magnitude_percentile"] = float(magnitude_stats["percentile"])
        wave["duration_percentile"] = float(duration_stats["percentile"])
        wave["extreme_density_percentile"] = float(density_stats["percentile"])
        wave["magnitude_zscore"] = float(magnitude_stats["zscore"])
        wave["duration_zscore"] = float(duration_stats["zscore"])
        wave["extreme_density_zscore"] = float(density_stats["zscore"])
        history.append(wave)


def _initial_active_state(
    pivot: PivotPoint,
    direction: WaveDirection,
    candidates: list[ExtremeCandidate],
) -> ActiveWaveState:
    return ActiveWaveState(
        start_index=int(pivot.index),
        start_date=pivot.pivot_date,
        reference_price=float(pivot.price),
        direction=direction,
        event_candidates=[item for item in candidates if item.index >= pivot.index],
    )


def _advance_active_state(state: ActiveWaveState, current_index: int) -> None:
    while state.next_event_ptr < len(state.event_candidates):
        event = state.event_candidates[state.next_event_ptr]
        if event.index > current_index:
            break
        state.next_event_ptr += 1
        state.extreme_count += 1
        state.last_extreme_seq = state.extreme_count
        state.last_extreme_date = event.event_date
        state.last_extreme_price = float(event.price)
        if event.failure_index is not None:
            state.failure_schedule.append(int(event.failure_index))
            state.failure_schedule.sort()

    while state.failure_ptr < len(state.failure_schedule):
        failure_index = state.failure_schedule[state.failure_ptr]
        if failure_index > current_index:
            break
        state.failure_ptr += 1
        state.two_b_failure_count += 1


def _gene_score_from_percentiles(
    magnitude_percentile: float,
    duration_percentile: float,
    density_percentile: float,
    direction: WaveDirection,
) -> tuple[float, float, float]:
    composite = float(np.nanmean([magnitude_percentile, duration_percentile, density_percentile]))
    if direction == "UP":
        return composite, 0.0, composite
    return 0.0, composite, composite


def _build_daily_snapshots(
    code: str,
    frame: pd.DataFrame,
    pivots: list[PivotPoint],
    waves: list[dict[str, object]],
    up_candidates: list[ExtremeCandidate],
    down_candidates: list[ExtremeCandidate],
) -> list[dict[str, object]]:
    if frame.empty or not pivots:
        return []

    dates = pd.to_datetime(frame["date"]).dt.date.to_list()
    closes = pd.to_numeric(frame["adj_close"], errors="coerce").to_numpy(dtype=float)

    completed_by_direction: dict[str, list[dict[str, object]]] = {"UP": [], "DOWN": []}
    latest_completed_reversal = "NONE"
    trend_direction = "UNSET"
    wave_cursor = 0
    pivot_cursor = 0
    current_pivot = pivots[0]
    active_state = _initial_active_state(
        pivot=current_pivot,
        direction="UP" if current_pivot.kind == "LOW" else "DOWN",
        candidates=up_candidates if current_pivot.kind == "LOW" else down_candidates,
    )
    snapshots: list[dict[str, object]] = []

    for idx, calc_date in enumerate(dates):
        while wave_cursor < len(waves) and int(waves[wave_cursor]["end_confirm_index"]) <= idx:
            completed = waves[wave_cursor]
            completed_by_direction[str(completed["direction"])].append(completed)
            trend_direction = str(completed["trend_direction_after"])
            latest_completed_reversal = str(completed["reversal_tag"])
            wave_cursor += 1

        while pivot_cursor + 1 < len(pivots) and pivots[pivot_cursor + 1].confirm_index <= idx:
            pivot_cursor += 1
            current_pivot = pivots[pivot_cursor]
            direction: WaveDirection = "UP" if current_pivot.kind == "LOW" else "DOWN"
            active_state = _initial_active_state(
                pivot=current_pivot,
                direction=direction,
                candidates=up_candidates if direction == "UP" else down_candidates,
            )

        _advance_active_state(active_state, idx)
        direction = active_state.direction
        current_close = float(closes[idx]) if np.isfinite(closes[idx]) else float(active_state.reference_price)
        signed_return_pct = (
            ((current_close - active_state.reference_price) / active_state.reference_price) * 100.0
            if active_state.reference_price > 0
            else 0.0
        )
        magnitude_pct = abs(signed_return_pct)
        age_trade_days = int(idx - active_state.start_index + 1)
        density = float(active_state.extreme_count / max(age_trade_days, 1))
        history = completed_by_direction[direction]
        magnitude_stats = _relative_strength_stats(
            [float(item["magnitude_pct"]) for item in history],
            magnitude_pct,
        )
        duration_stats = _relative_strength_stats(
            [float(item["duration_trade_days"]) for item in history],
            float(age_trade_days),
        )
        density_stats = _relative_strength_stats(
            [float(item["extreme_density"]) for item in history],
            density,
        )
        bull_score, bear_score, gene_score = _gene_score_from_percentiles(
            magnitude_percentile=float(magnitude_stats["percentile"]),
            duration_percentile=float(duration_stats["percentile"]),
            density_percentile=float(density_stats["percentile"]),
            direction=direction,
        )
        if latest_completed_reversal.startswith("ONE_TWO_THREE") and trend_direction == direction:
            reversal_state = latest_completed_reversal
        elif active_state.two_b_failure_count > 0:
            reversal_state = "TWO_B_WATCH"
        elif trend_direction not in {"UNSET", direction}:
            reversal_state = "COUNTERTREND_WATCH"
        else:
            reversal_state = "NONE"

        current_wave_role = "MAINSTREAM" if trend_direction in {"UNSET", direction} else "COUNTERTREND"
        snapshots.append(
            {
                "code": code,
                "calc_date": calc_date,
                "bull_score": bull_score,
                "bear_score": bear_score,
                "gene_score": gene_score,
                "new_high_freq": density if direction == "UP" else 0.0,
                "new_low_freq": density if direction == "DOWN" else 0.0,
                "strength_ratio": float(magnitude_stats["percentile"] / 100.0) if direction == "UP" else 0.0,
                "weakness_ratio": float(magnitude_stats["percentile"] / 100.0) if direction == "DOWN" else 0.0,
                "resilience": float(duration_stats["percentile"] / 100.0) if direction == "UP" else 0.0,
                "fragility": float(duration_stats["percentile"] / 100.0) if direction == "DOWN" else 0.0,
                "trend_direction": trend_direction if trend_direction != "UNSET" else direction,
                "current_wave_id": f"{code}::{active_state.start_date.isoformat()}::{direction}",
                "current_wave_direction": direction,
                "current_wave_role": current_wave_role,
                "reversal_state": reversal_state,
                "latest_completed_reversal_tag": latest_completed_reversal,
                "current_wave_start_date": active_state.start_date,
                "current_wave_reference_price": float(active_state.reference_price),
                "current_wave_terminal_price": current_close,
                "current_wave_age_trade_days": age_trade_days,
                "current_wave_signed_return_pct": float(signed_return_pct),
                "current_wave_magnitude_pct": magnitude_pct,
                "current_wave_extreme_count": int(active_state.extreme_count),
                "current_wave_extreme_density": density,
                "current_wave_last_extreme_seq": active_state.last_extreme_seq,
                "current_wave_last_extreme_date": active_state.last_extreme_date,
                "current_wave_last_extreme_price": active_state.last_extreme_price,
                "current_wave_two_b_failure_count": int(active_state.two_b_failure_count),
                "current_wave_history_sample_size": int(magnitude_stats["sample_size"]),
                "current_wave_magnitude_rank": int(magnitude_stats["rank"]),
                "current_wave_duration_rank": int(duration_stats["rank"]),
                "current_wave_extreme_density_rank": int(density_stats["rank"]),
                "current_wave_magnitude_percentile": float(magnitude_stats["percentile"]),
                "current_wave_duration_percentile": float(duration_stats["percentile"]),
                "current_wave_extreme_density_percentile": float(density_stats["percentile"]),
                "current_wave_magnitude_zscore": float(magnitude_stats["zscore"]),
                "current_wave_duration_zscore": float(duration_stats["zscore"]),
                "current_wave_extreme_density_zscore": float(density_stats["zscore"]),
            }
        )
    return snapshots


def _apply_cross_section_ranks(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    if snapshot_df.empty:
        return snapshot_df
    ranked = snapshot_df.copy()
    group_cols = ["calc_date", "current_wave_direction"]
    metric_map = {
        "current_wave_magnitude_pct": ("cross_section_magnitude_rank", "cross_section_magnitude_percentile"),
        "current_wave_age_trade_days": ("cross_section_duration_rank", "cross_section_duration_percentile"),
        "current_wave_extreme_density": (
            "cross_section_extreme_density_rank",
            "cross_section_extreme_density_percentile",
        ),
    }
    for metric, (rank_col, pct_col) in metric_map.items():
        ranked[rank_col] = (
            ranked.groupby(group_cols)[metric]
            .rank(method="dense", ascending=False)
            .astype("Int64")
        )
        ranked[pct_col] = ranked.groupby(group_cols)[metric].rank(method="max", pct=True) * 100.0
    return ranked


def _build_code_gene_payload(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    code = str(frame["code"].iloc[0])
    pivots = _build_confirmed_pivots(frame)
    up_candidates = _build_extreme_candidates(frame, "UP")
    down_candidates = _build_extreme_candidates(frame, "DOWN")
    wave_rows, event_rows = _build_wave_rows(
        code=code,
        pivots=pivots,
        up_candidates=up_candidates,
        down_candidates=down_candidates,
    )
    _assign_wave_trend_context(wave_rows)
    _apply_wave_history_scores(wave_rows)
    snapshot_rows = _build_daily_snapshots(
        code=code,
        frame=frame,
        pivots=pivots,
        waves=wave_rows,
        up_candidates=up_candidates,
        down_candidates=down_candidates,
    )
    return pd.DataFrame(snapshot_rows), pd.DataFrame(wave_rows), pd.DataFrame(event_rows)


def compute_gene(store: Store, start: date, end: date) -> int:
    """
    第一版历史波段标尺：
    - 只消费 L2 复权日线
    - 输出 completed wave ledger、extreme event ledger 与 daily snapshot
    - 不参与实时选股漏斗，只作为第四战场研究对象层
    """
    rebuild_start = _lookback_trade_start(store, start, GENE_LOOKBACK_TRADE_DAYS)
    _clear_gene_range(store, rebuild_start, end)
    df = _load_gene_input(store, rebuild_start, end)
    if df.empty:
        return 0

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    snapshot_frames: list[pd.DataFrame] = []
    wave_frames: list[pd.DataFrame] = []
    event_frames: list[pd.DataFrame] = []

    for _, group in df.groupby("code", sort=True):
        snapshot_df, wave_df, event_df = _build_code_gene_payload(group.reset_index(drop=True))
        if not snapshot_df.empty:
            snapshot_frames.append(snapshot_df)
        if not wave_df.empty:
            wave_frames.append(wave_df)
        if not event_df.empty:
            event_frames.append(event_df)

    total_written = 0

    if snapshot_frames:
        snapshot_df = pd.concat(snapshot_frames, ignore_index=True)
        snapshot_df = _apply_cross_section_ranks(snapshot_df)
        snapshot_df = snapshot_df.loc[
            (snapshot_df["calc_date"] >= rebuild_start) & (snapshot_df["calc_date"] <= end)
        ].copy()
        if not snapshot_df.empty:
            total_written += store.bulk_upsert("l3_stock_gene", snapshot_df)

    if wave_frames:
        wave_df = pd.concat(wave_frames, ignore_index=True)
        wave_df = wave_df.loc[
            (wave_df["end_date"] >= rebuild_start) & (wave_df["end_date"] <= end)
        ].copy()
        if not wave_df.empty:
            total_written += store.bulk_upsert("l3_gene_wave", wave_df)

    if event_frames:
        event_df = pd.concat(event_frames, ignore_index=True)
        event_df = event_df.loc[
            (event_df["event_date"] >= rebuild_start) & (event_df["event_date"] <= end)
        ].copy()
        if not event_df.empty:
            total_written += store.bulk_upsert("l3_gene_event", event_df)

    return total_written
