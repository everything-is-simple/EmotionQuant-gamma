from __future__ import annotations

from src.config import Settings
from src.strategy.ranker import DTT_VARIANTS, MSS_OVERLAY_DTT_VARIANT, apply_dtt_variant_runtime

LEGACY_BASELINE_VARIANT = "legacy_bof_baseline"
REPLAY_VARIANTS = frozenset({LEGACY_BASELINE_VARIANT, *DTT_VARIANTS.keys()})


def is_legacy_replay_variant(label: str) -> bool:
    return label.strip().lower() == LEGACY_BASELINE_VARIANT


def apply_replay_variant_runtime(cfg: Settings, label: str) -> Settings:
    normalized = label.strip().lower()
    if is_legacy_replay_variant(normalized):
        # Gate replay 允许把 frozen legacy baseline 和当前 DTT 候选放进同一组对照里。
        # legacy 不消费 DTT rank sidecar，因此这里显式回到历史 pipeline 语义，
        # 同时把 Broker shrink alias 复位到 hard_cap，避免 carryover_buffer 等 DTT 运行态串进去。
        cfg.pipeline_mode = "legacy"
        cfg.enable_dtt_mode = False
        cfg.dtt_variant = LEGACY_BASELINE_VARIANT
        cfg.enable_mss_gate = True
        cfg.enable_irs_filter = True
        cfg.mss_risk_overlay_variant = MSS_OVERLAY_DTT_VARIANT
        cfg.mss_max_positions_mode = "hard_cap"
        cfg.mss_max_positions_buffer_slots = 0
        return cfg

    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    return apply_dtt_variant_runtime(cfg, normalized)
