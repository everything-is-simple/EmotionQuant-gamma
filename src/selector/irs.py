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
IRS_TRACE_FILL_SCORE = 50.0

IRS_FACTOR_WEIGHT_RS = 0.30
IRS_FACTOR_WEIGHT_RV = 0.25
IRS_FACTOR_WEIGHT_RT = 0.15
IRS_FACTOR_WEIGHT_BD = 0.15
IRS_FACTOR_WEIGHT_GN = 0.15
IRS_RT_LOOKBACK_DAYS = 5
IRS_TOP_RANK_THRESHOLD = 3
IRS_HISTORY_LOOKBACK_DAYS = 25
IRS_FACTOR_MODE_LITE = "lite"
IRS_FACTOR_MODE_RSRV = "rsrv"
IRS_FACTOR_MODE_FULL = "rsrvrtbdgn"
# 这组常量保留“无配置时的安全默认值”：
# 真正运行时会优先吃 config.py 传下来的窗口、阈值和权重。


def normalize_irs_factor_mode(value: str | None) -> str:
    raw = str(value or IRS_FACTOR_MODE_FULL).strip().lower().replace("-", "").replace("_", "")
    if raw in {"lite", "legacy", "irslite"}:
        return IRS_FACTOR_MODE_LITE
    if raw in {"rsrv", "irsrsrv"}:
        return IRS_FACTOR_MODE_RSRV
    if raw in {"full", "rsrvrtbdgn", "irsrsrvrtbdgn"}:
        return IRS_FACTOR_MODE_FULL
    raise ValueError(f"Unsupported IRS factor mode: {value}")


def _trace_variant_for_factor_mode(factor_mode: str) -> str:
    normalized = normalize_irs_factor_mode(factor_mode)
    if normalized == IRS_FACTOR_MODE_LITE:
        return "IRS_DAILY_LITE"
    if normalized == IRS_FACTOR_MODE_RSRV:
        return "IRS_DAILY_RSRV"
    return "IRS_DAILY_RSRVRTBDGN"


def _build_irs_trace_run_id(start: date, end: date, factor_mode: str) -> str:
    normalized = normalize_irs_factor_mode(factor_mode)
    return f"IRS_DAILY::{normalized}::{start.isoformat()}::{end.isoformat()}"


def _build_irs_trace_signal_id(trade_date: date, industry: str) -> str:
    normalized_industry = str(industry or "__DAY__").strip() or "__DAY__"
    return f"IRS_DAILY::{trade_date.isoformat()}::{normalized_industry}"


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _safe_float(value: object, default: float = 0.0) -> float:
    cast = pd.to_numeric(value, errors="coerce")
    if pd.isna(cast):
        return float(default)
    return float(cast)


def _zscore_or_fill(value: float | None, mean: float, std: float) -> float:
    if value is None or not np.isfinite(float(value)):
        return IRS_TRACE_FILL_SCORE
    return zscore_single(float(value), mean, std)


def _rolling_compound_return(series: pd.Series, window: int) -> pd.Series:
    clipped = pd.to_numeric(series, errors="coerce").fillna(0.0).clip(lower=-0.99)
    return np.exp(np.log1p(clipped).rolling(window, min_periods=window).sum()) - 1.0


def _lookback_trade_start(store: Store, start: date, days: int) -> date:
    current = start
    for _ in range(max(0, days)):
        prev = store.prev_trade_date(current)
        if prev is None:
            return current
        current = prev
    return current


def _load_benchmark_snapshot_map(store: Store, start: date, end: date) -> dict[date, dict[str, float | bool]]:
    benchmark_df = store.read_df(
        """
        SELECT date, pct_chg
        FROM l1_index_daily
        WHERE ts_code = ? AND date BETWEEN ? AND ?
        ORDER BY date ASC
        """,
        (IRS_TRACE_BENCHMARK_CODE, start, end),
    )
    if benchmark_df.empty:
        return {}
    benchmark_df = benchmark_df.copy()
    benchmark_df["date"] = pd.to_datetime(benchmark_df["date"]).dt.date
    benchmark_df["pct_chg"] = pd.to_numeric(benchmark_df["pct_chg"], errors="coerce")
    benchmark_df["return_5d"] = _rolling_compound_return(benchmark_df["pct_chg"], 5)
    benchmark_df["return_20d"] = _rolling_compound_return(benchmark_df["pct_chg"], 20)
    snapshot_map: dict[date, dict[str, float | bool]] = {}
    for _, row in benchmark_df.iterrows():
        snapshot_map[row["date"]] = {
            "pct_chg": _safe_float(row["pct_chg"], 0.0),
            "return_5d": _safe_float(row["return_5d"], 0.0),
            "return_20d": _safe_float(row["return_20d"], 0.0),
            "filled": bool(pd.isna(row["pct_chg"]) or pd.isna(row["return_5d"]) or pd.isna(row["return_20d"])),
        }
    return snapshot_map


def _rank_stability_raw(rank_history: list[int], industry_count_today: int, rt_lookback_days: int) -> float:
    if len(rank_history) < rt_lookback_days:
        return 0.5
    denominator = max(industry_count_today / 3.0, 1.0)
    return 1.0 - _clip01(float(np.std(rank_history, ddof=0)) / denominator)


def _count_consecutive_top_ranks(rank_window: list[int], top_rank_threshold: int) -> int:
    streak = 0
    for rank in reversed(rank_window):
        if int(rank) <= top_rank_threshold:
            streak += 1
        else:
            break
    return streak


def _resolve_rotation_status(
    rank: int,
    top_rank_streak_5d: int,
    rotation_slope: float,
    momentum_consistency: float,
    top_rank_threshold: int,
) -> str:
    if rank <= top_rank_threshold and top_rank_streak_5d in {1, 2} and rotation_slope >= 2.0:
        return "START"
    if rank <= top_rank_threshold and top_rank_streak_5d >= 3 and momentum_consistency >= 0.50:
        return "CONTINUE"
    if rank <= max(5, top_rank_threshold + 2) and rotation_slope < 0.0 and momentum_consistency < 0.50:
        return "EXHAUST"
    if rank > max(5, top_rank_threshold + 2) and rotation_slope <= -2.0:
        return "FALLBACK"
    return "NEUTRAL"


def _compute_rs_components(
    industry_row: pd.Series,
    benchmark_snapshot: dict[str, float | bool],
    rank_history: list[int],
    industry_count_today: int,
    baseline: dict[str, float],
    rt_lookback_days: int,
) -> dict[str, float]:
    rs_1d_raw = _safe_float(industry_row.get("pct_chg"), 0.0) - float(benchmark_snapshot["pct_chg"])
    rs_5d_raw = (
        _safe_float(industry_row.get("return_5d"), 0.0) - float(benchmark_snapshot["return_5d"])
        if pd.notna(pd.to_numeric(industry_row.get("return_5d"), errors="coerce"))
        else None
    )
    rs_20d_raw = (
        _safe_float(industry_row.get("return_20d"), 0.0) - float(benchmark_snapshot["return_20d"])
        if pd.notna(pd.to_numeric(industry_row.get("return_20d"), errors="coerce"))
        else None
    )
    rank_stability = _rank_stability_raw(rank_history, industry_count_today, rt_lookback_days)
    rs_score = (
        0.35 * _zscore_or_fill(rs_1d_raw, baseline["rs_score_mean"], baseline["rs_score_std"])
        + 0.35 * _zscore_or_fill(rs_5d_raw, baseline["rs_score_mean"], baseline["rs_score_std"])
        + 0.20 * _zscore_or_fill(rs_20d_raw, baseline["rs_score_mean"], baseline["rs_score_std"])
        + 0.10 * (100.0 * rank_stability)
    )
    return {
        "rs_1d_raw": float(rs_1d_raw),
        "rs_5d_raw": IRS_TRACE_FILL_SCORE if rs_5d_raw is None else float(rs_5d_raw),
        "rs_20d_raw": IRS_TRACE_FILL_SCORE if rs_20d_raw is None else float(rs_20d_raw),
        "rank_stability_raw": float(rank_stability),
        "rs_score": float(rs_score),
    }


def _compute_rv_components(industry_row: pd.Series, baseline: dict[str, float]) -> dict[str, float]:
    amount = _safe_float(industry_row.get("amount"), 0.0)
    market_total_amount = _safe_float(industry_row.get("market_total_amount"), 0.0)
    amount_ma20 = pd.to_numeric(industry_row.get("amount_ma20"), errors="coerce")
    amount_10d_ago = pd.to_numeric(industry_row.get("amount_10d_ago"), errors="coerce")
    strong_amount_share = pd.to_numeric(industry_row.get("strong_stock_amount_share"), errors="coerce")
    flow_share = safe_ratio(amount, market_total_amount, np.nan)
    amount_vs_self_20d = safe_ratio(amount, float(amount_ma20), np.nan) if pd.notna(amount_ma20) else np.nan
    amount_delta_10d = safe_ratio(amount, float(amount_10d_ago), np.nan) - 1.0 if pd.notna(amount_10d_ago) else np.nan
    strong_amount_component = 100.0 * _clip01(float(strong_amount_share)) if pd.notna(strong_amount_share) else IRS_TRACE_FILL_SCORE
    rv_score = (
        0.35 * _zscore_or_fill(amount_vs_self_20d, baseline["cf_score_mean"], baseline["cf_score_std"])
        + 0.25 * _zscore_or_fill(flow_share, baseline["cf_score_mean"], baseline["cf_score_std"])
        + 0.20 * _zscore_or_fill(amount_delta_10d, baseline["cf_score_mean"], baseline["cf_score_std"])
        + 0.20 * strong_amount_component
    )
    legacy_cf_raw = 0.0
    if np.isfinite(flow_share):
        legacy_cf_raw += float(flow_share)
    if np.isfinite(amount_delta_10d):
        legacy_cf_raw += float(amount_delta_10d)
    return {
        "amount": amount,
        "market_total_amount": market_total_amount,
        "amount_delta_10d": IRS_TRACE_FILL_SCORE if not np.isfinite(amount_delta_10d) else float(amount_delta_10d),
        "flow_share": IRS_TRACE_FILL_SCORE if not np.isfinite(flow_share) else float(flow_share),
        "amount_vs_self_20d": IRS_TRACE_FILL_SCORE if not np.isfinite(amount_vs_self_20d) else float(amount_vs_self_20d),
        "strong_amount_share": IRS_TRACE_FILL_SCORE if pd.isna(strong_amount_share) else float(_clip01(float(strong_amount_share))),
        "cf_raw": float(legacy_cf_raw),
        "rv_score": float(rv_score),
    }


def _compute_legacy_cf_components(flow_share: float, amount_delta_10d: float, baseline: dict[str, float]) -> dict[str, float]:
    cf_raw = 0.0
    if np.isfinite(flow_share):
        cf_raw += float(flow_share)
    if np.isfinite(amount_delta_10d):
        cf_raw += float(amount_delta_10d)
    cf_score = _zscore_or_fill(cf_raw, baseline["cf_score_mean"], baseline["cf_score_std"])
    return {"cf_raw": float(cf_raw), "cf_score": float(cf_score)}


def _compute_bd_components(industry_row: pd.Series) -> dict[str, float]:
    if not bool(industry_row.get("structure_available", False)):
        return {"bd_score": IRS_TRACE_FILL_SCORE}
    stock_count = max(int(_safe_float(industry_row.get("stock_count"), 0.0)), 1)
    up_ratio = _clip01(_safe_float(industry_row.get("rise_count"), 0.0) / stock_count)
    net_breadth = (_safe_float(industry_row.get("rise_count"), 0.0) - _safe_float(industry_row.get("fall_count"), 0.0)) / stock_count
    strong_up_ratio = _clip01(_safe_float(industry_row.get("strong_up_count"), 0.0) / stock_count)
    new_high_ratio = _clip01(_safe_float(industry_row.get("new_high_count"), 0.0) / stock_count)
    bof_density = _clip01(_safe_float(industry_row.get("bof_hit_density_5d"), 0.0) * 5.0)
    bd_score = 100.0 * _clip01(
        0.30 * up_ratio
        + 0.25 * ((max(-1.0, min(1.0, net_breadth)) + 1.0) / 2.0)
        + 0.20 * strong_up_ratio
        + 0.15 * new_high_ratio
        + 0.10 * bof_density
    )
    return {"bd_score": float(bd_score)}


def _compute_gn_components(industry_row: pd.Series) -> dict[str, float]:
    if not bool(industry_row.get("structure_available", False)):
        return {"gn_score": IRS_TRACE_FILL_SCORE}
    stock_count = max(int(_safe_float(industry_row.get("stock_count"), 0.0)), 1)
    leader_count_ratio = _clip01(_safe_float(industry_row.get("leader_count"), 0.0) / stock_count)
    leader_strength = _clip01(_safe_float(industry_row.get("leader_strength"), 0.0))
    leader_follow = _clip01(_safe_float(industry_row.get("leader_follow_through"), 0.0))
    strong_stock_ratio = _clip01(_safe_float(industry_row.get("strong_stock_ratio"), 0.0))
    gn_score = 100.0 * _clip01(
        0.35 * leader_strength
        + 0.25 * leader_count_ratio
        + 0.20 * leader_follow
        + 0.20 * strong_stock_ratio
    )
    return {"gn_score": float(gn_score)}


def _compute_rt_components(
    provisional_rank: int,
    provisional_score: float,
    rank_history: list[int],
    score_history: list[float],
    top_rank_threshold: int,
    rt_lookback_days: int,
) -> dict[str, float | str]:
    if len(rank_history) < rt_lookback_days - 1 or len(score_history) < rt_lookback_days - 1:
        return {
            "rt_score": IRS_TRACE_FILL_SCORE,
            "rotation_status": "NEUTRAL",
            "rotation_slope": 0.0,
            "top_rank_streak_5d": 0,
            "momentum_consistency": 0.5,
        }
    rank_window = rank_history[-(rt_lookback_days - 1) :] + [int(provisional_rank)]
    score_window = score_history[-(rt_lookback_days - 1) :] + [float(provisional_score)]
    top_rank_streak_5d = _count_consecutive_top_ranks(rank_window, top_rank_threshold)
    rotation_slope = (score_window[-1] - score_window[0]) / max(rt_lookback_days - 1, 1)
    diffs = np.diff(np.asarray(score_window, dtype=float))
    momentum_consistency = float((diffs > 0).sum()) / max(len(diffs), 1)
    rotation_status = _resolve_rotation_status(
        provisional_rank,
        top_rank_streak_5d,
        float(rotation_slope),
        momentum_consistency,
        top_rank_threshold,
    )
    rt_core = 100.0 * _clip01(
        0.40 * (top_rank_streak_5d / 5.0)
        + 0.35 * _clip01((rotation_slope + 4.0) / 8.0)
        + 0.25 * momentum_consistency
    )
    status_bonus = 5.0 if rotation_status in {"START", "CONTINUE"} else -5.0 if rotation_status in {"EXHAUST", "FALLBACK"} else 0.0
    return {
        "rt_score": float(np.clip(rt_core + status_bonus, 0.0, 100.0)),
        "rotation_status": rotation_status,
        "rotation_slope": float(rotation_slope),
        "top_rank_streak_5d": int(top_rank_streak_5d),
        "momentum_consistency": float(momentum_consistency),
    }


def _weighted_score(components: list[tuple[float, float]], fallback: float) -> float:
    # 允许某些因子在 ablation 中权重为 0；此时自动回落到 fallback，
    # 避免除以 0 或把“关闭的因子”误算成噪声。
    positive = [(float(score), float(weight)) for score, weight in components if float(weight) > 0.0]
    total_weight = sum(weight for _, weight in positive)
    if total_weight <= 0:
        return float(fallback)
    return sum(score * weight for score, weight in positive) / total_weight


def _pre_rt_score_for_mode(
    rs_score: float,
    cf_score: float,
    rv_score: float,
    bd_score: float,
    gn_score: float,
    factor_mode: str,
    factor_weight_rs: float,
    factor_weight_rv: float,
    factor_weight_bd: float,
    factor_weight_gn: float,
) -> float:
    normalized = normalize_irs_factor_mode(factor_mode)
    if normalized == IRS_FACTOR_MODE_LITE:
        return 0.55 * rs_score + 0.45 * cf_score
    if normalized == IRS_FACTOR_MODE_RSRV:
        return _weighted_score(
            [(rs_score, factor_weight_rs), (rv_score, factor_weight_rv)],
            fallback=IRS_TRACE_FILL_SCORE,
        )
    return _weighted_score(
        [
            (rs_score, factor_weight_rs),
            (rv_score, factor_weight_rv),
            (bd_score, factor_weight_bd),
            (gn_score, factor_weight_gn),
        ],
        fallback=IRS_TRACE_FILL_SCORE,
    )


def _total_score_for_mode(
    rs_score: float,
    cf_score: float,
    rv_score: float,
    rt_score: float,
    bd_score: float,
    gn_score: float,
    factor_mode: str,
    factor_weight_rs: float,
    factor_weight_rv: float,
    factor_weight_rt: float,
    factor_weight_bd: float,
    factor_weight_gn: float,
) -> float:
    normalized = normalize_irs_factor_mode(factor_mode)
    if normalized == IRS_FACTOR_MODE_LITE:
        return 0.55 * rs_score + 0.45 * cf_score
    if normalized == IRS_FACTOR_MODE_RSRV:
        return _weighted_score(
            [(rs_score, factor_weight_rs), (rv_score, factor_weight_rv)],
            fallback=IRS_TRACE_FILL_SCORE,
        )
    return _weighted_score(
        [
            (rs_score, factor_weight_rs),
            (rv_score, factor_weight_rv),
            (rt_score, factor_weight_rt),
            (bd_score, factor_weight_bd),
            (gn_score, factor_weight_gn),
        ],
        fallback=IRS_TRACE_FILL_SCORE,
    )


def _build_industry_trace_row(
    trace_run_id: str,
    trade_date: date,
    industry_row: pd.Series,
    components: dict[str, object],
    coverage_flag: str,
    variant_label: str,
    industry_score: float | None = None,
    industry_rank: int | None = None,
    benchmark_pct: float = 0.0,
) -> dict[str, object]:
    resolved_score = float(industry_score if industry_score is not None else pd.to_numeric(components.get("total_score"), errors="coerce"))
    if not np.isfinite(resolved_score):
        resolved_score = 0.0
    return {
        "run_id": trace_run_id,
        "signal_id": _build_irs_trace_signal_id(trade_date, str(industry_row.get("industry", ""))),
        "signal_date": trade_date,
        "code": "",
        "industry": str(industry_row.get("industry", "")),
        "variant": variant_label,
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
        "industry_pct_chg": _safe_float(components.get("industry_pct"), 0.0),
        "amount": _safe_float(components.get("amount"), 0.0),
        "market_total_amount": _safe_float(components.get("market_total_amount"), 0.0),
        "amount_delta_10d": _safe_float(components.get("amount_delta_10d"), IRS_TRACE_FILL_SCORE),
        "rs_raw": _safe_float(components.get("rs_1d_raw"), 0.0),
        "cf_raw": _safe_float(components.get("cf_raw"), 0.0),
        "rs_score": _safe_float(components.get("rs_score"), IRS_TRACE_FILL_SCORE),
        "cf_score": _safe_float(components.get("cf_score"), IRS_TRACE_FILL_SCORE),
        "rv_score": _safe_float(components.get("rv_score"), IRS_TRACE_FILL_SCORE),
        "rt_score": _safe_float(components.get("rt_score"), IRS_TRACE_FILL_SCORE),
        "bd_score": _safe_float(components.get("bd_score"), IRS_TRACE_FILL_SCORE),
        "gn_score": _safe_float(components.get("gn_score"), IRS_TRACE_FILL_SCORE),
        "rotation_status": str(components.get("rotation_status", "NEUTRAL")),
        "rotation_slope": _safe_float(components.get("rotation_slope"), 0.0),
        "industry_count_today": int(_safe_float(components.get("industry_count_today"), 0.0)),
        "rs_1d_raw": _safe_float(components.get("rs_1d_raw"), IRS_TRACE_FILL_SCORE),
        "rs_5d_raw": _safe_float(components.get("rs_5d_raw"), IRS_TRACE_FILL_SCORE),
        "rs_20d_raw": _safe_float(components.get("rs_20d_raw"), IRS_TRACE_FILL_SCORE),
        "rank_stability_raw": _safe_float(components.get("rank_stability_raw"), 0.5),
        "flow_share": _safe_float(components.get("flow_share"), IRS_TRACE_FILL_SCORE),
        "amount_vs_self_20d": _safe_float(components.get("amount_vs_self_20d"), IRS_TRACE_FILL_SCORE),
        "strong_amount_share": _safe_float(components.get("strong_amount_share"), IRS_TRACE_FILL_SCORE),
        "top_rank_streak_5d": int(_safe_float(components.get("top_rank_streak_5d"), 0.0)),
        "momentum_consistency": _safe_float(components.get("momentum_consistency"), 0.5),
        "industry_score": resolved_score,
        "industry_rank": industry_rank,
        "coverage_flag": coverage_flag,
    }


def compute_irs_single(
    industry_row: pd.Series,
    benchmark_pct: float,
    baseline: dict[str, float] | None = None,
    factor_mode: str = IRS_FACTOR_MODE_FULL,
    factor_weight_rs: float = IRS_FACTOR_WEIGHT_RS,
    factor_weight_rv: float = IRS_FACTOR_WEIGHT_RV,
    factor_weight_rt: float = IRS_FACTOR_WEIGHT_RT,
    factor_weight_bd: float = IRS_FACTOR_WEIGHT_BD,
    factor_weight_gn: float = IRS_FACTOR_WEIGHT_GN,
) -> tuple[float, float, float]:
    base = baseline or IRS_BASELINE
    normalized_factor_mode = normalize_irs_factor_mode(factor_mode)
    seeded = industry_row.copy()
    seeded["market_total_amount"] = _safe_float(industry_row.get("market_total_amount"), _safe_float(industry_row.get("amount"), 0.0))
    seeded["stock_count"] = max(int(_safe_float(industry_row.get("stock_count"), 1.0)), 1)
    seeded["structure_available"] = bool(industry_row.get("structure_available", False))
    rs = _compute_rs_components(
        seeded,
        {"pct_chg": float(benchmark_pct), "return_5d": 0.0, "return_20d": 0.0, "filled": False},
        [],
        int(seeded["stock_count"]),
        base,
        IRS_RT_LOOKBACK_DAYS,
    )
    rv = _compute_rv_components(seeded, base)
    legacy_cf = _compute_legacy_cf_components(rv["flow_share"], rv["amount_delta_10d"], base)
    bd = _compute_bd_components(seeded)
    gn = _compute_gn_components(seeded)
    total_score = _total_score_for_mode(
        rs["rs_score"],
        legacy_cf["cf_score"],
        rv["rv_score"],
        IRS_TRACE_FILL_SCORE,
        bd["bd_score"],
        gn["gn_score"],
        normalized_factor_mode,
        factor_weight_rs,
        factor_weight_rv,
        factor_weight_rt,
        factor_weight_bd,
        factor_weight_gn,
    )
    secondary_score = legacy_cf["cf_score"] if normalized_factor_mode == IRS_FACTOR_MODE_LITE else rv["rv_score"]
    return rs["rs_score"], float(secondary_score), float(total_score)


def compute_irs(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
    min_industries_per_day: int = 1,
    rt_lookback_days: int = IRS_RT_LOOKBACK_DAYS,
    top_rank_threshold: int = IRS_TOP_RANK_THRESHOLD,
    factor_mode: str = IRS_FACTOR_MODE_FULL,
    factor_weight_rs: float = IRS_FACTOR_WEIGHT_RS,
    factor_weight_rv: float = IRS_FACTOR_WEIGHT_RV,
    factor_weight_rt: float = IRS_FACTOR_WEIGHT_RT,
    factor_weight_bd: float = IRS_FACTOR_WEIGHT_BD,
    factor_weight_gn: float = IRS_FACTOR_WEIGHT_GN,
) -> int:
    normalized_factor_mode = normalize_irs_factor_mode(factor_mode)
    trace_variant = _trace_variant_for_factor_mode(normalized_factor_mode)
    trace_run_id = _build_irs_trace_run_id(start, end, normalized_factor_mode)
    base = baseline or IRS_BASELINE
    # 只回看“够支撑 RT/多周期收益”的最小历史，不把整段 history_start..today 一次吞进来。
    history_start = _lookback_trade_start(store, start, IRS_HISTORY_LOOKBACK_DAYS)
    store.conn.execute(
        """
        DELETE FROM irs_industry_trace_exp
        WHERE run_id = ? AND COALESCE(trace_scope, ?) = ?
        """,
        [trace_run_id, IRS_TRACE_SCOPE_SIGNAL_ATTACH, IRS_TRACE_SCOPE_INDUSTRY_DAILY],
    )
    store.conn.execute("DELETE FROM l3_irs_daily WHERE date BETWEEN ? AND ?", [start, end])
    industry_df = store.read_df(
        """
        SELECT
            d.*,
            s.strong_up_count,
            s.new_high_count,
            s.leader_count,
            s.leader_strength,
            s.strong_stock_ratio,
            s.strong_stock_amount_share,
            s.leader_follow_through,
            s.bof_hit_density_5d
        FROM l2_industry_daily d
        LEFT JOIN l2_industry_structure_daily s
            ON s.industry = d.industry AND s.date = d.date
        WHERE d.date BETWEEN ? AND ?
        ORDER BY d.date ASC, d.industry ASC
        """,
        (history_start, end),
    )
    # 这里仍会把“受控窗口内的行业日线”物化到 pandas；
    # 当前行业层体量足够小、而且 Phase 2 需要逐日推进 RT 状态，所以这是可接受的折中。
    # 如果后续 IRS 继续横向扩因子/扩 trace，优先考虑把更多聚合前推回 DuckDB。
    if industry_df.empty:
        return 0

    industry_df = industry_df.copy()
    industry_df["date"] = pd.to_datetime(industry_df["date"]).dt.date
    industry_df["industry"] = industry_df["industry"].fillna("未知").astype(str)
    industry_df["market_total_amount"] = industry_df.groupby("date")["amount"].transform("sum")
    industry_df["amount_10d_ago"] = industry_df.groupby("industry")["amount"].shift(10)
    industry_df["structure_available"] = industry_df["strong_up_count"].notna()
    benchmark_map = _load_benchmark_snapshot_map(store, history_start, end)
    market_total_map = {day: float(total or 0.0) for day, total in industry_df.groupby("date")["amount"].sum().items()}

    output_rows: list[dict[str, object]] = []
    trace_rows: list[dict[str, object]] = []
    rank_history_by_industry: dict[str, list[int]] = {}
    score_history_by_industry: dict[str, list[float]] = {}

    for day, day_df in industry_df.groupby("date", sort=True):
        # IRS 是“按交易日推进”的状态计算：
        # RS/RV/BD/GN 先在当日行业横截面上得 provisional score，
        # RT 再利用近几日 rank/score 历史补 rotation 语义，最后才产正式 daily rank。
        benchmark_snapshot = benchmark_map.get(day, {"pct_chg": 0.0, "return_5d": 0.0, "return_20d": 0.0, "filled": True})
        benchmark_pct = float(benchmark_snapshot["pct_chg"])
        coverage_flag = "BENCHMARK_FILL" if bool(benchmark_snapshot["filled"]) else "NORMAL"
        day_df = day_df.copy()
        unknown_df = day_df[day_df["industry"] == "未知"].copy()
        known_df = day_df[day_df["industry"] != "未知"].copy()
        # “未知行业”只保留 trace，不进入 formal 排名。
        # 这样可以显式暴露覆盖缺口，同时避免把错误行业桶带进 DTT attach。

        if start <= day <= end:
            for _, row in unknown_df.iterrows():
                trace_rows.append(
                    _build_industry_trace_row(
                        trace_run_id,
                        day,
                        row,
                        {
                            "industry_pct": _safe_float(row.get("pct_chg"), 0.0),
                            "amount": _safe_float(row.get("amount"), 0.0),
                            "market_total_amount": market_total_map.get(day, 0.0),
                            "amount_delta_10d": IRS_TRACE_FILL_SCORE,
                            "rs_1d_raw": _safe_float(row.get("pct_chg"), 0.0) - benchmark_pct,
                            "rs_5d_raw": IRS_TRACE_FILL_SCORE,
                            "rs_20d_raw": IRS_TRACE_FILL_SCORE,
                            "rank_stability_raw": 0.5,
                            "rs_score": _zscore_or_fill(_safe_float(row.get("pct_chg"), 0.0) - benchmark_pct, base["rs_score_mean"], base["rs_score_std"]),
                            "cf_raw": 0.0,
                            "cf_score": IRS_TRACE_FILL_SCORE,
                            "rv_score": IRS_TRACE_FILL_SCORE,
                            "rt_score": IRS_TRACE_FILL_SCORE,
                            "bd_score": IRS_TRACE_FILL_SCORE,
                            "gn_score": IRS_TRACE_FILL_SCORE,
                            "rotation_status": "NEUTRAL",
                            "rotation_slope": 0.0,
                            "industry_count_today": len(known_df),
                            "flow_share": IRS_TRACE_FILL_SCORE,
                            "amount_vs_self_20d": IRS_TRACE_FILL_SCORE,
                            "strong_amount_share": IRS_TRACE_FILL_SCORE,
                            "top_rank_streak_5d": 0,
                            "momentum_consistency": 0.5,
                            "total_score": 0.0,
                        },
                        "UNKNOWN_DROPPED",
                        trace_variant,
                        benchmark_pct=benchmark_pct,
                    )
                )
        if known_df.empty:
            continue

        industry_count_today = len(known_df)
        day_components: list[dict[str, object]] = []
        for _, row in known_df.iterrows():
            industry = str(row["industry"])
            rs = _compute_rs_components(
                row,
                benchmark_snapshot,
                rank_history_by_industry.get(industry, []),
                industry_count_today,
                base,
                rt_lookback_days,
            )
            rv = _compute_rv_components(row, base)
            legacy_cf = _compute_legacy_cf_components(rv["flow_share"], rv["amount_delta_10d"], base)
            bd = _compute_bd_components(row)
            gn = _compute_gn_components(row)
            day_components.append(
                {
                    "industry": industry,
                    "industry_row": row,
                    "rank_history": list(rank_history_by_industry.get(industry, [])),
                    "score_history": list(score_history_by_industry.get(industry, [])),
                    "provisional_score": _pre_rt_score_for_mode(
                        rs["rs_score"],
                        legacy_cf["cf_score"],
                        rv["rv_score"],
                        bd["bd_score"],
                        gn["gn_score"],
                        normalized_factor_mode,
                        factor_weight_rs,
                        factor_weight_rv,
                        factor_weight_bd,
                        factor_weight_gn,
                    ),
                    **rs,
                    **rv,
                    **legacy_cf,
                    **bd,
                    **gn,
                }
            )

        provisional_df = pd.DataFrame(
            [{"industry": item["industry"], "score": float(item["provisional_score"])} for item in day_components]
        ).sort_values(["score", "industry"], ascending=[False, True]).reset_index(drop=True)
        provisional_df["rank"] = np.arange(1, len(provisional_df) + 1, dtype=int)
        provisional_rank_map = {str(row["industry"]): int(row["rank"]) for _, row in provisional_df.iterrows()}
        # RT 不直接参与 provisional rank；
        # 它的职责是根据 provisional rank + 历史 rank/score，判断“启动/延续/衰竭”。

        day_results: list[dict[str, object]] = []
        for item in day_components:
            rt = _compute_rt_components(
                provisional_rank_map[item["industry"]],
                float(item["provisional_score"]),
                item["rank_history"],
                item["score_history"],
                top_rank_threshold,
                rt_lookback_days,
            )
            total_score = _total_score_for_mode(
                float(item["rs_score"]),
                float(item["cf_score"]),
                float(item["rv_score"]),
                float(rt["rt_score"]),
                float(item["bd_score"]),
                float(item["gn_score"]),
                normalized_factor_mode,
                factor_weight_rs,
                factor_weight_rv,
                factor_weight_rt,
                factor_weight_bd,
                factor_weight_gn,
            )
            day_results.append({**item, **rt, "score": float(total_score), "industry_count_today": industry_count_today})

        if len(day_results) < max(1, min_industries_per_day):
            if start <= day <= end:
                for item in day_results:
                    trace_rows.append(
                        _build_industry_trace_row(
                            trace_run_id,
                            day,
                            item["industry_row"],
                            {
                                "industry_pct": _safe_float(item["industry_row"].get("pct_chg"), 0.0),
                                "amount": _safe_float(item["amount"], 0.0),
                                "market_total_amount": _safe_float(item["market_total_amount"], 0.0),
                                "amount_delta_10d": _safe_float(item["amount_delta_10d"], IRS_TRACE_FILL_SCORE),
                                "rs_1d_raw": _safe_float(item["rs_1d_raw"], 0.0),
                                "rs_5d_raw": _safe_float(item["rs_5d_raw"], IRS_TRACE_FILL_SCORE),
                                "rs_20d_raw": _safe_float(item["rs_20d_raw"], IRS_TRACE_FILL_SCORE),
                                "rank_stability_raw": _safe_float(item["rank_stability_raw"], 0.5),
                                "rs_score": _safe_float(item["rs_score"], IRS_TRACE_FILL_SCORE),
                                "cf_raw": _safe_float(item["cf_raw"], 0.0),
                                "cf_score": _safe_float(item["cf_score"], IRS_TRACE_FILL_SCORE),
                                "rv_score": _safe_float(item["rv_score"], IRS_TRACE_FILL_SCORE),
                                "rt_score": _safe_float(item["rt_score"], IRS_TRACE_FILL_SCORE),
                                "bd_score": _safe_float(item["bd_score"], IRS_TRACE_FILL_SCORE),
                                "gn_score": _safe_float(item["gn_score"], IRS_TRACE_FILL_SCORE),
                                "rotation_status": str(item["rotation_status"]),
                                "rotation_slope": _safe_float(item["rotation_slope"], 0.0),
                                "industry_count_today": industry_count_today,
                                "flow_share": _safe_float(item["flow_share"], IRS_TRACE_FILL_SCORE),
                                "amount_vs_self_20d": _safe_float(item["amount_vs_self_20d"], IRS_TRACE_FILL_SCORE),
                                "strong_amount_share": _safe_float(item["strong_amount_share"], IRS_TRACE_FILL_SCORE),
                                "top_rank_streak_5d": int(_safe_float(item["top_rank_streak_5d"], 0.0)),
                                "momentum_consistency": _safe_float(item["momentum_consistency"], 0.5),
                                "total_score": _safe_float(item["score"], 0.0),
                            },
                            "MIN_INDUSTRIES_SKIP",
                            trace_variant,
                            benchmark_pct=benchmark_pct,
                        )
                    )
            continue

        ranked_df = pd.DataFrame(
            [{"industry": item["industry"], "score": float(item["score"])} for item in day_results]
        ).sort_values(["score", "industry"], ascending=[False, True]).reset_index(drop=True)
        ranked_df["rank"] = np.arange(1, len(ranked_df) + 1, dtype=int)
        rank_map = {str(row["industry"]): int(row["rank"]) for _, row in ranked_df.iterrows()}
        score_map = {str(row["industry"]): float(row["score"]) for _, row in ranked_df.iterrows()}

        for item in day_results:
            industry = item["industry"]
            rank_history = rank_history_by_industry.setdefault(industry, [])
            score_history = score_history_by_industry.setdefault(industry, [])
            rank_history.append(rank_map[industry])
            score_history.append(score_map[industry])
            # 只保留 RT 需要的近几日历史，避免 score/rank 序列随回测窗口无限增长。
            if len(rank_history) > rt_lookback_days:
                del rank_history[0]
            if len(score_history) > rt_lookback_days:
                del score_history[0]

        if day < start:
            continue

        for item in day_results:
            industry = item["industry"]
            output_rows.append(
                {
                    "date": day,
                    "industry": industry,
                    "score": score_map[industry],
                    "rank": rank_map[industry],
                    "rs_score": float(item["rs_score"]),
                    "cf_score": float(item["cf_score"]),
                    "rv_score": float(item["rv_score"]),
                    "rt_score": float(item["rt_score"]),
                    "bd_score": float(item["bd_score"]),
                    "gn_score": float(item["gn_score"]),
                    "rotation_status": str(item["rotation_status"]),
                    "rotation_slope": float(item["rotation_slope"]),
                }
            )
            trace_rows.append(
                _build_industry_trace_row(
                    trace_run_id,
                    day,
                    item["industry_row"],
                    {
                        "industry_pct": _safe_float(item["industry_row"].get("pct_chg"), 0.0),
                        "amount": _safe_float(item["amount"], 0.0),
                        "market_total_amount": _safe_float(item["market_total_amount"], 0.0),
                        "amount_delta_10d": _safe_float(item["amount_delta_10d"], IRS_TRACE_FILL_SCORE),
                        "rs_1d_raw": _safe_float(item["rs_1d_raw"], 0.0),
                        "rs_5d_raw": _safe_float(item["rs_5d_raw"], IRS_TRACE_FILL_SCORE),
                        "rs_20d_raw": _safe_float(item["rs_20d_raw"], IRS_TRACE_FILL_SCORE),
                        "rank_stability_raw": _safe_float(item["rank_stability_raw"], 0.5),
                        "rs_score": _safe_float(item["rs_score"], IRS_TRACE_FILL_SCORE),
                        "cf_raw": _safe_float(item["cf_raw"], 0.0),
                        "cf_score": _safe_float(item["cf_score"], IRS_TRACE_FILL_SCORE),
                        "rv_score": _safe_float(item["rv_score"], IRS_TRACE_FILL_SCORE),
                        "rt_score": _safe_float(item["rt_score"], IRS_TRACE_FILL_SCORE),
                        "bd_score": _safe_float(item["bd_score"], IRS_TRACE_FILL_SCORE),
                        "gn_score": _safe_float(item["gn_score"], IRS_TRACE_FILL_SCORE),
                        "rotation_status": str(item["rotation_status"]),
                        "rotation_slope": _safe_float(item["rotation_slope"], 0.0),
                        "industry_count_today": industry_count_today,
                        "flow_share": _safe_float(item["flow_share"], IRS_TRACE_FILL_SCORE),
                        "amount_vs_self_20d": _safe_float(item["amount_vs_self_20d"], IRS_TRACE_FILL_SCORE),
                        "strong_amount_share": _safe_float(item["strong_amount_share"], IRS_TRACE_FILL_SCORE),
                        "top_rank_streak_5d": int(_safe_float(item["top_rank_streak_5d"], 0.0)),
                        "momentum_consistency": _safe_float(item["momentum_consistency"], 0.5),
                        "total_score": score_map[industry],
                    },
                    coverage_flag,
                    trace_variant,
                    industry_score=score_map[industry],
                    industry_rank=rank_map[industry],
                    benchmark_pct=benchmark_pct,
                )
            )

    # 这里按 run 末尾一次写回的前提是：行业层日记录量可控，且 trace 需要和正式 ranking 一起落地。
    # 若未来行业维度或 trace 宽度显著增加，应优先改成按日分批 upsert，而不是继续扩大这两个列表。
    if trace_rows:
        store.bulk_upsert("irs_industry_trace_exp", pd.DataFrame(trace_rows))
    if not output_rows:
        return 0
    return store.bulk_upsert("l3_irs_daily", pd.DataFrame(output_rows))
