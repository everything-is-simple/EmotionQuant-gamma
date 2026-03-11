from __future__ import annotations

from src.backtest.replay_variants import (
    LEGACY_BASELINE_VARIANT,
    apply_replay_variant_runtime,
    is_legacy_replay_variant,
)
from src.config import Settings
from src.strategy.ranker import MSS_CARRYOVER_BUFFER_VARIANT


def test_apply_replay_variant_runtime_restores_legacy_pipeline_semantics() -> None:
    cfg = Settings(
        PIPELINE_MODE="dtt",
        DTT_VARIANT=MSS_CARRYOVER_BUFFER_VARIANT,
        MSS_MAX_POSITIONS_MODE="carryover_buffer",
        MSS_MAX_POSITIONS_BUFFER_SLOTS=1,
    )

    runtime_cfg = apply_replay_variant_runtime(cfg, LEGACY_BASELINE_VARIANT)

    assert is_legacy_replay_variant(LEGACY_BASELINE_VARIANT) is True
    assert runtime_cfg.pipeline_mode == "legacy"
    assert runtime_cfg.enable_dtt_mode is False
    assert runtime_cfg.dtt_variant_normalized == LEGACY_BASELINE_VARIANT
    assert runtime_cfg.mss_max_positions_mode_normalized == "hard_cap"
    assert runtime_cfg.mss_max_positions_buffer_slots == 0


def test_apply_replay_variant_runtime_keeps_dtt_alias_runtime_override() -> None:
    cfg = Settings(
        PIPELINE_MODE="legacy",
        DTT_VARIANT=LEGACY_BASELINE_VARIANT,
        MSS_MAX_POSITIONS_MODE="hard_cap",
        MSS_MAX_POSITIONS_BUFFER_SLOTS=0,
    )

    runtime_cfg = apply_replay_variant_runtime(cfg, MSS_CARRYOVER_BUFFER_VARIANT)

    assert runtime_cfg.pipeline_mode == "dtt"
    assert runtime_cfg.enable_dtt_mode is True
    assert runtime_cfg.dtt_variant_normalized == MSS_CARRYOVER_BUFFER_VARIANT
    assert runtime_cfg.mss_max_positions_mode_normalized == "carryover_buffer"
    assert runtime_cfg.mss_max_positions_buffer_slots == 1
