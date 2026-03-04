from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings, get_settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.registry import get_active_detectors


def _combine_signals(signals: list[Signal], mode: str = "ANY") -> list[Signal]:
    """
    多检测器组合规则：
    - ANY: 任一触发即保留
    - ALL: 同股同日需所有激活检测器触发（v0.01 默认不会用到）
    - VOTE: 票数过半保留
    """
    if not signals:
        return []
    mode_norm = mode.upper()
    if mode_norm == "ANY":
        # 同股同日只保留强度最高的一条，避免重复下单。
        best_by_key: dict[tuple[str, date], Signal] = {}
        for s in signals:
            key = (s.code, s.signal_date)
            prev = best_by_key.get(key)
            if prev is None or s.strength > prev.strength:
                best_by_key[key] = s
        return list(best_by_key.values())
    # v0.01 阶段提供兼容分支，后续多形态时再细化门槛。
    return signals


def _load_code_history(store: Store, code: str, asof_date: date, lookback_days: int) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT *
        FROM l2_stock_adj_daily
        WHERE code = ? AND date <= ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (code, asof_date, lookback_days),
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
        if history.empty:
            continue
        for detector in detectors:
            signal = detector.detect(candidate.code, asof_date, history)
            if signal is not None:
                all_signals.append(signal)

    merged = _combine_signals(all_signals, cfg.pas_combination)
    if merged:
        rows = pd.DataFrame([s.model_dump() for s in merged])
        # 信号表必须 upsert：同 signal_id 重跑覆盖，不允许重复累积。
        store.bulk_upsert("l3_signals", rows)
    return merged

