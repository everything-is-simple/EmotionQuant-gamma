from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path

import pandas as pd

from src.data.store import Store


def _series_quantiles(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"p05": None, "p25": None, "p50": None, "p75": None, "p95": None}
    return {
        "p05": float(values.quantile(0.05)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p95": float(values.quantile(0.95)),
    }


def summarize_selector_distributions(store: Store, start: date, end: date) -> dict:
    mss = store.read_df(
        """
        SELECT date, score, signal
        FROM l3_mss_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    irs = store.read_df(
        """
        SELECT date, industry, score, rank
        FROM l3_irs_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY date, rank
        """,
        (start, end),
    )

    if mss.empty:
        mss_summary = {
            "days": 0,
            "signal_counts": {},
            "signal_ratios": {},
            "score_quantiles": _series_quantiles(pd.Series(dtype=float)),
        }
    else:
        signal_counts = {str(k): int(v) for k, v in mss["signal"].value_counts().sort_index().items()}
        total_days = max(int(len(mss)), 1)
        mss_summary = {
            "days": int(len(mss)),
            "signal_counts": signal_counts,
            "signal_ratios": {k: float(v / total_days) for k, v in signal_counts.items()},
            "score_quantiles": _series_quantiles(mss["score"]),
        }

    if irs.empty:
        irs_summary = {
            "rows": 0,
            "days": 0,
            "distinct_industries": 0,
            "score_quantiles": _series_quantiles(pd.Series(dtype=float)),
            "rank_range": {"min": None, "max": None},
            "industries_per_day": {"min": None, "median": None, "max": None},
            "ranks_per_day": {"min": None, "median": None, "max": None},
            "duplicate_rank_days": 0,
        }
    else:
        by_day = irs.groupby("date").agg(
            industries=("industry", "nunique"),
            unique_ranks=("rank", "nunique"),
        )
        irs_summary = {
            "rows": int(len(irs)),
            "days": int(irs["date"].nunique()),
            "distinct_industries": int(irs["industry"].nunique()),
            "score_quantiles": _series_quantiles(irs["score"]),
            "rank_range": {
                "min": int(pd.to_numeric(irs["rank"], errors="coerce").min()),
                "max": int(pd.to_numeric(irs["rank"], errors="coerce").max()),
            },
            "industries_per_day": {
                "min": int(by_day["industries"].min()),
                "median": float(by_day["industries"].median()),
                "max": int(by_day["industries"].max()),
            },
            "ranks_per_day": {
                "min": int(by_day["unique_ranks"].min()),
                "median": float(by_day["unique_ranks"].median()),
                "max": int(by_day["unique_ranks"].max()),
            },
            "duplicate_rank_days": int((by_day["industries"] != by_day["unique_ranks"]).sum()),
        }

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "mss": mss_summary,
        "irs": irs_summary,
    }


def write_selector_distribution_evidence(output_path: str | Path, payload: dict) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
