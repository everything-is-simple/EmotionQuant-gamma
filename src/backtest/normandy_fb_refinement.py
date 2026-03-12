from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import duckdb

from src.backtest import normandy_volman_alpha as volman_helpers
from src.config import Settings

NORMANDY_FB_REFINEMENT_DTT_VARIANT = volman_helpers.NORMANDY_VOLMAN_ALPHA_DTT_VARIANT


def build_normandy_fb_refinement_scenarios(
    _config: Settings | None = None,
) -> list[volman_helpers.NormandyVolmanAlphaScenario]:
    return [
        volman_helpers.NormandyVolmanAlphaScenario(
            label="BOF_CONTROL",
            family="BOF_CONTROL",
            detector_key="bof_control",
            signal_pattern="bof",
            detector_ready=True,
            control=True,
            detector_status="ready",
            notes="Current validated baseline detector; fixed control for FB refinement.",
            backing_pas_pattern="bof",
        ),
        volman_helpers.NormandyVolmanAlphaScenario(
            label="FB_CLEANER",
            family="FB_REFINED",
            detector_key="fb_cleaner",
            signal_pattern="fb_cleaner",
            detector_ready=True,
            control=False,
            detector_status="ready",
            notes="Restrict FB to cleaner 0/1-touch first-pullback samples.",
        ),
        volman_helpers.NormandyVolmanAlphaScenario(
            label="FB_BOUNDARY",
            family="FB_REFINED",
            detector_key="fb_boundary",
            signal_pattern="fb_boundary",
            detector_ready=True,
            control=False,
            detector_status="ready",
            notes="Isolate the 2-touch boundary-loaded FB branch for refinement replay.",
        ),
    ]


def run_normandy_fb_refinement_matrix(**kwargs) -> dict[str, object]:
    config = kwargs["config"]
    payload = volman_helpers.run_normandy_volman_alpha_matrix(
        **kwargs,
        scenarios=build_normandy_fb_refinement_scenarios(config),
    )
    payload["research_parent"] = "FB"
    payload["research_question"] = "Which FB branch carries the current edge: cleaner 0/1 touch or boundary 2 touch?"
    return payload


def _finite_or_none(value: object) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if cast != cast or cast in (float("inf"), float("-inf")):
        return None
    return cast


def _find_result(matrix_payload: dict[str, object], label: str) -> dict[str, object]:
    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")
    for item in results:
        if isinstance(item, dict) and str(item.get("label") or "") == label:
            return item
    raise ValueError(f"matrix_payload.results must include {label}")


def _sample_density_ok(trade_count: int, participation_rate: float | None) -> bool:
    return trade_count >= volman_helpers.NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES or (
        participation_rate is not None
        and participation_rate >= volman_helpers.NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION
    )


def _complementary_edge_ok(overlap_rate: float | None, incremental_trades: int) -> bool:
    if overlap_rate is not None and overlap_rate <= volman_helpers.NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT:
        return True
    return incremental_trades >= volman_helpers.NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES


def _sort_branch_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda item: (
            1 if bool(item.get("refined_second_alpha_candidate")) else 0,
            1 if bool(item.get("positive_edge_ok")) else 0,
            -999.0 if item.get("expected_value") is None else float(item["expected_value"]),
            -999.0 if item.get("profit_factor") is None else float(item["profit_factor"]),
            int(item.get("trade_count") or 0),
        ),
        reverse=True,
    )


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


FB_REFINEMENT_SIGNAL_YEAR_QUERY = """
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
    SELECT signal_id, code, execute_date AS entry_date, quantity AS entry_qty, price AS entry_price
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
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY execute_date, COALESCE(trade_id, order_id)) AS exit_seq
    FROM broker_order_lifecycle_trace_exp
    WHERE run_id = ?
      AND action = 'SELL'
      AND event_stage IN ('MATCH_FILLED', 'FORCE_CLOSE_FILLED')
),
paired AS (
    SELECT
        e.signal_date,
        e.pattern_strength,
        (x.exit_price - b.entry_price) / NULLIF(b.entry_price, 0) AS gross_return
    FROM entries e
    JOIN buyfills b ON e.signal_id = b.signal_id AND e.code = b.code
    JOIN exits x ON e.code = x.code AND e.entry_seq = x.exit_seq AND b.entry_qty = x.exit_qty
)
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


def _collect_signal_year_slices(matrix_payload: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    db_path_raw = matrix_payload.get("db_path")
    if not db_path_raw:
        return {}
    db_path = Path(str(db_path_raw)).expanduser().resolve()
    if not db_path.exists():
        return {}

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        return {}

    branch_rows: dict[str, list[dict[str, object]]] = {}
    connection = duckdb.connect(str(db_path))
    try:
        for label in ("FB_CLEANER", "FB_BOUNDARY"):
            result = next(
                (
                    item
                    for item in results
                    if isinstance(item, dict) and str(item.get("label") or "") == label
                ),
                None,
            )
            if result is None:
                continue
            run_id = str(result.get("run_id") or "").strip()
            if not run_id:
                continue
            branch_rows[label] = _query_dicts(connection, FB_REFINEMENT_SIGNAL_YEAR_QUERY, (run_id, run_id, run_id))
    finally:
        connection.close()
    return branch_rows


def _dominant_environment_share(result: dict[str, object]) -> float | None:
    breakdown = result.get("environment_breakdown")
    if not isinstance(breakdown, dict):
        return None
    counts: list[float] = []
    for metrics in breakdown.values():
        if not isinstance(metrics, dict):
            continue
        trade_count = _finite_or_none(metrics.get("trade_count"))
        if trade_count is not None:
            counts.append(trade_count)
    if not counts:
        return None
    total = sum(counts)
    if total <= 0:
        return None
    return max(counts) / total


def build_normandy_fb_refinement_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
            "matrix_path": matrix_payload.get("matrix_path"),
            "start": matrix_payload.get("start"),
            "end": matrix_payload.get("end"),
            "dtt_variant": matrix_payload.get("dtt_variant"),
            "matrix_status": matrix_status,
            "control_label": "BOF_CONTROL",
            "parent_candidate": "FB",
            "refined_second_alpha_candidates": [],
            "branch_leader": None,
            "refinement_verdict": "matrix_not_completed",
            "decision": "rerun_refinement_matrix",
            "scorecard": [],
            "risk_flags": ["matrix_not_completed"],
            "conclusion": "FB refinement matrix 尚未完成，当前不能裁决 cleaner / boundary 分支。",
        }

    control = _find_result(matrix_payload, "BOF_CONTROL")
    cleaner = _find_result(matrix_payload, "FB_CLEANER")
    boundary = _find_result(matrix_payload, "FB_BOUNDARY")
    control_ev = _finite_or_none(control.get("expected_value"))
    control_pf = _finite_or_none(control.get("profit_factor"))
    signal_year_slices = _collect_signal_year_slices(matrix_payload)

    scorecard: list[dict[str, object]] = []
    for result in [cleaner, boundary]:
        label = str(result.get("label") or "")
        trade_count = int(result.get("trade_count") or 0)
        ev = _finite_or_none(result.get("expected_value"))
        pf = _finite_or_none(result.get("profit_factor"))
        mdd = _finite_or_none(result.get("max_drawdown"))
        participation = _finite_or_none(result.get("participation_rate"))
        overlap_rate = _finite_or_none(result.get("overlap_rate_vs_bof_control"))
        incremental_trades = int(result.get("incremental_buy_trades_vs_bof_control") or 0)
        dominant_environment_share = _dominant_environment_share(result)
        branch_signal_year_slices = signal_year_slices.get(label, [])
        negative_signal_years = [
            int(row["signal_year"])
            for row in branch_signal_year_slices
            if int(row.get("trade_count") or 0) >= 2 and _finite_or_none(row.get("avg_gross_return")) is not None
            and float(row["avg_gross_return"]) < 0
        ]
        positive_edge_ok = ev is not None and ev > 0 and pf is not None and pf >= 1.0
        sample_density_ok = _sample_density_ok(trade_count, participation)
        complementary_edge_ok = _complementary_edge_ok(overlap_rate, incremental_trades)
        refined_second_alpha_candidate = bool(positive_edge_ok and sample_density_ok and complementary_edge_ok)
        stability_flags: list[str] = []
        if dominant_environment_share is not None and dominant_environment_share >= 0.85:
            stability_flags.append("single_bucket_dependency")
        if negative_signal_years:
            stability_flags.append("negative_signal_year_slices")
        scorecard.append(
            {
                "label": label,
                "family": result.get("family") or "FB_REFINED",
                "signal_pattern": result.get("signal_pattern"),
                "trade_count": trade_count,
                "expected_value": ev,
                "profit_factor": pf,
                "max_drawdown": mdd,
                "participation_rate": participation,
                "overlap_rate_vs_bof_control": overlap_rate,
                "incremental_buy_trades_vs_bof_control": incremental_trades,
                "expected_value_delta_vs_bof_control": (
                    None if ev is None or control_ev is None else ev - control_ev
                ),
                "profit_factor_delta_vs_bof_control": (
                    None if pf is None or control_pf is None else pf - control_pf
                ),
                "positive_edge_ok": positive_edge_ok,
                "sample_density_ok": sample_density_ok,
                "complementary_edge_ok": complementary_edge_ok,
                "refined_second_alpha_candidate": refined_second_alpha_candidate,
                "dominant_environment_share": dominant_environment_share,
                "signal_year_slices": branch_signal_year_slices,
                "negative_signal_years": negative_signal_years,
                "stability_flags": stability_flags,
                "best_environment_bucket": result.get("best_environment_bucket"),
            }
        )

    sorted_scorecard = _sort_branch_rows(scorecard)
    branch_leader = str(sorted_scorecard[0]["label"]) if sorted_scorecard else None
    positive_edge_branches = [str(row["label"]) for row in sorted_scorecard if bool(row["positive_edge_ok"])]
    refined_candidates = [str(row["label"]) for row in sorted_scorecard if bool(row["refined_second_alpha_candidate"])]
    leader_row = sorted_scorecard[0] if sorted_scorecard else None
    leader_stability_flags = [str(item) for item in (leader_row or {}).get("stability_flags", [])]

    risk_flags: list[str] = []
    if positive_edge_branches == ["FB_BOUNDARY"]:
        risk_flags.extend(["boundary_branch_carries_edge", "cleaner_branch_loses_edge"])
    elif positive_edge_branches == ["FB_CLEANER"]:
        risk_flags.extend(["cleaner_branch_carries_edge", "boundary_branch_loses_edge"])
    elif len(positive_edge_branches) == 2:
        risk_flags.append("both_branches_positive")
    else:
        risk_flags.append("no_branch_keeps_positive_edge")

    if not refined_candidates:
        risk_flags.append("no_branch_clears_full_second_alpha_gate")
    if leader_stability_flags:
        risk_flags.extend(
            [
                flag
                for flag in leader_stability_flags
                if flag not in risk_flags
            ]
        )
        risk_flags.append("leader_branch_still_fragile_after_refinement")

    if refined_candidates == ["FB_BOUNDARY"]:
        refinement_verdict = "boundary_branch_promoted"
        if leader_stability_flags:
            decision = "boundary_stability_follow_up_before_n2"
            conclusion = "FB refinement 当前由 `FB_BOUNDARY` 保住正向 edge 并通过第二 alpha 门槛，但跨年与 bucket 稳定性仍偏脆弱，暂不直接打开 N2。"
        else:
            decision = "promote_fb_boundary_to_follow_up"
            conclusion = "FB refinement 当前由 `FB_BOUNDARY` 保住正向 edge 并通过第二 alpha 门槛；后续应围绕 boundary 分支继续推进。"
    elif refined_candidates == ["FB_CLEANER"]:
        refinement_verdict = "cleaner_branch_promoted"
        if leader_stability_flags:
            decision = "cleaner_stability_follow_up_before_n2"
            conclusion = "FB refinement 当前由 `FB_CLEANER` 保住正向 edge 并通过第二 alpha 门槛，但跨年与 bucket 稳定性仍偏脆弱，暂不直接打开 N2。"
        else:
            decision = "promote_fb_cleaner_to_follow_up"
            conclusion = "FB refinement 当前由 `FB_CLEANER` 保住正向 edge 并通过第二 alpha 门槛；后续应围绕 cleaner 分支继续推进。"
    elif positive_edge_branches == ["FB_BOUNDARY"]:
        refinement_verdict = "boundary_branch_carries_edge_but_not_fully_ready"
        decision = "keep_fb_boundary_only_and_hold_n2"
        conclusion = "FB refinement 当前显示 edge 主要由 `FB_BOUNDARY` 承担，但它还没完整通过第二 alpha 门槛，暂不直接打开 N2。"
    elif positive_edge_branches == ["FB_CLEANER"]:
        refinement_verdict = "cleaner_branch_carries_edge_but_not_fully_ready"
        decision = "keep_fb_cleaner_only_and_hold_n2"
        conclusion = "FB refinement 当前显示 edge 主要由 `FB_CLEANER` 承担，但它还没完整通过第二 alpha 门槛，暂不直接打开 N2。"
    elif len(positive_edge_branches) == 2:
        refinement_verdict = "both_branches_survive_needs_next_slice"
        decision = "keep_both_branches_for_next_slice"
        conclusion = "FB refinement 当前两支都保留正向 edge，说明 cleaner / boundary 还没有收敛成单支正式答案。"
    else:
        refinement_verdict = "no_branch_survives_refinement"
        decision = "fb_route_recheck_or_no_go"
        conclusion = "FB refinement 当前没有任何分支保住正向 edge，FB 路线需要重新审视是否继续保留。"

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "upstream_matrix_path": matrix_payload.get("upstream_matrix_path"),
        "start": matrix_payload.get("start"),
        "end": matrix_payload.get("end"),
        "dtt_variant": matrix_payload.get("dtt_variant"),
        "matrix_status": matrix_status,
        "control_label": "BOF_CONTROL",
        "parent_candidate": "FB",
        "research_question": matrix_payload.get("research_question"),
        "candidate_rule": {
            "expected_value_must_be_positive": True,
            "profit_factor_floor": 1.0,
            "min_trade_count": volman_helpers.NORMANDY_VOLMAN_CANDIDATE_MIN_TRADES,
            "min_participation_rate": volman_helpers.NORMANDY_VOLMAN_CANDIDATE_MIN_PARTICIPATION,
            "max_overlap_for_independent": volman_helpers.NORMANDY_VOLMAN_MAX_OVERLAP_FOR_INDEPENDENT,
            "min_incremental_trades": volman_helpers.NORMANDY_VOLMAN_MIN_INCREMENTAL_TRADES,
        },
        "scorecard": sorted_scorecard,
        "positive_edge_branches": positive_edge_branches,
        "refined_second_alpha_candidates": refined_candidates,
        "branch_leader": branch_leader,
        "leader_stability_flags": leader_stability_flags,
        "refinement_verdict": refinement_verdict,
        "decision": decision,
        "risk_flags": risk_flags,
        "conclusion": conclusion,
    }
