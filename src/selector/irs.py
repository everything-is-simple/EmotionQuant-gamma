from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.data.store import Store
from src.selector.baseline import IRS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single


def compute_irs_single(
    industry_row: pd.Series,
    benchmark_pct: float,
    baseline: dict[str, float] | None = None,
) -> tuple[float, float, float]:
    """
    IRS 单行业评分纯函数：
    - rs_score: 行业相对强度
    - cf_score: 资金流向强度
    - total_score: 综合得分
    """
    base = baseline or IRS_BASELINE
    industry_pct = float(industry_row.get("pct_chg", 0.0) or 0.0)
    rs_raw = industry_pct - benchmark_pct
    flow_share = safe_ratio(industry_row.get("amount", 0.0), industry_row.get("market_total_amount", 0.0), 0.0)
    flow_delta = float(industry_row.get("amount_delta_10d", 0.0) or 0.0)
    cf_raw = flow_share + flow_delta

    rs_score = zscore_single(rs_raw, base["rs_score_mean"], base["rs_score_std"])
    cf_score = zscore_single(cf_raw, base["cf_score_mean"], base["cf_score_std"])
    total_score = 0.55 * rs_score + 0.45 * cf_score
    return rs_score, cf_score, total_score


def compute_irs(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
    min_industries_per_day: int = 1,
) -> int:
    """
    批量计算 IRS 并写入 l3_irs_daily。
    """
    industry_df = store.read_df(
        """
        SELECT * FROM l2_industry_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY industry, date
        """,
        (start, end),
    )
    if industry_df.empty:
        return 0

    benchmark_df = store.read_df(
        """
        SELECT date, pct_chg
        FROM l1_index_daily
        WHERE ts_code = '000001.SH' AND date BETWEEN ? AND ?
        """,
        (start, end),
    )
    if benchmark_df.empty:
        benchmark_map = {}
    else:
        benchmark_map = {
            (row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"]): float(
                row["pct_chg"] or 0.0
            )
            for _, row in benchmark_df.iterrows()
        }

    industry_df = industry_df.copy()
    industry_df["industry"] = industry_df["industry"].fillna("未知").astype(str)
    industry_df = industry_df[industry_df["industry"] != "未知"].copy()
    if industry_df.empty:
        return 0
    industry_df["market_total_amount"] = industry_df.groupby("date")["amount"].transform("sum")
    # 资金流向动量：10 日成交额变化，窗口不足时置 0，避免噪声放大。
    industry_df["amount_delta_10d"] = (
        industry_df.groupby("industry")["amount"]
        .transform(lambda s: (s / s.shift(10) - 1.0).replace([np.inf, -np.inf], np.nan))
        .fillna(0.0)
    )

    output_rows: list[dict] = []
    for day, day_df in industry_df.groupby("date"):
        day_value = day.date() if isinstance(day, pd.Timestamp) else day
        benchmark_pct = benchmark_map.get(day_value, 0.0)
        day_scores = []
        for _, row in day_df.iterrows():
            rs_score, cf_score, total_score = compute_irs_single(row, benchmark_pct, baseline=baseline)
            day_scores.append(
                {
                    "date": day_value,
                    "industry": row["industry"],
                    "score": total_score,
                    "rs_score": rs_score,
                    "cf_score": cf_score,
                }
            )
        day_scores_df = pd.DataFrame(day_scores)
        if len(day_scores_df) < max(1, min_industries_per_day):
            continue
        # 部分日期可能因原始缺失导致分数非有限值；按 0 兜底，保证日内排序稳定可执行。
        day_scores_df["score"] = pd.to_numeric(day_scores_df["score"], errors="coerce").fillna(0.0)
        # v0.01 验收要求“当日行业排名无重复”，即使分数并列也要给出稳定唯一顺序。
        day_scores_df = day_scores_df.sort_values(["score", "industry"], ascending=[False, True]).reset_index(drop=True)
        day_scores_df["rank"] = np.arange(1, len(day_scores_df) + 1, dtype=int)
        output_rows.extend(day_scores_df.to_dict(orient="records"))

    if not output_rows:
        return 0
    return store.bulk_upsert("l3_irs_daily", pd.DataFrame(output_rows))
