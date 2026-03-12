from __future__ import annotations

from datetime import datetime


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


def _bucket_rows(result: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    environment_breakdown = result.get("environment_breakdown")
    if not isinstance(environment_breakdown, dict):
        return rows
    total_trades = max(_int_or_zero(result.get("trade_count")), 1)
    for bucket, metrics in environment_breakdown.items():
        if not isinstance(metrics, dict):
            continue
        trade_count = _int_or_zero(metrics.get("trade_count"))
        rows.append(
            {
                "bucket": str(bucket),
                "trade_count": trade_count,
                "expected_value": _float_or_none(metrics.get("expected_value")),
                "profit_factor": _float_or_none(metrics.get("profit_factor")),
                "win_rate": _float_or_none(metrics.get("win_rate")),
                "share_of_candidate_trades": trade_count / total_trades,
            }
        )
    rows.sort(key=lambda item: int(item["trade_count"]), reverse=True)
    return rows


def _risk_flags(
    *,
    candidate: dict[str, object],
    control: dict[str, object],
    bucket_rows: list[dict[str, object]],
) -> list[str]:
    flags: list[str] = []
    trade_count = _int_or_zero(candidate.get("trade_count"))
    candidate_ev = _float_or_none(candidate.get("expected_value"))
    control_ev = _float_or_none(control.get("expected_value"))
    overlap = _float_or_none(candidate.get("overlap_rate_vs_bof_control"))
    candidate_mdd = _float_or_none(candidate.get("max_drawdown"))
    control_mdd = _float_or_none(control.get("max_drawdown"))

    if trade_count < 50:
        flags.append("low_sample_count")
    if bucket_rows and float(bucket_rows[0]["share_of_candidate_trades"]) >= 0.8:
        flags.append("dominant_bucket_dependency")
    bullish_row = next((row for row in bucket_rows if row["bucket"] == "BULLISH"), None)
    if bullish_row and _int_or_zero(bullish_row.get("trade_count")) > 0:
        bullish_ev = _float_or_none(bullish_row.get("expected_value"))
        if bullish_ev is not None and bullish_ev < 0:
            flags.append("bullish_failure_observed")
    if candidate_ev is not None and control_ev is not None and candidate_ev < control_ev:
        flags.append("edge_below_bof_control")
    if overlap is not None and overlap > 0.5:
        flags.append("high_overlap_with_bof_control")
    if candidate_mdd is not None and control_mdd is not None and candidate_mdd > control_mdd:
        flags.append("drawdown_above_bof_control")
    return flags


def build_normandy_fb_candidate_report(
    matrix_payload: dict[str, object],
    digest_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    fb_result = _find_result(matrix_payload, "FB")
    bof_result = _find_result(matrix_payload, "BOF_CONTROL")
    bucket_rows = _bucket_rows(fb_result)

    digest_candidates = []
    if digest_payload and isinstance(digest_payload.get("second_alpha_candidates"), list):
        digest_candidates = [str(item) for item in digest_payload["second_alpha_candidates"]]

    qualified = "FB" in digest_candidates
    flags = _risk_flags(candidate=fb_result, control=bof_result, bucket_rows=bucket_rows)

    qualification = (
        "qualified_second_alpha_candidate_with_risk_flags"
        if qualified and flags
        else "qualified_second_alpha_candidate"
        if qualified
        else "candidate_not_qualified"
    )
    positive_buckets = [
        str(row["bucket"])
        for row in bucket_rows
        if _float_or_none(row.get("expected_value")) is not None and float(row["expected_value"]) > 0
    ]
    negative_buckets = [
        str(row["bucket"])
        for row in bucket_rows
        if _float_or_none(row.get("expected_value")) is not None and float(row["expected_value"]) < 0
    ]
    best_bucket = fb_result.get("best_environment_bucket")
    next_actions = [
        "做 FB regime slicing，确认当前正向 edge 是否主要依赖 NEUTRAL bucket",
        "做 first-pullback purity audit，确认当前 detector 是否混入普通 PB 或 late continuation",
        "在 BOF_CONTROL 对照下评估 FB 的最简 exit decomposition，再判断是否进入更深阶段",
    ]

    conclusion = (
        "FB 当前已经通过第二个 alpha 候选门槛，但仍带有样本规模与环境依赖风险；"
        "下一步不应直接升主线，而应继续做 focused provenance。"
        if qualified
        else "FB 当前还未通过第二个 alpha 候选门槛；下一步优先继续做 detector refinement。"
    )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id"),
        "digest_summary_run_id": digest_payload.get("summary_run_id") if digest_payload else None,
        "matrix_path": matrix_payload.get("matrix_path"),
        "candidate_label": "FB",
        "control_label": "BOF_CONTROL",
        "qualification": qualification,
        "qualified_second_alpha_candidate": qualified,
        "candidate_summary": {
            "trade_count": _int_or_zero(fb_result.get("trade_count")),
            "expected_value": _float_or_none(fb_result.get("expected_value")),
            "profit_factor": _float_or_none(fb_result.get("profit_factor")),
            "max_drawdown": _float_or_none(fb_result.get("max_drawdown")),
            "participation_rate": _float_or_none(fb_result.get("participation_rate")),
            "overlap_rate_vs_bof_control": _float_or_none(fb_result.get("overlap_rate_vs_bof_control")),
            "incremental_buy_trades_vs_bof_control": _int_or_zero(
                fb_result.get("incremental_buy_trades_vs_bof_control")
            ),
        },
        "control_summary": {
            "trade_count": _int_or_zero(bof_result.get("trade_count")),
            "expected_value": _float_or_none(bof_result.get("expected_value")),
            "profit_factor": _float_or_none(bof_result.get("profit_factor")),
            "max_drawdown": _float_or_none(bof_result.get("max_drawdown")),
            "participation_rate": _float_or_none(bof_result.get("participation_rate")),
        },
        "bucket_breakdown": bucket_rows,
        "positive_buckets": positive_buckets,
        "negative_buckets": negative_buckets,
        "best_environment_bucket": best_bucket,
        "risk_flags": flags,
        "next_actions": next_actions,
        "conclusion": conclusion,
    }
