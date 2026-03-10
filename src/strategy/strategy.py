from __future__ import annotations

import json
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


PAS_TRACE_SCHEMA_VERSION = 2
# 这些是“仍保留稳定列投影”的字段。
# 其余 detector-specific 观测统一进入 pattern_context_json，避免 trace schema 再回到 BOF-only。
PAS_TRACE_PROJECTED_PAYLOAD_KEYS = {
    "signal_id",
    "pattern",
    "triggered",
    "skip_reason",
    "detect_reason",
    "reason_code",
    "selected_pattern",
    "pattern_group",
    "registry_run_label",
    "history_days",
    "min_history_days",
    "strength",
    "bof_strength",
    "lower_bound",
    "today_low",
    "today_close",
    "today_open",
    "today_high",
    "close_pos",
    "volume",
    "volume_ma20",
    "volume_ratio",
    "cond_break",
    "cond_recover",
    "cond_close_pos",
    "cond_volume",
    "pattern_quality_score",
    "quality_breakdown_json",
    "quality_status",
    "entry_ref",
    "stop_ref",
    "target_ref",
    "risk_reward_ref",
    "failure_handling_tag",
    "reference_status",
}


def _trace_has_value(value: object) -> bool:
    if value is None:
        return False
    try:
        return not bool(pd.isna(value))
    except (TypeError, ValueError):
        return True


def _normalize_trace_json_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _normalize_trace_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize_trace_json_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "item") and not isinstance(value, (str, bytes, bytearray)):
        try:
            return _normalize_trace_json_value(value.item())
        except (TypeError, ValueError):
            pass
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return None if pd.isna(value) else float(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value if isinstance(value, str) else str(value)


def _build_trace_payload_json(payload: dict[str, object]) -> str | None:
    if not payload:
        return None
    normalized_payload = {
        str(key): _normalize_trace_json_value(value)
        for key, value in payload.items()
        if _trace_has_value(value)
    }
    if not normalized_payload:
        return None
    return json.dumps(normalized_payload, ensure_ascii=False, sort_keys=True)


def _build_pattern_context_json(payload: dict[str, object]) -> str | None:
    if not payload:
        return None
    # pattern_context_json 是 PAS trace 的 pattern-neutral 扩展位：
    # 任何没有投影成稳定列的 detector 观测，都应留在这里，而不是静默丢掉。
    context_payload = {
        str(key): _normalize_trace_json_value(value)
        for key, value in payload.items()
        if key not in PAS_TRACE_PROJECTED_PAYLOAD_KEYS and _trace_has_value(value)
    }
    if not context_payload:
        return None
    return json.dumps(context_payload, ensure_ascii=False, sort_keys=True)


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
    """
    多形态信号组合仲裁（Phase 1 核心）：
    
    三种模式：
    - ANY: 任一形态触发即通过（取最强形态）
    - ALL: 所有形态都触发才通过
    - VOTE: 超过半数形态触发才通过
    
    同股同日多形态时，按优先级选择：
    1. 强度（strength）降序
    2. 形态优先级（pattern_priority）升序
    3. signal_id 字典序（稳定排序）
    """
    if not signals:
        return []
    mode_norm = mode.upper()
    grouped: dict[tuple[str, date], list[Signal]] = {}
    for signal in signals:
        grouped.setdefault((signal.code, signal.signal_date), []).append(signal)

    merged: list[Signal] = []
    for group in grouped.values():
        # 一个 code + signal_date 最终最多只能带出一个 formal Signal；
        # 多形态竞争时先选“最值得代表这只票”的那个 pattern，再决定是否通过组合规则。
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
    # 用窗口函数一次性拉每只票最近 N 天历史，避免 detector 逐只查库造成 O(n) 往返。
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
            pattern_strength DOUBLE NOT NULL,
            irs_score    DOUBLE NOT NULL,
            mss_score    DOUBLE NOT NULL,
            final_score  DOUBLE NOT NULL
        )
        """
    )
    # 兼容长会话里已存在的旧 temp schema：至少保证新主线需要的 pattern_strength 列存在。
    for ddl in ("ALTER TABLE _tmp_dtt_rank_stage ADD COLUMN IF NOT EXISTS pattern_strength DOUBLE",):
        try:
            store.conn.execute(ddl)
        except Exception:
            pass


def _detector_name(detector: object) -> str:
    return getattr(detector, "name", detector.__class__.__name__.lower())


def _detector_min_history_days(detector: object, config: Settings) -> int:
    required_window = getattr(detector, "required_window", None)
    if required_window is not None:
        return max(1, int(required_window))
    return max(1, int(config.pas_min_history_days))


def _build_insufficient_history_trace_payload(
    code: str,
    asof_date: date,
    detector_name: str,
    registry_run_label: str,
) -> dict[str, object]:
    return {
        "signal_id": build_signal_id(code, asof_date, detector_name),
        "pattern": detector_name,
        "triggered": False,
        "skip_reason": "INSUFFICIENT_HISTORY",
        "detect_reason": "INSUFFICIENT_HISTORY",
        "reason_code": f"PAS_{detector_name.upper()}",
        "pattern_group": PATTERN_GROUP.get(detector_name, detector_name.upper()),
        "registry_run_label": registry_run_label,
    }


def _evaluate_detector(
    detector: object,
    code: str,
    asof_date: date,
    history: pd.DataFrame,
    registry_run_label: str,
) -> tuple[Signal | None, dict[str, object]]:
    detector_name = _detector_name(detector)
    evaluate = getattr(detector, "evaluate", None)
    if callable(evaluate):
        signal, trace_payload = evaluate(code, asof_date, history)
    else:
        signal = detector.detect(code, asof_date, history)
        trace_payload = {
            "signal_id": build_signal_id(code, asof_date, detector_name),
            "pattern": detector_name,
            "triggered": signal is not None,
            "skip_reason": None if signal is not None else "NOT_TRIGGERED",
            "detect_reason": None if signal is not None else "NOT_TRIGGERED",
            "reason_code": None if signal is None else signal.reason_code,
            "strength": None if signal is None else float(signal.strength),
            "pattern_strength": None if signal is None else signal.resolved_pattern_strength(),
        }

    normalized_trace_payload = dict(trace_payload)
    normalized_trace_payload.setdefault("pattern", detector_name)
    normalized_trace_payload.setdefault("pattern_group", PATTERN_GROUP.get(detector_name, detector_name.upper()))
    normalized_trace_payload.setdefault("registry_run_label", registry_run_label)
    return signal, normalized_trace_payload


def _evaluate_batch_candidates(
    store: Store,
    batch: list[StockCandidate],
    detectors: list[object],
    asof_date: date,
    config: Settings,
    run_id_text: str,
    registry_run_label: str,
    candidate_rank_map: dict[str, int],
) -> tuple[list[Signal], list[dict[str, object]], dict[tuple[str, str], dict[str, object]]]:
    batch_codes = [candidate.code for candidate in batch]
    histories = _load_candidate_histories_batch(store, batch_codes, asof_date, config.pas_lookback_days)

    # 一个 batch 只查一次历史，再按 code 切给各 detector，避免每个 pattern 重复 IO。
    history_by_code = {
        str(code): frame.reset_index(drop=True)
        for code, frame in histories.groupby("code", sort=False)
    }
    batch_signals: list[Signal] = []
    batch_trace_rows: list[dict[str, object]] = []
    trace_payload_by_key: dict[tuple[str, str], dict[str, object]] = {}
    active_detector_count = len(detectors)

    for candidate in batch:
        history = history_by_code.get(candidate.code)
        history_days = 0 if history is None or history.empty else len(history)
        for detector in detectors:
            detector_name = _detector_name(detector)
            min_history_days = _detector_min_history_days(detector, config)
            if history is None or history.empty or history_days < min_history_days:
                trace_payload = _build_insufficient_history_trace_payload(
                    candidate.code,
                    asof_date,
                    detector_name,
                    registry_run_label,
                )
                trace_payload_by_key[(candidate.code, detector_name)] = dict(trace_payload)
                if run_id_text:
                    batch_trace_rows.append(
                        _build_pas_trace_row(
                            run_id=run_id_text,
                            asof_date=asof_date,
                            code=candidate.code,
                            detector_name=detector_name,
                            candidate_rank=candidate_rank_map.get(candidate.code),
                            active_detector_count=active_detector_count,
                            combination_mode=config.pas_combination,
                            min_history_days=min_history_days,
                            history_days=history_days,
                            trace_payload=trace_payload,
                        )
                    )
                continue

            signal, trace_payload = _evaluate_detector(
                detector,
                candidate.code,
                asof_date,
                history,
                registry_run_label,
            )
            trace_payload_by_key[(candidate.code, detector_name)] = dict(trace_payload)
            if run_id_text:
                batch_trace_rows.append(
                    _build_pas_trace_row(
                        run_id=run_id_text,
                        asof_date=asof_date,
                        code=candidate.code,
                        detector_name=detector_name,
                        candidate_rank=candidate_rank_map.get(candidate.code),
                        active_detector_count=active_detector_count,
                        combination_mode=config.pas_combination,
                        min_history_days=min_history_days,
                        history_days=history_days,
                        trace_payload=trace_payload,
                    )
                )
            if signal is not None:
                batch_signals.append(signal)

    return batch_signals, batch_trace_rows, trace_payload_by_key


def _enrich_batch_trace_rows(
    batch_trace_rows: list[dict[str, object]],
    merged_batch: list[Signal],
    trace_payload_by_key: dict[tuple[str, str], dict[str, object]],
    detectors: list[object],
    asof_date: date,
    config: Settings,
    run_id_text: str,
    registry_run_label: str,
    candidate_rank_map: dict[str, int],
) -> None:
    if not batch_trace_rows:
        return

    selected_signal_map = {signal.code: signal for signal in merged_batch}
    for row in batch_trace_rows:
        selected_signal = selected_signal_map.get(str(row["code"]))
        row["selected_pattern"] = None if selected_signal is None else selected_signal.pattern
        row["pattern_group"] = row.get("pattern_group") or PATTERN_GROUP.get(str(row["pattern"]), str(row["pattern"]).upper())
        row["registry_run_label"] = row.get("registry_run_label") or registry_run_label

    min_history_by_detector = {
        _detector_name(detector): _detector_min_history_days(detector, config) for detector in detectors
    }
    active_detector_count = len(detectors)
    for signal in merged_batch:
        payload_key = (signal.code, signal.pattern)
        trace_payload = trace_payload_by_key.get(payload_key)
        if trace_payload is None:
            continue
        # quality / reference 只给最终被选中的 pattern 补，避免把“候选解释层”误当成正式触发结果。
        enriched_payload = _enrich_selected_trace_payload(trace_payload, config, registry_run_label)
        # 这里是 O(n*m) 的小循环，但 batch_size 已经被 pas_eval_batch_size 限住；
        # 当前优先保留实现直观性，而不是为了这点规模提前引入更复杂的索引结构。
        for row in batch_trace_rows:
            if str(row["code"]) == signal.code and str(row["detector"]) == signal.pattern:
                row.update(
                    _build_pas_trace_row(
                        run_id=run_id_text,
                        asof_date=asof_date,
                        code=signal.code,
                        detector_name=signal.pattern,
                        candidate_rank=candidate_rank_map.get(signal.code),
                        active_detector_count=active_detector_count,
                        combination_mode=config.pas_combination,
                        min_history_days=min_history_by_detector.get(signal.pattern, max(1, int(config.pas_min_history_days))),
                        history_days=int(enriched_payload.get("history_days") or row.get("history_days") or 0),
                        trace_payload=enriched_payload,
                    )
                )
                row["selected_pattern"] = signal.pattern
                break


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
    trace_payload_json = _build_trace_payload_json(payload)
    pattern_context_json = _build_pattern_context_json(payload)
    # 这里保持“稳定列 + 兼容字段”策略：
    # formal Signal 继续最小化，PAS 的解释层统一进入 trace 表，供回放和专项证据使用。
    # v2 起完整 detector payload 进入 trace_payload_json；legacy 列只保留可直接筛查的投影字段。
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
        "trace_schema_version": PAS_TRACE_SCHEMA_VERSION,
        "trace_payload_json": trace_payload_json,
        "pattern_context_json": pattern_context_json,
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
            # reference 层只补解释位，不直接驱动 Broker 的执行价格/止损。
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
                # quality 分数当前也只服务于 sidecar / evidence，不进入 formal Signal。
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
    """
    信号生成主流程（Phase 1 完整链路）：
    
    流程：
    1. 加载活跃 detector（根据 pas_patterns 配置）
    2. 批量加载候选股历史数据（batch_size 控制内存）
    3. 逐股逐形态调用 detector.evaluate，收集 signal + trace
    4. 多形态组合仲裁（ANY/ALL/VOTE）
    5. 选中形态补充 quality/reference sidecar（如果启用）
    6. DTT 主线：写入 _tmp_dtt_rank_stage，最终排序后取 top_n
    7. Legacy 主线：直接写入 l3_signals
    8. 所有 trace 写入 pas_trigger_trace_exp
    
    关键约束：
    - DTT 主线必须提供 run_id
    - 批量加载避免单股查询性能瓶颈
    - trace 记录触发与未触发候选，便于后续分析
    """
    cfg = config or get_settings()
    detectors = get_active_detectors(cfg)
    if not detectors or not candidates:
        return []

    detector_names = [_detector_name(detector) for detector in detectors]
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
        batch_signals, batch_trace_rows, trace_payload_by_key = _evaluate_batch_candidates(
            store=store,
            batch=batch,
            detectors=detectors,
            asof_date=asof_date,
            config=cfg,
            run_id_text=run_id_text,
            registry_run_label=registry_run_label,
            candidate_rank_map=candidate_rank_map,
        )

        merged_batch = _combine_signals(
            batch_signals,
            len(detectors),
            cfg.pas_combination,
            cfg.pas_pattern_priority_list,
        )
        if batch_trace_rows:
            _enrich_batch_trace_rows(
                batch_trace_rows=batch_trace_rows,
                merged_batch=merged_batch,
                trace_payload_by_key=trace_payload_by_key,
                detectors=detectors,
                asof_date=asof_date,
                config=cfg,
                run_id_text=run_id_text,
                registry_run_label=registry_run_label,
                candidate_rank_map=candidate_rank_map,
            )
            pas_trace_rows.extend(batch_trace_rows)
        if not merged_batch:
            continue

        prepared_batch = [
            signal
            if signal.pattern_strength is not None
            else signal.model_copy(
                update={
                    "pattern_strength": signal.resolved_pattern_strength(),
                }
            )
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
            # DTT staging 先把 batch 层打分结果落进临时表，最后再统一做全量 final_rank。
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
               pattern_strength, irs_score, mss_score, final_score
        FROM _tmp_dtt_rank_stage
        WHERE run_id = ?
        ORDER BY final_score DESC, signal_id ASC
        """,
        (run_id_text,),
    )
    rank_frame = finalize_dtt_rank_frame(score_frame, cfg.dtt_top_n)
    if not rank_frame.empty:
        store.bulk_upsert("l3_signal_rank_exp", rank_frame)

    # formal l3_signals 只落最终入选的 signal；排序真相源继续留在 l3_signal_rank_exp。
    selected = materialize_ranked_signals(list(prepared_signals_by_id.values()), rank_frame)
    if selected:
        rows = pd.DataFrame([signal.to_formal_signal_row() for signal in selected])
        store.bulk_upsert("l3_signals", rows)
    # staging temp table 按 run_id 清理，避免长会话里不同 run 的 batch 排序结果互相污染。
    store.conn.execute("DELETE FROM _tmp_dtt_rank_stage WHERE run_id = ?", (run_id_text,))
    return selected
