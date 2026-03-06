from __future__ import annotations


# MSS baseline calibrated from l2_market_snapshot over 2023-01-03..2026-02-24.
# Threshold semantics remain frozen elsewhere; this file only stores normalization anchors.
MSS_BASELINE = {
    "market_coefficient_mean": 0.4773860533555573,
    "market_coefficient_std": 0.23364959561646687,
    "profit_effect_mean": 0.02001627879301641,
    "profit_effect_std": 0.02405607273268048,
    "loss_effect_mean": 0.01498781726283301,
    "loss_effect_std": 0.030001566738781904,
    "continuity_mean": 0.1929883692056652,
    "continuity_std": 0.09005146213678802,
    "extreme_mean": 0.41160185981493663,
    "extreme_std": 0.13036907349337296,
    "volatility_mean": 0.18112868209847394,
    "volatility_std": 0.05756783616858019,
}

IRS_BASELINE = {
    "rs_score_mean": 0.0,
    "rs_score_std": 1.0,
    "cf_score_mean": 0.0,
    "cf_score_std": 1.0,
}
