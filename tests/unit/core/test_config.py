from __future__ import annotations

from src.config import Settings


def test_default_min_amount_uses_tushare_thousand_yuan_unit() -> None:
    cfg = Settings()
    assert cfg.min_amount == 50_000
