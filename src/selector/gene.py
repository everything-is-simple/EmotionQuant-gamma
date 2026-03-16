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
FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS = 10
FACTOR_EVAL_SAMPLE_SCOPE = "SELF_HISTORY_PERCENTILE"
FACTOR_EVAL_DIRECTION_SCOPE = "ALL"
FACTOR_EVAL_BIN_METHOD = "FIXED_PERCENTILE_20"
FACTOR_EVAL_BIN_EDGES = [0.0, 20.0, 40.0, 60.0, 80.0, 100.000001]
FACTOR_EVAL_BIN_LABELS = ["P0_20", "P20_40", "P40_60", "P60_80", "P80_100"]
G2_DISTRIBUTION_SAMPLE_SCOPE = "SELF_HISTORY_DISTRIBUTION"
G2_DISTRIBUTION_BAND_METHOD = "P65_P95"
G2_BAND_NORMAL = "NORMAL"
G2_BAND_STRONG = "STRONG"
G2_BAND_EXTREME = "EXTREME"
G2_BAND_UNSCALED = "UNSCALED"
EVENT_FAMILY_EXTREME = "EXTREME"
EVENT_FAMILY_STRUCTURE = "STRUCTURE"
TURN_CONFIRM_NONE = "NONE"
TURN_CONFIRM_UP = "CONFIRMED_TURN_UP"
TURN_CONFIRM_DOWN = "CONFIRMED_TURN_DOWN"
TWO_B_TOP = "2B_TOP"
TWO_B_BOTTOM = "2B_BOTTOM"
STEP1_EVENT = "123_STEP1"
STEP2_EVENT = "123_STEP2"
STEP3_EVENT = "123_STEP3"
G4_VALIDATION_SAMPLE_SCOPE = "SELF_HISTORY_CURRENT_WAVE"
G4_PRIMARY_RULER = "PRIMARY_RULER"
G4_SUPPORTING_RULER = "SUPPORTING_RULER"
G4_WEAK_COMPONENT = "WEAK_COMPONENT"
G4_KEEP_COMPOSITE = "KEEP_COMPOSITE"
G4_SUMMARY_ONLY = "SUMMARY_ONLY"
G4_DOWNGRADE_COMPONENT_PANEL = "DOWNGRADE_COMPONENT_PANEL"


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
    store.conn.execute("DELETE FROM l3_gene_factor_eval WHERE calc_date BETWEEN ? AND ?", [start, end])
    store.conn.execute("DELETE FROM l3_gene_distribution_eval WHERE calc_date BETWEEN ? AND ?", [start, end])
    store.conn.execute("DELETE FROM l3_gene_validation_eval WHERE calc_date BETWEEN ? AND ?", [start, end])


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


def _distribution_thresholds(history: list[float]) -> dict[str, float | int]:
    if not history:
        return {"sample_size": 0, "p65": np.nan, "p95": np.nan}
    arr = np.asarray(history, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"sample_size": 0, "p65": np.nan, "p95": np.nan}
    return {
        "sample_size": int(len(arr)),
        "p65": float(np.percentile(arr, 65)),
        "p95": float(np.percentile(arr, 95)),
    }


def _optional_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not np.isfinite(number):
        return None
    return number


def _distribution_band(value: float, thresholds: dict[str, float | int]) -> str:
    sample_size = int(thresholds["sample_size"])
    p65 = _optional_float(thresholds["p65"])
    p95 = _optional_float(thresholds["p95"])
    if sample_size <= 0 or p65 is None or p95 is None or not np.isfinite(value):
        return G2_BAND_UNSCALED
    if value < p65:
        return G2_BAND_NORMAL
    if value <= p95:
        return G2_BAND_STRONG
    return G2_BAND_EXTREME


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
                "event_family": EVENT_FAMILY_EXTREME,
                "structure_direction": None,
                "anchor_wave_id": wave_id,
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
                "turn_confirm_type": TURN_CONFIRM_NONE,
                "turn_step1_date": None,
                "turn_step2_date": None,
                "turn_step3_date": None,
                "two_b_confirm_type": TURN_CONFIRM_NONE,
                "two_b_confirm_date": None,
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
                if major_trend == "UNSET":
                    reversal_tag = "INITIAL_TREND_UP"
                major_trend = "UP"
                role = "MAINSTREAM"
        else:
            end_price = float(wave["end_price"])
            if lowest_down_end is None or end_price < lowest_down_end:
                lowest_down_end = end_price
                if major_trend == "UNSET":
                    reversal_tag = "INITIAL_TREND_DOWN"
                major_trend = "DOWN"
                role = "MAINSTREAM"
        if reversal_tag == "NONE" and int(wave["two_b_failure_count"]) > 0:
            reversal_tag = "TWO_B_WATCH"
        wave["trend_direction_before"] = before
        wave["trend_direction_after"] = major_trend if major_trend != "UNSET" else direction
        wave["wave_role"] = role
        wave["reversal_tag"] = reversal_tag


def _wave_for_date(waves: list[dict[str, object]], event_date: date | None) -> dict[str, object] | None:
    if event_date is None:
        return None
    for wave in waves:
        start_date = wave["start_date"]
        end_date = wave["end_date"]
        if start_date is None or end_date is None:
            continue
        if start_date <= event_date <= end_date:
            return wave
    return None


def _renumber_wave_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    ordered = sorted(
        events,
        key=lambda row: (
            str(row["wave_id"]),
            row["event_date"],
            0 if row.get("event_family") == EVENT_FAMILY_EXTREME else 1,
            str(row["event_type"]),
        ),
    )
    seq_by_wave: dict[str, int] = {}
    for row in ordered:
        wave_id = str(row["wave_id"])
        seq = seq_by_wave.get(wave_id, 0) + 1
        seq_by_wave[wave_id] = seq
        row["event_seq"] = seq
    return ordered


def _apply_structure_labels(waves: list[dict[str, object]], events: list[dict[str, object]]) -> list[dict[str, object]]:
    if not waves:
        return events

    structure_events: list[dict[str, object]] = []

    for event in events:
        failure_date = event.get("failure_date")
        if failure_date is None:
            continue
        if str(event["event_type"]) == "NEW_HIGH":
            event_type = TWO_B_TOP
            structure_direction = "DOWN"
        elif str(event["event_type"]) == "NEW_LOW":
            event_type = TWO_B_BOTTOM
            structure_direction = "UP"
        else:
            continue
        target_wave = _wave_for_date(waves, failure_date)
        if target_wave is None:
            continue
        target_wave["two_b_failure_count"] = int(target_wave["two_b_failure_count"]) + 1
        target_wave["two_b_confirm_type"] = event_type
        target_wave["two_b_confirm_date"] = failure_date
        if str(target_wave["reversal_tag"]) == "NONE":
            target_wave["reversal_tag"] = "TWO_B_WATCH"
        structure_events.append(
            {
                "code": target_wave["code"],
                "wave_id": target_wave["wave_id"],
                "event_seq": 0,
                "event_date": failure_date,
                "direction": target_wave["direction"],
                "event_type": event_type,
                "event_price": event["previous_extreme_price"],
                "previous_extreme_price": event["previous_extreme_price"],
                "spacing_trade_days": None,
                "density_after_event": None,
                "is_two_b_failure": True,
                "failure_date": failure_date,
                "event_family": EVENT_FAMILY_STRUCTURE,
                "structure_direction": structure_direction,
                "anchor_wave_id": event["wave_id"],
            }
        )

    for idx in range(2, len(waves)):
        wave_a = waves[idx - 2]
        wave_b = waves[idx - 1]
        wave_c = waves[idx]
        if str(wave_c["turn_confirm_type"]) != TURN_CONFIRM_NONE:
            continue

        turn_direction: str | None = None
        reversal_tag: str | None = None
        if (
            str(wave_a["direction"]) == "UP"
            and str(wave_b["direction"]) == "DOWN"
            and str(wave_c["direction"]) == "UP"
            and float(wave_b["end_price"]) > float(wave_a["start_price"])
            and float(wave_c["end_price"]) > float(wave_a["end_price"])
        ):
            turn_direction = "UP"
            reversal_tag = "ONE_TWO_THREE_UP"
            wave_c["turn_confirm_type"] = TURN_CONFIRM_UP
        elif (
            str(wave_a["direction"]) == "DOWN"
            and str(wave_b["direction"]) == "UP"
            and str(wave_c["direction"]) == "DOWN"
            and float(wave_b["end_price"]) < float(wave_a["start_price"])
            and float(wave_c["end_price"]) < float(wave_a["end_price"])
        ):
            turn_direction = "DOWN"
            reversal_tag = "ONE_TWO_THREE_DOWN"
            wave_c["turn_confirm_type"] = TURN_CONFIRM_DOWN

        if turn_direction is None or reversal_tag is None:
            continue

        wave_c["turn_step1_date"] = wave_a["end_date"]
        wave_c["turn_step2_date"] = wave_b["end_date"]
        wave_c["turn_step3_date"] = wave_c["end_date"]
        wave_c["reversal_tag"] = reversal_tag
        structure_events.extend(
            [
                {
                    "code": wave_a["code"],
                    "wave_id": wave_a["wave_id"],
                    "event_seq": 0,
                    "event_date": wave_a["end_date"],
                    "direction": wave_a["direction"],
                    "event_type": STEP1_EVENT,
                    "event_price": wave_a["end_price"],
                    "previous_extreme_price": None,
                    "spacing_trade_days": None,
                    "density_after_event": None,
                    "is_two_b_failure": False,
                    "failure_date": None,
                    "event_family": EVENT_FAMILY_STRUCTURE,
                    "structure_direction": turn_direction,
                    "anchor_wave_id": wave_a["wave_id"],
                },
                {
                    "code": wave_b["code"],
                    "wave_id": wave_b["wave_id"],
                    "event_seq": 0,
                    "event_date": wave_b["end_date"],
                    "direction": wave_b["direction"],
                    "event_type": STEP2_EVENT,
                    "event_price": wave_b["end_price"],
                    "previous_extreme_price": None,
                    "spacing_trade_days": None,
                    "density_after_event": None,
                    "is_two_b_failure": False,
                    "failure_date": None,
                    "event_family": EVENT_FAMILY_STRUCTURE,
                    "structure_direction": turn_direction,
                    "anchor_wave_id": wave_a["wave_id"],
                },
                {
                    "code": wave_c["code"],
                    "wave_id": wave_c["wave_id"],
                    "event_seq": 0,
                    "event_date": wave_c["end_date"],
                    "direction": wave_c["direction"],
                    "event_type": STEP3_EVENT,
                    "event_price": wave_c["end_price"],
                    "previous_extreme_price": None,
                    "spacing_trade_days": None,
                    "density_after_event": None,
                    "is_two_b_failure": False,
                    "failure_date": None,
                    "event_family": EVENT_FAMILY_STRUCTURE,
                    "structure_direction": turn_direction,
                    "anchor_wave_id": wave_a["wave_id"],
                },
            ]
        )

    return _renumber_wave_events(events + structure_events)


def _apply_wave_history_scores(waves: list[dict[str, object]]) -> None:
    history_by_direction: dict[str, list[dict[str, object]]] = {"UP": [], "DOWN": []}
    for wave in waves:
        history = history_by_direction[str(wave["direction"])]
        magnitude_history = [float(item["magnitude_pct"]) for item in history]
        duration_history = [float(item["duration_trade_days"]) for item in history]
        density_history = [float(item["extreme_density"]) for item in history]
        magnitude_value = float(wave["magnitude_pct"])
        duration_value = float(wave["duration_trade_days"])
        density_value = float(wave["extreme_density"])
        magnitude_stats = _relative_strength_stats(magnitude_history, magnitude_value)
        duration_stats = _relative_strength_stats(duration_history, duration_value)
        density_stats = _relative_strength_stats(density_history, density_value)
        magnitude_thresholds = _distribution_thresholds(magnitude_history)
        duration_thresholds = _distribution_thresholds(duration_history)
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
        wave["magnitude_p65"] = _optional_float(magnitude_thresholds["p65"])
        wave["magnitude_p95"] = _optional_float(magnitude_thresholds["p95"])
        wave["magnitude_band"] = _distribution_band(magnitude_value, magnitude_thresholds)
        wave["duration_p65"] = _optional_float(duration_thresholds["p65"])
        wave["duration_p95"] = _optional_float(duration_thresholds["p95"])
        wave["duration_band"] = _distribution_band(duration_value, duration_thresholds)
        wave["wave_age_band"] = str(wave["duration_band"])
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
    latest_confirmed_turn_type = TURN_CONFIRM_NONE
    latest_confirmed_turn_date: date | None = None
    latest_two_b_confirm_type = TURN_CONFIRM_NONE
    latest_two_b_confirm_date: date | None = None
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
            if str(completed["turn_confirm_type"]) != TURN_CONFIRM_NONE:
                latest_confirmed_turn_type = str(completed["turn_confirm_type"])
                latest_confirmed_turn_date = completed["turn_step3_date"]
            if str(completed["two_b_confirm_type"]) != TURN_CONFIRM_NONE:
                latest_two_b_confirm_type = str(completed["two_b_confirm_type"])
                latest_two_b_confirm_date = completed["two_b_confirm_date"]
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
        magnitude_history = [float(item["magnitude_pct"]) for item in history]
        duration_history = [float(item["duration_trade_days"]) for item in history]
        density_history = [float(item["extreme_density"]) for item in history]
        magnitude_stats = _relative_strength_stats(magnitude_history, magnitude_pct)
        duration_stats = _relative_strength_stats(duration_history, float(age_trade_days))
        density_stats = _relative_strength_stats(density_history, density)
        magnitude_thresholds = _distribution_thresholds(magnitude_history)
        duration_thresholds = _distribution_thresholds(duration_history)
        bull_score, bear_score, gene_score = _gene_score_from_percentiles(
            magnitude_percentile=float(magnitude_stats["percentile"]),
            duration_percentile=float(duration_stats["percentile"]),
            density_percentile=float(density_stats["percentile"]),
            direction=direction,
        )
        if latest_confirmed_turn_type != TURN_CONFIRM_NONE and trend_direction == direction:
            reversal_state = latest_confirmed_turn_type
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
                "latest_confirmed_turn_type": latest_confirmed_turn_type,
                "latest_confirmed_turn_date": latest_confirmed_turn_date,
                "latest_two_b_confirm_type": latest_two_b_confirm_type,
                "latest_two_b_confirm_date": latest_two_b_confirm_date,
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
                "current_wave_magnitude_p65": _optional_float(magnitude_thresholds["p65"]),
                "current_wave_magnitude_p95": _optional_float(magnitude_thresholds["p95"]),
                "current_wave_magnitude_band": _distribution_band(magnitude_pct, magnitude_thresholds),
                "current_wave_duration_p65": _optional_float(duration_thresholds["p65"]),
                "current_wave_duration_p95": _optional_float(duration_thresholds["p95"]),
                "current_wave_duration_band": _distribution_band(float(age_trade_days), duration_thresholds),
                "current_wave_age_band": _distribution_band(float(age_trade_days), duration_thresholds),
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


def _future_terminal_close(closes: np.ndarray) -> float | None:
    finite = closes[np.isfinite(closes)]
    if len(finite) == 0:
        return None
    return float(finite[-1])


def _future_window_metrics(
    direction: WaveDirection,
    end_price: float,
    future_highs: np.ndarray,
    future_lows: np.ndarray,
    future_closes: np.ndarray,
) -> dict[str, float | bool] | None:
    if end_price <= 0:
        return None
    terminal_close = _future_terminal_close(future_closes)
    if terminal_close is None:
        return None

    max_high = float(np.nanmax(future_highs)) if np.isfinite(future_highs).any() else terminal_close
    min_low = float(np.nanmin(future_lows)) if np.isfinite(future_lows).any() else terminal_close

    if direction == "UP":
        aligned_close_return = ((terminal_close - end_price) / end_price) * 100.0
        favorable_excursion = max(0.0, ((max_high - end_price) / end_price) * 100.0)
        adverse_excursion = max(0.0, ((end_price - min_low) / end_price) * 100.0)
    else:
        aligned_close_return = ((end_price - terminal_close) / end_price) * 100.0
        favorable_excursion = max(0.0, ((end_price - min_low) / end_price) * 100.0)
        adverse_excursion = max(0.0, ((max_high - end_price) / end_price) * 100.0)

    return {
        "aligned_close_return_pct": float(aligned_close_return),
        "favorable_excursion_pct": float(favorable_excursion),
        "adverse_excursion_pct": float(adverse_excursion),
        "continuation_flag": bool(favorable_excursion > adverse_excursion and favorable_excursion > 0.0),
        "reversal_flag": bool(adverse_excursion > favorable_excursion and adverse_excursion > 0.0),
    }


def _build_factor_eval_samples(
    code: str,
    frame: pd.DataFrame,
    waves: list[dict[str, object]],
) -> pd.DataFrame:
    if not waves:
        return pd.DataFrame()

    highs = pd.to_numeric(frame["adj_high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(frame["adj_low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(frame["adj_close"], errors="coerce").to_numpy(dtype=float)

    rows: list[dict[str, object]] = []
    for wave in waves:
        end_confirm_index = int(wave["end_confirm_index"])
        start_index = end_confirm_index + 1
        if start_index >= len(frame):
            continue
        stop_index = min(len(frame), start_index + FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS)
        metrics = _future_window_metrics(
            direction=str(wave["direction"]),
            end_price=float(wave["end_price"]),
            future_highs=highs[start_index:stop_index],
            future_lows=lows[start_index:stop_index],
            future_closes=closes[start_index:stop_index],
        )
        if metrics is None:
            continue
        rows.append(
            {
                "code": code,
                "wave_id": str(wave["wave_id"]),
                "direction": str(wave["direction"]),
                "end_date": wave["end_date"],
                "magnitude_raw_pct": float(wave["magnitude_pct"]),
                "duration_raw_trade_days": float(wave["duration_trade_days"]),
                "magnitude_band": str(wave["magnitude_band"]),
                "duration_band": str(wave["duration_band"]),
                "wave_age_band": str(wave["wave_age_band"]),
                "magnitude": float(wave["magnitude_percentile"]),
                "duration": float(wave["duration_percentile"]),
                "extreme_density": float(wave["extreme_density_percentile"]),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def _spearman_like(values: pd.Series, outcomes: pd.Series) -> float:
    if len(values) < 2 or len(outcomes) < 2:
        return 0.0
    if values.nunique(dropna=True) < 2 or outcomes.nunique(dropna=True) < 2:
        return 0.0
    score = values.rank(method="average").corr(outcomes.rank(method="average"))
    if pd.isna(score):
        return 0.0
    return float(score)


def _factor_eval_row(
    calc_date: date,
    factor_name: str,
    bin_label: str,
    frame: pd.DataFrame,
    monotonicity_score: float,
) -> dict[str, object]:
    return {
        "calc_date": calc_date,
        "factor_name": factor_name,
        "sample_scope": FACTOR_EVAL_SAMPLE_SCOPE,
        "direction_scope": FACTOR_EVAL_DIRECTION_SCOPE,
        "forward_horizon_trade_days": FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS,
        "bin_method": FACTOR_EVAL_BIN_METHOD,
        "bin_label": bin_label,
        "sample_size": int(len(frame)),
        "continuation_rate": float(frame["continuation_flag"].mean()) if len(frame) else 0.0,
        "reversal_rate": float(frame["reversal_flag"].mean()) if len(frame) else 0.0,
        "median_forward_return": float(frame["aligned_close_return_pct"].median()) if len(frame) else 0.0,
        "median_forward_drawdown": float(frame["adverse_excursion_pct"].median()) if len(frame) else 0.0,
        "monotonicity_score": monotonicity_score,
    }


def _build_factor_eval_rows(samples_df: pd.DataFrame, calc_date: date) -> pd.DataFrame:
    if samples_df.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for factor_name in ("magnitude", "duration", "extreme_density"):
        factor_frame = samples_df[
            [
                factor_name,
                "aligned_close_return_pct",
                "adverse_excursion_pct",
                "continuation_flag",
                "reversal_flag",
            ]
        ].dropna()
        if factor_frame.empty:
            continue
        monotonicity_score = _spearman_like(
            factor_frame[factor_name],
            factor_frame["aligned_close_return_pct"],
        )
        rows.append(
            _factor_eval_row(
                calc_date=calc_date,
                factor_name=factor_name,
                bin_label="ALL",
                frame=factor_frame,
                monotonicity_score=monotonicity_score,
            )
        )
        bucketed = factor_frame.assign(
            bin_label=pd.cut(
                factor_frame[factor_name],
                bins=FACTOR_EVAL_BIN_EDGES,
                labels=FACTOR_EVAL_BIN_LABELS,
                include_lowest=True,
                right=True,
            )
        )
        for bin_label in FACTOR_EVAL_BIN_LABELS:
            bucket = bucketed.loc[bucketed["bin_label"] == bin_label].copy()
            if bucket.empty:
                continue
            rows.append(
                _factor_eval_row(
                    calc_date=calc_date,
                    factor_name=factor_name,
                    bin_label=bin_label,
                    frame=bucket,
                    monotonicity_score=monotonicity_score,
                )
            )
    return pd.DataFrame(rows)


def _outcome_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    if frame.empty:
        return {
            "band_sample_size": 0,
            "continuation_base_rate": 0.0,
            "reversal_base_rate": 0.0,
            "median_forward_return": 0.0,
            "median_forward_drawdown": 0.0,
        }
    return {
        "band_sample_size": int(len(frame)),
        "continuation_base_rate": float(frame["continuation_flag"].mean()),
        "reversal_base_rate": float(frame["reversal_flag"].mean()),
        "median_forward_return": float(frame["aligned_close_return_pct"].median()),
        "median_forward_drawdown": float(frame["adverse_excursion_pct"].median()),
    }


def _build_distribution_eval_rows(
    samples_df: pd.DataFrame,
    final_snapshot_df: pd.DataFrame,
    calc_date: date,
) -> pd.DataFrame:
    if samples_df.empty or final_snapshot_df.empty:
        return pd.DataFrame()

    metric_specs = [
        {
            "metric_name": "magnitude_pct",
            "current_value_col": "current_wave_magnitude_pct",
            "current_percentile_col": "current_wave_magnitude_percentile",
            "p65_col": "current_wave_magnitude_p65",
            "p95_col": "current_wave_magnitude_p95",
            "band_col": "current_wave_magnitude_band",
            "sample_band_col": "magnitude_band",
        },
        {
            "metric_name": "duration_trade_days",
            "current_value_col": "current_wave_age_trade_days",
            "current_percentile_col": "current_wave_duration_percentile",
            "p65_col": "current_wave_duration_p65",
            "p95_col": "current_wave_duration_p95",
            "band_col": "current_wave_age_band",
            "sample_band_col": "wave_age_band",
        },
    ]

    rows: list[dict[str, object]] = []
    for snapshot in final_snapshot_df.itertuples(index=False):
        code = str(snapshot.code)
        direction = str(snapshot.current_wave_direction)
        code_samples = samples_df.loc[
            (samples_df["code"] == code) & (samples_df["direction"] == direction)
        ].copy()
        for spec in metric_specs:
            band_label = str(getattr(snapshot, spec["band_col"]))
            band_samples = code_samples.loc[code_samples[spec["sample_band_col"]] == band_label].copy()
            summary = _outcome_summary(band_samples)
            rows.append(
                {
                    "code": code,
                    "calc_date": calc_date,
                    "current_wave_id": str(snapshot.current_wave_id),
                    "direction": direction,
                    "metric_name": spec["metric_name"],
                    "sample_scope": G2_DISTRIBUTION_SAMPLE_SCOPE,
                    "band_method": G2_DISTRIBUTION_BAND_METHOD,
                    "history_sample_size": int(snapshot.current_wave_history_sample_size),
                    "band_sample_size": int(summary["band_sample_size"]),
                    "current_value": float(getattr(snapshot, spec["current_value_col"])),
                    "current_percentile": float(getattr(snapshot, spec["current_percentile_col"])),
                    "threshold_p65": _optional_float(getattr(snapshot, spec["p65_col"])),
                    "threshold_p95": _optional_float(getattr(snapshot, spec["p95_col"])),
                    "band_label": band_label,
                    "continuation_base_rate": float(summary["continuation_base_rate"]),
                    "reversal_base_rate": float(summary["reversal_base_rate"]),
                    "median_forward_return": float(summary["median_forward_return"]),
                    "median_forward_drawdown": float(summary["median_forward_drawdown"]),
                }
            )
    return pd.DataFrame(rows)


def _load_snapshot_validation_metric_samples(store: Store, calc_date: date, metric_column: str) -> pd.DataFrame:
    horizon = FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS
    query = f"""
        WITH price_forward AS (
            SELECT
                code,
                date AS calc_date,
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
            WHERE date <= ?
        )
        SELECT
            s.calc_date,
            CAST(s.{metric_column} AS DOUBLE) AS metric_value,
            CASE
                WHEN s.current_wave_direction = 'UP'
                    THEN ((p.future_terminal_close - s.current_wave_terminal_price) / s.current_wave_terminal_price) * 100.0
                ELSE ((s.current_wave_terminal_price - p.future_terminal_close) / s.current_wave_terminal_price) * 100.0
            END AS aligned_close_return_pct,
            CASE
                WHEN s.current_wave_direction = 'UP'
                    THEN GREATEST(0.0, ((p.future_max_high - s.current_wave_terminal_price) / s.current_wave_terminal_price) * 100.0)
                ELSE GREATEST(0.0, ((s.current_wave_terminal_price - p.future_min_low) / s.current_wave_terminal_price) * 100.0)
            END AS favorable_excursion_pct,
            CASE
                WHEN s.current_wave_direction = 'UP'
                    THEN GREATEST(0.0, ((s.current_wave_terminal_price - p.future_min_low) / s.current_wave_terminal_price) * 100.0)
                ELSE GREATEST(0.0, ((p.future_max_high - s.current_wave_terminal_price) / s.current_wave_terminal_price) * 100.0)
            END AS adverse_excursion_pct
        FROM l3_stock_gene s
        JOIN price_forward p
          ON s.code = p.code
         AND s.calc_date = p.calc_date
        WHERE s.calc_date <= ?
          AND s.current_wave_terminal_price > 0
          AND s.current_wave_direction IN ('UP', 'DOWN')
          AND s.{metric_column} IS NOT NULL
          AND p.future_terminal_close IS NOT NULL
    """
    frame = store.read_df(query, (horizon, calc_date, calc_date))
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


def _validation_bucket_summary(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {
            "continuation_rate": 0.0,
            "median_forward_return": 0.0,
            "median_forward_drawdown": 0.0,
        }
    return {
        "continuation_rate": float(frame["continuation_flag"].mean()),
        "median_forward_return": float(frame["aligned_close_return_pct"].median()),
        "median_forward_drawdown": float(frame["adverse_excursion_pct"].median()),
    }


def _build_validation_eval_row(calc_date: date, metric_name: str, samples_df: pd.DataFrame) -> dict[str, object]:
    monotonicity_score = _spearman_like(samples_df["metric_value"], samples_df["aligned_close_return_pct"])
    bucketed = samples_df.assign(
        bin_label=pd.cut(
            samples_df["metric_value"],
            bins=FACTOR_EVAL_BIN_EDGES,
            labels=FACTOR_EVAL_BIN_LABELS,
            include_lowest=True,
            right=True,
        )
    )
    bottom = bucketed.loc[bucketed["bin_label"] == "P0_20"].copy()
    top = bucketed.loc[bucketed["bin_label"] == "P80_100"].copy()
    bottom_summary = _validation_bucket_summary(bottom)
    top_summary = _validation_bucket_summary(top)

    daily_corrs: list[float] = []
    for _, part in samples_df.groupby("calc_date", sort=True):
        corr = _spearman_like(part["metric_value"], part["aligned_close_return_pct"])
        daily_corrs.append(float(corr))
    avg_daily_rank_corr = float(np.mean(daily_corrs)) if daily_corrs else 0.0
    positive_daily_rank_corr_rate = float(np.mean([corr > 0.0 for corr in daily_corrs])) if daily_corrs else 0.0

    return {
        "calc_date": calc_date,
        "metric_name": metric_name,
        "sample_scope": G4_VALIDATION_SAMPLE_SCOPE,
        "forward_horizon_trade_days": FACTOR_EVAL_FORWARD_HORIZON_TRADE_DAYS,
        "sample_size": int(len(samples_df)),
        "monotonicity_score": float(monotonicity_score),
        "avg_daily_rank_corr": float(avg_daily_rank_corr),
        "positive_daily_rank_corr_rate": float(positive_daily_rank_corr_rate),
        "top_bucket_continuation_rate": float(top_summary["continuation_rate"]),
        "bottom_bucket_continuation_rate": float(bottom_summary["continuation_rate"]),
        "top_bucket_median_forward_return": float(top_summary["median_forward_return"]),
        "bottom_bucket_median_forward_return": float(bottom_summary["median_forward_return"]),
        "top_bucket_median_forward_drawdown": float(top_summary["median_forward_drawdown"]),
        "bottom_bucket_median_forward_drawdown": float(bottom_summary["median_forward_drawdown"]),
        "decision_tag": "",
    }


def _attach_validation_decisions(validation_df: pd.DataFrame) -> pd.DataFrame:
    if validation_df.empty:
        return validation_df

    scored = validation_df.copy()
    scored["strength_score"] = scored["monotonicity_score"].abs() + scored["avg_daily_rank_corr"].abs()

    factor_mask = scored["metric_name"].isin(
        ["magnitude_percentile", "duration_percentile", "extreme_density_percentile"]
    )
    factor_df = scored.loc[factor_mask].copy()
    best_factor_metric = "magnitude_percentile"
    best_factor_score = 0.0
    if not factor_df.empty:
        best_idx = factor_df["strength_score"].idxmax()
        best_factor_metric = str(factor_df.loc[best_idx, "metric_name"])
        best_factor_score = float(factor_df.loc[best_idx, "strength_score"])

    def _factor_decision(row: pd.Series) -> str:
        if str(row["metric_name"]) == best_factor_metric:
            return G4_PRIMARY_RULER
        if best_factor_score <= 1e-12:
            return G4_SUPPORTING_RULER
        if float(row["strength_score"]) >= best_factor_score * 0.5:
            return G4_SUPPORTING_RULER
        return G4_WEAK_COMPONENT

    decisions: list[str] = []
    for row in scored.itertuples(index=False):
        metric_name = str(row.metric_name)
        if metric_name in {"magnitude_percentile", "duration_percentile", "extreme_density_percentile"}:
            decisions.append(_factor_decision(pd.Series(row._asdict())))
            continue
        if metric_name == "gene_score":
            if best_factor_score <= 1e-12:
                decisions.append(G4_KEEP_COMPOSITE)
            elif float(row.strength_score) >= best_factor_score * 0.8:
                decisions.append(G4_KEEP_COMPOSITE)
            elif float(row.strength_score) >= best_factor_score * 0.5:
                decisions.append(G4_SUMMARY_ONLY)
            else:
                decisions.append(G4_DOWNGRADE_COMPONENT_PANEL)
            continue
        decisions.append(G4_WEAK_COMPONENT)

    scored["decision_tag"] = decisions
    return scored.drop(columns=["strength_score"])


def compute_gene_validation(store: Store, calc_date: date) -> int:
    metric_map = {
        "gene_score": "gene_score",
        "magnitude_percentile": "current_wave_magnitude_percentile",
        "duration_percentile": "current_wave_duration_percentile",
        "extreme_density_percentile": "current_wave_extreme_density_percentile",
    }
    rows: list[dict[str, object]] = []
    for metric_name, metric_column in metric_map.items():
        samples_df = _load_snapshot_validation_metric_samples(store, calc_date, metric_column)
        if samples_df.empty:
            continue
        rows.append(_build_validation_eval_row(calc_date, metric_name, samples_df))

    store.conn.execute("DELETE FROM l3_gene_validation_eval WHERE calc_date = ?", [calc_date])
    if not rows:
        return 0
    validation_df = _attach_validation_decisions(pd.DataFrame(rows))
    return store.bulk_upsert("l3_gene_validation_eval", validation_df)


def _concat_sparse_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    normalized = [frame.dropna(axis=1, how="all") for frame in frames if not frame.empty]
    if not normalized:
        return pd.DataFrame()
    return pd.concat(normalized, ignore_index=True, sort=False)


def _build_code_gene_payload(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
    event_rows = _apply_structure_labels(wave_rows, event_rows)
    _apply_wave_history_scores(wave_rows)
    snapshot_rows = _build_daily_snapshots(
        code=code,
        frame=frame,
        pivots=pivots,
        waves=wave_rows,
        up_candidates=up_candidates,
        down_candidates=down_candidates,
    )
    factor_eval_samples = _build_factor_eval_samples(
        code=code,
        frame=frame,
        waves=wave_rows,
    )
    return (
        pd.DataFrame(snapshot_rows),
        pd.DataFrame(wave_rows),
        pd.DataFrame(event_rows),
        factor_eval_samples,
    )


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
    factor_eval_sample_frames: list[pd.DataFrame] = []

    for _, group in df.groupby("code", sort=True):
        snapshot_df, wave_df, event_df, factor_eval_sample_df = _build_code_gene_payload(
            group.reset_index(drop=True)
        )
        if not snapshot_df.empty:
            snapshot_frames.append(snapshot_df)
        if not wave_df.empty:
            wave_frames.append(wave_df)
        if not event_df.empty:
            event_frames.append(event_df)
        if not factor_eval_sample_df.empty:
            factor_eval_sample_frames.append(factor_eval_sample_df)

    total_written = 0
    final_snapshot_df = pd.DataFrame()

    if snapshot_frames:
        snapshot_df = _concat_sparse_frames(snapshot_frames)
        snapshot_df = _apply_cross_section_ranks(snapshot_df)
        snapshot_df = snapshot_df.loc[
            (snapshot_df["calc_date"] >= rebuild_start) & (snapshot_df["calc_date"] <= end)
        ].copy()
        if not snapshot_df.empty:
            final_snapshot_df = snapshot_df.loc[snapshot_df["calc_date"] == end].copy()
            total_written += store.bulk_upsert("l3_stock_gene", snapshot_df)

    if wave_frames:
        wave_df = _concat_sparse_frames(wave_frames)
        wave_df = wave_df.loc[
            (wave_df["end_date"] >= rebuild_start) & (wave_df["end_date"] <= end)
        ].copy()
        if not wave_df.empty:
            total_written += store.bulk_upsert("l3_gene_wave", wave_df)

    if event_frames:
        event_df = _concat_sparse_frames(event_frames)
        event_df = event_df.loc[
            (event_df["event_date"] >= rebuild_start) & (event_df["event_date"] <= end)
        ].copy()
        if not event_df.empty:
            total_written += store.bulk_upsert("l3_gene_event", event_df)

    if factor_eval_sample_frames:
        factor_eval_samples_df = _concat_sparse_frames(factor_eval_sample_frames)
        factor_eval_df = _build_factor_eval_rows(factor_eval_samples_df, calc_date=end)
        if not factor_eval_df.empty:
            total_written += store.bulk_upsert("l3_gene_factor_eval", factor_eval_df)
        distribution_eval_df = _build_distribution_eval_rows(
            samples_df=factor_eval_samples_df,
            final_snapshot_df=final_snapshot_df,
            calc_date=end,
        )
        if not distribution_eval_df.empty:
            total_written += store.bulk_upsert("l3_gene_distribution_eval", distribution_eval_df)

    if not final_snapshot_df.empty:
        total_written += compute_gene_validation(store, end)

    return total_written
