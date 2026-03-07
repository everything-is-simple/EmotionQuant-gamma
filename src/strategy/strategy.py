from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings, get_settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.ranker import build_dtt_rank_frame, materialize_ranked_signals
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
    run_id: str | None = None,
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
    if not merged:
        return []

    prepared = [
        signal
        if signal.bof_strength is not None
        else signal.model_copy(update={"bof_strength": float(signal.strength)})
        for signal in merged
    ]

    if not cfg.use_dtt_pipeline:
        # legacy 对照链继续沿用旧 formal schema，只做 BOF 输出。
        rows = pd.DataFrame([signal.to_formal_signal_row() for signal in prepared])
        store.bulk_upsert("l3_signals", rows)
        return prepared

    if run_id is None or not run_id.strip():
        raise ValueError("DTT pipeline requires run_id for l3_signal_rank_exp traceability.")

    # DTT 主线先写 sidecar 真相源，再把入选 Top-N 的正式信号写回 l3_signals。
    rank_frame = build_dtt_rank_frame(
        store=store,
        signals=prepared,
        candidates=candidates,
        asof_date=asof_date,
        run_id=run_id.strip(),
        config=cfg,
    )
    if not rank_frame.empty:
        store.bulk_upsert("l3_signal_rank_exp", rank_frame)

    selected = materialize_ranked_signals(prepared, rank_frame)
    if selected:
        rows = pd.DataFrame([signal.to_formal_signal_row() for signal in selected])
        store.bulk_upsert("l3_signals", rows)
    return selected
