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
