from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.config import Settings, get_settings
from src.contracts import StockCandidate
from src.data.store import Store
from src.logging_utils import logger

MSS_GATE_MODES = {"bearish_only", "bullish_required", "soft_gate"}
PRESELECT_SCORE_MODES = {
    "amount_plus_volume_ratio",
    "amount_only",
    "volume_ratio_only",
}


def _industry_priority_map(store: Store, calc_date: date) -> dict[str, float]:
    rows = store.read_df(
        """
        SELECT industry, rank
        FROM l3_irs_daily
        WHERE date = ?
        """,
        (calc_date,),
    )
    if rows.empty:
        return {}

    max_rank = max(int(rows["rank"].max()), 1)
    priority: dict[str, float] = {}
    for _, row in rows.iterrows():
        rank = int(row["rank"])
        # legacy 对照链仍保留行业优先分，便于和历史漏斗结果对齐。
        priority[str(row["industry"])] = float((max_rank - rank + 1) / max_rank * 100.0)
    return priority


def _load_universe_snapshot(store: Store, calc_date: date) -> pd.DataFrame:
    """
    读取当日候选快照：
    - L2 给出流动性/波动等加工字段
    - L1 给出停牌真相
    - stock_info 采用 as-of 最近生效信息
    """
    # 这是 Selector 最重的单日快照查询：
    # 需要在一个 SQL 里把 L2 横截面、行业归属、ST/上市状态拼齐，
    # 后面所有过滤和 preselect 都建立在这张 snapshot 上。
    return store.read_df(
        """
        SELECT
            l2.code,
            l2.date,
            l2.amount,
            l2.pct_chg,
            l2.volume_ratio,
            l1.is_halt,
            COALESCE((
                SELECT m.industry_name
                FROM l1_sw_industry_member m
                WHERE split_part(m.ts_code, '.', 1) = l2.code
                  AND m.in_date <= l2.date
                  AND (m.out_date IS NULL OR m.out_date >= l2.date)
                ORDER BY m.in_date DESC, m.industry_code ASC
                LIMIT 1
            ), '未知') AS industry,
            COALESCE((
                SELECT info.is_st
                FROM l1_stock_info info
                WHERE split_part(info.ts_code, '.', 1) = l2.code
                  AND info.effective_from <= l2.date
                ORDER BY info.effective_from DESC
                LIMIT 1
            ), FALSE) AS is_st,
            (
                SELECT info.list_status
                FROM l1_stock_info info
                WHERE split_part(info.ts_code, '.', 1) = l2.code
                  AND info.effective_from <= l2.date
                ORDER BY info.effective_from DESC
                LIMIT 1
            ) AS list_status,
            (
                SELECT info.list_date
                FROM l1_stock_info info
                WHERE split_part(info.ts_code, '.', 1) = l2.code
                  AND info.effective_from <= l2.date
                ORDER BY info.effective_from DESC
                LIMIT 1
            ) AS list_date
        FROM l2_stock_adj_daily l2
        LEFT JOIN l1_stock_daily l1
            ON split_part(l1.ts_code, '.', 1) = l2.code AND l1.date = l2.date
        WHERE l2.date = ?
        """,
        (calc_date,),
    )


def _annotate_basic_filters(df: pd.DataFrame, calc_date: date, config: Settings) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    work["industry"] = work["industry"].fillna("未知")
    work["is_halt"] = work["is_halt"].fillna(False)
    work["is_st"] = work["is_st"].fillna(False)
    work["list_status"] = work["list_status"].fillna("UNKNOWN")
    work["list_date"] = pd.to_datetime(work["list_date"], errors="coerce")
    work["list_days"] = (pd.Timestamp(calc_date) - work["list_date"]).dt.days
    # 先 annotate 再 filter：被挡掉的票也要保留 reject_reason，供 trace 回放。
    work["filters_passed"] = "LIST_STATUS;HALT;ST;LIST_DAYS;AMOUNT"
    work["reject_reason"] = ""
    work.loc[work["list_status"] != "L", "reject_reason"] = "NOT_LIVE"
    work.loc[~work["reject_reason"].astype(bool) & work["is_halt"], "reject_reason"] = "HALTED"
    work.loc[~work["reject_reason"].astype(bool) & work["is_st"], "reject_reason"] = "ST"
    work.loc[
        ~work["reject_reason"].astype(bool) & (work["list_days"].fillna(0) < config.min_list_days),
        "reject_reason",
    ] = "TOO_NEW"
    work.loc[
        ~work["reject_reason"].astype(bool) & (work["amount"].fillna(0) < config.min_amount),
        "reject_reason",
    ] = "LOW_LIQUIDITY"
    work["liquidity_tag"] = np.where(
        work["amount"].fillna(0) >= config.min_amount * 2,
        "HIGH",
        np.where(work["amount"].fillna(0) >= config.min_amount, "MEDIUM", "LOW"),
    )
    return work


def _apply_basic_filters(df: pd.DataFrame, calc_date: date, config: Settings) -> pd.DataFrame:
    work = _annotate_basic_filters(df, calc_date, config)
    if work.empty:
        return work
    return work[work["reject_reason"] == ""].copy()


def _persist_selector_candidate_trace(
    store: Store,
    calc_date: date,
    cfg: Settings,
    run_id: str,
    annotated: pd.DataFrame,
    ranked_all: pd.DataFrame,
    ranked_top_n: pd.DataFrame,
) -> None:
    if not run_id:
        return

    trace = annotated.copy()
    if trace.empty:
        return

    rank_map = {str(row.code): idx for idx, row in enumerate(ranked_all.itertuples(index=False), start=1)}
    top_codes = set(ranked_top_n["code"].astype(str).tolist())

    trace["run_id"] = run_id
    trace["signal_date"] = calc_date
    trace["pipeline_mode"] = cfg.pipeline_mode_normalized
    trace["preselect_score_mode"] = cfg.preselect_score_mode
    trace["candidate_rank"] = trace["code"].astype(str).map(rank_map)
    trace["candidate_top_n"] = int(max(1, int(cfg.candidate_top_n)))
    trace["selected"] = trace["code"].astype(str).isin(top_codes)
    # 当前主线是 Selector -> PAS；这里记录的是“是否进入 PAS 层”，不再绑死到 BOF 命名。
    trace["selected_for_pas"] = trace["selected"]
    trace["candidate_reason"] = np.where(trace["selected"], "PRESELECT_TOP_N", None)
    trace["coverage_flag"] = np.where(
        trace["industry"].fillna("未知").astype(str) == "未知",
        "UNKNOWN_INDUSTRY",
        "NORMAL",
    )
    trace["source_snapshot_date"] = calc_date
    trace["final_score"] = pd.to_numeric(trace.get("score"), errors="coerce")
    trace["reject_reason"] = trace["reject_reason"].replace("", None)

    store.bulk_upsert(
        "selector_candidate_trace_exp",
        trace.loc[
            :,
            [
                "run_id",
                "signal_date",
                "code",
                "pipeline_mode",
                "preselect_score_mode",
                "industry",
                "amount",
                "volume_ratio",
                "filters_passed",
                "reject_reason",
                "candidate_reason",
                "coverage_flag",
                "source_snapshot_date",
                "liquidity_tag",
                "preselect_score",
                "final_score",
                "candidate_rank",
                "candidate_top_n",
                "selected",
                "selected_for_pas",
            ],
        ].reset_index(drop=True),
    )


def _load_mss_signal(store: Store, calc_date: date, config: Settings) -> str | None:
    if not config.enable_mss_gate:
        return None
    row = store.read_df("SELECT signal FROM l3_mss_daily WHERE date = ?", (calc_date,))
    if row.empty:
        return None
    return str(row.iloc[0]["signal"]).upper()


def _apply_mss_gate(mss_signal: str | None, config: Settings, df: pd.DataFrame) -> pd.DataFrame:
    if not config.enable_mss_gate:
        return df
    if mss_signal is None:
        # legacy 对照链在 MSS 缺失时直接返回空池，确保和历史门控口径一致。
        return df.iloc[0:0]
    if config.mss_gate_mode not in MSS_GATE_MODES:
        raise ValueError(
            f"Unsupported MSS gate mode: {config.mss_gate_mode}. Expected one of {sorted(MSS_GATE_MODES)}."
        )
    if config.mss_gate_mode == "bearish_only":
        if mss_signal == "BEARISH":
            return df.iloc[0:0]
        return df
    if config.mss_gate_mode == "bullish_required":
        if mss_signal != "BULLISH":
            return df.iloc[0:0]
        return df
    if mss_signal == "BEARISH":
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


def _select_dtt_candidates_frame(
    store: Store,
    calc_date: date,
    cfg: Settings,
    universe: pd.DataFrame,
    run_id: str = "",
) -> pd.DataFrame:
    annotated = _annotate_basic_filters(universe, calc_date, cfg)
    filtered = annotated[annotated["reject_reason"] == ""].copy()
    if filtered.empty:
        _persist_selector_candidate_trace(
            store=store,
            calc_date=calc_date,
            cfg=cfg,
            run_id=run_id,
            annotated=annotated,
            ranked_all=filtered,
            ranked_top_n=filtered,
        )
        logger.info(f"selector {calc_date}: mode=dtt, universe={len(universe)}, filtered=0, final=0")
        return filtered

    data = filtered.copy()
    # DTT 主线里的 preselect_score 只服务于算力调度，不承载 MSS/IRS 交易语义。
    amount_component = np.log1p(data["amount"].fillna(0))
    activity_component = data["volume_ratio"].fillna(0)
    if cfg.preselect_score_mode == "amount_plus_volume_ratio":
        data["preselect_score"] = amount_component + activity_component
    elif cfg.preselect_score_mode == "amount_only":
        data["preselect_score"] = amount_component
    elif cfg.preselect_score_mode == "volume_ratio_only":
        data["preselect_score"] = activity_component
    else:
        raise ValueError(
            f"Unsupported preselect score mode: {cfg.preselect_score_mode}. "
            f"Expected one of {sorted(PRESELECT_SCORE_MODES)}."
        )
    data["score"] = data["preselect_score"]
    ranked_all = data.sort_values(["preselect_score", "code"], ascending=[False, True]).reset_index(drop=True)
    annotated = annotated.merge(
        ranked_all.loc[:, ["code", "preselect_score", "score"]],
        on="code",
        how="left",
    )
    ranked = (
        ranked_all
        .head(max(1, int(cfg.candidate_top_n)))
        .loc[
            :,
            ["code", "industry", "preselect_score", "score", "filters_passed", "reject_reason", "liquidity_tag"],
        ]
        .reset_index(drop=True)
    )
    # DTT 主线在这里就把算力预算切成 top_n：
    # 这一步不是交易决策，只是决定哪些票会进入 PAS 层继续算。
    _persist_selector_candidate_trace(
        store=store,
        calc_date=calc_date,
        cfg=cfg,
        run_id=run_id,
        annotated=annotated,
        ranked_all=ranked_all,
        ranked_top_n=ranked,
    )
    logger.info(
        f"selector {calc_date}: mode=dtt, universe={len(universe)}, filtered={len(filtered)}, final={len(ranked)}"
    )
    return ranked


def _select_legacy_candidates_frame(
    store: Store,
    calc_date: date,
    cfg: Settings,
    universe: pd.DataFrame,
) -> pd.DataFrame:
    stage1 = _apply_basic_filters(universe, calc_date, cfg)
    if not stage1.empty:
        # legacy 对照链继续保留“先粗筛再门控”的历史行为，用于 compare / rollback。
        stage1 = stage1.copy()
        stage1["rough_rank_score"] = np.log1p(stage1["amount"].fillna(0)) + stage1["volume_ratio"].fillna(0)
        stage1 = stage1.sort_values("rough_rank_score", ascending=False).head(200)
    mss_signal = _load_mss_signal(store, calc_date, cfg)
    stage2 = _apply_mss_gate(mss_signal, cfg, stage1)
    stage3 = _apply_irs_filter(store, calc_date, cfg, stage2)
    if stage3.empty:
        logger.info(
            f"selector {calc_date}: mode=legacy, universe={len(universe)}, "
            f"stage1={len(stage1)}, stage2={len(stage2)}, stage3={len(stage3)}, "
            f"gate_mode={cfg.mss_gate_mode}, mss_signal={mss_signal or 'DISABLED'}"
        )
        return stage3

    data = stage3.copy()
    irs_priority = _industry_priority_map(store, calc_date)
    data["liquidity_score"] = np.log1p(data["amount"].fillna(0))
    data["stability_score"] = 100.0 - np.minimum(data["pct_chg"].fillna(0).abs() * 1000.0, 100.0)
    data["industry_priority_score"] = data["industry"].map(irs_priority).fillna(0.0)
    data["score"] = (
        0.4 * data["liquidity_score"]
        + 0.3 * data["stability_score"]
        + 0.3 * data["industry_priority_score"]
    )

    ranked = (
        data.sort_values("score", ascending=False)
        .head(cfg.candidate_top_n)
        .loc[:, ["code", "industry", "score", "filters_passed", "reject_reason", "liquidity_tag"]]
        .reset_index(drop=True)
    )
    if cfg.enable_mss_gate and cfg.mss_gate_mode == "soft_gate" and mss_signal == "NEUTRAL":
        ranked = ranked.head(max(1, cfg.mss_soft_gate_candidate_top_n)).reset_index(drop=True)

    logger.info(
        f"selector {calc_date}: mode=legacy, universe={len(universe)}, "
        f"stage1={len(stage1)}, stage2={len(stage2)}, stage3={len(stage3)}, "
        f"final={len(ranked)}, gate_mode={cfg.mss_gate_mode}, mss_signal={mss_signal or 'DISABLED'}"
    )
    return ranked


def select_candidates(
    store: Store,
    calc_date: date,
    config: Settings | None = None,
    run_id: str | None = None,
) -> list[StockCandidate]:
    top = select_candidates_frame(store, calc_date, config=config, run_id=run_id)
    if top.empty:
        return []
    candidates: list[StockCandidate] = []
    for _, row in top.iterrows():
        preselect_score = row["preselect_score"] if "preselect_score" in row else row["score"]
        candidates.append(
            StockCandidate(
                code=str(row["code"]),
                industry=str(row["industry"]),
                score=float(row["score"]),
                trade_date=calc_date,
                preselect_score=float(preselect_score),
                candidate_rank=int(row.name) + 1,
                candidate_reason="PRESELECT_TOP_N",
                liquidity_tag=str(row["liquidity_tag"]) if pd.notna(row.get("liquidity_tag")) else None,
            )
        )
    return candidates


def select_candidates_frame(
    store: Store,
    calc_date: date,
    config: Settings | None = None,
    run_id: str | None = None,
) -> pd.DataFrame:
    cfg = config or get_settings()
    universe = _load_universe_snapshot(store, calc_date)
    if cfg.use_dtt_pipeline:
        return _select_dtt_candidates_frame(store, calc_date, cfg, universe, run_id=(run_id or "").strip())
    return _select_legacy_candidates_frame(store, calc_date, cfg, universe)
