from __future__ import annotations

from src.config import Settings
from src.strategy.pas_sidecar import compute_pattern_quality, compute_reference_layer


def test_compute_reference_layer_bof_falls_back_when_optional_fields_are_missing() -> None:
    payload = {
        "today_close": 10.5,
        "today_high": 10.8,
        "today_low": 10.0,
        "lower_bound": 9.9,
        "volume_ratio": 1.4,
        "required_mult": 1.2,
    }

    reference = compute_reference_layer("bof", payload)

    assert reference["entry_ref"] == 10.5
    assert reference["stop_ref"] > 0
    assert reference["target_ref"] >= 10.5
    assert reference["risk_reward_ref"] > 0


def test_compute_pattern_quality_bof_falls_back_when_body_ratio_is_missing() -> None:
    payload = {
        "today_close": 10.5,
        "today_high": 10.8,
        "today_low": 10.0,
        "lower_bound": 9.9,
        "close_pos": 0.7,
        "volume_ratio": 1.4,
        "history_days": 30,
        "required_window": 20,
    }
    reference = compute_reference_layer("bof", payload)

    quality = compute_pattern_quality("bof", payload, reference, Settings())

    assert quality["pattern_quality_score"] > 0
    assert quality["quality_breakdown_json"] is not None
