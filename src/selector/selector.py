from __future__ import annotations

"""运行时候选选择层。

这个模块负责回答一个非常具体的问题：
“今天哪些股票值得继续送去 PAS 触发器层做精算？”

它不是最终买卖决策层，而是主线漏斗里位于 PAS 之前的候选调度层。
当前同时保留两条路径：
1. legacy：历史冻结参照链，用于对照、回滚、解释旧结果。
2. dtt：当前主线使用的调度链，更偏算力预算分配，而不是最终 alpha 结论。
"""

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
SELECTOR_TRACE_COLUMNS = [
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
]


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


# 读取某个交易日的候选宇宙快照。
# 这是 Selector 的底板数据：后面所有过滤、预选、trace 都建立在这张单日快照上。
# 这里必须一次性拼齐 L2 日线加工字段、停牌信息、行业归属、ST 状态和上市状态，
# 否则后面的过滤链会因为“信息不在同一张表”而出现口径漂移。
# 构建某个交易日的 Selector 原始宇宙快照。
# 输出不是“已经可交易的股票列表”，而是“带完整过滤上下文的候选全集”。
# 后面的基础过滤、DTT 预选、legacy 对照链和 trace 回放都从这张单日快照起步。
def _load_universe_snapshot(store: Store, calc_date: date) -> pd.DataFrame:
    """从 L2 日线、停牌信息和个股元数据构建单日 Selector 宇宙快照。"""

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


# 给候选宇宙打上基础可交易过滤标签。
# 这里故意先 annotate、后 filter，而不是直接删行。原因是：
# 被挡掉的股票也需要保留 reject_reason，事后才能回答
# “它为什么没进入 PAS / 为什么今天根本没资格参加候选”。
# 给单日宇宙打上基础可交易过滤标签。
# 重点不是删掉谁，而是明确写出谁为什么被拒绝。
# 只有这样，后续 trace / report 才能回答“今天这只票为什么连 PAS 资格都没有”。
def _annotate_basic_filters(df: pd.DataFrame, calc_date: date, config: Settings) -> pd.DataFrame:
    """打上硬性可交易过滤标签，并保留拒绝原因供 trace 回放。"""

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


# 把 Selector 漏斗过程落成 trace 表。
# 这不是运行必需物，而是复盘必需物。没有这张 trace，后面就很难解释：
# - 候选宇宙当时长什么样
# - 哪些票被过滤掉
# - 哪些票进入 top_n
# - 哪些票真正被送去 PAS
# 这张 trace 表记录的是“筛选过程”，不是最终信号。
# 它把宇宙快照、拒绝原因、候选排名、是否进入 PAS 预算池
# 放在同一条记录里，后面定位问题时就不需要再靠猜。
def _persist_selector_candidate_trace(
    store: Store,
    calc_date: date,
    cfg: Settings,
    run_id: str,
    annotated: pd.DataFrame,
    ranked_all: pd.DataFrame,
    ranked_top_n: pd.DataFrame,
) -> None:
    """把 Selector 漏斗完整落盘，供后续 evidence 复盘。"""

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
    # trace 行来自 annotate/merge 的不同分支，不能假设每个分支都已经补齐同一列集；
    # 缺失列统一补成 NA，避免长窗回放在 selector trace 写入时因单列缺口中断。
    trace = trace.reindex(columns=SELECTOR_TRACE_COLUMNS, fill_value=pd.NA)

    store.bulk_upsert(
        "selector_candidate_trace_exp",
        trace.reset_index(drop=True),
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


# 按 IRS 的行业 Top-N 白名单做二次过滤。
# 这一步是典型的“行业先行”门：如果行业当天不在允许名单里，
# 个股再活跃也不会继续向下游传递。
# 按 IRS 行业白名单做二次过滤。
# 这是 legacy 链中“行业先行”的典型做法：个股先通过基础可交易性，
# 再看它所处行业今天是否被 IRS 允许继续下传。
def _apply_irs_filter(store: Store, calc_date: date, config: Settings, df: pd.DataFrame) -> pd.DataFrame:
    """在开启 IRS 白名单时，只保留允许继续下传的行业。"""

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


# 当前主线使用的 DTT 候选路径。
# 这里的核心含义不是“谁最值得买”，而是“谁值得占用 PAS 的计算预算”。
# 因此 preselect_score 主要由流动性和活跃度组成，尽量不提前混入
# MSS / IRS / Gene 这种更强交易语义的层。
# 当前主线升格的 DTT 候选路径。
# 这条链回答的不是“谁最该买”，而是“谁值得占用 PAS 的计算预算”。
# 因此分数故意偏轻，只用流动性和活跃度做代理，不提前混入过强的交易语义。
def _select_dtt_candidates_frame(
    store: Store,
    calc_date: date,
    cfg: Settings,
    universe: pd.DataFrame,
    run_id: str = "",
) -> pd.DataFrame:
    """当前主线升格的 DTT 候选路径。

    DTT 主要回答“今天哪些票值得占用 PAS 计算预算”，
    它故意比真正的交易打分更轻，只承担调度，不承担最终买卖语义。
    """

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


# 历史冻结参照链。
# 这条链保留旧时代的粗筛 + MSS 门控 + IRS 白名单 + 简单综合分逻辑，
# 主要用于历史对齐、对照实验和 rollback。
# 历史冻结参照链。
# 这条路径保留旧时代的粗评分和行业/市场门控，用于历史对齐、迁移期对照实验和 rollback。
def _select_legacy_candidates_frame(
    store: Store,
    calc_date: date,
    cfg: Settings,
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """保留用于历史对照和回退的冻结参照链。"""

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


# 对外导出的运行时入口：把最终候选表转成 StockCandidate 对象列表。
# 这是 Selector 的对象出口：下游 Strategy 拿到的是 StockCandidate 契约，
# 而不是带各种中间字段的 DataFrame，符合“模块间只传结果契约”的治理要求。
def select_candidates(
    store: Store,
    calc_date: date,
    config: Settings | None = None,
    run_id: str | None = None,
) -> list[StockCandidate]:
    """按选定的 Selector 路径返回运行时 `StockCandidate` 契约对象。"""

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


# 返回某个交易日最终入围的候选 DataFrame。
# 这里只负责分派 legacy / dtt 路径，不直接承载买卖逻辑。
# 这个入口主要给研究、回测脚本、trace 和调试工具使用。
# 正式运行时更推荐 `select_candidates()`，因为它会把输出收敛到契约对象。
def select_candidates_frame(
    store: Store,
    calc_date: date,
    config: Settings | None = None,
    run_id: str | None = None,
) -> pd.DataFrame:
    """返回指定交易日最终入围的候选 `DataFrame`。"""

    cfg = config or get_settings()
    universe = _load_universe_snapshot(store, calc_date)
    if cfg.use_dtt_pipeline:
        return _select_dtt_candidates_frame(store, calc_date, cfg, universe, run_id=(run_id or "").strip())
    return _select_legacy_candidates_frame(store, calc_date, cfg, universe)
