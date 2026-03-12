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


def _find_result(payload: dict[str, object], label: str) -> dict[str, object]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise KeyError(f"Payload missing results for {label}")
    for item in results:
        if isinstance(item, dict) and str(item.get("label") or "") == label:
            return item
    raise KeyError(f"Unable to find result for {label}")


def _find_scorecard_row(payload: dict[str, object], label: str) -> dict[str, object]:
    rows = payload.get("scorecard")
    if not isinstance(rows, list):
        raise KeyError(f"Digest payload missing scorecard for {label}")
    for item in rows:
        if isinstance(item, dict) and str(item.get("label") or "") == label:
            return item
    raise KeyError(f"Unable to find scorecard row for {label}")


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


def _resolve_boundary_run_id(matrix_payload: dict[str, object]) -> str:
    boundary_result = _find_result(matrix_payload, "FB_BOUNDARY")
    run_id = str(boundary_result.get("run_id") or "").strip()
    if not run_id:
        raise KeyError("FB_BOUNDARY result missing run_id")
    return run_id


def _maybe_open_snapshot_db(
    db_path: str | Path | None,
) -> tuple[duckdb.DuckDBPyConnection | None, Path | None]:
    if db_path is None:
        return None, None
    resolved = Path(db_path).expanduser().resolve()
    if not resolved.exists():
        return None, resolved
    return duckdb.connect(str(resolved)), resolved


FB_BOUNDARY_PAIRED_TRACE_CTE = """
WITH entries AS (
    SELECT
        signal_id,
        signal_date,
        code,
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
    FB_BOUNDARY_PAIRED_TRACE_CTE
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
    FB_BOUNDARY_PAIRED_TRACE_CTE
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
    AVG(CAST(json_extract_string(trace_payload_json, '$.pullback_depth') AS DOUBLE)) AS avg_pullback_depth
FROM pas_trigger_trace_exp
WHERE run_id = ?
  AND detected = TRUE
  AND selected_pattern = detector
GROUP BY 1
ORDER BY MIN(signal_date)
"""


NEGATIVE_EXAMPLES_QUERY = (
    FB_BOUNDARY_PAIRED_TRACE_CTE
    + """
SELECT
    signal_date,
    code,
    entry_date,
    exit_date,
    gross_return,
    pattern_strength
FROM paired
WHERE gross_return < 0
ORDER BY gross_return ASC, signal_date ASC
LIMIT 8
"""
)


def collect_normandy_fb_boundary_stability_snapshot(
    matrix_payload: dict[str, object],
    db_path: str | Path | None,
) -> dict[str, object]:
    run_id = _resolve_boundary_run_id(matrix_payload)
    connection, resolved_path = _maybe_open_snapshot_db(db_path)
    if connection is None:
        return {
            "snapshot_status": "missing",
            "snapshot_db_path": str(resolved_path) if resolved_path is not None else None,
            "boundary_run_id": run_id,
            "pairing_diagnostics": {},
            "signal_year_slices": [],
            "quarter_activity": [],
            "negative_examples": [],
        }
    try:
        params = [run_id, run_id, run_id]
        pairing = _query_dicts(connection, PAIRING_DIAGNOSTICS_QUERY, params)
        signal_year_slices = _query_dicts(connection, SIGNAL_YEAR_SLICES_QUERY, params)
        quarter_activity = _query_dicts(connection, QUARTER_ACTIVITY_QUERY, [run_id])
        negative_examples = _query_dicts(connection, NEGATIVE_EXAMPLES_QUERY, params)
    finally:
        connection.close()

    return {
        "snapshot_status": "available",
        "snapshot_db_path": str(resolved_path),
        "boundary_run_id": run_id,
        "pairing_diagnostics": pairing[0] if pairing else {},
        "signal_year_slices": _normalize_rows(signal_year_slices),
        "quarter_activity": _normalize_rows(quarter_activity),
        "negative_examples": _normalize_rows(negative_examples),
    }


def build_normandy_fb_boundary_stability_report(
    matrix_payload: dict[str, object],
    refinement_digest_payload: dict[str, object],
    snapshot_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = snapshot_payload or {}
    boundary_result = _find_result(matrix_payload, "FB_BOUNDARY")
    bof_result = _find_result(matrix_payload, "BOF_CONTROL")
    boundary_scorecard = _find_scorecard_row(refinement_digest_payload, "FB_BOUNDARY")
    signal_year_slices = [
        row for row in snapshot.get("signal_year_slices", []) if isinstance(row, dict)
    ]
    quarter_activity = [
        row for row in snapshot.get("quarter_activity", []) if isinstance(row, dict)
    ]
    negative_examples = [
        row for row in snapshot.get("negative_examples", []) if isinstance(row, dict)
    ]
    meaningful_negative_years = [
        int(row["signal_year"])
        for row in signal_year_slices
        if _int_or_zero(row.get("trade_count")) >= 2
        and _float_or_none(row.get("avg_gross_return")) is not None
        and float(row["avg_gross_return"]) < 0
    ]
    negative_example_years = sorted(
        {
            date.fromisoformat(str(row["signal_date"])).year
            for row in negative_examples
            if row.get("signal_date")
        }
    )
    leader_stability_flags = [
        str(item)
        for item in refinement_digest_payload.get("leader_stability_flags", [])
        if isinstance(item, str)
    ]

    stability_flags: list[str] = []
    if "single_bucket_dependency" in leader_stability_flags:
        stability_flags.append("single_bucket_dependency")
    if meaningful_negative_years:
        stability_flags.append("negative_signal_year_slices")
    if len(negative_example_years) >= 3:
        stability_flags.append("losses_not_isolated")
    if _int_or_zero(boundary_result.get("trade_count")) < 20:
        stability_flags.append("sample_still_small")

    snapshot_status = str(snapshot.get("snapshot_status") or "missing")
    if snapshot_status != "available":
        stability_status = "snapshot_missing"
        decision = "snapshot_recovery_needed"
        conclusion = "FB_BOUNDARY stability follow-up 缺少快照库，当前不能完成 focused stability slice。"
    elif stability_flags:
        stability_status = "fragile_boundary_not_n2_ready"
        decision = "hold_n2_and_demote_boundary_to_watch_candidate"
        conclusion = (
            "FB_BOUNDARY 虽然已经是 FB family 的 retained branch，"
            "但 focused stability follow-up 仍显示它高度依赖单一 bucket，"
            f"并在 {', '.join(str(year) for year in meaningful_negative_years) or '若干年度'} 出现负切片；"
            "当前不应直接打开 N2。"
        )
    else:
        stability_status = "boundary_ready_for_n2"
        decision = "open_n2_for_bof_vs_fb_boundary"
        conclusion = "FB_BOUNDARY 当前已通过 focused stability follow-up，可进入 BOF vs FB_BOUNDARY 的 N2 exit decomposition。"

    next_actions = (
        [
            "保持 FB_BOUNDARY 为 retained branch，但先降级为 watch candidate。",
            "主队列切到 N1.10 / SB refinement or no-go。",
            "除非出现新的更强证据，否则当前不直接打开 BOF vs FB_BOUNDARY 的 N2。",
        ]
        if decision == "hold_n2_and_demote_boundary_to_watch_candidate"
        else [
            "打开 N2 / BOF vs FB_BOUNDARY controlled exit decomposition。",
            "优先回答 boundary entry 当前是买对卖坏，还是 exit 还在吞收益。",
        ]
    )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "refinement_digest_summary_run_id": refinement_digest_payload.get("summary_run_id"),
        "refinement_digest_path": refinement_digest_payload.get("matrix_path"),
        "snapshot_status": snapshot_status,
        "snapshot_db_path": snapshot.get("snapshot_db_path"),
        "boundary_run_id": snapshot.get("boundary_run_id") or boundary_result.get("run_id"),
        "candidate_label": "FB_BOUNDARY",
        "parent_candidate": "FB",
        "control_label": "BOF_CONTROL",
        "candidate_summary": {
            "trade_count": _int_or_zero(boundary_result.get("trade_count")),
            "expected_value": _float_or_none(boundary_result.get("expected_value")),
            "profit_factor": _float_or_none(boundary_result.get("profit_factor")),
            "max_drawdown": _float_or_none(boundary_result.get("max_drawdown")),
            "participation_rate": _float_or_none(boundary_result.get("participation_rate")),
        },
        "control_summary": {
            "trade_count": _int_or_zero(bof_result.get("trade_count")),
            "expected_value": _float_or_none(bof_result.get("expected_value")),
            "profit_factor": _float_or_none(bof_result.get("profit_factor")),
            "max_drawdown": _float_or_none(bof_result.get("max_drawdown")),
            "participation_rate": _float_or_none(bof_result.get("participation_rate")),
        },
        "pairing_diagnostics": snapshot.get("pairing_diagnostics", {}),
        "signal_year_slices": signal_year_slices,
        "quarter_activity": quarter_activity,
        "negative_examples": negative_examples,
        "active_quarters": len(quarter_activity),
        "meaningful_negative_signal_years": meaningful_negative_years,
        "negative_example_years": negative_example_years,
        "dominant_environment_share": _float_or_none(boundary_scorecard.get("dominant_environment_share")),
        "best_environment_bucket": boundary_scorecard.get("best_environment_bucket"),
        "leader_stability_flags": leader_stability_flags,
        "stability_flags": stability_flags,
        "stability_status": stability_status,
        "decision": decision,
        "conclusion": conclusion,
        "next_actions": next_actions,
        "notes": [
            "focused stability follow-up 只围绕 N1.9 retained branch `FB_BOUNDARY`，不重新打开 family-level FB。",
            "negative_examples 使用 lifecycle pairing proxy，只服务 N1.9A 的稳定性读数，不替代上游 formal EV。",
        ],
    }
