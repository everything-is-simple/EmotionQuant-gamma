from __future__ import annotations

from pathlib import Path

import pytest

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


def test_default_phase2_irs_factor_config_matches_card() -> None:
    cfg = Settings()
    assert cfg.irs_factor_mode == "rsrvrtbdgn"
    assert cfg.irs_rt_lookback_days == 5
    assert cfg.irs_top_rank_threshold == 3
    assert cfg.irs_factor_weight_rs == 0.30
    assert cfg.irs_factor_weight_rv == 0.25
    assert cfg.irs_factor_weight_rt == 0.15
    assert cfg.irs_factor_weight_bd == 0.15
    assert cfg.irs_factor_weight_gn == 0.15


def test_phase2_irs_factor_config_can_be_overridden_from_env_aliases() -> None:
    cfg = Settings(
        IRS_FACTOR_MODE="rsrv",
        IRS_RT_LOOKBACK_DAYS=7,
        IRS_TOP_RANK_THRESHOLD=2,
        IRS_FACTOR_WEIGHT_RS=0.4,
        IRS_FACTOR_WEIGHT_RV=0.3,
        IRS_FACTOR_WEIGHT_RT=0.1,
        IRS_FACTOR_WEIGHT_BD=0.1,
        IRS_FACTOR_WEIGHT_GN=0.1,
    )
    assert cfg.irs_factor_mode == "rsrv"
    assert cfg.irs_rt_lookback_days == 7
    assert cfg.irs_top_rank_threshold == 2
    assert cfg.irs_factor_weight_rs == 0.4
    assert cfg.irs_factor_weight_rv == 0.3
    assert cfg.irs_factor_weight_rt == 0.1
    assert cfg.irs_factor_weight_bd == 0.1
    assert cfg.irs_factor_weight_gn == 0.1


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
    assert cfg.dtt_variant == "v0_01_dtt_pattern_plus_irs_score"
    assert cfg.dtt_top_n == 50
    assert cfg.preselect_score_mode == "amount_plus_volume_ratio"


def test_dtt_pattern_variant_and_weight_use_canonical_names() -> None:
    cfg = Settings(
        DTT_VARIANT="v0_01_dtt_pattern_plus_irs_score",
        DTT_PATTERN_WEIGHT=0.45,
    )
    assert cfg.dtt_variant_normalized == "v0_01_dtt_pattern_plus_irs_score"
    assert cfg.dtt_pattern_weight == 0.45


def test_pas_priority_and_single_pattern_override() -> None:
    cfg = Settings(
        PAS_PATTERNS="bof,bpb,pb,tst,cpb",
        PAS_PATTERN_PRIORITY="pb,bpb",
        PAS_SINGLE_PATTERN_MODE="tst",
    )
    assert cfg.pas_pattern_priority_list == ["pb", "bpb", "tst", "cpb", "bof"]
    assert cfg.pas_effective_patterns == ["tst"]


@pytest.mark.smoke
def test_default_paths_follow_operations_directory_discipline() -> None:
    cfg = Settings(DATA_PATH="", TEMP_PATH="", LOG_PATH="")
    repo_drive = Path(__file__).resolve().drive

    if repo_drive:
        assert cfg.resolved_data_path == Path(f"{repo_drive}\\EmotionQuant_data").resolve()
        assert cfg.resolved_temp_path == Path(f"{repo_drive}\\EmotionQuant-temp").resolve()
    else:
        data_candidates = {
            Path("/data/emotionquant").resolve(),
            (Path.home() / ".emotionquant" / "data").resolve(),
        }
        temp_candidates = {
            Path("/tmp/emotionquant").resolve(),
            (Path.home() / ".emotionquant" / "temp").resolve(),
        }
        assert cfg.resolved_data_path in data_candidates
        assert cfg.resolved_temp_path in temp_candidates

    assert cfg.db_path == cfg.resolved_data_path / "emotionquant.duckdb"
