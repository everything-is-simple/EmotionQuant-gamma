from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.config import Settings, get_settings
from src.contracts import StockCandidate
from src.data.store import Store


def _load_universe_snapshot(store: Store, calc_date: date) -> pd.DataFrame:
    """
    读取当日候选快照：
    - L2 给出流动性/波动等加工字段
    - L1 给出停牌真相
    - stock_info 采用 as-of 最近生效信息
    """
    return store.read_df(
        """
        WITH joined AS (
            SELECT
                l2.code,
                l2.date,
                l2.amount,
                l2.pct_chg,
                l2.volume_ratio,
                l1.is_halt,
                info.industry,
                info.is_st,
                info.list_date,
                ROW_NUMBER() OVER (
                    PARTITION BY l2.code, l2.date
                    ORDER BY info.effective_from DESC NULLS LAST
                ) AS rn
            FROM l2_stock_adj_daily l2
            LEFT JOIN l1_stock_daily l1
                ON split_part(l1.ts_code, '.', 1) = l2.code AND l1.date = l2.date
            LEFT JOIN l1_stock_info info
                ON split_part(info.ts_code, '.', 1) = l2.code
               AND info.effective_from <= l2.date
            WHERE l2.date = ?
        )
        SELECT
            code,
            date,
            amount,
            pct_chg,
            volume_ratio,
            is_halt,
            industry,
            is_st,
            list_date
        FROM joined
        WHERE rn = 1
        """,
        (calc_date,),
    )


def _apply_basic_filters(df: pd.DataFrame, calc_date: date, config: Settings) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    work["industry"] = work["industry"].fillna("未知")
    work["is_halt"] = work["is_halt"].fillna(False)
    work["is_st"] = work["is_st"].fillna(False)
    work["list_date"] = pd.to_datetime(work["list_date"], errors="coerce")
    work["list_days"] = (pd.Timestamp(calc_date) - work["list_date"]).dt.days

    # 粗筛目标：先剔除不可交易与明显质量差样本，再做排序。
    filtered = work[
        (~work["is_halt"])
        & (~work["is_st"])
        & (work["list_days"].fillna(0) >= config.min_list_days)
        & (work["amount"].fillna(0) >= config.min_amount)
    ].copy()
    return filtered


def _apply_mss_gate(store: Store, calc_date: date, config: Settings, df: pd.DataFrame) -> pd.DataFrame:
    if not config.enable_mss_gate:
        return df
    row = store.read_df("SELECT signal FROM l3_mss_daily WHERE date = ?", (calc_date,))
    if row.empty:
        # 缺 MSS 结果时，为防漂移直接返回空池，强制上游先补数据。
        return df.iloc[0:0]
    if str(row.iloc[0]["signal"]).upper() == "BEARISH":
        return df.iloc[0:0]
    return df


def _apply_irs_filter(store: Store, calc_date: date, config: Settings, df: pd.DataFrame) -> pd.DataFrame:
    if not config.enable_irs_filter or df.empty:
        return df
    top_industries = store.read_df(
        """
        SELECT industry
        FROM l3_irs_daily
        WHERE date = ?
        ORDER BY rank ASC
        LIMIT ?
        """,
        (calc_date, config.irs_top_n),
    )
    if top_industries.empty:
        return df.iloc[0:0]
    allowed = set(top_industries["industry"].tolist())
    return df[df["industry"].isin(allowed)].copy()


def select_candidates(
    store: Store,
    calc_date: date,
    config: Settings | None = None,
) -> list[StockCandidate]:
    cfg = config or get_settings()
    universe = _load_universe_snapshot(store, calc_date)
    stage1 = _apply_basic_filters(universe, calc_date, cfg)
    stage2 = _apply_mss_gate(store, calc_date, cfg, stage1)
    stage3 = _apply_irs_filter(store, calc_date, cfg, stage2)
    if stage3.empty:
        return []

    # v0.01 候选评分只做排序，不参与 PAS 触发本身。
    data = stage3.copy()
    data["liquidity_score"] = np.log1p(data["amount"].fillna(0))
    data["stability_score"] = -data["pct_chg"].fillna(0).abs()
    data["activity_score"] = data["volume_ratio"].fillna(0)
    data["score"] = 0.4 * data["liquidity_score"] + 0.3 * data["stability_score"] + 0.3 * data[
        "activity_score"
    ]

    top = data.sort_values("score", ascending=False).head(cfg.candidate_top_n)
    return [
        StockCandidate(code=str(row["code"]), industry=str(row["industry"]), score=float(row["score"]))
        for _, row in top.iterrows()
    ]
