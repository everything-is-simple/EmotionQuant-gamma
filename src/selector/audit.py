from __future__ import annotations

"""Selector 审计与证据摘要工具。

这里不负责重新计算 MSS / IRS，只负责把已经落库的正式结果压缩成
文档和 evidence 文件容易消费的摘要结构。

换句话说，这里解决的是“如何总结”，不是“如何打分”。
"""

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.data.store import Store


def _series_quantiles(series: pd.Series) -> dict[str, float | None]:
    """把数值序列压成常用分位数面板，供 evidence 摘要直接引用。"""

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


# 这份摘要不是研究报告，而是给 evidence / record 直接引用的“体检面板”。
# 它回答的是：
# 1. MSS 在这个窗口里一共覆盖了多少天，各类 signal 各出现多少次。
# 2. IRS 覆盖了多少天、多少行业、每天的 rank 是否存在异常重复。
# 3. 两套分数大致落在什么分位区间，是否明显漂移。
def summarize_selector_distributions(store: Store, start: date, end: date) -> dict:
    """汇总指定区间内 MSS / IRS 的输出分布。

    目标不是推导研究结论，而是回答几个记录层问题：
    - MSS 一共多少天，signal 各自出现了多少次。
    - IRS 一共多少行、覆盖多少行业、每天 rank 是否有重复。
    - 两者的 score 大致落在什么分布区间。
    """

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


# 强制写成 UTF-8 JSON，避免 Windows 本地环境把中文 evidence 写成不可读编码。
def write_selector_distribution_evidence(output_path: str | Path, payload: dict) -> Path:
    """把摘要 payload 以 UTF-8 JSON 形式写入证据目录。"""

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
