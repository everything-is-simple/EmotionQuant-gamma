from __future__ import annotations

from datetime import date

import pandas as pd

from src.report.market_lifespan_report import (
    build_market_lifespan_report_payload,
    write_market_lifespan_report_bundle,
)


def _surface_row(
    surface_label: str,
    *,
    regime_label: str,
    wave_role: str,
    amplitude_metric_name: str,
    sample_size: int,
    current_wave_matches_surface: bool,
    current_wave_joint_percentile: float | None,
    current_wave_average_remaining_prob: float | None,
    current_wave_average_aged_prob: float | None,
    current_wave_remaining_vs_aged_odds: float | None,
) -> dict[str, object]:
    return {
        "surface_label": surface_label,
        "market_regime_label": regime_label,
        "wave_role": wave_role,
        "amplitude_metric_name": amplitude_metric_name,
        "history_reference_trade_days": 1260,
        "sample_size": sample_size,
        "sample_first_wave_start_date": date(2020, 1, 1),
        "sample_last_wave_end_date": date(2026, 3, 20),
        "amplitude_min": 4.0,
        "amplitude_q25": 10.0,
        "amplitude_q50": 18.0,
        "amplitude_q75": 27.0,
        "amplitude_max": 48.0,
        "duration_min": 16.0,
        "duration_q25": 40.0,
        "duration_q50": 92.0,
        "duration_q75": 158.0,
        "duration_max": 342.0,
        "current_wave_matches_surface": current_wave_matches_surface,
        "current_wave_amplitude_percentile": 62.0 if current_wave_matches_surface else None,
        "current_wave_duration_percentile": 68.0 if current_wave_matches_surface else None,
        "current_wave_joint_percentile": current_wave_joint_percentile,
        "current_wave_average_remaining_prob": current_wave_average_remaining_prob,
        "current_wave_average_aged_prob": current_wave_average_aged_prob,
        "current_wave_remaining_vs_aged_odds": current_wave_remaining_vs_aged_odds,
        "current_wave_aged_vs_remaining_odds": (
            None
            if current_wave_remaining_vs_aged_odds in (None, 0.0)
            else 1.0 / float(current_wave_remaining_vs_aged_odds)
        ),
        "entity_name": "000300.SH",
    }


def test_market_lifespan_report_bundle_writes_markdown_png_and_json(tmp_path) -> None:
    frame = pd.DataFrame(
        [
            _surface_row(
                "BULL_MAINSTREAM",
                regime_label="BULL",
                wave_role="MAINSTREAM",
                amplitude_metric_name="magnitude_pct",
                sample_size=18,
                current_wave_matches_surface=True,
                current_wave_joint_percentile=65.0,
                current_wave_average_remaining_prob=0.35,
                current_wave_average_aged_prob=0.65,
                current_wave_remaining_vs_aged_odds=0.54,
            ),
            _surface_row(
                "BULL_COUNTERTREND",
                regime_label="BULL",
                wave_role="COUNTERTREND",
                amplitude_metric_name="retracement_vs_prior_mainstream_pct",
                sample_size=0,
                current_wave_matches_surface=False,
                current_wave_joint_percentile=None,
                current_wave_average_remaining_prob=None,
                current_wave_average_aged_prob=None,
                current_wave_remaining_vs_aged_odds=None,
            ),
            _surface_row(
                "BEAR_MAINSTREAM",
                regime_label="BEAR",
                wave_role="MAINSTREAM",
                amplitude_metric_name="magnitude_pct",
                sample_size=12,
                current_wave_matches_surface=False,
                current_wave_joint_percentile=None,
                current_wave_average_remaining_prob=None,
                current_wave_average_aged_prob=None,
                current_wave_remaining_vs_aged_odds=None,
            ),
            _surface_row(
                "BEAR_COUNTERTREND",
                regime_label="BEAR",
                wave_role="COUNTERTREND",
                amplitude_metric_name="retracement_vs_prior_mainstream_pct",
                sample_size=9,
                current_wave_matches_surface=False,
                current_wave_joint_percentile=None,
                current_wave_average_remaining_prob=None,
                current_wave_average_aged_prob=None,
                current_wave_remaining_vs_aged_odds=None,
            ),
        ]
    )

    payload = build_market_lifespan_report_payload(
        frame,
        calc_date=date(2026, 3, 20),
        entity_scope="MARKET",
        entity_code="000300.SH",
    )
    outputs = write_market_lifespan_report_bundle(tmp_path, payload)

    assert outputs["markdown"].exists()
    assert outputs["distribution_figure"].exists()
    assert outputs["odds_figure"].exists()
    assert outputs["json"].exists()
    markdown = outputs["markdown"].read_text(encoding="utf-8")
    assert "Market Lifespan Framework Report" in markdown
    assert "BULL_MAINSTREAM" in markdown
    assert "BULL_COUNTERTREND" in markdown
