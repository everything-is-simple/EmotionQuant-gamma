from __future__ import annotations

from src.config import Settings


def test_default_min_amount_uses_tushare_thousand_yuan_unit() -> None:
    cfg = Settings()
    assert cfg.min_amount == 50_000


def test_default_pas_min_history_days_is_30() -> None:
    cfg = Settings()
    assert cfg.pas_min_history_days == 30
