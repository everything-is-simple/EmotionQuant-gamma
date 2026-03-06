from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings, get_settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.registry import get_active_detectors


def _combine_signals(signals: list[Signal], active_detector_count: int, mode: str = "ANY") -> list[Signal]:
    """
    多检测器组合规则：
    - ANY: 任一触发即保留
    - ALL: 同股同日需所有激活检测器触发（v0.01 默认不会用到）
    - VOTE: 票数过半保留
    """
    if not signals:
        return []
    mode_norm = mode.upper()
    grouped: dict[tuple[str, date], list[Signal]] = {}
    for signal in signals:
        grouped.setdefault((signal.code, signal.signal_date), []).append(signal)

    merged: list[Signal] = []
    for group in grouped.values():
        best = max(group, key=lambda s: s.strength)
        unique_patterns = {s.pattern for s in group}
        if mode_norm == "ANY":
            merged.append(best)
            continue
        if mode_norm == "ALL":
            if len(unique_patterns) >= active_detector_count:
                merged.append(best)
            continue
        if mode_norm == "VOTE":
            if len(unique_patterns) > active_detector_count / 2:
                merged.append(best)
            continue
        raise ValueError(f"Unsupported PAS_COMBINATION mode: {mode}")
    return merged


def _load_code_history(store: Store, code: str, asof_date: date, lookback_days: int) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT *
        FROM l2_stock_adj_daily
        WHERE code = ? AND date <= ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (code, asof_date, lookback_days + 1),
    ).sort_values("date")


def generate_signals(
    store: Store,
    candidates: list[StockCandidate],
    asof_date: date,
    config: Settings | None = None,
) -> list[Signal]:
    cfg = config or get_settings()
    detectors = get_active_detectors(cfg)
    if not detectors or not candidates:
        return []

    all_signals: list[Signal] = []
    for candidate in candidates:
        history = _load_code_history(store, candidate.code, asof_date, cfg.pas_lookback_days)
        if history.empty or len(history) < cfg.pas_min_history_days:
            continue
        for detector in detectors:
            signal = detector.detect(candidate.code, asof_date, history)
            if signal is not None:
                all_signals.append(signal)

    merged = _combine_signals(all_signals, len(detectors), cfg.pas_combination)
    if merged:
        rows = pd.DataFrame([s.model_dump() for s in merged])
        # 信号表必须 upsert：同 signal_id 重跑覆盖，不允许重复累积。
        store.bulk_upsert("l3_signals", rows)
    return merged
