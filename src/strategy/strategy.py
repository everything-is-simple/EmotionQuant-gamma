from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings, get_settings
from src.contracts import Signal, StockCandidate, build_signal_id
from src.data.store import Store
from src.strategy.pas_sidecar import (
    PATTERN_GROUP,
    build_registry_run_label,
    compute_pattern_quality,
    compute_reference_layer,
)
from src.strategy.ranker import (
    build_dtt_score_frame,
    finalize_dtt_rank_frame,
    materialize_ranked_signals,
)
from src.strategy.registry import get_active_detectors


def _pattern_priority_rank(pattern: str, pattern_priority: list[str] | None = None) -> int:
    priorities = pattern_priority or ["bpb", "pb", "tst", "cpb", "bof"]
    try:
        return priorities.index(pattern)
    except ValueError:
        return len(priorities)


def _select_preferred_signal(group: list[Signal], pattern_priority: list[str] | None = None) -> Signal:
    return max(
        group,
        key=lambda signal: (
            float(signal.strength),
            -_pattern_priority_rank(signal.pattern, pattern_priority),
            signal.signal_id,
        ),
    )


def _combine_signals(
    signals: list[Signal],
    active_detector_count: int,
    mode: str = "ANY",
    pattern_priority: list[str] | None = None,
) -> list[Signal]:
    if not signals:
        return []
    mode_norm = mode.upper()
    grouped: dict[tuple[str, date], list[Signal]] = {}
    for signal in signals:
        grouped.setdefault((signal.code, signal.signal_date), []).append(signal)

    merged: list[Signal] = []
    for group in grouped.values():
        best = _select_preferred_signal(group, pattern_priority)
        unique_patterns = {signal.pattern for signal in group}
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


def _build_pas_trace_row(
    run_id: str,
    asof_date: date,
    code: str,
    detector_name: str,
    candidate_rank: int | None,
    active_detector_count: int,
    combination_mode: str,
    min_history_days: int,
    history_days: int,
    trace_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = trace_payload or {}
    signal_id = str(payload.get("signal_id") or build_signal_id(code, asof_date, detector_name))
    strength = payload.get("strength")
    bof_strength = payload.get("bof_strength")
    triggered = bool(payload.get("triggered", False))
    detect_reason = payload.get("detect_reason") or payload.get("skip_reason")
    return {
        "run_id": run_id,
        "signal_date": asof_date,
        "code": code,
        "detector": detector_name,
        "signal_id": signal_id,
        "pattern": str(payload.get("pattern") or detector_name),
        "candidate_rank": None if candidate_rank is None else int(candidate_rank),
        "selected_pattern": payload.get("selected_pattern"),
        "active_detector_count": int(active_detector_count),
        "combination_mode": combination_mode.upper(),
        "history_days": int(history_days),
        "min_history_days": int(min_history_days),
        "triggered": triggered,
        "detected": triggered,
        "skip_reason": payload.get("skip_reason"),
        "detect_reason": detect_reason,
        "reason_code": payload.get("reason_code"),
        "strength": None if strength is None else float(strength),
        "pattern_strength": None if strength is None else float(strength),
        "bof_strength": None if bof_strength is None else float(bof_strength),
        "lower_bound": payload.get("lower_bound"),
        "today_low": payload.get("today_low"),
        "today_close": payload.get("today_close"),
        "today_open": payload.get("today_open"),
        "today_high": payload.get("today_high"),
        "close_pos": payload.get("close_pos"),
        "volume": payload.get("volume"),
        "volume_ma20": payload.get("volume_ma20"),
        "volume_ratio": payload.get("volume_ratio"),
        "cond_break": payload.get("cond_break"),
        "cond_recover": payload.get("cond_recover"),
        "cond_close_pos": payload.get("cond_close_pos"),
        "cond_volume": payload.get("cond_volume"),
        "pattern_quality_score": payload.get("pattern_quality_score"),
        "quality_breakdown_json": payload.get("quality_breakdown_json"),
        "quality_status": payload.get("quality_status"),
        "entry_ref": payload.get("entry_ref"),
        "stop_ref": payload.get("stop_ref"),
        "target_ref": payload.get("target_ref"),
        "risk_reward_ref": payload.get("risk_reward_ref"),
        "failure_handling_tag": payload.get("failure_handling_tag"),
        "pattern_group": payload.get("pattern_group"),
        "registry_run_label": payload.get("registry_run_label"),
        "reference_status": payload.get("reference_status"),
    }


def _enrich_selected_trace_payload(
    payload: dict[str, object],
    config: Settings,
    registry_run_label: str,
) -> dict[str, object]:
    enriched = dict(payload)
    pattern = str(enriched.get("pattern") or "")
    enriched["pattern_group"] = PATTERN_GROUP.get(pattern, pattern.upper())
    enriched["registry_run_label"] = registry_run_label

    reference: dict[str, object] | None = None
    if config.pas_reference_enabled:
        try:
            reference = compute_reference_layer(pattern, enriched)
            enriched.update(reference)
            enriched["reference_status"] = "OK"
        except Exception:
            enriched["reference_status"] = "ERROR"
    else:
        enriched["reference_status"] = "DISABLED"

    if config.pas_quality_enabled:
        if reference is not None:
            try:
                enriched.update(compute_pattern_quality(pattern, enriched, reference, config))
                enriched["quality_status"] = "OK"
            except Exception:
                enriched["quality_status"] = "ERROR"
        else:
            enriched["quality_status"] = "REFERENCE_UNAVAILABLE"
    else:
        enriched["quality_status"] = "DISABLED"

    return enriched


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

    detector_names = [getattr(detector, "name", detector.__class__.__name__.lower()) for detector in detectors]
    registry_run_label = build_registry_run_label(detector_names, cfg.pas_combination, cfg.pas_quality_enabled)
    run_id_text = (run_id or "").strip()
    if cfg.use_dtt_pipeline:
        if not run_id_text:
            raise ValueError("DTT pipeline requires run_id for l3_signal_rank_exp traceability.")
        _ensure_dtt_stage_table(store)
        store.conn.execute("DELETE FROM _tmp_dtt_rank_stage WHERE run_id = ?", (run_id_text,))
    candidate_rank_map = {
        candidate.code: int(candidate.candidate_rank) if candidate.candidate_rank is not None else index
        for index, candidate in enumerate(candidates, start=1)
    }
    prepared_signals_by_id: dict[str, Signal] = {}
    legacy_prepared: list[Signal] = []
    pas_trace_rows: list[dict[str, object]] = []

    for batch in _iter_candidate_batches(candidates, cfg.pas_eval_batch_size):
        batch_codes = [candidate.code for candidate in batch]
        histories = _load_candidate_histories_batch(store, batch_codes, asof_date, cfg.pas_lookback_days)

        history_by_code = {
            str(code): frame.reset_index(drop=True)
            for code, frame in histories.groupby("code", sort=False)
        }
        batch_signals: list[Signal] = []
        batch_trace_rows: list[dict[str, object]] = []
        trace_payload_by_key: dict[tuple[str, str], dict[str, object]] = {}
        for candidate in batch:
            history = history_by_code.get(candidate.code)
            for detector in detectors:
                detector_name = getattr(detector, "name", detector.__class__.__name__.lower())
                history_days = 0 if history is None or history.empty else len(history)
                if history is None or history.empty or history_days < cfg.pas_min_history_days:
                    if run_id_text:
                        trace_payload = {
                            "signal_id": build_signal_id(candidate.code, asof_date, detector_name),
                            "pattern": detector_name,
                            "triggered": False,
                            "skip_reason": "INSUFFICIENT_HISTORY",
                            "detect_reason": "INSUFFICIENT_HISTORY",
                            "reason_code": f"PAS_{detector_name.upper()}",
                            "pattern_group": PATTERN_GROUP.get(detector_name, detector_name.upper()),
                            "registry_run_label": registry_run_label,
                        }
                        trace_payload_by_key[(candidate.code, detector_name)] = dict(trace_payload)
                        batch_trace_rows.append(
                            _build_pas_trace_row(
                                run_id=run_id_text,
                                asof_date=asof_date,
                                code=candidate.code,
                                detector_name=detector_name,
                                candidate_rank=candidate_rank_map.get(candidate.code),
                                active_detector_count=len(detectors),
                                combination_mode=cfg.pas_combination,
                                min_history_days=cfg.pas_min_history_days,
                                history_days=history_days,
                                trace_payload=trace_payload,
                            )
                        )
                    continue

                evaluate = getattr(detector, "evaluate", None)
                if callable(evaluate):
                    signal, trace_payload = evaluate(candidate.code, asof_date, history)
                else:
                    signal = detector.detect(candidate.code, asof_date, history)
                    trace_payload = {
                        "signal_id": build_signal_id(candidate.code, asof_date, detector_name),
                        "pattern": detector_name,
                        "triggered": signal is not None,
                        "skip_reason": None if signal is not None else "NOT_TRIGGERED",
                        "detect_reason": None if signal is not None else "NOT_TRIGGERED",
                        "reason_code": None if signal is None else signal.reason_code,
                        "strength": None if signal is None else float(signal.strength),
                        "bof_strength": None
                        if signal is None or signal.bof_strength is None
                        else float(signal.bof_strength),
                    }

                trace_payload = dict(trace_payload)
                trace_payload.setdefault("pattern", detector_name)
                trace_payload.setdefault("pattern_group", PATTERN_GROUP.get(detector_name, detector_name.upper()))
                trace_payload.setdefault("registry_run_label", registry_run_label)
                trace_payload_by_key[(candidate.code, detector_name)] = dict(trace_payload)

                if run_id_text:
                    batch_trace_rows.append(
                        _build_pas_trace_row(
                            run_id=run_id_text,
                            asof_date=asof_date,
                            code=candidate.code,
                            detector_name=detector_name,
                            candidate_rank=candidate_rank_map.get(candidate.code),
                            active_detector_count=len(detectors),
                            combination_mode=cfg.pas_combination,
                            min_history_days=cfg.pas_min_history_days,
                            history_days=history_days,
                            trace_payload=trace_payload,
                        )
                    )
                if signal is not None:
                    batch_signals.append(signal)

        merged_batch = _combine_signals(
            batch_signals,
            len(detectors),
            cfg.pas_combination,
            cfg.pas_pattern_priority_list,
        )
        if batch_trace_rows:
            selected_signal_map = {signal.code: signal for signal in merged_batch}
            for row in batch_trace_rows:
                selected_signal = selected_signal_map.get(str(row["code"]))
                row["selected_pattern"] = None if selected_signal is None else selected_signal.pattern
                row["pattern_group"] = row.get("pattern_group") or PATTERN_GROUP.get(str(row["pattern"]), str(row["pattern"]).upper())
                row["registry_run_label"] = row.get("registry_run_label") or registry_run_label

            for signal in merged_batch:
                payload_key = (signal.code, signal.pattern)
                trace_payload = trace_payload_by_key.get(payload_key)
                if trace_payload is None:
                    continue
                enriched_payload = _enrich_selected_trace_payload(trace_payload, cfg, registry_run_label)
                for row in batch_trace_rows:
                    if str(row["code"]) == signal.code and str(row["detector"]) == signal.pattern:
                        row.update(_build_pas_trace_row(
                            run_id=run_id_text,
                            asof_date=asof_date,
                            code=signal.code,
                            detector_name=signal.pattern,
                            candidate_rank=candidate_rank_map.get(signal.code),
                            active_detector_count=len(detectors),
                            combination_mode=cfg.pas_combination,
                            min_history_days=cfg.pas_min_history_days,
                            history_days=int(enriched_payload.get("history_days") or 0),
                            trace_payload=enriched_payload,
                        ))
                        row["selected_pattern"] = signal.pattern
                        break
            pas_trace_rows.extend(batch_trace_rows)
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

    if run_id_text and pas_trace_rows:
        store.bulk_upsert("pas_trigger_trace_exp", pd.DataFrame(pas_trace_rows))

    if not cfg.use_dtt_pipeline:
        if not legacy_prepared:
            return []
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

