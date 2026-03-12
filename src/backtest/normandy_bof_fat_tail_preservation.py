from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.backtest.normandy_bof_exit import (
    NormandyBofExitVariant,
    _normalize_rows,
    _simulate_counterfactual_exit,
    _summarize_exit_rows,
    read_normandy_bof_control_exit_payload,
    resolve_normandy_bof_control_exit_variants,
    write_normandy_bof_control_exit_evidence,
)
from src.backtest.normandy_bof_trailing_stop import (
    _build_control_context,
    _float_or_zero,
    _lookup_by_signal,
)
from src.config import Settings

NORMANDY_BOF_CONTROL_FAT_TAIL_PRESERVATION_SCOPE = "normandy_bof_control_fat_tail_preservation"
DEFAULT_FAT_TAIL_PRESERVATION_VARIANT_LABELS = [
    "PROFIT_GATED_TRAIL_22_5P",
    "PROFIT_GATED_TRAIL_25P",
    "PROFIT_GATED_TRAIL_27_5P",
    "PROFIT_GATED_TRAIL_30P",
]


def build_normandy_bof_control_fat_tail_preservation_variants(
    config: Settings,
) -> list[NormandyBofExitVariant]:
    stop_loss_pct = float(config.stop_loss_pct)
    trailing_stop_pct = float(config.trailing_stop_pct)
    return [
        NormandyBofExitVariant(
            label="PROFIT_GATED_TRAIL_22_5P",
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct,
            trailing_activation_delay_trade_days=None,
            trailing_activation_profit_pct=0.225,
            notes="Keep current hard stop and current trail width, but do not activate trailing-stop until the trade has reached +22.5% unrealized profit.",
        ),
        NormandyBofExitVariant(
            label="PROFIT_GATED_TRAIL_25P",
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct,
            trailing_activation_delay_trade_days=None,
            trailing_activation_profit_pct=0.25,
            notes="Keep current hard stop and current trail width, but do not activate trailing-stop until the trade has reached +25% unrealized profit.",
        ),
        NormandyBofExitVariant(
            label="PROFIT_GATED_TRAIL_27_5P",
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct,
            trailing_activation_delay_trade_days=None,
            trailing_activation_profit_pct=0.275,
            notes="Keep current hard stop and current trail width, but do not activate trailing-stop until the trade has reached +27.5% unrealized profit.",
        ),
        NormandyBofExitVariant(
            label="PROFIT_GATED_TRAIL_30P",
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct,
            trailing_activation_delay_trade_days=None,
            trailing_activation_profit_pct=0.30,
            notes="Keep current hard stop and current trail width, but do not activate trailing-stop until the trade has reached +30% unrealized profit.",
        ),
    ]


def resolve_normandy_bof_control_fat_tail_preservation_variants(
    config: Settings,
    requested_labels: list[str] | None = None,
) -> list[NormandyBofExitVariant]:
    variants = build_normandy_bof_control_fat_tail_preservation_variants(config)
    labels = requested_labels or DEFAULT_FAT_TAIL_PRESERVATION_VARIANT_LABELS

    requested = {str(label).strip().upper() for label in labels if str(label).strip()}
    if not requested:
        return [variant for variant in variants if variant.label in DEFAULT_FAT_TAIL_PRESERVATION_VARIANT_LABELS]

    known = {variant.label for variant in variants}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(f"Unknown Normandy BOF fat-tail preservation variants: {', '.join(unknown)}")
    return [variant for variant in variants if variant.label in requested]


def _build_category_signal_ids(case_rows: list[dict[str, object]]) -> dict[str, set[str]]:
    signal_ids_by_category: dict[str, set[str]] = {}
    for row in case_rows:
        signal_id = str(row.get("signal_id") or "").strip()
        category = str(row.get("case_category") or "ambiguous_mixed").strip() or "ambiguous_mixed"
        if not signal_id:
            continue
        signal_ids_by_category.setdefault(category, set()).add(signal_id)
    signal_ids_by_category["all_trailing_stop_rows"] = {
        str(row.get("signal_id") or "").strip() for row in case_rows if str(row.get("signal_id") or "").strip()
    }
    return signal_ids_by_category


def _simulate_variant_rows(
    *,
    entries: list[dict[str, object]],
    context: dict[str, object],
    variant: NormandyBofExitVariant,
) -> list[dict[str, object]]:
    return [
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


def _subset_rows(rows: list[dict[str, object]], signal_ids: set[str]) -> list[dict[str, object]]:
    return [row for row in rows if str(row.get("signal_id") or "") in signal_ids]


def _build_subset_tradeoff(
    *,
    signal_ids: set[str],
    control_lookup: dict[str, dict[str, object]],
    candidate_lookup: dict[str, dict[str, object]],
    stop_only_lookup: dict[str, dict[str, object]],
) -> dict[str, object]:
    candidate_total_delta_vs_control = 0.0
    stop_only_total_delta_vs_control = 0.0
    candidate_improved_trade_count = 0
    candidate_worsened_trade_count = 0
    candidate_flat_trade_count = 0
    for signal_id in sorted(signal_ids):
        control = control_lookup.get(signal_id)
        candidate = candidate_lookup.get(signal_id)
        stop_only = stop_only_lookup.get(signal_id)
        if control is None or candidate is None or stop_only is None:
            continue
        candidate_delta = _float_or_zero(candidate.get("pnl")) - _float_or_zero(control.get("pnl"))
        stop_only_delta = _float_or_zero(stop_only.get("pnl")) - _float_or_zero(control.get("pnl"))
        candidate_total_delta_vs_control += candidate_delta
        stop_only_total_delta_vs_control += stop_only_delta
        if candidate_delta > 0:
            candidate_improved_trade_count += 1
        elif candidate_delta < 0:
            candidate_worsened_trade_count += 1
        else:
            candidate_flat_trade_count += 1

    capture_share_vs_stop_only = None
    protection_damage_share_vs_stop_only = None
    if stop_only_total_delta_vs_control > 0:
        capture_share_vs_stop_only = (
            None if candidate_total_delta_vs_control <= 0 else float(candidate_total_delta_vs_control / stop_only_total_delta_vs_control)
        )
    elif stop_only_total_delta_vs_control < 0:
        protection_damage_share_vs_stop_only = float(
            abs(candidate_total_delta_vs_control) / abs(stop_only_total_delta_vs_control)
        )

    return {
        "trade_count": int(len(signal_ids)),
        "candidate_total_pnl_delta_vs_control": float(candidate_total_delta_vs_control),
        "stop_only_total_pnl_delta_vs_control": float(stop_only_total_delta_vs_control),
        "capture_share_vs_stop_only": capture_share_vs_stop_only,
        "protection_damage_share_vs_stop_only": protection_damage_share_vs_stop_only,
        "candidate_improved_trade_count_vs_control": int(candidate_improved_trade_count),
        "candidate_worsened_trade_count_vs_control": int(candidate_worsened_trade_count),
        "candidate_flat_trade_count_vs_control": int(candidate_flat_trade_count),
    }


def run_normandy_bof_control_fat_tail_preservation(
    *,
    followup_payload: dict[str, object],
    config: Settings,
    variant_labels: list[str] | None = None,
) -> dict[str, object]:
    followup_status = str(followup_payload.get("followup_status") or "")
    if followup_status != "completed":
        raise ValueError("Fat-tail preservation requires a completed N2A trailing-stop follow-up payload")

    matrix_path = str(followup_payload.get("matrix_path") or "").strip()
    if not matrix_path:
        raise ValueError("followup_payload is missing matrix_path")
    matrix_payload = read_normandy_bof_control_exit_payload(matrix_path)
    matrix_payload["matrix_path"] = matrix_path
    context = _build_control_context(matrix_payload=matrix_payload, config=config)

    case_rows = followup_payload.get("trailing_stop_case_table")
    if not isinstance(case_rows, list):
        raise ValueError("followup_payload.trailing_stop_case_table must be a list")
    category_signal_ids = _build_category_signal_ids(case_rows)

    all_signal_ids = category_signal_ids["all_trailing_stop_rows"]
    control_rows = [
        row for row in context["control_rows"] if str(row.get("signal_id") or "") in all_signal_ids
    ]
    if not control_rows:
        raise ValueError("No trailing-stop control rows found for fat-tail preservation study")
    control_lookup = _lookup_by_signal(control_rows)

    stop_only_variant = resolve_normandy_bof_control_exit_variants(["STOP_ONLY"])[0]
    stop_only_rows = _simulate_variant_rows(entries=control_rows, context=context, variant=stop_only_variant)
    stop_only_lookup = _lookup_by_signal(stop_only_rows)

    candidate_variants = resolve_normandy_bof_control_fat_tail_preservation_variants(config, variant_labels)
    variant_payloads: list[dict[str, object]] = []
    stop_only_total_delta_vs_control = float(
        sum(_float_or_zero(stop.get("pnl")) - _float_or_zero(control_lookup[str(stop.get("signal_id") or "")].get("pnl")) for stop in stop_only_rows)
    )

    for variant in candidate_variants:
        candidate_rows = _simulate_variant_rows(entries=control_rows, context=context, variant=variant)
        candidate_lookup = _lookup_by_signal(candidate_rows)
        category_tradeoff = {
            category: _build_subset_tradeoff(
                signal_ids=signal_ids,
                control_lookup=control_lookup,
                candidate_lookup=candidate_lookup,
                stop_only_lookup=stop_only_lookup,
            )
            for category, signal_ids in category_signal_ids.items()
        }
        overall_total_delta = float(category_tradeoff["all_trailing_stop_rows"]["candidate_total_pnl_delta_vs_control"])
        overall_capture_share_vs_stop_only = None
        if stop_only_total_delta_vs_control > 0 and overall_total_delta > 0:
            overall_capture_share_vs_stop_only = float(overall_total_delta / stop_only_total_delta_vs_control)
        variant_payloads.append(
            {
                "label": variant.label,
                "notes": variant.notes,
                "stop_loss_pct": float(variant.stop_loss_pct),
                "trailing_stop_pct": float(variant.trailing_stop_pct),
                "trailing_activation_delay_trade_days": variant.trailing_activation_delay_trade_days,
                "trailing_activation_profit_pct": variant.trailing_activation_profit_pct,
                "overall_summary": _summarize_exit_rows(candidate_rows),
                "category_tradeoff": category_tradeoff,
                "overall_capture_share_vs_stop_only": overall_capture_share_vs_stop_only,
                "sample_rows": _normalize_rows(candidate_rows[:5]),
            }
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "preservation_status": "completed",
        "research_parent": "BOF_CONTROL",
        "preservation_focus": "fat_tail_preservation_mechanism_research",
        "followup_summary_run_id": followup_payload.get("summary_run_id") or followup_payload.get("followup_summary_run_id"),
        "followup_path": followup_payload.get("followup_path"),
        "matrix_path": matrix_path,
        "baseline_run_id": context["baseline_run_id"],
        "db_path": context["db_path"],
        "start": context["start"].isoformat(),
        "end": context["end"].isoformat(),
        "dtt_variant": followup_payload.get("dtt_variant") or matrix_payload.get("dtt_variant"),
        "control_trailing_stop_trade_count": int(len(control_rows)),
        "category_signal_counts": {key: int(len(value)) for key, value in category_signal_ids.items()},
        "control_summary": _summarize_exit_rows(control_rows),
        "stop_only_reference_summary": _summarize_exit_rows(stop_only_rows),
        "stop_only_reference_total_pnl_delta_vs_control": stop_only_total_delta_vs_control,
        "variants": variant_payloads,
    }


def build_normandy_bof_control_fat_tail_preservation_digest(
    preservation_payload: dict[str, object],
) -> dict[str, object]:
    preservation_status = str(preservation_payload.get("preservation_status") or "completed")
    if preservation_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "preservation_status": preservation_status,
            "decision": "rerun_fat_tail_preservation",
            "conclusion": "Fat-tail preservation readout 尚未完成，当前不能形成 targeted preservation verdict。",
        }

    variants = preservation_payload.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("preservation_payload.variants must be a non-empty list")

    ranked_variants: list[dict[str, object]] = []
    for item in variants:
        if not isinstance(item, dict):
            continue
        category_tradeoff = item.get("category_tradeoff")
        if not isinstance(category_tradeoff, dict):
            continue
        fat_tail = dict(category_tradeoff.get("fat_tail_winner_cut") or {})
        legitimate = dict(category_tradeoff.get("legitimate_protection") or {})
        overall = dict(category_tradeoff.get("all_trailing_stop_rows") or {})
        fat_tail_capture = _float_or_zero(fat_tail.get("capture_share_vs_stop_only"))
        protection_damage = legitimate.get("protection_damage_share_vs_stop_only")
        protection_damage = 1.0 if protection_damage is None else _float_or_zero(protection_damage)
        overall_capture = item.get("overall_capture_share_vs_stop_only")
        overall_capture = 0.0 if overall_capture is None else _float_or_zero(overall_capture)
        score = float((fat_tail_capture * 0.55) + (max(0.0, overall_capture) * 0.25) + (max(0.0, 1.0 - protection_damage) * 0.20))
        ranked_variants.append(
            {
                "label": item.get("label"),
                "fat_tail_capture_share_vs_stop_only": fat_tail_capture,
                "legitimate_protection_damage_share_vs_stop_only": protection_damage,
                "overall_capture_share_vs_stop_only": overall_capture,
                "overall_total_pnl_delta_vs_control": _float_or_zero(overall.get("candidate_total_pnl_delta_vs_control")),
                "preservation_score": score,
            }
        )

    ranked_variants.sort(key=lambda item: item["preservation_score"], reverse=True)
    best = ranked_variants[0]

    if (
        best["fat_tail_capture_share_vs_stop_only"] >= 0.35
        and best["legitimate_protection_damage_share_vs_stop_only"] <= 0.40
        and best["overall_capture_share_vs_stop_only"] >= 0.10
    ):
        diagnosis = "targeted_preservation_candidate_found"
        decision = "continue_mechanism_specific_follow_up"
        conclusion = (
            f"当前已经出现相对平衡的 targeted preservation 候选 `{best['label']}`，"
            "它在保留部分 fat-tail uplift 的同时，没有复制出 STOP_ONLY 级别的 protection damage。"
        )
    elif best["overall_total_pnl_delta_vs_control"] > 0 and best["fat_tail_capture_share_vs_stop_only"] >= 0.15:
        diagnosis = "partial_preservation_tradeoff_only"
        decision = "keep_research_narrow_and_do_not_rewrite_defaults"
        conclusion = (
            f"当前最好的 preservation 候选 `{best['label']}` 只给出部分 trade-off 改善，"
            "值得继续收窄研究，但还不支持把它翻译成默认语义改写。"
        )
    else:
        diagnosis = "no_clean_preservation_candidate_yet"
        decision = "hold_n2a_verdict_and_continue_only_if_new_targeted_hypothesis_exists"
        conclusion = (
            "当前没有出现足够干净的 fat-tail preservation 候选。"
            "N2A 的 outlier-truncation 结论保持成立，但还没有形成可以继续升格的 preservation mechanism。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "preservation_summary_run_id": preservation_payload.get("summary_run_id"),
        "preservation_status": preservation_status,
        "research_parent": preservation_payload.get("research_parent"),
        "preservation_focus": preservation_payload.get("preservation_focus"),
        "diagnosis": diagnosis,
        "decision": decision,
        "best_candidate_label": best["label"],
        "best_candidate_fat_tail_capture_share_vs_stop_only": best["fat_tail_capture_share_vs_stop_only"],
        "best_candidate_legitimate_protection_damage_share_vs_stop_only": best["legitimate_protection_damage_share_vs_stop_only"],
        "best_candidate_overall_capture_share_vs_stop_only": best["overall_capture_share_vs_stop_only"],
        "best_candidate_overall_total_pnl_delta_vs_control": best["overall_total_pnl_delta_vs_control"],
        "ranked_candidates": ranked_variants,
        "conclusion": conclusion,
        "next_actions": [
            "若出现 targeted_preservation_candidate_found，就继续围绕该具体 gate 语义做更细的 path readout。",
            "若只有 partial trade-off，就保持研究范围收窄，不把结果翻译成全局 trailing-stop 重写。",
            "若没有 clean candidate，就保留 N2A 的 outlier truncation 结论，等待新的 targeted hypothesis。",
        ],
    }


def read_normandy_bof_control_fat_tail_preservation_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_bof_control_fat_tail_preservation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    return write_normandy_bof_control_exit_evidence(output_path, payload)
