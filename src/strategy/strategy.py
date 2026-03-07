from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings, get_settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store
from src.strategy.ranker import (
    build_dtt_score_frame,
    finalize_dtt_rank_frame,
    materialize_ranked_signals,
)
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
        SELECT code, date, adj_low, adj_close, adj_open, adj_high, volume, volume_ma20
        FROM l2_stock_adj_daily
        WHERE code = ? AND date <= ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (code, asof_date, lookback_days + 1),
    ).sort_values("date")


def _iter_candidate_batches(candidates: list[StockCandidate], batch_size: int) -> list[list[StockCandidate]]:
    size = max(1, int(batch_size))
    return [candidates[index : index + size] for index in range(0, len(candidates), size)]


def _load_candidate_histories_batch(
    store: Store,
    codes: list[str],
    asof_date: date,
    lookback_days: int,
) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame(
            columns=["code", "date", "adj_low", "adj_close", "adj_open", "adj_high", "volume", "volume_ma20"]
        )

    placeholders = ", ".join(["?"] * len(codes))
    sql = f"""
        WITH recent AS (
            SELECT
                code,
                date,
                adj_low,
                adj_close,
                adj_open,
                adj_high,
                volume,
                volume_ma20,
                ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) AS rn
            FROM l2_stock_adj_daily
            WHERE code IN ({placeholders})
              AND date <= ?
        )
        SELECT code, date, adj_low, adj_close, adj_open, adj_high, volume, volume_ma20
        FROM recent
        WHERE rn <= ?
        ORDER BY code ASC, date ASC
    """
    params = tuple(codes) + (asof_date, lookback_days + 1)
    return store.read_df(sql, params)


def _ensure_dtt_stage_table(store: Store) -> None:
    # DTT 排序中间结果先落本地临时表，避免长窗口里所有 batch 都堆在 Python 内存。
    store.conn.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS _tmp_dtt_rank_stage (
            run_id       VARCHAR NOT NULL,
            signal_id    VARCHAR NOT NULL,
            signal_date  DATE    NOT NULL,
            code         VARCHAR NOT NULL,
            industry     VARCHAR,
            variant      VARCHAR NOT NULL,
            bof_strength DOUBLE NOT NULL,
            irs_score    DOUBLE NOT NULL,
            mss_score    DOUBLE NOT NULL,
            final_score  DOUBLE NOT NULL
        )
        """
    )


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

    if cfg.use_dtt_pipeline:
        if run_id is None or not run_id.strip():
            raise ValueError("DTT pipeline requires run_id for l3_signal_rank_exp traceability.")
        run_id_text = run_id.strip()
        _ensure_dtt_stage_table(store)
        store.conn.execute("DELETE FROM _tmp_dtt_rank_stage WHERE run_id = ?", (run_id_text,))
    else:
        run_id_text = ""
    prepared_signals_by_id: dict[str, Signal] = {}
    legacy_prepared: list[Signal] = []

    for batch in _iter_candidate_batches(candidates, cfg.pas_eval_batch_size):
        batch_codes = [candidate.code for candidate in batch]
        histories = _load_candidate_histories_batch(store, batch_codes, asof_date, cfg.pas_lookback_days)
        if histories.empty:
            continue

        history_by_code = {
            str(code): frame.reset_index(drop=True)
            for code, frame in histories.groupby("code", sort=False)
        }
        batch_signals: list[Signal] = []
        for candidate in batch:
            history = history_by_code.get(candidate.code)
            if history is None or history.empty or len(history) < cfg.pas_min_history_days:
                continue
            for detector in detectors:
                signal = detector.detect(candidate.code, asof_date, history)
                if signal is not None:
                    batch_signals.append(signal)

        merged_batch = _combine_signals(batch_signals, len(detectors), cfg.pas_combination)
        if not merged_batch:
            continue

        prepared_batch = [
            signal
            if signal.bof_strength is not None
            else signal.model_copy(update={"bof_strength": float(signal.strength)})
            for signal in merged_batch
        ]

        if not cfg.use_dtt_pipeline:
            legacy_prepared.extend(prepared_batch)
            continue

        score_frame = build_dtt_score_frame(
            store=store,
            signals=prepared_batch,
            candidates=batch,
            asof_date=asof_date,
            run_id=run_id_text,
            config=cfg,
        )
        if not score_frame.empty:
            store.bulk_insert("_tmp_dtt_rank_stage", score_frame)
        for signal in prepared_batch:
            prepared_signals_by_id[signal.signal_id] = signal

    if not cfg.use_dtt_pipeline:
        if not legacy_prepared:
            return []
        # legacy 对照链继续沿用旧 formal schema，只做 BOF 输出。
        rows = pd.DataFrame([signal.to_formal_signal_row() for signal in legacy_prepared])
        store.bulk_upsert("l3_signals", rows)
        return legacy_prepared

    score_frame = store.read_df(
        """
        SELECT run_id, signal_id, signal_date, code, industry, variant,
               bof_strength, irs_score, mss_score, final_score
        FROM _tmp_dtt_rank_stage
        WHERE run_id = ?
        ORDER BY final_score DESC, signal_id ASC
        """,
        (run_id_text,),
    )
    rank_frame = finalize_dtt_rank_frame(score_frame, cfg.dtt_top_n)
    if not rank_frame.empty:
        store.bulk_upsert("l3_signal_rank_exp", rank_frame)

    selected = materialize_ranked_signals(list(prepared_signals_by_id.values()), rank_frame)
    if selected:
        rows = pd.DataFrame([signal.to_formal_signal_row() for signal in selected])
        store.bulk_upsert("l3_signals", rows)
    store.conn.execute("DELETE FROM _tmp_dtt_rank_stage WHERE run_id = ?", (run_id_text,))
    return selected
