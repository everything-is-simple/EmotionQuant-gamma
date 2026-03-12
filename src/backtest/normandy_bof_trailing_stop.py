from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import duckdb

from src.backtest.normandy_bof_exit import (
    BASELINE_PAIRED_TRADES_QUERY,
    _build_realized_control_rows,
    _load_market_bars,
    _load_trade_calendar,
    _normalize_rows,
    _query_dicts,
    _summarize_exit_rows,
    _to_date,
    resolve_normandy_bof_control_exit_variants,
    write_normandy_bof_control_exit_evidence,
    _simulate_counterfactual_exit,
)
from src.broker.matcher import Matcher
from src.config import Settings

NORMANDY_BOF_CONTROL_TRAILING_STOP_SCOPE = "normandy_bof_control_trailing_stop_followup"
DEFAULT_TRAILING_STOP_VARIANT_LABELS = ["LOOSE_EXIT", "STOP_ONLY", "TRAIL_ONLY"]


def _float_or_zero(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _int_or_zero(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _build_control_context(
    *,
    matrix_payload: dict[str, object],
    config: Settings,
) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "")
    if matrix_status != "completed":
        raise ValueError("Trailing-stop follow-up requires a completed BOF control exit matrix payload")

    baseline_run_id = str(matrix_payload.get("baseline_run_id") or "").strip()
    if not baseline_run_id:
        raise ValueError("matrix_payload is missing baseline_run_id")

    db_path = Path(str(matrix_payload.get("db_path") or "")).expanduser().resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"Baseline working DB not found: {db_path}")

    start = _to_date(matrix_payload.get("start"))
    end = _to_date(matrix_payload.get("end"))
    if start is None or end is None:
        raise ValueError("matrix_payload must include start/end dates")

    matcher = Matcher(config)
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        paired_rows = _query_dicts(
            connection,
            BASELINE_PAIRED_TRADES_QUERY,
            [baseline_run_id, baseline_run_id, baseline_run_id, baseline_run_id],
        )
        if not paired_rows:
            raise ValueError("No paired BOF_CONTROL trades found in baseline working DB")
        calendar_start = min(_to_date(row.get("entry_date")) for row in paired_rows if _to_date(row.get("entry_date")) is not None)
        if calendar_start is None:
            raise ValueError("Unable to resolve calendar_start from paired BOF_CONTROL trades")
        trade_days, next_trade_day, trade_day_index = _load_trade_calendar(connection, calendar_start, end)
        codes = sorted({str(row.get("code") or "") for row in paired_rows if str(row.get("code") or "")})
        market_bars = _load_market_bars(connection, codes, calendar_start, end)
    finally:
        connection.close()

    control_rows = _build_realized_control_rows(paired_rows, matcher, trade_day_index)
    control_lookup = {str(row.get("signal_id") or ""): row for row in control_rows}
    return {
        "db_path": str(db_path),
        "baseline_run_id": baseline_run_id,
        "start": start,
        "end": end,
        "matcher": matcher,
        "trade_days": trade_days,
        "next_trade_day": next_trade_day,
        "trade_day_index": trade_day_index,
        "market_bars": market_bars,
        "control_rows": control_rows,
        "control_lookup": control_lookup,
    }


def _build_variant_rows_for_entries(
    *,
    entries: list[dict[str, object]],
    context: dict[str, object],
    requested_variant_labels: list[str] | None = None,
) -> dict[str, list[dict[str, object]]]:
    variants = resolve_normandy_bof_control_exit_variants(requested_variant_labels or DEFAULT_TRAILING_STOP_VARIANT_LABELS)
    rows_by_label: dict[str, list[dict[str, object]]] = {}
    for variant in variants:
        rows_by_label[variant.label] = [
            _simulate_counterfactual_exit(
                entry=entry,
                bars_by_date=context["market_bars"].get(str(entry.get("code") or ""), {}),
                trade_days=context["trade_days"],
                next_trade_day=context["next_trade_day"],
                trade_day_index=context["trade_day_index"],
                matcher=context["matcher"],
                variant=variant,
                end=context["end"],
            )
            for entry in entries
        ]
    return rows_by_label


def _lookup_by_signal(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("signal_id") or ""): row for row in rows}


def _classify_trailing_stop_case(case: dict[str, object]) -> tuple[str, str]:
    stop_delta_pct = _float_or_zero(case.get("stop_only_pnl_pct_delta_vs_control"))
    stop_delta_pnl = _float_or_zero(case.get("stop_only_pnl_delta_vs_control"))
    stop_timing_delta = _int_or_zero(case.get("stop_only_exit_timing_delta_trade_days"))
    stop_exit_reason = str(case.get("stop_only_exit_reason") or "UNKNOWN")
    loose_delta_pnl = _float_or_zero(case.get("loose_exit_pnl_delta_vs_control"))
    loose_timing_delta = _int_or_zero(case.get("loose_exit_timing_delta_trade_days"))
    trail_only_delta_pnl = _float_or_zero(case.get("trail_only_pnl_delta_vs_control"))

    if stop_delta_pnl <= 0 and loose_delta_pnl <= 0:
        return (
            "legitimate_protection",
            "Removing or loosening trailing-stop did not improve this trade; current trailing-stop likely protected capital or avoided later damage.",
        )
    if stop_exit_reason == "FORCE_CLOSE" and stop_delta_pct >= 0.50 and stop_timing_delta >= 40 and trail_only_delta_pnl <= 0:
        return (
            "fat_tail_winner_cut",
            "Disabling trailing-stop turned this trade into a much later force-close winner while keeping trailing-only did not help, indicating premature truncation of a fat-tail winner.",
        )
    if stop_delta_pct >= 0.12 and loose_delta_pnl > 0 and loose_timing_delta >= 10 and trail_only_delta_pnl <= 0:
        return (
            "repeatable_trend_premature_exit",
            "Both removing and loosening trailing-stop improved the path, suggesting the current trailing-stop is exiting trend continuation too early.",
        )
    return (
        "ambiguous_mixed",
        "The alternative paths are directionally mixed or too concentrated to classify as clear protection or clear premature trend exit.",
    )


def _build_trailing_stop_case_row(
    *,
    control_row: dict[str, object],
    stop_only_row: dict[str, object] | None,
    loose_row: dict[str, object] | None,
    trail_only_row: dict[str, object] | None,
    trade_day_index: dict[date, int],
) -> dict[str, object]:
    control_exit_date = _to_date(control_row.get("exit_date"))
    control_idx = None if control_exit_date is None else trade_day_index.get(control_exit_date)

    def _candidate_metrics(candidate: dict[str, object] | None, prefix: str) -> dict[str, object]:
        if candidate is None:
            return {
                f"{prefix}_exit_date": None,
                f"{prefix}_exit_reason": None,
                f"{prefix}_pnl": None,
                f"{prefix}_pnl_pct": None,
                f"{prefix}_pnl_delta_vs_control": None,
                f"{prefix}_pnl_pct_delta_vs_control": None,
                f"{prefix}_exit_timing_delta_trade_days": None,
            }
        candidate_exit_date = _to_date(candidate.get("exit_date"))
        candidate_idx = None if candidate_exit_date is None else trade_day_index.get(candidate_exit_date)
        candidate_pnl = _float_or_zero(candidate.get("pnl"))
        control_pnl = _float_or_zero(control_row.get("pnl"))
        candidate_pnl_pct = _float_or_zero(candidate.get("pnl_pct"))
        control_pnl_pct = _float_or_zero(control_row.get("pnl_pct"))
        return {
            f"{prefix}_exit_date": None if candidate_exit_date is None else candidate_exit_date.isoformat(),
            f"{prefix}_exit_reason": str(candidate.get("exit_reason") or "UNKNOWN"),
            f"{prefix}_pnl": candidate_pnl,
            f"{prefix}_pnl_pct": candidate_pnl_pct,
            f"{prefix}_pnl_delta_vs_control": float(candidate_pnl - control_pnl),
            f"{prefix}_pnl_pct_delta_vs_control": float(candidate_pnl_pct - control_pnl_pct),
            f"{prefix}_exit_timing_delta_trade_days": None
            if candidate_idx is None or control_idx is None
            else int(candidate_idx - control_idx),
        }

    case = {
        "signal_id": str(control_row.get("signal_id") or ""),
        "code": str(control_row.get("code") or ""),
        "entry_date": str(control_row.get("entry_date") or ""),
        "control_exit_date": None if control_exit_date is None else control_exit_date.isoformat(),
        "control_exit_reason": str(control_row.get("exit_reason") or "UNKNOWN"),
        "control_hold_trade_days": control_row.get("hold_trade_days"),
        "control_pnl": _float_or_zero(control_row.get("pnl")),
        "control_pnl_pct": _float_or_zero(control_row.get("pnl_pct")),
    }
    case.update(_candidate_metrics(stop_only_row, "stop_only"))
    case.update(_candidate_metrics(loose_row, "loose_exit"))
    case.update(_candidate_metrics(trail_only_row, "trail_only"))
    category, rationale = _classify_trailing_stop_case(case)
    case["case_category"] = category
    case["case_rationale"] = rationale
    return case


def _build_path_report(case_rows: list[dict[str, object]]) -> dict[str, object]:
    category_counts: dict[str, int] = {}
    category_stop_only_delta: dict[str, float] = {}
    positive_cases = sorted(
        (row for row in case_rows if _float_or_zero(row.get("stop_only_pnl_delta_vs_control")) > 0),
        key=lambda row: _float_or_zero(row.get("stop_only_pnl_delta_vs_control")),
        reverse=True,
    )
    negative_cases = sorted(
        (row for row in case_rows if _float_or_zero(row.get("stop_only_pnl_delta_vs_control")) < 0),
        key=lambda row: _float_or_zero(row.get("stop_only_pnl_delta_vs_control")),
    )
    for row in case_rows:
        category = str(row.get("case_category") or "ambiguous_mixed")
        category_counts[category] = category_counts.get(category, 0) + 1
        category_stop_only_delta[category] = category_stop_only_delta.get(category, 0.0) + _float_or_zero(
            row.get("stop_only_pnl_delta_vs_control")
        )
    return {
        "category_counts": category_counts,
        "category_stop_only_pnl_delta_vs_control": category_stop_only_delta,
        "positive_stop_only_case_count": len(positive_cases),
        "negative_stop_only_case_count": len(negative_cases),
        "top_positive_stop_only_cases": _normalize_rows(positive_cases[:10]),
        "top_negative_stop_only_cases": _normalize_rows(negative_cases[:10]),
        "top_fat_tail_winner_cut_cases": _normalize_rows(
            [row for row in positive_cases if str(row.get("case_category") or "") == "fat_tail_winner_cut"][:10]
        ),
        "top_repeatable_trend_cases": _normalize_rows(
            [row for row in positive_cases if str(row.get("case_category") or "") == "repeatable_trend_premature_exit"][:10]
        ),
        "top_legitimate_protection_cases": _normalize_rows(
            [row for row in negative_cases if str(row.get("case_category") or "") == "legitimate_protection"][:10]
        ),
    }


def run_normandy_bof_control_trailing_stop_followup(
    *,
    matrix_payload: dict[str, object],
    config: Settings,
    variant_labels: list[str] | None = None,
) -> dict[str, object]:
    context = _build_control_context(matrix_payload=matrix_payload, config=config)
    control_rows = context["control_rows"]
    trailing_stop_rows = [
        row for row in control_rows if str(row.get("exit_reason") or "UNKNOWN") == "TRAILING_STOP"
    ]
    variant_rows_by_label = _build_variant_rows_for_entries(
        entries=trailing_stop_rows,
        context=context,
        requested_variant_labels=variant_labels,
    )
    variant_lookup_by_label = {label: _lookup_by_signal(rows) for label, rows in variant_rows_by_label.items()}

    case_rows = []
    for control_row in trailing_stop_rows:
        signal_id = str(control_row.get("signal_id") or "")
        case_rows.append(
            _build_trailing_stop_case_row(
                control_row=control_row,
                stop_only_row=variant_lookup_by_label.get("STOP_ONLY", {}).get(signal_id),
                loose_row=variant_lookup_by_label.get("LOOSE_EXIT", {}).get(signal_id),
                trail_only_row=variant_lookup_by_label.get("TRAIL_ONLY", {}).get(signal_id),
                trade_day_index=context["trade_day_index"],
            )
        )

    path_report = _build_path_report(case_rows)
    variant_summaries = {
        label: _summarize_exit_rows(rows) for label, rows in variant_rows_by_label.items()
    }
    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "followup_status": "completed",
        "research_parent": "BOF_CONTROL",
        "followup_focus": "targeted_trailing_stop_path_decomposition",
        "matrix_summary_run_id": matrix_payload.get("summary_run_id") or matrix_payload.get("matrix_summary_run_id"),
        "matrix_path": matrix_payload.get("matrix_path"),
        "baseline_run_id": context["baseline_run_id"],
        "db_path": context["db_path"],
        "start": context["start"].isoformat(),
        "end": context["end"].isoformat(),
        "dtt_variant": matrix_payload.get("dtt_variant"),
        "control_trade_count": int(len(control_rows)),
        "control_trailing_stop_trade_count": int(len(trailing_stop_rows)),
        "requested_variant_labels": list(variant_rows_by_label.keys()),
        "control_trailing_stop_summary": _summarize_exit_rows(trailing_stop_rows),
        "variant_trailing_stop_summaries": variant_summaries,
        "path_report": path_report,
        "trailing_stop_case_table": _normalize_rows(case_rows),
    }


def build_normandy_bof_control_trailing_stop_digest(followup_payload: dict[str, object]) -> dict[str, object]:
    followup_status = str(followup_payload.get("followup_status") or "completed")
    if followup_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "followup_status": followup_status,
            "decision": "rerun_trailing_stop_followup",
            "conclusion": "Trailing-stop follow-up 尚未完成，当前不能形成 targeted readout。",
        }

    case_rows = followup_payload.get("trailing_stop_case_table")
    if not isinstance(case_rows, list):
        raise ValueError("followup_payload.trailing_stop_case_table must be a list")
    path_report = followup_payload.get("path_report")
    if not isinstance(path_report, dict):
        raise ValueError("followup_payload.path_report must be a dict")

    total_cases = int(len(case_rows))
    positive_cases = sorted(
        (_float_or_zero(row.get("stop_only_pnl_delta_vs_control")) for row in case_rows if _float_or_zero(row.get("stop_only_pnl_delta_vs_control")) > 0),
        reverse=True,
    )
    total_positive_delta = float(sum(positive_cases))
    top10_positive_delta = float(sum(positive_cases[:10]))
    top10_share = 0.0 if total_positive_delta <= 0 else float(top10_positive_delta / total_positive_delta)

    category_counts = {
        str(key): int(value) for key, value in dict(path_report.get("category_counts") or {}).items()
    }
    category_delta = {
        str(key): _float_or_zero(value) for key, value in dict(path_report.get("category_stop_only_pnl_delta_vs_control") or {}).items()
    }
    fat_tail_count = category_counts.get("fat_tail_winner_cut", 0)
    repeatable_count = category_counts.get("repeatable_trend_premature_exit", 0)
    legitimate_count = category_counts.get("legitimate_protection", 0)
    fat_tail_delta_share = 0.0 if total_positive_delta <= 0 else float(category_delta.get("fat_tail_winner_cut", 0.0) / total_positive_delta)
    repeatable_delta_share = 0.0 if total_positive_delta <= 0 else float(category_delta.get("repeatable_trend_premature_exit", 0.0) / total_positive_delta)

    if total_positive_delta <= 0 or (fat_tail_count + repeatable_count) == 0:
        diagnosis = "not_robust_enough_to_act"
        decision = "hold_current_mixed_verdict"
        conclusion = "当前 trailing-stop follow-up 没有形成足够稳的正向结构证据，baseline lane 暂时维持 mixed verdict。"
    elif fat_tail_count <= max(10, int(total_cases * 0.15)) and top10_share >= 0.60 and fat_tail_delta_share >= 0.50:
        diagnosis = "small_cluster_of_outlier_truncation"
        decision = "investigate_fat_tail_preservation_before_global_change"
        conclusion = "当前 trailing-stop 伤害更像少数 fat-tail winners 被提前砍掉，而不是整条路径都 uniformly 卖坏。"
    elif repeatable_count >= max(12, int(total_cases * 0.25)) and repeatable_delta_share >= 0.40:
        diagnosis = "repeatable_trend_premature_exit_pattern"
        decision = "prioritize_targeted_trailing_semantics_follow_up"
        conclusion = "当前 trailing-stop 伤害更像可重复的 trend-premature-exit 模式，值得继续做 targeted trailing semantics follow-up。"
    else:
        diagnosis = "mixed_trailing_stop_damage"
        decision = "keep_targeted_follow_up_without_global_rewrite"
        conclusion = "当前 trailing-stop 伤害既不只是极少 outlier，也还不够稳到支持全局重写；更合理的是继续 targeted follow-up。"

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "followup_summary_run_id": followup_payload.get("summary_run_id") or followup_payload.get("matrix_summary_run_id"),
        "followup_status": followup_status,
        "research_parent": followup_payload.get("research_parent"),
        "followup_focus": followup_payload.get("followup_focus"),
        "diagnosis": diagnosis,
        "decision": decision,
        "trailing_stop_case_count": total_cases,
        "positive_stop_only_delta_total": total_positive_delta,
        "top10_positive_delta_share": top10_share,
        "fat_tail_winner_cut_count": fat_tail_count,
        "repeatable_trend_premature_exit_count": repeatable_count,
        "legitimate_protection_count": legitimate_count,
        "fat_tail_winner_cut_delta_share": fat_tail_delta_share,
        "repeatable_trend_delta_share": repeatable_delta_share,
        "conclusion": conclusion,
        "next_actions": [
            "若 diagnosis 指向 outlier truncation，就继续做 fat-tail preservation 方向的 targeted decomposition。",
            "若 diagnosis 指向 repeatable trend pattern，就继续做 trailing-stop semantics follow-up，而不是直接改写主线。",
            "保持 N2 promotion lane 继续锁住，不把 targeted trailing-stop follow-up 误读成 branch promotion。",
        ],
        "top_fat_tail_cases": path_report.get("top_fat_tail_winner_cut_cases"),
        "top_repeatable_cases": path_report.get("top_repeatable_trend_cases"),
        "top_legitimate_protection_cases": path_report.get("top_legitimate_protection_cases"),
    }


def read_normandy_bof_control_trailing_stop_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_bof_control_trailing_stop_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    return write_normandy_bof_control_exit_evidence(output_path, payload)
