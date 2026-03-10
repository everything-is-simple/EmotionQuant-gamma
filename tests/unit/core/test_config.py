from __future__ import annotations

from src.config import Settings


def test_default_min_amount_uses_tushare_thousand_yuan_unit() -> None:
    cfg = Settings()
    assert cfg.min_amount == 50_000


def test_default_pas_min_history_days_is_30() -> None:
    cfg = Settings()
    assert cfg.pas_min_history_days == 30


def test_default_irs_min_industries_per_day_is_25() -> None:
    cfg = Settings()
    assert cfg.irs_min_industries_per_day == 25


def test_default_mss_thresholds_match_v001_gate() -> None:
    cfg = Settings()
    assert cfg.mss_bullish_threshold == 65.0
    assert cfg.mss_bearish_threshold == 35.0


def test_default_mss_gate_mode_and_soft_gate_limit() -> None:
    cfg = Settings()
    assert cfg.mss_variant == "zscore_weighted6"
    assert cfg.mss_gate_mode == "bearish_only"
    assert cfg.mss_soft_gate_candidate_top_n == 30


def test_default_pipeline_mode_uses_dtt_mainline() -> None:
    cfg = Settings()
    assert cfg.use_dtt_pipeline is True
    assert cfg.pipeline_mode_normalized == "dtt"
    assert cfg.dtt_variant == "v0_01_dtt_bof_plus_irs_score"
    assert cfg.dtt_top_n == 50
    assert cfg.preselect_score_mode == "amount_plus_volume_ratio"


def test_pas_priority_and_single_pattern_override() -> None:
    cfg = Settings(
        PAS_PATTERNS="bof,bpb,pb,tst,cpb",
        PAS_PATTERN_PRIORITY="pb,bpb",
        PAS_SINGLE_PATTERN_MODE="tst",
    )
    assert cfg.pas_pattern_priority_list == ["pb", "bpb", "tst", "cpb", "bof"]
    assert cfg.pas_effective_patterns == ["tst"]
