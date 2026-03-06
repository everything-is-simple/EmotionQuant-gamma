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
from src.selector.mss import build_mss_raw_frame, calibrate_mss_baseline, score_mss_raw_frame


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _streak_lengths(flag: pd.Series) -> list[int]:
    values = flag.fillna(False).astype(bool).tolist()
    streaks: list[int] = []
    run = 0
    for value in values:
        if value:
            run += 1
        elif run:
            streaks.append(run)
            run = 0
    if run:
        streaks.append(run)
    return streaks


def _dry_spell_lengths(flag: pd.Series) -> list[int]:
    return _streak_lengths(~flag.fillna(False).astype(bool))


def _threshold_summary(scored: pd.DataFrame, threshold: float) -> dict[str, float | int]:
    bullish = scored["score"] >= threshold
    bullish_days = int(bullish.sum())
    total_days = max(int(len(scored)), 1)
    monthly_avg = float(bullish_days / max(scored["date"].nunique() / 21.0, 1.0))
    bullish_streaks = _streak_lengths(bullish)
    dry_spells = _dry_spell_lengths(bullish)
    return {
        "threshold": float(threshold),
        "bullish_days": bullish_days,
        "bullish_ratio": float(bullish_days / total_days),
        "monthly_avg_bullish_days": monthly_avg,
        "longest_bullish_streak": int(max(bullish_streaks) if bullish_streaks else 0),
        "longest_dry_spell": int(max(dry_spells) if dry_spells else 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate MSS baseline from l2_market_snapshot.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default="docs/spec/v0.01/evidence/v0.01-mss-baseline-calibration-20260306.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    start = _parse_date(args.start)
    end = _parse_date(args.end)
    cfg = get_settings()
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
        raw_df = build_mss_raw_frame(snapshot)
        baseline = calibrate_mss_baseline(raw_df)
        scored = score_mss_raw_frame(raw_df, baseline=baseline)

        payload = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": int(len(raw_df)),
            "baseline": baseline,
            "score_quantiles": {
                "p05": float(scored["score"].quantile(0.05)),
                "p25": float(scored["score"].quantile(0.25)),
                "p50": float(scored["score"].quantile(0.50)),
                "p75": float(scored["score"].quantile(0.75)),
                "p95": float(scored["score"].quantile(0.95)),
            },
            "signal_counts_at_65_35": {
                str(k): int(v) for k, v in scored["signal"].value_counts().sort_index().items()
            },
            "threshold_sensitivity": [
                _threshold_summary(scored, threshold) for threshold in (55.0, 58.0, 60.0, 62.0, 65.0)
            ],
        }
    finally:
        store.close()

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    print(json.dumps(payload["signal_counts_at_65_35"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
