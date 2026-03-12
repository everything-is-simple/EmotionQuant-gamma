from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import duckdb


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _find_result(matrix_payload: dict[str, object], label: str) -> dict[str, object]:
    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise KeyError(f"Matrix payload missing results for {label}")
    for item in results:
        if isinstance(item, dict) and str(item.get("label") or "") == label:
            return item
    raise KeyError(f"Unable to find result for {label}")


def _resolve_sb_run_id(matrix_payload: dict[str, object]) -> str:
    sb_result = _find_result(matrix_payload, "SB")
    run_id = str(sb_result.get("run_id") or "").strip()
    if not run_id:
        raise KeyError("SB result missing run_id")
    return run_id


def _normalize_scalar(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds") + "Z"
    if isinstance(value, date):
        return value.isoformat()
    return value


def _query_dicts(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    params: list[object] | tuple[object, ...],
) -> list[dict[str, object]]:
    cursor = connection.execute(query, params)
    columns = [str(item[0]) for item in (cursor.description or ())]
    rows: list[dict[str, object]] = []
    for values in cursor.fetchall():
        row = {columns[index]: _normalize_scalar(values[index]) for index in range(len(columns))}
        rows.append(row)
    return rows


def _normalize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        clean: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, float):
                clean[key] = float(value)
            elif isinstance(value, int):
                clean[key] = int(value)
            else:
                clean[key] = value
        normalized.append(clean)
    return normalized


def _maybe_open_snapshot_db(db_path: str | Path | None) -> tuple[duckdb.DuckDBPyConnection | None, Path | None]:
    if db_path is None:
        return None, None
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return None, path
    return duckdb.connect(str(path), read_only=True), path


SB_PAIRED_TRACE_CTE = """
WITH selected_entries AS (
    SELECT
        signal_id,
        signal_date,
        code,
        CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) AS trend_gain,
        CAST(json_extract_string(trace_payload_json, '$.retest_similarity') AS DOUBLE) AS retest_similarity,
        CAST(json_extract_string(trace_payload_json, '$.w_amplitude') AS DOUBLE) AS w_amplitude,
        CAST(json_extract_string(trace_payload_json, '$.volume_ratio') AS DOUBLE) AS volume_ratio,
        CAST(pattern_strength AS DOUBLE) AS pattern_strength
    FROM pas_trigger_trace_exp
    WHERE run_id = ?
      AND detected = TRUE
      AND selected_pattern = detector
),
buyfills AS (
    SELECT
        signal_id,
        code,
        execute_date AS entry_date,
        quantity AS entry_qty,
        price AS entry_price,
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY execute_date, COALESCE(trade_id, order_id)) AS buy_seq
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND action = 'BUY'
      AND event_stage = 'MATCH_FILLED'
),
executed_entries AS (
    SELECT
        e.signal_id,
        e.signal_date,
        e.code,
        e.trend_gain,
        e.retest_similarity,
        e.w_amplitude,
        e.volume_ratio,
        e.pattern_strength,
        b.entry_date,
        b.entry_qty,
        b.entry_price,
        b.buy_seq
    FROM selected_entries e
    JOIN buyfills b
      ON e.signal_id = b.signal_id
     AND e.code = b.code
),
exits AS (
    SELECT
        code,
        execute_date AS exit_date,
        quantity AS exit_qty,
        price AS exit_price,
        event_stage AS exit_stage,
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY execute_date, COALESCE(trade_id, order_id)) AS exit_seq
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND action = 'SELL'
      AND event_stage IN ('MATCH_FILLED', 'FORCE_CLOSE_FILLED')
),
paired AS (
    SELECT
        e.signal_id,
        e.signal_date,
        e.code,
        e.trend_gain,
        e.retest_similarity,
        e.w_amplitude,
        e.volume_ratio,
        e.pattern_strength,
        e.entry_date,
        e.entry_qty,
        e.entry_price,
        e.buy_seq,
        x.exit_date,
        x.exit_qty,
        x.exit_price,
        x.exit_stage,
        (x.exit_price - e.entry_price) / NULLIF(e.entry_price, 0) AS gross_return
    FROM executed_entries e
    JOIN exits x
      ON e.code = x.code
     AND e.buy_seq = x.exit_seq
     AND e.entry_qty = x.exit_qty
)
"""


PAIRING_DIAGNOSTICS_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    (SELECT COUNT(*) FROM selected_entries) AS selected_entry_count,
    (SELECT COUNT(*) FROM buyfills) AS buy_fill_count,
    (SELECT COUNT(*) FROM executed_entries) AS executed_entry_count,
    (SELECT COUNT(*) FROM exits) AS exit_fill_count,
    COUNT(*) AS paired_trade_count
FROM paired
"""
)


SIGNAL_YEAR_SLICES_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    CAST(EXTRACT(YEAR FROM signal_date) AS INTEGER) AS signal_year,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


SELECTED_TRACE_SUMMARY_QUERY = """
SELECT
    COUNT(*) AS selected_count,
    AVG(CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE)) AS avg_trend_gain,
    AVG(CAST(json_extract_string(trace_payload_json, '$.retest_similarity') AS DOUBLE)) AS avg_retest_similarity,
    AVG(CAST(json_extract_string(trace_payload_json, '$.w_amplitude') AS DOUBLE)) AS avg_w_amplitude,
    AVG(CAST(json_extract_string(trace_payload_json, '$.volume_ratio') AS DOUBLE)) AS avg_volume_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.retest_similarity') AS DOUBLE) <= 0.02
            THEN 1.0
            ELSE 0.0
        END
    ) AS tight_retest_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.w_amplitude') AS DOUBLE) < 0.08
            THEN 1.0
            ELSE 0.0
        END
    ) AS small_w_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.w_amplitude') AS DOUBLE) >= 0.12
            THEN 1.0
            ELSE 0.0
        END
    ) AS large_w_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) < 0.15
            THEN 1.0
            ELSE 0.0
        END
    ) AS low_trend_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) >= 0.25
            THEN 1.0
            ELSE 0.0
        END
    ) AS high_trend_ratio,
    AVG(
        CASE
            WHEN CAST(pattern_strength AS DOUBLE) >= 0.75
             AND CAST(pattern_strength AS DOUBLE) < 0.90
            THEN 1.0
            ELSE 0.0
        END
    ) AS mid_strength_ratio,
    MIN(CAST(pattern_strength AS DOUBLE)) AS min_strength,
    AVG(CAST(pattern_strength AS DOUBLE)) AS avg_strength,
    MAX(CAST(pattern_strength AS DOUBLE)) AS max_strength
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
"""


FAILURE_REASON_QUERY = """
SELECT
    reason,
    cnt AS count,
    cnt * 1.0 / SUM(cnt) OVER () AS share
FROM (
    SELECT
        COALESCE(skip_reason, detect_reason, 'NONE') AS reason,
        COUNT(*) AS cnt
    FROM pas_trigger_trace_exp
    WHERE run_id = ?
      AND NOT (detected = TRUE AND selected_pattern = detector)
    GROUP BY 1
)
ORDER BY count DESC, reason ASC
LIMIT 8
"""


STRENGTH_BUCKET_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN pattern_strength < 0.75 THEN 'low_strength'
        WHEN pattern_strength < 0.90 THEN 'mid_strength'
        ELSE 'high_strength'
    END AS strength_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


RETEST_BUCKET_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN retest_similarity <= 0.02 THEN 'tight_retest'
        ELSE 'mid_retest'
    END AS retest_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


TREND_BUCKET_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN trend_gain < 0.15 THEN 'low_trend'
        WHEN trend_gain < 0.25 THEN 'mid_trend'
        ELSE 'high_trend'
    END AS trend_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


W_BUCKET_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN w_amplitude < 0.08 THEN 'small_w'
        WHEN w_amplitude < 0.12 THEN 'medium_w'
        ELSE 'large_w'
    END AS w_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


BRANCH_CANDIDATE_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    branch_label,
    trade_count,
    avg_gross_return,
    win_rate,
    avg_strength
FROM (
    SELECT
        'SB_SMALL_W' AS branch_label,
        COUNT(*) AS trade_count,
        AVG(gross_return) AS avg_gross_return,
        SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
        AVG(pattern_strength) AS avg_strength
    FROM paired
    WHERE w_amplitude < 0.08
    UNION ALL
    SELECT
        'SB_SMALL_W_MID_STRENGTH' AS branch_label,
        COUNT(*) AS trade_count,
        AVG(gross_return) AS avg_gross_return,
        SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
        AVG(pattern_strength) AS avg_strength
    FROM paired
    WHERE w_amplitude < 0.08
      AND pattern_strength >= 0.75
      AND pattern_strength < 0.90
    UNION ALL
    SELECT
        'SB_LOW_TREND_MID_STRENGTH' AS branch_label,
        COUNT(*) AS trade_count,
        AVG(gross_return) AS avg_gross_return,
        SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
        AVG(pattern_strength) AS avg_strength
    FROM paired
    WHERE trend_gain < 0.15
      AND pattern_strength >= 0.75
      AND pattern_strength < 0.90
    UNION ALL
    SELECT
        'SB_SMALL_W_MID_PLUS_TREND' AS branch_label,
        COUNT(*) AS trade_count,
        AVG(gross_return) AS avg_gross_return,
        SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
        AVG(pattern_strength) AS avg_strength
    FROM paired
    WHERE w_amplitude < 0.08
      AND trend_gain < 0.25
)
WHERE trade_count > 0
ORDER BY avg_gross_return DESC, trade_count DESC, branch_label ASC
"""
)


NEGATIVE_EXAMPLES_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    signal_date,
    code,
    entry_date,
    exit_date,
    gross_return,
    trend_gain,
    retest_similarity,
    w_amplitude,
    pattern_strength
FROM paired
WHERE gross_return < 0
ORDER BY gross_return ASC, signal_date ASC
LIMIT 8
"""
)


POSITIVE_EXAMPLES_QUERY = (
    SB_PAIRED_TRACE_CTE
    + """
SELECT
    signal_date,
    code,
    entry_date,
    exit_date,
    gross_return,
    trend_gain,
    retest_similarity,
    w_amplitude,
    pattern_strength
FROM paired
ORDER BY gross_return DESC, signal_date ASC
LIMIT 8
"""
)


def collect_normandy_sb_refinement_snapshot(
    matrix_payload: dict[str, object],
    db_path: str | Path | None,
) -> dict[str, object]:
    run_id = _resolve_sb_run_id(matrix_payload)
    connection, resolved_path = _maybe_open_snapshot_db(db_path)
    if connection is None:
        return {
            "snapshot_status": "missing",
            "snapshot_db_path": str(resolved_path) if resolved_path else None,
            "sb_run_id": run_id,
            "pairing_diagnostics": {},
            "signal_year_slices": [],
            "selected_trace_summary": {},
            "failure_reason_breakdown": [],
            "performance_by_strength_bucket": [],
            "performance_by_retest_bucket": [],
            "performance_by_trend_bucket": [],
            "performance_by_w_bucket": [],
            "branch_candidates": [],
            "positive_examples": [],
            "negative_examples": [],
        }

    try:
        params = [run_id, run_id, run_id]
        diagnostics = _query_dicts(connection, PAIRING_DIAGNOSTICS_QUERY, params)
        signal_year_slices = _query_dicts(connection, SIGNAL_YEAR_SLICES_QUERY, params)
        selected_trace_summary = _query_dicts(connection, SELECTED_TRACE_SUMMARY_QUERY, [run_id])
        failure_reason_breakdown = _query_dicts(connection, FAILURE_REASON_QUERY, [run_id])
        strength_buckets = _query_dicts(connection, STRENGTH_BUCKET_QUERY, params)
        retest_buckets = _query_dicts(connection, RETEST_BUCKET_QUERY, params)
        trend_buckets = _query_dicts(connection, TREND_BUCKET_QUERY, params)
        w_buckets = _query_dicts(connection, W_BUCKET_QUERY, params)
        branch_candidates = _query_dicts(connection, BRANCH_CANDIDATE_QUERY, params)
        positive_examples = _query_dicts(connection, POSITIVE_EXAMPLES_QUERY, params)
        negative_examples = _query_dicts(connection, NEGATIVE_EXAMPLES_QUERY, params)
    finally:
        connection.close()

    return {
        "snapshot_status": "available",
        "snapshot_db_path": str(resolved_path),
        "sb_run_id": run_id,
        "pairing_diagnostics": diagnostics[0] if diagnostics else {},
        "signal_year_slices": _normalize_rows(signal_year_slices),
        "selected_trace_summary": selected_trace_summary[0] if selected_trace_summary else {},
        "failure_reason_breakdown": _normalize_rows(failure_reason_breakdown),
        "performance_by_strength_bucket": _normalize_rows(strength_buckets),
        "performance_by_retest_bucket": _normalize_rows(retest_buckets),
        "performance_by_trend_bucket": _normalize_rows(trend_buckets),
        "performance_by_w_bucket": _normalize_rows(w_buckets),
        "branch_candidates": _normalize_rows(branch_candidates),
        "positive_examples": _normalize_rows(positive_examples),
        "negative_examples": _normalize_rows(negative_examples),
    }


def _dominant_environment_bucket(
    environment_breakdown: object,
    trade_count: int,
) -> dict[str, object] | None:
    if not isinstance(environment_breakdown, dict):
        return None
    best_bucket: str | None = None
    best_metrics: dict[str, object] | None = None
    best_count = -1.0
    for bucket, metrics in environment_breakdown.items():
        if not isinstance(metrics, dict):
            continue
        bucket_count = _float_or_none(metrics.get("trade_count"))
        if bucket_count is None or bucket_count <= best_count:
            continue
        best_count = bucket_count
        best_bucket = str(bucket)
        best_metrics = metrics
    if best_bucket is None or best_metrics is None:
        return None
    share = None
    if trade_count > 0:
        share = best_count / trade_count
    return {
        "bucket": best_bucket,
        "trade_count": int(best_count),
        "expected_value": _float_or_none(best_metrics.get("expected_value")),
        "profit_factor": _float_or_none(best_metrics.get("profit_factor")),
        "share_of_trades": share,
    }


def _with_branch_notes(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    notes = {
        "SB_SMALL_W": "只保留较窄 W 振幅，测试是否来自更干净的二次失败结构。",
        "SB_SMALL_W_MID_STRENGTH": "同时要求窄 W 与中等强度，回避当前高强度但失真的样本。",
        "SB_LOW_TREND_MID_STRENGTH": "同时约束低趋势增益与中等强度，测试是否需要放弃过强趋势背景。",
        "SB_SMALL_W_MID_PLUS_TREND": "窄 W + 非高趋势的宽松分支，作为过渡型观察口径。",
    }
    enriched: list[dict[str, object]] = []
    for row in rows:
        enriched.append(
            {
                **row,
                "branch_notes": notes.get(str(row.get("branch_label") or ""), "SB coarse candidate branch."),
            }
        )
    return enriched


def build_normandy_sb_refinement_report(
    matrix_payload: dict[str, object],
    snapshot_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = snapshot_payload or {}
    sb_result = _find_result(matrix_payload, "SB")
    bof_result = _find_result(matrix_payload, "BOF_CONTROL")

    trade_count = _int_or_zero(sb_result.get("trade_count"))
    expected_value = _float_or_none(sb_result.get("expected_value"))
    max_drawdown = _float_or_none(sb_result.get("max_drawdown"))
    best_environment_bucket = (
        sb_result.get("best_environment_bucket")
        if isinstance(sb_result.get("best_environment_bucket"), dict)
        else {}
    )
    best_environment_share = None
    best_environment_trade_count = _float_or_none(best_environment_bucket.get("trade_count"))
    if trade_count > 0 and best_environment_trade_count is not None:
        best_environment_share = best_environment_trade_count / trade_count

    signal_year_slices = [row for row in snapshot.get("signal_year_slices", []) if isinstance(row, dict)]
    branch_candidates = [
        row for row in snapshot.get("branch_candidates", []) if isinstance(row, dict)
    ]
    enriched_branch_candidates = _with_branch_notes(branch_candidates)
    selected_trace_summary = (
        snapshot.get("selected_trace_summary")
        if isinstance(snapshot.get("selected_trace_summary"), dict)
        else {}
    )
    pairing_diagnostics = (
        snapshot.get("pairing_diagnostics")
        if isinstance(snapshot.get("pairing_diagnostics"), dict)
        else {}
    )
    positive_examples = [
        row for row in snapshot.get("positive_examples", []) if isinstance(row, dict)
    ]
    negative_examples = [
        row for row in snapshot.get("negative_examples", []) if isinstance(row, dict)
    ]

    meaningful_negative_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if _int_or_zero(row.get("trade_count")) >= 20
        and _float_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) < 0
    ]
    meaningful_positive_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if _int_or_zero(row.get("trade_count")) >= 20
        and _float_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) > 0
    ]

    retained_watch_branches = [
        row
        for row in enriched_branch_candidates
        if _int_or_zero(row.get("trade_count")) >= 50
        and (_float_or_none(row.get("avg_gross_return")) or 0.0) > 0.015
    ]
    retained_watch_branches.sort(
        key=lambda row: (
            -(_float_or_none(row.get("avg_gross_return")) or -999.0),
            -_int_or_zero(row.get("trade_count")),
            str(row.get("branch_label") or ""),
        )
    )
    retained_watch_branch = retained_watch_branches[0] if retained_watch_branches else None

    selected_entry_count = _int_or_zero(pairing_diagnostics.get("selected_entry_count"))
    executed_entry_count = _int_or_zero(pairing_diagnostics.get("executed_entry_count"))
    selected_to_fill_ratio = None
    if executed_entry_count > 0:
        selected_to_fill_ratio = selected_entry_count / executed_entry_count

    refinement_flags: list[str] = []
    if expected_value is not None and expected_value < 0:
        refinement_flags.append("negative_full_detector_edge")
    if max_drawdown is not None and max_drawdown >= 0.30:
        refinement_flags.append("extreme_drawdown_profile")
    if meaningful_negative_years:
        refinement_flags.append("multi_year_negative_signal_slices")
    if best_environment_share is not None and best_environment_share < 0.10:
        refinement_flags.append("positive_environment_too_small")
    if selected_to_fill_ratio is not None and selected_to_fill_ratio >= 4.0:
        refinement_flags.append("detector_overwide_vs_execution")
    if retained_watch_branch is not None:
        refinement_flags.append("narrow_positive_watch_branch_only")

    dominant_environment = _dominant_environment_bucket(
        sb_result.get("environment_breakdown"),
        trade_count,
    )
    snapshot_status = str(snapshot.get("snapshot_status") or "missing")

    if snapshot_status != "available":
        refinement_status = "snapshot_missing"
        refinement_verdict = "snapshot_missing"
        decision = "snapshot_recovery_needed"
        conclusion = "N1.10 缺少 SB 快照库，当前只能复述 N1.5 的负向结论，无法完成 refinement / no-go formal readout。"
        next_main_queue_card = None
    elif expected_value is not None and expected_value < 0:
        if retained_watch_branch is not None:
            refinement_status = "full_detector_no_go_watch_branch_only"
            refinement_verdict = "current_sb_detector_no_go_narrow_watch_branch_only"
            decision = "freeze_full_sb_and_shift_main_queue"
            conclusion = (
                "SB 当前 full detector 路线已经可以判为 no-go：长窗 EV 仍为负、MDD 明显过大，"
                f"且负 signal-year 切片横跨 {', '.join(str(year) for year in meaningful_negative_years) or '多个年度'}。"
                f"当前只观察到一个值得保留的窄 watch branch：{retained_watch_branch['branch_label']}，"
                "它可以进入 backlog，但不足以继续占用 Normandy 主队列。"
            )
        else:
            refinement_status = "full_detector_no_go"
            refinement_verdict = "current_sb_detector_no_go"
            decision = "close_sb_route_and_shift_main_queue"
            conclusion = (
                "SB 当前 full detector 路线已经可以判为 no-go：长窗 EV 为负、MDD 过大，"
                "且未观察到达到留队门槛的窄正向分支。"
            )
        next_main_queue_card = "N1.11 / BOF pinbar quality provenance"
    else:
        refinement_status = "retained_for_further_refinement"
        refinement_verdict = "current_sb_detector_retained"
        decision = "continue_sb_refinement"
        conclusion = "SB 当前仍保留继续 refinement 的资格，但仍需先把 detector 收缩成更窄分支。"
        next_main_queue_card = "SB micro-refinement follow-up"

    next_actions = (
        [
            "冻结当前 full SB detector，不再把它当作独立第二 alpha 候选继续推进。",
            "仅保留最强窄分支为 watch/backlog 候选，等待未来单独 micro-contract 卡。",
            "Normandy 主队列切到 BOF pinbar quality provenance。",
        ]
        if decision in {"freeze_full_sb_and_shift_main_queue", "close_sb_route_and_shift_main_queue"}
        else [
            "先把 SB 收缩为更窄 detector，再决定是否需要新的长窗 matrix。",
            "继续保持 BOF_CONTROL 为统一 baseline。",
        ]
    )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "snapshot_status": snapshot_status,
        "snapshot_db_path": snapshot.get("snapshot_db_path"),
        "sb_run_id": snapshot.get("sb_run_id") or sb_result.get("run_id"),
        "candidate_label": "SB",
        "control_label": "BOF_CONTROL",
        "pairing_method": "buy_fill_sequence_to_exit_sequence",
        "candidate_summary": {
            "trade_count": trade_count,
            "expected_value": expected_value,
            "profit_factor": _float_or_none(sb_result.get("profit_factor")),
            "max_drawdown": max_drawdown,
            "participation_rate": _float_or_none(sb_result.get("participation_rate")),
            "overlap_rate_vs_bof_control": _float_or_none(sb_result.get("overlap_rate_vs_bof_control")),
            "incremental_buy_trades_vs_bof_control": _int_or_zero(
                sb_result.get("incremental_buy_trades_vs_bof_control")
            ),
        },
        "control_summary": {
            "trade_count": _int_or_zero(bof_result.get("trade_count")),
            "expected_value": _float_or_none(bof_result.get("expected_value")),
            "profit_factor": _float_or_none(bof_result.get("profit_factor")),
            "max_drawdown": _float_or_none(bof_result.get("max_drawdown")),
            "participation_rate": _float_or_none(bof_result.get("participation_rate")),
        },
        "best_environment_bucket": best_environment_bucket,
        "best_environment_share": best_environment_share,
        "dominant_environment_bucket": dominant_environment,
        "environment_breakdown": sb_result.get("environment_breakdown", {}),
        "pairing_diagnostics": pairing_diagnostics,
        "signal_year_slices": signal_year_slices,
        "meaningful_negative_signal_years": meaningful_negative_years,
        "meaningful_positive_signal_years": meaningful_positive_years,
        "selected_trace_summary": selected_trace_summary,
        "failure_reason_breakdown": snapshot.get("failure_reason_breakdown", []),
        "performance_by_strength_bucket": snapshot.get("performance_by_strength_bucket", []),
        "performance_by_retest_bucket": snapshot.get("performance_by_retest_bucket", []),
        "performance_by_trend_bucket": snapshot.get("performance_by_trend_bucket", []),
        "performance_by_w_bucket": snapshot.get("performance_by_w_bucket", []),
        "branch_candidates": enriched_branch_candidates,
        "retained_watch_branch": retained_watch_branch,
        "positive_examples": positive_examples,
        "negative_examples": negative_examples,
        "refinement_flags": refinement_flags,
        "refinement_status": refinement_status,
        "refinement_verdict": refinement_verdict,
        "decision": decision,
        "next_main_queue_card": next_main_queue_card,
        "conclusion": conclusion,
        "next_actions": next_actions,
        "notes": [
            "SB 的 paired trade 重建采用 buy-fill sequence 作为锚点，而不是 selected entry sequence。",
            "当前 branch_candidates 只是 coarse bucket watchlist，不等于已完成 detector split。",
        ],
    }
