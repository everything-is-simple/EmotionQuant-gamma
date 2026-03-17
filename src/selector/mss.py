from __future__ import annotations

"""市场情绪评分器 MSS。

MSS 的对象不是个股，也不是行业，而是“整个市场的一天”。
它先把当天市场快照压成六个原始因子，再映射成统一分数，最后派生出：
- signal：BULLISH / NEUTRAL / BEARISH
- phase：当前所处阶段
- risk_regime：Broker 可以直接消费的风险状态
- position_advice：解释层建议仓位带
"""

from datetime import date
from typing import Literal, Sequence

import numpy as np
import pandas as pd

from src.contracts import MarketScore
from src.data.store import Store
from src.selector.baseline import MSS_BASELINE
from src.selector.normalize import safe_ratio, zscore_single

MssSignalType = Literal["BULLISH", "NEUTRAL", "BEARISH"]
MssPhaseTrendType = Literal["UP", "SIDEWAYS", "DOWN"]
MssPhaseType = Literal[
    "EMERGENCE",
    "FERMENTATION",
    "ACCELERATION",
    "DIVERGENCE",
    "CLIMAX",
    "DIFFUSION",
    "RECESSION",
    "UNKNOWN",
]
MssRiskRegimeType = Literal["RISK_ON", "RISK_NEUTRAL", "RISK_OFF"]
MssTrendQualityType = Literal["NORMAL", "COLD_START"]

MSS_FACTOR_NAMES = [
    "market_coefficient",
    "profit_effect",
    "loss_effect",
    "continuity",
    "extreme",
    "volatility",
]

MSS_POSITION_ADVICE = {
    "EMERGENCE": "80%-100%",
    "FERMENTATION": "60%-80%",
    "ACCELERATION": "50%-70%",
    "DIVERGENCE": "40%-60%",
    "CLIMAX": "20%-40%",
    "DIFFUSION": "30%-50%",
    "RECESSION": "0%-20%",
    "UNKNOWN": "0%-20%",
}


def _signal_from_score(
    score: float,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> MssSignalType:
    if score >= bullish_threshold:
        return "BULLISH"
    if score <= bearish_threshold:
        return "BEARISH"
    return "NEUTRAL"


# 从单日市场快照提取 MSS 六个原始因子。
# 这一步只负责“把市场现象转成原始量”，还不做标准化，也不做状态解释。
def _compute_mss_raw_components(row: pd.Series) -> dict[str, float]:
    """从单日市场快照中提取 MSS 六个原始因子。

    注意这里仍然是“原始观测量”，不是正式分数：
    1. `market_coefficient` 看市场广度。
    2. `profit_effect` 看赚钱效应。
    3. `loss_effect` 看亏钱效应。
    4. `continuity` 看强势延续。
    5. `extreme` 看尾盘恐慌/挤压等极端情绪。
    6. `volatility` 看当日整体扰动强度。
    """

    """
    MSS 六因子原始值计算：
    1. market_coefficient: 上涨家数占比（市场广度）
    2. profit_effect: 赚钱效应（涨停 + 新高 + 强势上涨）
    3. loss_effect: 亏钱效应（炸板 + 跌停 + 强势下跌 + 新低）
    4. continuity: 连续性（连板 + 连续新高）
    5. extreme: 极端情绪（恐慌尾盘 + 挤压尾盘）
    6. volatility: 波动率（涨跌幅标准差 + 成交额波动）
    """
    total_stocks = row.get("total_stocks", 0) or 0
    limit_up_count = row.get("limit_up_count", 0) or 0
    new_high_count = row.get("new_100d_high_count", 0) or 0

    # 市场广度：上涨家数 / 总股票数
    market_coefficient_raw = safe_ratio(row.get("rise_count", 0), total_stocks, default=0.0)

    limit_up_ratio = safe_ratio(limit_up_count, total_stocks, default=0.0)
    new_high_ratio = safe_ratio(new_high_count, total_stocks, default=0.0)
    strong_up_ratio = safe_ratio(row.get("strong_up_count", 0), total_stocks, default=0.0)
    profit_effect_raw = 0.4 * limit_up_ratio + 0.3 * new_high_ratio + 0.3 * strong_up_ratio

    broken_rate = safe_ratio(row.get("touched_limit_up_count", 0), limit_up_count, default=0.0)
    limit_down_ratio = safe_ratio(row.get("limit_down_count", 0), total_stocks, default=0.0)
    strong_down_ratio = safe_ratio(row.get("strong_down_count", 0), total_stocks, default=0.0)
    new_low_ratio = safe_ratio(row.get("new_100d_low_count", 0), total_stocks, default=0.0)
    loss_effect_raw = (
        0.3 * broken_rate
        + 0.2 * limit_down_ratio
        + 0.3 * strong_down_ratio
        + 0.2 * new_low_ratio
    )

    cont_limit_up_ratio = safe_ratio(
        row.get("continuous_limit_up_2d", 0) + row.get("continuous_limit_up_3d_plus", 0),
        limit_up_count,
        default=0.0,
    )
    cont_new_high_ratio = safe_ratio(row.get("continuous_new_high_2d_plus", 0), new_high_count, default=0.0)
    continuity_raw = 0.5 * cont_limit_up_ratio + 0.5 * cont_new_high_ratio

    panic_tail_ratio = safe_ratio(row.get("high_open_low_close_count", 0), total_stocks, default=0.0)
    squeeze_tail_ratio = safe_ratio(row.get("low_open_high_close_count", 0), total_stocks, default=0.0)
    extreme_raw = panic_tail_ratio + squeeze_tail_ratio

    pct_chg_std = float(row.get("pct_chg_std", 0.0) or 0.0)
    amount_vol = float(row.get("amount_volatility", 0.0) or 0.0)
    amount_vol_ratio = amount_vol / (amount_vol + 1e6) if amount_vol > 0 else 0.0
    volatility_raw = 0.5 * pct_chg_std + 0.5 * amount_vol_ratio

    return {
        "market_coefficient_raw": market_coefficient_raw,
        "profit_effect_raw": profit_effect_raw,
        "loss_effect_raw": loss_effect_raw,
        "continuity_raw": continuity_raw,
        "extreme_raw": extreme_raw,
        "volatility_raw": volatility_raw,
    }


def compute_mss_raw_components(row: pd.Series) -> dict[str, float]:
    """公开原始六因子，供 Broker trace 解释层复用。"""
    return _compute_mss_raw_components(row)


def _normalize_score_history(score_history: Sequence[float] | None) -> list[float]:
    # 状态层只接受“可比较的历史分数”，把空值/非法值尽早滤掉，
    # 避免 cold start、趋势窗和 phase_days 在脏历史上产生假状态。
    normalized: list[float] = []
    for value in score_history or []:
        if value is None or pd.isna(value):
            continue
        numeric = float(value)
        if np.isfinite(numeric):
            normalized.append(numeric)
    return normalized


# 根据最近一段 MSS 分数历史，推断“市场状态趋势”。
# 这里看的是 MSS 自己的轨迹，而不是指数价格本身。
# 这里看的不是指数价格趋势，而是 MSS 自己这套情绪分的轨迹。
# 指数没明显走坏，并不代表情绪面没有先转弱。
def resolve_mss_phase_trend(
    score_history: Sequence[float] | None,
) -> tuple[MssPhaseTrendType, MssTrendQualityType]:
    """从近窗 MSS 分数历史推断当前趋势方向与质量。"""

    scores = _normalize_score_history(score_history)
    if len(scores) >= 8:
        # 正常路径优先用 8 日趋势窗：这是 blueprint 固定的主口径，
        # 目的是让 trend 判断依赖 MSS 自身历史，而不是上游信号或 Broker 状态。
        short_window = pd.Series(scores[-8:], dtype=float)
        ema_short = float(short_window.ewm(span=3, adjust=False).mean().iloc[-1])
        ema_long = float(short_window.ewm(span=8, adjust=False).mean().iloc[-1])
        slope_5d = (scores[-1] - scores[-5]) / 4.0
        trend_band = max(0.8, 0.15 * float(np.std(scores[-20:], ddof=0)))
        if ema_short > ema_long and slope_5d >= trend_band:
            return "UP", "NORMAL"
        if ema_short < ema_long and slope_5d <= -trend_band:
            return "DOWN", "NORMAL"
        return "SIDEWAYS", "NORMAL"

    recent = scores[-3:]
    if len(recent) >= 3:
        # 历史不足 8 日时进入 cold start：
        # 只保留最保守的“三日严格单调”判断，避免在刚起步的窗口里过拟合趋势方向。
        if recent[0] < recent[1] < recent[2]:
            return "UP", "COLD_START"
        if recent[0] > recent[1] > recent[2]:
            return "DOWN", "COLD_START"
    return "SIDEWAYS", "COLD_START"


def resolve_mss_phase(score: float, phase_trend: str) -> MssPhaseType:
    if pd.isna(score) or not np.isfinite(float(score)):
        return "UNKNOWN"
    normalized_trend = str(phase_trend or "").strip().upper()
    if normalized_trend not in {"UP", "SIDEWAYS", "DOWN"}:
        return "UNKNOWN"

    current_score = float(score)
    if current_score >= 75.0:
        # 高分优先落 CLIMAX：Phase 3 明确要求“高位风险”优先于“看起来很强”。
        return "CLIMAX"
    if normalized_trend == "UP":
        if current_score < 30.0:
            return "EMERGENCE"
        if current_score < 45.0:
            return "FERMENTATION"
        if current_score < 60.0:
            return "ACCELERATION"
        return "DIVERGENCE"
    if normalized_trend == "SIDEWAYS":
        return "DIVERGENCE" if current_score >= 60.0 else "RECESSION"
    if normalized_trend == "DOWN":
        return "DIFFUSION" if current_score >= 60.0 else "RECESSION"
    return "UNKNOWN"


# 统计当前 phase 已经持续了多少个连续交易日。
def resolve_mss_phase_days(
    phase: str,
    prev_phase: str | None = None,
    prev_phase_days: int | None = None,
) -> int:
    """统计当前 phase 已连续维持了多少个交易日。"""
    # phase_days 只看“上一交易日是否仍在同一 phase”，不看自然日；
    # 这样缺一天数据时不会偷偷把状态延续下去。
    if (
        str(prev_phase or "").strip().upper() == str(phase or "").strip().upper()
        and prev_phase_days is not None
        and int(prev_phase_days) > 0
    ):
        return int(prev_phase_days) + 1
    return 1


def resolve_mss_position_advice(phase: str) -> str:
    return MSS_POSITION_ADVICE.get(str(phase or "").strip().upper(), "0%-20%")


def resolve_mss_risk_regime(phase: str, phase_trend: str) -> MssRiskRegimeType:
    normalized_phase = str(phase or "").strip().upper()
    normalized_trend = str(phase_trend or "").strip().upper()
    if normalized_phase in {"EMERGENCE", "FERMENTATION", "ACCELERATION"} and normalized_trend == "UP":
        return "RISK_ON"
    if normalized_phase in {"DIVERGENCE", "DIFFUSION"}:
        return "RISK_NEUTRAL"
    if normalized_phase == "ACCELERATION" and normalized_trend != "UP":
        return "RISK_NEUTRAL"
    return "RISK_OFF"


# 从 MSS 历史分数推导完整市场状态。
# 返回的不只是 phase，还包括 risk_regime / position_advice / trend_quality。
# 返回的不只是 phase，还包括 phase_trend、phase_days、risk_regime 和 position_advice，
# 这样 Broker / trace / report 都可以只读一张日表，不必各自重复推断状态层。
def resolve_mss_state(
    score_history: Sequence[float] | None,
    prev_phase: str | None = None,
    prev_phase_days: int | None = None,
) -> dict[str, str | int]:
    """由 MSS 分数历史推导完整市场状态。"""

    scores = _normalize_score_history(score_history)
    if not scores:
        # 无历史时不做乐观推断：按 UNKNOWN + RISK_OFF 返回，
        # 让 Broker 在缺状态时默认保守，而不是把空白解释成 risk_on。
        return {
            "phase_trend": "SIDEWAYS",
            "phase": "UNKNOWN",
            "phase_days": 1,
            "position_advice": resolve_mss_position_advice("UNKNOWN"),
            "risk_regime": "RISK_OFF",
            "trend_quality": "COLD_START",
        }

    phase_trend, trend_quality = resolve_mss_phase_trend(scores)
    phase = resolve_mss_phase(scores[-1], phase_trend)
    phase_days = resolve_mss_phase_days(phase, prev_phase=prev_phase, prev_phase_days=prev_phase_days)
    position_advice = resolve_mss_position_advice(phase)
    risk_regime = resolve_mss_risk_regime(phase, phase_trend)
    return {
        "phase_trend": phase_trend,
        "phase": phase,
        "phase_days": phase_days,
        "position_advice": position_advice,
        "risk_regime": risk_regime,
        "trend_quality": trend_quality,
    }


def _normalize_mss_components(raw: dict[str, float], baseline: dict[str, float] | None = None) -> dict[str, float]:
    base = baseline or MSS_BASELINE
    # v0.01 主链仍以 z-score 为正式口径；percentile 对照只放在实验模块中。
    return {
        "market_coefficient": zscore_single(
            raw["market_coefficient_raw"],
            base["market_coefficient_mean"],
            base["market_coefficient_std"],
        ),
        "profit_effect": zscore_single(
            raw["profit_effect_raw"],
            base["profit_effect_mean"],
            base["profit_effect_std"],
        ),
        "loss_effect": zscore_single(
            raw["loss_effect_raw"],
            base["loss_effect_mean"],
            base["loss_effect_std"],
        ),
        "continuity": zscore_single(
            raw["continuity_raw"],
            base["continuity_mean"],
            base["continuity_std"],
        ),
        "extreme": zscore_single(
            raw["extreme_raw"],
            base["extreme_mean"],
            base["extreme_std"],
        ),
        "volatility": zscore_single(
            raw["volatility_raw"],
            base["volatility_mean"],
            base["volatility_std"],
        ),
    }


def _aggregate_mss_score(components: dict[str, float]) -> float:
    """
    MSS 总分聚合公式（v0.01 口径）：
    - 市场广度 17%
    - 赚钱效应 34%
    - 亏钱效应反向 34%（100 - loss_effect）
    - 连续性 5%
    - 极端情绪 5%
    - 波动率反向 5%（100 - volatility）
    
    最终 clip 到 [0, 100]
    """
    return float(
        np.clip(
            0.17 * components["market_coefficient"]
            + 0.34 * components["profit_effect"]
            + 0.34 * (100.0 - components["loss_effect"])
            + 0.05 * components["continuity"]
            + 0.05 * components["extreme"]
            + 0.05 * (100.0 - components["volatility"]),
            0.0,
            100.0,
        )
    )


# 把一行市场快照展开成完整、可追溯的 MSS 日记录。
# 这是 trace / report / debug 最常用的入口，因为它同时给出 raw、normalized 和 state。
def materialize_mss_trace_snapshot(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
    score_history: Sequence[float] | None = None,
    prev_phase: str | None = None,
    prev_phase_days: int | None = None,
) -> dict[str, float | str | date]:
    """把单日市场快照展开成完整、可追溯的 MSS 记录。"""

    """把市场快照展开成 trace 友好的原始值、标准化值和总分。"""
    # 这个函数专门给 trace / debug / report 用：
    # 一次性把 raw、标准化值和聚合分数都展开，避免下游自己重算。
    raw = _compute_mss_raw_components(row)
    components = _normalize_mss_components(raw, baseline=baseline)
    score = _aggregate_mss_score(components)
    d = row["date"]
    if isinstance(d, pd.Timestamp):
        d = d.date()
    history = _normalize_score_history(score_history)
    if not history or not np.isclose(history[-1], score):
        # 当前日 score 必须显式进入状态窗；
        # 这样落库的 phase/risk_regime 永远对应“今天的正式市场分”，不会错位到上一日。
        history.append(score)
    state = resolve_mss_state(history, prev_phase=prev_phase, prev_phase_days=prev_phase_days)
    return {
        "date": d,
        "score": score,
        "signal": _signal_from_score(score, bullish_threshold=bullish_threshold, bearish_threshold=bearish_threshold),
        **raw,
        **components,
        **state,
    }


def _compute_mss_components(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> tuple[
    date,
    float,
    Literal["BULLISH", "NEUTRAL", "BEARISH"],
    float,
    float,
    float,
    float,
    float,
    float,
]:
    # 这个函数专门给 trace / debug / report 用：
    # 一次性把 raw、标准化值和聚合分数都展开，避免下游自己重算。
    raw = _compute_mss_raw_components(row)
    components = _normalize_mss_components(raw, baseline=baseline)
    score = _aggregate_mss_score(components)

    d = row["date"]
    if isinstance(d, pd.Timestamp):
        d = d.date()
    return (
        d,
        score,
        _signal_from_score(score, bullish_threshold=bullish_threshold, bearish_threshold=bearish_threshold),
        components["market_coefficient"],
        components["profit_effect"],
        components["loss_effect"],
        components["continuity"],
        components["extreme"],
        components["volatility"],
    )


def build_mss_raw_frame(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    if snapshot_df is None or snapshot_df.empty:
        return pd.DataFrame(columns=["date"] + [f"{name}_raw" for name in MSS_FACTOR_NAMES])
    records: list[dict[str, float | date]] = []
    for _, row in snapshot_df.iterrows():
        d = row["date"]
        if isinstance(d, pd.Timestamp):
            d = d.date()
        raw = _compute_mss_raw_components(row)
        records.append({"date": d, **raw})
    return pd.DataFrame(records)


def calibrate_mss_baseline(raw_df: pd.DataFrame) -> dict[str, float]:
    baseline: dict[str, float] = {}
    for factor in MSS_FACTOR_NAMES:
        values = pd.to_numeric(raw_df.get(f"{factor}_raw"), errors="coerce").dropna()
        mean = float(values.mean()) if not values.empty else 0.0
        std = float(values.std(ddof=0)) if not values.empty else 1.0
        baseline[f"{factor}_mean"] = mean
        baseline[f"{factor}_std"] = std if std > 0 else 1.0
    return baseline


def score_mss_raw_frame(
    raw_df: pd.DataFrame,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=["date", "score", "signal"] + MSS_FACTOR_NAMES)

    base = baseline or MSS_BASELINE
    # 这个 helper 主要服务校准/实验脚本，不在主链高频路径里；
    # 逐日展开比过度压缩成一段难维护的向量逻辑更合适。
    rows: list[dict[str, float | str | date]] = []
    for _, row in raw_df.iterrows():
        raw = {key: float(row[key]) for key in raw_df.columns if key.endswith("_raw")}
        components = _normalize_mss_components(raw, baseline=base)
        score = _aggregate_mss_score(components)
        if score >= bullish_threshold:
            signal = "BULLISH"
        elif score <= bearish_threshold:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        d = row["date"]
        if isinstance(d, pd.Timestamp):
            d = d.date()
        rows.append({"date": d, "score": score, "signal": signal, **components})
    return pd.DataFrame(rows)


def compute_mss_single(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> MarketScore:
    """
    MSS 单日纯函数：
    输入是一行 l2_market_snapshot，输出 MarketScore。
    """
    d, score, signal, *_ = _compute_mss_components(
        row,
        baseline=baseline,
        bullish_threshold=bullish_threshold,
        bearish_threshold=bearish_threshold,
    )
    return MarketScore(date=d, score=score, signal=signal)

# Main MSS batch entry point。
# build_l3 就是通过这里把整段市场状态落进 l3_mss_daily。
# 这是 MSS 的正式批量入口。它按交易日重建：
# 1. 六个原始因子
# 2. 归一化分量与总分
# 3. signal / phase / risk_regime / position_advice
# 最终形成 Broker 和报告链都能直接消费的正式日表。
def compute_mss(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> int:
    """批量计算 MSS，并写入完整市场状态表。"""
    """
    批量计算 MSS 并写入 l3_mss_daily（幂等 upsert）。
    """
    df = store.read_df(
        """
        SELECT * FROM l2_market_snapshot
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if df.empty:
        return 0

    score_history: list[float] = []
    prev_phase: str | None = None
    prev_phase_days: int | None = None
    prior_df = store.read_df(
        """
        SELECT date, score
        FROM l3_mss_daily
        WHERE date < ?
        ORDER BY date DESC
        LIMIT 20
        """,
        (start,),
    )
    if not prior_df.empty:
        # 启动窗口前最多回看 20 个交易日的 MSS 历史，只为恢复状态层上下文；
        # 不把旧 phase 直接当真相源复写，而是重新按当前规则推导出 prev_phase/prev_phase_days。
        for _, prior_row in prior_df.sort_values("date").iterrows():
            prior_score = prior_row["score"]
            if prior_score is None or pd.isna(prior_score):
                continue
            score_history.append(float(prior_score))
            score_history = score_history[-20:]
            prior_state = resolve_mss_state(
                score_history,
                prev_phase=prev_phase,
                prev_phase_days=prev_phase_days,
            )
            prev_phase = str(prior_state["phase"])
            prev_phase_days = int(prior_state["phase_days"])

    records = []
    for _, row in df.iterrows():
        # MSS 仍然是“市场日评分器”：每个交易日只产出一条 MarketScore，不参与个股横截面筛选。
        # 这里直接把 raw + normalized 一起持久化到 l3_mss_daily，避免 Broker 为了 trace 再回头重算。
        # 日级记录量本身很小，所以这里优先选“结果清晰、trace 完整”，不刻意把代码压成难读向量化。
        # Phase 3 新增状态层也在这里一次性落库，保证 l3_mss_daily 自己就能回答：
        # “今天是什么分数、处在哪个阶段、Broker 应该按哪个 regime 执行”。
        snapshot = materialize_mss_trace_snapshot(
            row,
            baseline=baseline,
            bullish_threshold=bullish_threshold,
            bearish_threshold=bearish_threshold,
            score_history=score_history,
            prev_phase=prev_phase,
            prev_phase_days=prev_phase_days,
        )
        records.append(snapshot)
        score_history.append(float(snapshot["score"]))
        score_history = score_history[-20:]
        prev_phase = str(snapshot["phase"])
        prev_phase_days = int(snapshot["phase_days"])
    return store.bulk_upsert("l3_mss_daily", pd.DataFrame(records))
