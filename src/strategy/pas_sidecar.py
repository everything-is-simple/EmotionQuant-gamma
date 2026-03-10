from __future__ import annotations

import json

from src.config import Settings
from src.strategy.pas_support import EPS, clip

DEFAULT_PRIORITY = ["bpb", "pb", "tst", "cpb", "bof"]
PATTERN_GROUP = {
    "bof": "FALSE_BREAK_REVERSAL",
    "bpb": "BREAKOUT_PULLBACK",
    "pb": "TREND_PULLBACK",
    "tst": "SUPPORT_TEST",
    "cpb": "COMPLEX_BASE",
}
FAILURE_TAGS = {
    "bof": ("BOF_VOLUME_COLLAPSE", "BOF_BACK_BELOW_LOWER_BOUND", "BOF_NO_FOLLOW_THROUGH"),
    "bpb": ("BPB_WEAK_VOLUME", "BPB_LOSE_BREAKOUT_REF", "BPB_CONFIRM_FAIL"),
    "pb": ("PB_VOLUME_FAIL", "PB_LOSE_PULLBACK_LOW", "PB_TREND_NOT_RESUME"),
    "tst": ("TST_FALSE_REJECTION", "TST_SUPPORT_LOST", "TST_NO_BOUNCE"),
    "cpb": ("CPB_BREAKOUT_WEAK", "CPB_SUPPORT_BAND_LOST", "CPB_NECKLINE_FAIL"),
}


def _payload_float(payload: dict[str, object], key: str, default: float) -> float:
    value = payload.get(key, default)
    if value is None:
        return float(default)
    return float(value)


def build_registry_run_label(patterns: list[str], combination_mode: str, quality_enabled: bool) -> str:
    # registry_run_label 用来稳定标识“这次 PAS 到底是哪个组合在跑”，
    # 供 ablation / report / trace 直接做横向对比。
    normalized = [pattern.strip().lower() for pattern in patterns if pattern.strip()]
    if normalized == DEFAULT_PRIORITY:
        label = "YTC5_ANY" if combination_mode.upper() == "ANY" else f"YTC5_{combination_mode.upper()}"
    elif len(normalized) == 1:
        label = normalized[0].upper()
    else:
        label = f"{'+'.join(pattern.upper() for pattern in normalized)}_{combination_mode.upper()}"
    if quality_enabled:
        return f"{label} + quality"
    return label


def required_volume_mult(pattern: str, config: Settings) -> float:
    mapping = {
        "bof": config.pas_bof_volume_mult,
        "bpb": config.pas_bpb_volume_mult,
        "pb": config.pas_pb_volume_mult,
        "tst": config.pas_tst_volume_mult,
        "cpb": config.pas_cpb_volume_mult,
    }
    return float(mapping[pattern])


def compute_reference_layer(pattern: str, payload: dict[str, object]) -> dict[str, object]:
    """
    参考层计算（Phase 1 核心）：
    
    为每个形态计算：
    - entry_ref: 入场参考价（当日收盘）
    - stop_ref: 止损参考价（形态关键支撑 * 0.99）
    - target_ref: 目标参考价（结构高点或 1.5R）
    - risk_reward_ref: 风险回报比
    - failure_handling_tag: 失败处理标签（量能/支撑/延续）
    
    防御性设计：
    - 优先使用正式字段，缺失时退回等价观测
    - 避免因个别字段缺失导致整个 sidecar 失败
    """
    entry_ref = _payload_float(payload, "today_close", _payload_float(payload, "today_high", 0.0))
    lower_bound = _payload_float(payload, "lower_bound", _payload_float(payload, "today_low", entry_ref))
    today_low = _payload_float(payload, "today_low", entry_ref)
    lookback_high_20 = _payload_float(payload, "lookback_high_20", _payload_float(payload, "today_high", entry_ref))
    pullback_low = _payload_float(payload, "pullback_low", today_low)
    support_level = _payload_float(payload, "support_level", today_low)
    support_band_low = _payload_float(payload, "support_band_low", today_low)
    breakout_peak = _payload_float(payload, "breakout_peak", entry_ref)
    trend_peak = _payload_float(payload, "trend_peak", entry_ref)
    structure_high = _payload_float(payload, "structure_high", entry_ref)
    neckline_ref = _payload_float(payload, "neckline_ref", entry_ref)

    # 参考层统一输出 entry / stop / target，但它仍是解释层，
    # 不是 Broker 当前版本的硬执行输入。
    if pattern == "bof":
        stop_ref = min(today_low, lower_bound) * 0.99
    elif pattern in {"bpb", "pb"}:
        stop_ref = pullback_low * 0.99
    elif pattern == "tst":
        stop_ref = support_level * 0.99
    else:
        stop_ref = support_band_low * 0.99

    risk = max(entry_ref - stop_ref, EPS)
    if pattern == "bof":
        target_ref = max(lookback_high_20, entry_ref + 1.5 * risk)
    elif pattern == "bpb":
        target_ref = max(breakout_peak, entry_ref + 1.5 * risk)
    elif pattern == "pb":
        target_ref = max(trend_peak, entry_ref + 1.5 * risk)
    elif pattern == "tst":
        target_ref = max(structure_high, entry_ref + 1.5 * risk)
    else:
        target_ref = max(neckline_ref + (neckline_ref - support_band_low), entry_ref + 1.5 * risk)

    risk_reward_ref = float((target_ref - entry_ref) / risk)
    # failure_handling_tag 不是“今天失败了”，而是给后续报告一个最可能的失效管理标签。
    volume_ratio = _payload_float(payload, "volume_ratio", 0.0)
    required_mult = _payload_float(payload, "required_mult", 0.0)
    today_close = entry_ref

    if volume_ratio < required_mult * 1.05:
        failure_handling_tag = FAILURE_TAGS[pattern][0]
    elif risk_reward_ref < 1.5:
        failure_handling_tag = FAILURE_TAGS[pattern][1]
    elif pattern == "bof" and today_close <= lower_bound * 1.01:
        failure_handling_tag = FAILURE_TAGS[pattern][1]
    else:
        failure_handling_tag = FAILURE_TAGS[pattern][2]

    return {
        "entry_ref": entry_ref,
        "stop_ref": float(stop_ref),
        "target_ref": float(target_ref),
        "risk_reward_ref": risk_reward_ref,
        "failure_handling_tag": failure_handling_tag,
    }


def compute_pattern_quality(
    pattern: str,
    payload: dict[str, object],
    reference: dict[str, object],
    config: Settings,
) -> dict[str, object]:
    """
    形态质量评分（Phase 1 核心）：
    
    四维度评分：
    1. structure_clarity (35%): 形态结构清晰度（各形态专属公式）
    2. volume_confirmation (25%): 量能确认强度
    3. position_advantage (20%): 风险回报比优势
    4. failure_risk (20%): 失败风险扣分（历史缓冲/量能边际/RR/结构宽度）
    
    最终得分 = 加权平均，范围 [0, 100]
    
    输出：
    - pattern_quality_score: 总分
    - quality_breakdown_json: 分项明细（JSON 字符串）
    """
    volume_ratio = _payload_float(payload, "volume_ratio", 0.0)
    required_mult = required_volume_mult(pattern, config)
    current_close = _payload_float(payload, "today_close", 0.0)
    current_low = _payload_float(payload, "today_low", current_close)
    current_high = _payload_float(payload, "today_high", current_close)

    if pattern == "bof":
        reclaim_score = clip(
            (current_close - _payload_float(payload, "lower_bound", 1.0))
            / max(0.05 * _payload_float(payload, "lower_bound", 1.0), EPS)
        )
        structure_clarity = 100.0 * (
            0.45 * _payload_float(payload, "close_pos", 0.0)
            + 0.30 * _payload_float(payload, "body_ratio", 0.0)
            + 0.25 * reclaim_score
        )
    elif pattern == "bpb":
        structure_clarity = 100.0 * (
            0.45 * _payload_float(payload, "confirm_strength", 0.0)
            + 0.30 * _payload_float(payload, "support_hold_score", 0.0)
            + 0.25 * _payload_float(payload, "depth_score", 0.0)
        )
    elif pattern == "pb":
        structure_clarity = 100.0 * (
            0.45 * _payload_float(payload, "rebound_strength", 0.0)
            + 0.30 * _payload_float(payload, "depth_quality", 0.0)
            + 0.25 * _payload_float(payload, "trend_quality", 0.0)
        )
    elif pattern == "tst":
        structure_clarity = 100.0 * (
            0.45 * _payload_float(payload, "support_closeness", 0.0)
            + 0.30 * _payload_float(payload, "bounce_strength", 0.0)
            + 0.25 * _payload_float(payload, "rejection_strength", 0.0)
        )
    else:
        structure_clarity = 100.0 * (
            0.45 * _payload_float(payload, "neckline_strength", 0.0)
            + 0.30 * _payload_float(payload, "retest_quality", 0.0)
            + 0.25 * _payload_float(payload, "compression_quality", 0.0)
        )

    volume_confirmation = min(100.0, 100.0 * clip(volume_ratio / max(required_mult, EPS), 0.0, 1.2))
    risk_reward_ref = float(reference["risk_reward_ref"])
    position_advantage = 100.0 * clip((risk_reward_ref - 1.0) / 1.0)

    deductions: list[dict[str, object]] = []
    # quality 里把常见“边缘触发”风险显式扣出来，避免高 strength 但低可交易性的票被误读。
    required_window = int(payload.get("required_window") or 0)
    if int(payload.get("history_days") or 0) < required_window + 5:
        deductions.append({"tag": "LOW_HISTORY_BUFFER", "penalty": 30})
    if volume_ratio < required_mult * 1.05:
        deductions.append({"tag": "VOLUME_EDGE_TOO_THIN", "penalty": 20})
    if risk_reward_ref < 1.5:
        deductions.append({"tag": "RR_TOO_THIN", "penalty": 25})
    if (current_high - current_low) / max(current_close, EPS) > 0.12:
        deductions.append({"tag": "STRUCTURE_TOO_WIDE", "penalty": 15})

    failure_risk = min(100, sum(int(item["penalty"]) for item in deductions))
    pattern_quality_score = (
        0.35 * structure_clarity
        + 0.25 * volume_confirmation
        + 0.20 * position_advantage
        + 0.20 * (100.0 - failure_risk)
    )
    breakdown = {
        "structure_clarity": round(structure_clarity, 6),
        "volume_confirmation": round(volume_confirmation, 6),
        "position_advantage": round(position_advantage, 6),
        "failure_risk": round(float(failure_risk), 6),
        "deductions": deductions,
    }
    return {
        "pattern_quality_score": round(float(pattern_quality_score), 6),
        "quality_breakdown_json": json.dumps(breakdown, ensure_ascii=False, sort_keys=True),
    }
