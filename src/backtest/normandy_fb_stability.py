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
        if isinstance(item, dict) and str(item.get("label")) == label:
            return item
    raise KeyError(f"Unable to find result for {label}")


def _resolve_fb_run_id(matrix_payload: dict[str, object]) -> str:
    fb_result = _find_result(matrix_payload, "FB")
    run_id = str(fb_result.get("run_id") or "").strip()
    if not run_id:
        raise KeyError("FB result missing run_id")
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


FB_PAIRED_TRACE_CTE = """
WITH entries AS (
    SELECT
        signal_id,
        signal_date,
        code,
        CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS INTEGER) AS prior_ema_touches,
        CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) AS trend_gain,
        CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) AS pullback_depth,
        CAST(json_extract_string(trace_payload_json, '$.volume_ratio') AS DOUBLE) AS volume_ratio,
        CAST(pattern_strength AS DOUBLE) AS pattern_strength,
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY signal_date, signal_id) AS entry_seq
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
        price AS entry_price
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND event_stage = 'MATCH_FILLED'
      AND action = 'BUY'
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
        e.prior_ema_touches,
        e.trend_gain,
        e.pullback_depth,
        e.volume_ratio,
        e.pattern_strength,
        b.entry_date,
        b.entry_qty,
        b.entry_price,
        x.exit_date,
        x.exit_qty,
        x.exit_price,
        x.exit_stage,
        (x.exit_price - b.entry_price) / NULLIF(b.entry_price, 0) AS gross_return
    FROM entries e
    JOIN buyfills b
      ON e.signal_id = b.signal_id
     AND e.code = b.code
    JOIN exits x
      ON e.code = x.code
     AND e.entry_seq = x.exit_seq
     AND b.entry_qty = x.exit_qty
)
"""


PAIRING_DIAGNOSTICS_QUERY = (
    FB_PAIRED_TRACE_CTE
    + """
SELECT
    (SELECT COUNT(*) FROM entries) AS selected_entry_count,
    (SELECT COUNT(*) FROM buyfills) AS buy_fill_count,
    (SELECT COUNT(*) FROM exits) AS exit_fill_count,
    COUNT(*) AS paired_trade_count
FROM paired
"""
)


SIGNAL_YEAR_SLICES_QUERY = (
    FB_PAIRED_TRACE_CTE
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


QUARTER_ACTIVITY_QUERY = """
SELECT
    CONCAT(
        CAST(EXTRACT(YEAR FROM signal_date) AS INTEGER),
        '-Q',
        CAST(EXTRACT(QUARTER FROM signal_date) AS INTEGER)
    ) AS signal_quarter,
    COUNT(*) AS selected_count,
    AVG(CAST(pattern_strength AS DOUBLE)) AS avg_strength,
    AVG(CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE)) AS avg_trend_gain,
    AVG(CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE)) AS avg_pullback_depth,
    AVG(CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS DOUBLE)) AS avg_prior_ema_touches
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
GROUP BY 1
ORDER BY MIN(signal_date)
"""


SELECTED_SUMMARY_QUERY = """
SELECT
    COUNT(*) AS selected_count,
    AVG(CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS DOUBLE)) AS avg_prior_ema_touches,
    MAX(CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS DOUBLE)) AS max_prior_ema_touches,
    AVG(CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE)) AS avg_pullback_depth,
    AVG(CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE)) AS avg_trend_gain,
    AVG(CAST(json_extract_string(trace_payload_json, '$.volume_ratio') AS DOUBLE)) AS avg_volume_ratio,
    AVG(CASE WHEN CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS DOUBLE) = 2 THEN 1.0 ELSE 0.0 END) AS edge_touch_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) <= 0.10
            THEN 1.0
            ELSE 0.0
        END
    ) AS near_floor_trend_ratio,
    AVG(
        CASE
            WHEN CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) < 0.25
              OR CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) > 0.50
            THEN 1.0
            ELSE 0.0
        END
    ) AS edge_depth_ratio,
    AVG(CASE WHEN CAST(json_extract_string(trace_payload_json, '$.volume_ratio') AS DOUBLE) >= 2.0 THEN 1.0 ELSE 0.0 END) AS strong_volume_ratio,
    MIN(CAST(pattern_strength AS DOUBLE)) AS min_strength,
    AVG(CAST(pattern_strength AS DOUBLE)) AS avg_strength,
    MAX(CAST(pattern_strength AS DOUBLE)) AS max_strength
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
"""


TOUCH_DISTRIBUTION_QUERY = """
SELECT
    CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS INTEGER) AS prior_ema_touches,
    COUNT(*) AS count,
    COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS share
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
GROUP BY 1
ORDER BY 1
"""


TOUCH_PERFORMANCE_QUERY = (
    FB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN prior_ema_touches = 2 THEN 'touch_2_boundary'
        ELSE 'touch_0_1_cleaner'
    END AS touch_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate,
    AVG(pattern_strength) AS avg_strength
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


DEPTH_PERFORMANCE_QUERY = (
    FB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN pullback_depth BETWEEN 0.25 AND 0.50 THEN 'core_depth_band'
        ELSE 'edge_depth_band'
    END AS depth_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


TREND_PERFORMANCE_QUERY = (
    FB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN trend_gain <= 0.10 THEN 'near_floor_trend'
        ELSE 'stronger_trend'
    END AS trend_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


VOLUME_PERFORMANCE_QUERY = (
    FB_PAIRED_TRACE_CTE
    + """
SELECT
    CASE
        WHEN volume_ratio >= 2.0 THEN 'strong_volume'
        ELSE 'base_volume'
    END AS volume_bucket,
    COUNT(*) AS trade_count,
    AVG(gross_return) AS avg_gross_return,
    SUM(CASE WHEN gross_return > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
FROM paired
GROUP BY 1
ORDER BY 1
"""
)


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


BOUNDARY_EXAMPLES_QUERY = """
SELECT
    signal_date,
    code,
    CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS INTEGER) AS prior_ema_touches,
    CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) AS trend_gain,
    CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) AS pullback_depth,
    CAST(pattern_strength AS DOUBLE) AS pattern_strength
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
  AND (
      CAST(json_extract_string(trace_payload_json, '$.prior_ema_touches') AS INTEGER) = 2
      OR CAST(json_extract_string(trace_payload_json, '$.trend_gain') AS DOUBLE) <= 0.10
      OR CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) < 0.25
      OR CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE) > 0.50
  )
ORDER BY signal_date, code
LIMIT 12
"""


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


def collect_normandy_fb_stability_snapshot(
    matrix_payload: dict[str, object],
    db_path: str | Path | None,
) -> dict[str, object]:
    run_id = _resolve_fb_run_id(matrix_payload)
    connection, resolved_path = _maybe_open_snapshot_db(db_path)
    if connection is None:
        return {
            "snapshot_status": "missing",
            "snapshot_db_path": str(resolved_path) if resolved_path else None,
            "fb_run_id": run_id,
            "pairing_diagnostics": {},
            "signal_year_slices": [],
            "quarter_activity": [],
        }
    try:
        params = [run_id, run_id, run_id]
        diagnostics = _query_dicts(connection, PAIRING_DIAGNOSTICS_QUERY, params)
        signal_year_slices = _query_dicts(connection, SIGNAL_YEAR_SLICES_QUERY, params)
        quarter_activity = _query_dicts(connection, QUARTER_ACTIVITY_QUERY, [run_id])
    finally:
        connection.close()
    return {
        "snapshot_status": "available",
        "snapshot_db_path": str(resolved_path),
        "fb_run_id": run_id,
        "pairing_diagnostics": diagnostics[0] if diagnostics else {},
        "signal_year_slices": _normalize_rows(signal_year_slices),
        "quarter_activity": _normalize_rows(quarter_activity),
    }


def collect_normandy_fb_purity_snapshot(
    matrix_payload: dict[str, object],
    db_path: str | Path | None,
) -> dict[str, object]:
    run_id = _resolve_fb_run_id(matrix_payload)
    connection, resolved_path = _maybe_open_snapshot_db(db_path)
    if connection is None:
        return {
            "snapshot_status": "missing",
            "snapshot_db_path": str(resolved_path) if resolved_path else None,
            "fb_run_id": run_id,
            "selected_summary": {},
            "prior_ema_touches_distribution": [],
            "failure_reason_breakdown": [],
            "performance_by_touch_bucket": [],
            "performance_by_depth_bucket": [],
            "performance_by_trend_bucket": [],
            "performance_by_volume_bucket": [],
            "boundary_examples": [],
        }
    try:
        params = [run_id, run_id, run_id]
        selected_summary = _query_dicts(connection, SELECTED_SUMMARY_QUERY, [run_id])
        touch_distribution = _query_dicts(connection, TOUCH_DISTRIBUTION_QUERY, [run_id])
        failure_reason_breakdown = _query_dicts(connection, FAILURE_REASON_QUERY, [run_id])
        touch_performance = _query_dicts(connection, TOUCH_PERFORMANCE_QUERY, params)
        depth_performance = _query_dicts(connection, DEPTH_PERFORMANCE_QUERY, params)
        trend_performance = _query_dicts(connection, TREND_PERFORMANCE_QUERY, params)
        volume_performance = _query_dicts(connection, VOLUME_PERFORMANCE_QUERY, params)
        boundary_examples = _query_dicts(connection, BOUNDARY_EXAMPLES_QUERY, [run_id])
    finally:
        connection.close()
    return {
        "snapshot_status": "available",
        "snapshot_db_path": str(resolved_path),
        "fb_run_id": run_id,
        "selected_summary": selected_summary[0] if selected_summary else {},
        "prior_ema_touches_distribution": _normalize_rows(touch_distribution),
        "failure_reason_breakdown": _normalize_rows(failure_reason_breakdown),
        "performance_by_touch_bucket": _normalize_rows(touch_performance),
        "performance_by_depth_bucket": _normalize_rows(depth_performance),
        "performance_by_trend_bucket": _normalize_rows(trend_performance),
        "performance_by_volume_bucket": _normalize_rows(volume_performance),
        "boundary_examples": _normalize_rows(boundary_examples),
    }


def _find_bucket_row(rows: list[dict[str, object]], key: str, value: str) -> dict[str, object] | None:
    for row in rows:
        if str(row.get(key)) == value:
            return row
    return None


def build_normandy_fb_stability_report(
    matrix_payload: dict[str, object],
    candidate_report_payload: dict[str, object],
    snapshot_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = snapshot_payload or {}
    fb_result = _find_result(matrix_payload, "FB")
    bof_result = _find_result(matrix_payload, "BOF_CONTROL")
    risk_flags = [str(item) for item in candidate_report_payload.get("risk_flags", []) if isinstance(item, str)]
    positive_buckets = [
        str(item) for item in candidate_report_payload.get("positive_buckets", []) if isinstance(item, str)
    ]
    negative_buckets = [
        str(item) for item in candidate_report_payload.get("negative_buckets", []) if isinstance(item, str)
    ]
    signal_year_slices = [
        row for row in snapshot.get("signal_year_slices", []) if isinstance(row, dict)
    ]
    quarter_activity = [
        row for row in snapshot.get("quarter_activity", []) if isinstance(row, dict)
    ]

    positive_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if _float_or_none(row.get("avg_gross_return")) is not None and float(row["avg_gross_return"]) > 0
    ]
    meaningful_negative_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if _int_or_zero(row.get("trade_count")) >= 5
        and _float_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) < 0
    ]

    stability_flags: list[str] = []
    if "dominant_bucket_dependency" in risk_flags or len(positive_buckets) <= 1:
        stability_flags.append("single_bucket_positive_edge")
    if meaningful_negative_years:
        stability_flags.append("negative_signal_year_slices")
    if signal_year_slices and len(positive_years) < len(signal_year_slices):
        stability_flags.append("time_slice_sign_flip")
    if _int_or_zero(fb_result.get("trade_count")) < 50:
        stability_flags.append("sample_still_small")

    snapshot_status = str(snapshot.get("snapshot_status") or "missing")
    if snapshot_status != "available":
        stability_status = "snapshot_missing"
        decision = "snapshot_recovery_needed"
        conclusion = "N1.7 stability report 缺少快照库，当前只能保留 N1.6 风险标记，无法完成时间切片审计。"
    else:
        stability_status = (
            "fragile_candidate_not_exit_ready" if stability_flags else "stable_candidate_exit_ready"
        )
        decision = "detector_refinement_before_n2" if stability_flags else "eligible_for_n2_exit_decomposition"
        active_quarter_count = len(quarter_activity)
        if stability_flags:
            conclusion = (
                f"FB 已跨 {active_quarter_count} 个季度出现，不是单次爆点；"
                f"但正向 edge 仍主要集中在 {', '.join(positive_buckets) or 'UNKNOWN'}，"
                f"且 signal-year 切片在 {', '.join(str(year) for year in meaningful_negative_years) or '若干年度'} 出现负读数。"
                "当前更合理的动作是先做 detector refinement，而不是直接进入 N2 exit decomposition。"
            )
        else:
            conclusion = "FB 当前已通过环境桶与时间切片复核，可进入 N2 exit decomposition。"

    next_actions = (
        [
            "先把 FB 拆成 cleaner / boundary 两个子 detector，再复跑长窗稳定性。",
            "保持 BOF_CONTROL 为 baseline，不直接把当前 FB detector 带进 N2。",
            "若 refinement 后稳定性回升，再进入 BOF vs FB 的 controlled exit decomposition。",
        ]
        if decision == "detector_refinement_before_n2"
        else [
            "在 BOF_CONTROL 对照下进入 N2 exit decomposition。",
            "优先回答 FB 当前是买对卖坏，还是 exit 已经与 BOF 同样健康。",
        ]
    )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "snapshot_status": snapshot_status,
        "snapshot_db_path": snapshot.get("snapshot_db_path"),
        "fb_run_id": snapshot.get("fb_run_id") or fb_result.get("run_id"),
        "candidate_label": "FB",
        "control_label": "BOF_CONTROL",
        "candidate_summary": candidate_report_payload.get("candidate_summary")
        or {
            "trade_count": _int_or_zero(fb_result.get("trade_count")),
            "expected_value": _float_or_none(fb_result.get("expected_value")),
            "profit_factor": _float_or_none(fb_result.get("profit_factor")),
            "max_drawdown": _float_or_none(fb_result.get("max_drawdown")),
            "participation_rate": _float_or_none(fb_result.get("participation_rate")),
        },
        "control_summary": candidate_report_payload.get("control_summary")
        or {
            "trade_count": _int_or_zero(bof_result.get("trade_count")),
            "expected_value": _float_or_none(bof_result.get("expected_value")),
            "profit_factor": _float_or_none(bof_result.get("profit_factor")),
            "max_drawdown": _float_or_none(bof_result.get("max_drawdown")),
            "participation_rate": _float_or_none(bof_result.get("participation_rate")),
        },
        "bucket_breakdown": candidate_report_payload.get("bucket_breakdown", []),
        "positive_buckets": positive_buckets,
        "negative_buckets": negative_buckets,
        "pairing_diagnostics": snapshot.get("pairing_diagnostics", {}),
        "signal_year_slices": signal_year_slices,
        "quarter_activity": quarter_activity,
        "positive_signal_years": positive_years,
        "meaningful_negative_signal_years": meaningful_negative_years,
        "stability_flags": stability_flags,
        "stability_status": stability_status,
        "decision": decision,
        "conclusion": conclusion,
        "next_actions": next_actions,
        "notes": [
            "signal_year_slices 使用 run snapshot 的 lifecycle 价格重建，作为 N1.7 时间切片代理读数。",
            "环境桶口径沿用上游 matrix / report 的 entry-side market environment 定义。",
        ],
    }


def build_normandy_fb_purity_audit(
    matrix_payload: dict[str, object],
    candidate_report_payload: dict[str, object],
    snapshot_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = snapshot_payload or {}
    fb_result = _find_result(matrix_payload, "FB")
    selected_summary = (
        snapshot.get("selected_summary") if isinstance(snapshot.get("selected_summary"), dict) else {}
    )
    touch_performance = [
        row for row in snapshot.get("performance_by_touch_bucket", []) if isinstance(row, dict)
    ]
    failure_reason_breakdown = [
        row for row in snapshot.get("failure_reason_breakdown", []) if isinstance(row, dict)
    ]
    touch_boundary = _find_bucket_row(touch_performance, "touch_bucket", "touch_2_boundary")
    touch_cleaner = _find_bucket_row(touch_performance, "touch_bucket", "touch_0_1_cleaner")
    late_pullback_guard = _find_bucket_row(failure_reason_breakdown, "reason", "NOT_FIRST_PULLBACK")

    purity_flags: list[str] = []
    if _float_or_none(selected_summary.get("edge_touch_ratio")) is not None and float(
        selected_summary["edge_touch_ratio"]
    ) >= 0.5:
        purity_flags.append("boundary_touch_loaded")
    if _float_or_none(selected_summary.get("edge_depth_ratio")) is not None and float(
        selected_summary["edge_depth_ratio"]
    ) >= 0.2:
        purity_flags.append("depth_band_boundary_mix")
    if (
        touch_boundary is not None
        and touch_cleaner is not None
        and _float_or_none(touch_boundary.get("avg_gross_return")) is not None
        and _float_or_none(touch_cleaner.get("avg_gross_return")) is not None
        and float(touch_boundary["avg_gross_return"]) > float(touch_cleaner["avg_gross_return"])
    ):
        purity_flags.append("boundary_samples_carry_edge")
    if (
        late_pullback_guard is not None
        and _float_or_none(late_pullback_guard.get("share")) is not None
        and float(late_pullback_guard["share"]) >= 0.05
    ):
        purity_flags.append("late_pullback_guardrail_active")

    snapshot_status = str(snapshot.get("snapshot_status") or "missing")
    if snapshot_status != "available":
        purity_verdict = "snapshot_missing"
        conclusion = "N1.7 purity audit 缺少快照库，当前无法读取 detector trace proxy。"
        next_actions = ["恢复 N1.5 快照库后再做 purity audit。"]
    else:
        purity_verdict = (
            "boundary_loaded_detector_refinement_required"
            if purity_flags
            else "purity_good_enough_for_n2"
        )
        if purity_verdict == "boundary_loaded_detector_refinement_required":
            conclusion = (
                "FB 当前并未表现出“大量普通 PB 混入已选集合”的直接证据，"
                "但超过一半的已选样本落在 prior_ema_touches=2 的 detector 边界，"
                "且边界样本的表现优于更干净的 0/1 touch 子集。"
                "这说明当前 alpha 更像 boundary-loaded FB，而不是 textbook-clean first pullback。"
            )
            next_actions = [
                "先把 FB 拆成 cleaner(0/1 touch) 与 boundary(2 touch) 两个子 detector。",
                "单独复核 boundary-loaded 子集是否才是真正 carrying edge 的对象。",
                "在 detector 语义未收紧前，不直接把当前 FB 带进 N2 exit decomposition。",
            ]
        else:
            conclusion = "FB 当前 purity proxy 已够干净，可带着现有 detector 进入 N2。"
            next_actions = [
                "保持现有 detector，进入 N2 exit decomposition。",
            ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "snapshot_status": snapshot_status,
        "snapshot_db_path": snapshot.get("snapshot_db_path"),
        "fb_run_id": snapshot.get("fb_run_id") or fb_result.get("run_id"),
        "candidate_label": "FB",
        "candidate_summary": candidate_report_payload.get("candidate_summary"),
        "selected_summary": selected_summary,
        "prior_ema_touches_distribution": snapshot.get("prior_ema_touches_distribution", []),
        "failure_reason_breakdown": failure_reason_breakdown,
        "performance_by_touch_bucket": touch_performance,
        "performance_by_depth_bucket": snapshot.get("performance_by_depth_bucket", []),
        "performance_by_trend_bucket": snapshot.get("performance_by_trend_bucket", []),
        "performance_by_volume_bucket": snapshot.get("performance_by_volume_bucket", []),
        "boundary_examples": snapshot.get("boundary_examples", []),
        "purity_flags": purity_flags,
        "purity_verdict": purity_verdict,
        "conclusion": conclusion,
        "next_actions": next_actions,
        "notes": [
            "purity audit 使用 N1.5 run snapshot 的 detector trace + lifecycle pairing proxy，不重跑 Volman matrix。",
            "performance_by_* 使用 gross_return proxy，只服务 N1.7 purity 排序，不替代上游 formal EV。",
        ],
    }
