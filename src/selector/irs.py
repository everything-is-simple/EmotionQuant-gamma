from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.data.store import Store
from src.selector.baseline import IRS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single

IRS_TRACE_SCOPE_INDUSTRY_DAILY = "INDUSTRY_DAILY"
IRS_TRACE_SCOPE_SIGNAL_ATTACH = "SIGNAL_ATTACH"
IRS_TRACE_SOURCE_CLASSIFICATION = "SW2021"
IRS_TRACE_BENCHMARK_CODE = "000001.SH"
IRS_TRACE_VARIANT = "IRS_DAILY"
IRS_TRACE_FILL_SCORE = 50.0


def _build_irs_trace_run_id(start: date, end: date) -> str:
    return f"IRS_DAILY::{start.isoformat()}::{end.isoformat()}"


def _build_irs_trace_signal_id(trade_date: date, industry: str) -> str:
    normalized_industry = str(industry or "__DAY__").strip() or "__DAY__"
    return f"IRS_DAILY::{trade_date.isoformat()}::{normalized_industry}"


def _compute_irs_components(
    industry_row: pd.Series,
    benchmark_pct: float,
    baseline: dict[str, float] | None = None,
) -> dict[str, float]:
    base = baseline or IRS_BASELINE
    industry_pct = float(industry_row.get("pct_chg", 0.0) or 0.0)
    rs_raw = industry_pct - benchmark_pct
    market_total_amount = float(industry_row.get("market_total_amount", 0.0) or 0.0)
    amount = float(industry_row.get("amount", 0.0) or 0.0)
    flow_share = safe_ratio(amount, market_total_amount, 0.0)
    flow_delta = float(industry_row.get("amount_delta_10d", 0.0) or 0.0)
    cf_raw = flow_share + flow_delta

    rs_score = zscore_single(rs_raw, base["rs_score_mean"], base["rs_score_std"])
    cf_score = zscore_single(cf_raw, base["cf_score_mean"], base["cf_score_std"])
    total_score = 0.55 * rs_score + 0.45 * cf_score
    return {
        "industry_pct": industry_pct,
        "market_total_amount": market_total_amount,
        "amount": amount,
        "amount_delta_10d": flow_delta,
        "rs_raw": rs_raw,
        "cf_raw": cf_raw,
        "rs_score": rs_score,
        "cf_score": cf_score,
        "total_score": total_score,
    }


def _build_industry_trace_row(
    trace_run_id: str,
    trade_date: date,
    industry_row: pd.Series,
    components: dict[str, float],
    coverage_flag: str,
    industry_score: float | None = None,
    industry_rank: int | None = None,
    benchmark_pct: float = 0.0,
) -> dict[str, object]:
    resolved_score = float(
        industry_score if industry_score is not None else pd.to_numeric(components["total_score"], errors="coerce")
    )
    if not np.isfinite(resolved_score):
        resolved_score = 0.0
    return {
        "run_id": trace_run_id,
        "signal_id": _build_irs_trace_signal_id(trade_date, str(industry_row.get("industry", ""))),
        "signal_date": trade_date,
        "code": "",
        "industry": str(industry_row.get("industry", "")),
        "variant": IRS_TRACE_VARIANT,
        "uses_irs": True,
        "daily_score": resolved_score,
        "daily_rank": industry_rank,
        "signal_irs_score": 0.0,
        "fill_score": IRS_TRACE_FILL_SCORE,
        "status": IRS_TRACE_SCOPE_INDUSTRY_DAILY,
        "trace_scope": IRS_TRACE_SCOPE_INDUSTRY_DAILY,
        "industry_code": None,
        "source_classification": IRS_TRACE_SOURCE_CLASSIFICATION,
        "benchmark_code": IRS_TRACE_BENCHMARK_CODE,
        "benchmark_pct": float(benchmark_pct),
        "industry_pct_chg": float(components["industry_pct"]),
        "amount": float(components["amount"]),
        "market_total_amount": float(components["market_total_amount"]),
        "amount_delta_10d": float(components["amount_delta_10d"]),
        "rs_raw": float(components["rs_raw"]),
        "cf_raw": float(components["cf_raw"]),
        "rs_score": float(components["rs_score"]),
        "cf_score": float(components["cf_score"]),
        "industry_score": resolved_score,
        "industry_rank": industry_rank,
        "coverage_flag": coverage_flag,
    }


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
    components = _compute_irs_components(industry_row, benchmark_pct, baseline=baseline)
    return components["rs_score"], components["cf_score"], components["total_score"]


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
    trace_run_id = _build_irs_trace_run_id(start, end)
    store.conn.execute(
        """
        DELETE FROM irs_industry_trace_exp
        WHERE run_id = ? AND COALESCE(trace_scope, ?) = ?
        """,
        [trace_run_id, IRS_TRACE_SCOPE_SIGNAL_ATTACH, IRS_TRACE_SCOPE_INDUSTRY_DAILY],
    )
    # IRS 支持按日期局部重建；先清分区，避免行业集合变小时残留旧 rank。
    store.conn.execute("DELETE FROM l3_irs_daily WHERE date BETWEEN ? AND ?", [start, end])
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
    unknown_df = industry_df[industry_df["industry"] == "未知"].copy()
    industry_df = industry_df[industry_df["industry"] != "未知"].copy()
    if industry_df.empty:
        trace_rows: list[dict[str, object]] = []
        for _, row in unknown_df.iterrows():
            trade_date = row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"]
            benchmark_pct = benchmark_map.get(trade_date, 0.0)
            trace_rows.append(
                _build_industry_trace_row(
                    trace_run_id=trace_run_id,
                    trade_date=trade_date,
                    industry_row=row,
                    components={
                        "industry_pct": float(row.get("pct_chg", 0.0) or 0.0),
                        "amount": float(row.get("amount", 0.0) or 0.0),
                        "market_total_amount": 0.0,
                        "amount_delta_10d": 0.0,
                        "rs_raw": float(row.get("pct_chg", 0.0) or 0.0) - benchmark_pct,
                        "cf_raw": 0.0,
                        "rs_score": zscore_single(
                            float(row.get("pct_chg", 0.0) or 0.0) - benchmark_pct,
                            (baseline or IRS_BASELINE)["rs_score_mean"],
                            (baseline or IRS_BASELINE)["rs_score_std"],
                        ),
                        "cf_score": 50.0,
                        "total_score": 0.0,
                    },
                    coverage_flag="UNKNOWN_DROPPED",
                    benchmark_pct=benchmark_pct,
                )
            )
        if trace_rows:
            store.bulk_upsert("irs_industry_trace_exp", pd.DataFrame(trace_rows))
        return 0
    industry_df["market_total_amount"] = industry_df.groupby("date")["amount"].transform("sum")
    # 资金流向动量：10 日成交额变化，窗口不足时置 0，避免噪声放大。
    industry_df["amount_delta_10d"] = (
        industry_df.groupby("industry")["amount"]
        .transform(lambda s: (s / s.shift(10) - 1.0).replace([np.inf, -np.inf], np.nan))
        .fillna(0.0)
    )
    market_total_map = {
        (day.date() if isinstance(day, pd.Timestamp) else day): float(total or 0.0)
        for day, total in industry_df.groupby("date")["amount"].sum().items()
    }

    output_rows: list[dict] = []
    trace_rows: list[dict[str, object]] = []
    for _, row in unknown_df.iterrows():
        trade_date = row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"]
        benchmark_pct = benchmark_map.get(trade_date, 0.0)
        components = {
            "industry_pct": float(row.get("pct_chg", 0.0) or 0.0),
            "amount": float(row.get("amount", 0.0) or 0.0),
            "market_total_amount": market_total_map.get(trade_date, 0.0),
            "amount_delta_10d": 0.0,
            "rs_raw": float(row.get("pct_chg", 0.0) or 0.0) - benchmark_pct,
            "cf_raw": 0.0,
            "rs_score": zscore_single(
                float(row.get("pct_chg", 0.0) or 0.0) - benchmark_pct,
                (baseline or IRS_BASELINE)["rs_score_mean"],
                (baseline or IRS_BASELINE)["rs_score_std"],
            ),
            "cf_score": 50.0,
            "total_score": 0.0,
        }
        trace_rows.append(
            _build_industry_trace_row(
                trace_run_id=trace_run_id,
                trade_date=trade_date,
                industry_row=row,
                components=components,
                coverage_flag="UNKNOWN_DROPPED",
                benchmark_pct=benchmark_pct,
            )
        )
    for day, day_df in industry_df.groupby("date"):
        day_value = day.date() if isinstance(day, pd.Timestamp) else day
        benchmark_filled = day_value not in benchmark_map
        benchmark_pct = benchmark_map.get(day_value, 0.0)
        day_scores = []
        day_trace_inputs: list[tuple[pd.Series, dict[str, float]]] = []
        for _, row in day_df.iterrows():
            components = _compute_irs_components(row, benchmark_pct, baseline=baseline)
            day_scores.append(
                {
                    "date": day_value,
                    "industry": row["industry"],
                    "score": components["total_score"],
                    "rs_score": components["rs_score"],
                    "cf_score": components["cf_score"],
                }
            )
            day_trace_inputs.append((row, components))
        day_scores_df = pd.DataFrame(day_scores)
        if len(day_scores_df) < max(1, min_industries_per_day):
            for row, components in day_trace_inputs:
                trace_rows.append(
                    _build_industry_trace_row(
                        trace_run_id=trace_run_id,
                        trade_date=day_value,
                        industry_row=row,
                        components=components,
                        coverage_flag="MIN_INDUSTRIES_SKIP",
                        benchmark_pct=benchmark_pct,
                    )
                )
            continue
        # 部分日期可能因原始缺失导致分数非有限值；按 0 兜底，保证日内排序稳定可执行。
        day_scores_df["score"] = pd.to_numeric(day_scores_df["score"], errors="coerce").fillna(0.0)
        # v0.01 验收要求“当日行业排名无重复”，即使分数并列也要给出稳定唯一顺序。
        day_scores_df = day_scores_df.sort_values(["score", "industry"], ascending=[False, True]).reset_index(drop=True)
        day_scores_df["rank"] = np.arange(1, len(day_scores_df) + 1, dtype=int)
        output_rows.extend(day_scores_df.to_dict(orient="records"))
        score_lookup = {
            str(row["industry"]): (float(row["score"]), int(row["rank"])) for _, row in day_scores_df.iterrows()
        }
        coverage_flag = "BENCHMARK_FILL" if benchmark_filled else "NORMAL"
        for row, components in day_trace_inputs:
            score_value, rank_value = score_lookup[str(row["industry"])]
            trace_rows.append(
                _build_industry_trace_row(
                    trace_run_id=trace_run_id,
                    trade_date=day_value,
                    industry_row=row,
                    components=components,
                    coverage_flag=coverage_flag,
                    industry_score=score_value,
                    industry_rank=rank_value,
                    benchmark_pct=benchmark_pct,
                )
            )

    if trace_rows:
        store.bulk_upsert("irs_industry_trace_exp", pd.DataFrame(trace_rows))
    if not output_rows:
        return 0
    return store.bulk_upsert("l3_irs_daily", pd.DataFrame(output_rows))
