from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.data.store import Store
from src.selector.mss import build_mss_raw_frame, calibrate_mss_baseline
from src.selector.mss_experiments import MSS_VARIANTS, score_mss_variant


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _series_quantiles(series: pd.Series) -> dict[str, float]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "p05": float(values.quantile(0.05)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p95": float(values.quantile(0.95)),
    }


def _threshold_summary(scored: pd.DataFrame, threshold: float) -> dict[str, float | int]:
    bullish = scored["score"] >= threshold
    bullish_days = int(bullish.sum())
    total_days = max(int(len(scored)), 1)
    return {
        "threshold": float(threshold),
        "bullish_days": bullish_days,
        "bullish_ratio": float(bullish_days / total_days),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare MSS normalization and aggregation variants.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01/evidence/v0.01-mss-variant-comparison-YYYYMMDD.json",
    )
    args = parser.parse_args()

    start = _parse_date(args.start)
    end = _parse_date(args.end)
    cfg = get_settings()
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT / "docs" / "spec" / "v0.01" / "evidence" / f"v0.01-mss-variant-comparison-{date.today():%Y%m%d}.json"
    )

    store = Store(cfg.db_path)
    try:
        snapshot = store.read_df(
            """
            SELECT *
            FROM l2_market_snapshot
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            """,
            (start, end),
        )
    finally:
        store.close()

    raw_df = build_mss_raw_frame(snapshot)
    baseline = calibrate_mss_baseline(raw_df)
    variants_payload: list[dict] = []
    for variant in MSS_VARIANTS:
        scored = score_mss_variant(raw_df, variant, baseline=baseline)
        score_std = float(pd.to_numeric(scored["score"], errors="coerce").std(ddof=0))
        signal_counts = {str(k): int(v) for k, v in scored["signal"].value_counts().sort_index().items()}
        variants_payload.append(
            {
                "label": variant.label,
                "normalization": variant.normalization,
                "aggregation": variant.aggregation,
                "days": int(len(scored)),
                "score_std": score_std,
                "score_quantiles": _series_quantiles(scored["score"]),
                "signal_counts_at_65_35": signal_counts,
                "threshold_sensitivity": [_threshold_summary(scored, threshold) for threshold in (55.0, 58.0, 60.0, 62.0, 65.0)],
            }
        )

    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": int(len(raw_df)),
        "baseline": baseline,
        "variants": variants_payload,
        "comparison_groups": {
            "normalization": ["zscore_weighted6", "percentile_weighted6"],
            "aggregation": ["zscore_weighted6", "zscore_core3"],
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
