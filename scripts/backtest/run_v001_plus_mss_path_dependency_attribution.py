from __future__ import annotations

# Phase 4.1-B / MSS path dependency attribution:
# 1. 正式执行库固定走 DATA_PATH；working copy / artifact cache 固定走 TEMP_PATH，
#    仓库根目录只落脚本、records 与最终 evidence。
# 2. 这个脚本不负责抓数；若窗口缺数据，先看 RAW_DB_PATH / 本地旧库，
#    再按 TUSHARE_PRIMARY_* -> TUSHARE_FALLBACK_* 的双 key 顺序补数。
# 3. 当前只回答 MSS -> Broker 的路径问题：
#    slot scarcity / signal competition / position carryover / delayed entry，
#    不重开 PAS / IRS 默认参数。

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings, get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import _pair_trades
from src.run_metadata import build_artifact_name, build_run_id, finish_run, start_run

DEFAULT_SLOT_DATES = [
    "2026-01-30",
    "2026-02-02",
    "2026-02-06",
    "2026-02-09",
    "2026-02-24",
]
DEFAULT_SIZING_DATES = [
    "2026-01-13",
    "2026-01-20",
    "2026-01-29",
    "2026-02-04",
    "2026-02-05",
]
EPSILON = 1e-9


@dataclass(frozen=True)
class ScenarioSpec:
    label: str
    description: str
    dtt_variant: str
    active_knobs: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioArtifacts:
    label: str
    run_id: str
    signal_context: pd.DataFrame
    buy_attr: pd.DataFrame
    trades: pd.DataFrame
    holdings_before_by_execute_date: dict[str, list[str]]


SCENARIOS = [
    ScenarioSpec(
        label="baseline_no_overlay",
        description="当前默认 DTT 排序口径，不启用 MSS overlay。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_score",
        active_knobs=(),
    ),
    ScenarioSpec(
        label="only_max_positions",
        description="只保留 max_positions 缩容，用于定位 slot scarcity 主链。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("max_positions",),
    ),
    ScenarioSpec(
        label="full_overlay",
        description="正式 full overlay，用于补看 sizing 对 surviving trades 的二级影响。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("max_positions", "risk_per_trade", "max_position_pct"),
    ),
]


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _parse_date_list(raw_values: list[str]) -> list[str]:
    values: list[str] = []
    for raw in raw_values:
        for item in raw.split(","):
            token = item.strip()
            if token:
                values.append(_parse_date(token).isoformat())
    return values


def _parse_patterns(raw: str | None, cfg: Settings) -> list[str]:
    source = raw if raw is not None else cfg.pas_patterns
    patterns = [item.strip().lower() for item in source.split(",") if item.strip()]
    return patterns or ["bof"]


def _set_knob_family_to_identity(cfg: Settings, knob: str) -> None:
    if knob == "max_positions":
        cfg.mss_bullish_max_positions_mult = 1.0
        cfg.mss_neutral_max_positions_mult = 1.0
        cfg.mss_bearish_max_positions_mult = 1.0
        return
    if knob == "risk_per_trade":
        cfg.mss_bullish_risk_per_trade_mult = 1.0
        cfg.mss_neutral_risk_per_trade_mult = 1.0
        cfg.mss_bearish_risk_per_trade_mult = 1.0
        return
    if knob == "max_position_pct":
        cfg.mss_bullish_max_position_mult = 1.0
        cfg.mss_neutral_max_position_mult = 1.0
        cfg.mss_bearish_max_position_mult = 1.0


def _build_scenario_config(base: Settings, spec: ScenarioSpec) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.dtt_variant = spec.dtt_variant
    active = set(spec.active_knobs)
    for knob in ("max_positions", "risk_per_trade", "max_position_pct"):
        if knob not in active:
            _set_knob_family_to_identity(cfg, knob)
    return cfg


def _read_overlay_trace(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            run_id,
            signal_id,
            signal_date,
            code,
            pattern,
            variant,
            overlay_enabled,
            overlay_state,
            coverage_flag,
            overlay_reason,
            market_signal,
            market_score,
            phase,
            phase_trend,
            phase_days,
            position_advice,
            risk_regime,
            trend_quality,
            regime_source,
            base_max_positions,
            base_risk_per_trade_pct,
            base_max_position_pct,
            effective_max_positions,
            effective_risk_per_trade_pct,
            effective_max_position_pct,
            holdings_before,
            available_cash,
            portfolio_market_value,
            decision_status,
            decision_bucket,
            decision_reason,
            reserved_cash
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ?
        ORDER BY signal_date ASC, signal_id ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    return frame


def _read_buy_orders(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            signal_id,
            execute_date,
            code,
            pattern,
            quantity,
            status,
            reject_reason
        FROM l4_orders
        WHERE action = 'BUY'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _read_rank_frame(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            run_id,
            signal_id,
            signal_date,
            code,
            variant,
            final_score,
            final_rank,
            selected
        FROM l3_signal_rank_exp
        WHERE run_id = ?
        ORDER BY signal_date ASC, final_rank ASC, signal_id ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    return frame


def _read_buy_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            o.signal_id,
            t.execute_date,
            t.code,
            t.pattern,
            t.quantity,
            t.price,
            t.fee
        FROM l4_trades t
        INNER JOIN l4_orders o
            ON o.order_id = t.order_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date ASC, t.code ASC, o.signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _read_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            trade_id,
            order_id,
            code,
            execute_date,
            action,
            pattern,
            price,
            quantity,
            fee
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _build_buy_attribution(buy_trades: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    if buy_trades.empty:
        return pd.DataFrame(
            columns=["signal_id", "execute_date", "code", "pattern", "quantity", "price", "fee", "entry_pnl", "entry_pnl_pct"]
        )
    if trades.empty:
        frame = buy_trades.copy()
        frame["entry_pnl"] = 0.0
        frame["entry_pnl_pct"] = 0.0
        return frame

    paired = _pair_trades(trades)
    if paired.empty:
        frame = buy_trades.copy()
        frame["entry_pnl"] = 0.0
        frame["entry_pnl_pct"] = 0.0
        return frame

    paired["entry_date"] = paired["entry_date"].apply(_to_iso)
    buy_frame = buy_trades.copy()
    buy_frame["entry_notional"] = (
        buy_frame["price"].astype(float) * buy_frame["quantity"].astype(float) + buy_frame["fee"].astype(float)
    )
    buy_agg = (
        buy_frame.groupby(["signal_id", "execute_date", "code", "pattern"], as_index=False)
        .agg(quantity=("quantity", "sum"), price=("price", "mean"), fee=("fee", "sum"), entry_notional=("entry_notional", "sum"))
    )
    pnl_agg = (
        paired.groupby(["entry_date", "code", "pattern"], as_index=False)
        .agg(entry_pnl=("pnl", "sum"))
        .rename(columns={"entry_date": "execute_date"})
    )
    merged = buy_agg.merge(pnl_agg, on=["execute_date", "code", "pattern"], how="left")
    merged["entry_pnl"] = merged["entry_pnl"].fillna(0.0)
    merged["entry_pnl_pct"] = merged.apply(
        lambda row: 0.0 if float(row["entry_notional"] or 0.0) <= 0 else float(row["entry_pnl"]) / float(row["entry_notional"]),
        axis=1,
    )
    return merged[["signal_id", "execute_date", "code", "pattern", "quantity", "price", "fee", "entry_pnl", "entry_pnl_pct"]]


def _build_signal_context(overlay_trace: pd.DataFrame, buy_orders: pd.DataFrame, rank_frame: pd.DataFrame) -> pd.DataFrame:
    if overlay_trace.empty:
        return pd.DataFrame()
    return overlay_trace.merge(
        buy_orders,
        on=["signal_id", "code", "pattern"],
        how="left",
        suffixes=("", "_order"),
    ).merge(
        rank_frame[["signal_id", "final_score", "final_rank", "selected"]],
        on="signal_id",
        how="left",
    )


def _build_holdings_snapshots(trades: pd.DataFrame, focus_dates: list[str]) -> dict[str, list[str]]:
    positions: dict[str, int] = {}
    snapshots: dict[str, list[str]] = {}
    trade_dates = sorted(set(trades["execute_date"].tolist())) if not trades.empty else []
    date_axis = sorted(set(focus_dates) | set(trade_dates))
    for execute_date in date_axis:
        snapshots[execute_date] = sorted(code for code, quantity in positions.items() if quantity > 0)
        if trades.empty:
            continue
        day_trades = trades[trades["execute_date"] == execute_date]
        if day_trades.empty:
            continue
        for _, row in day_trades[day_trades["action"].str.upper() == "SELL"].iterrows():
            code = str(row["code"])
            quantity = int(row["quantity"] or 0)
            positions[code] = positions.get(code, 0) - quantity
            if positions[code] <= 0:
                positions.pop(code, None)
        for _, row in day_trades[day_trades["action"].str.upper() == "BUY"].iterrows():
            code = str(row["code"])
            quantity = int(row["quantity"] or 0)
            positions[code] = positions.get(code, 0) + quantity
    return snapshots


def _safe_float(value: object | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _find_delayed_entry(code: str, execute_date: str, buy_attr: pd.DataFrame) -> dict[str, object] | None:
    future = buy_attr[(buy_attr["code"] == code) & (buy_attr["execute_date"] > execute_date)].sort_values(
        ["execute_date", "signal_id"], ascending=[True, True]
    )
    if future.empty:
        return None
    row = future.iloc[0]
    return {
        "execute_date": str(row["execute_date"]),
        "signal_id": row["signal_id"],
        "quantity": int(row["quantity"]),
        "entry_pnl": _safe_float(row["entry_pnl"]),
        "entry_pnl_pct": _safe_float(row["entry_pnl_pct"]),
    }


def _summarize_competition_rows(frame: pd.DataFrame, limit: int = 8) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if frame.empty:
        return rows
    for _, row in frame.sort_values(["final_rank", "signal_id"], ascending=[True, True]).head(limit).iterrows():
        rows.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "final_rank": None if pd.isna(row.get("final_rank")) else int(row["final_rank"]),
                "final_score": _safe_float(row.get("final_score")),
                "decision_status": row.get("decision_status"),
                "decision_reason": row.get("decision_reason"),
                "risk_regime": row.get("risk_regime"),
                "overlay_reason": row.get("overlay_reason"),
                "holdings_before": None if pd.isna(row.get("holdings_before")) else int(row["holdings_before"]),
                "effective_max_positions": None
                if pd.isna(row.get("effective_max_positions"))
                else int(row["effective_max_positions"]),
            }
        )
    return rows


def _build_slot_date_payload(
    execute_date: str,
    baseline: ScenarioArtifacts,
    slot_only: ScenarioArtifacts,
) -> dict[str, object]:
    left_day = baseline.buy_attr[baseline.buy_attr["execute_date"] == execute_date].copy()
    right_day = slot_only.buy_attr[slot_only.buy_attr["execute_date"] == execute_date].copy()
    merged = left_day.merge(
        right_day,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="outer",
        suffixes=("_baseline", "_slot"),
        indicator=True,
    )
    left_only = merged[merged["_merge"] == "left_only"].copy()
    right_only = merged[merged["_merge"] == "right_only"].copy()

    rejects = slot_only.signal_context[
        (slot_only.signal_context["execute_date"] == execute_date)
        & (slot_only.signal_context["decision_reason"] == "MAX_POSITIONS_REACHED")
    ].copy()
    accepted = slot_only.signal_context[
        (slot_only.signal_context["execute_date"] == execute_date)
        & (slot_only.signal_context["decision_status"] == "ACCEPTED")
    ].copy()

    left_only_payload: list[dict[str, object]] = []
    for _, row in left_only.iterrows():
        delayed_entry = _find_delayed_entry(str(row["code"]), execute_date, slot_only.buy_attr)
        left_only_payload.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "pattern": row["pattern"],
                "baseline_quantity": int(row["quantity_baseline"]),
                "baseline_entry_pnl": _safe_float(row["entry_pnl_baseline"]),
                "baseline_entry_pnl_pct": _safe_float(row["entry_pnl_pct_baseline"]),
                "delayed_entry_in_slot_path": delayed_entry,
            }
        )

    reject_payload: list[dict[str, object]] = []
    for _, row in rejects.sort_values(["final_rank", "signal_id"], ascending=[True, True]).iterrows():
        delayed_entry = _find_delayed_entry(str(row["code"]), execute_date, slot_only.buy_attr)
        reject_payload.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "pattern": row["pattern"],
                "final_rank": None if pd.isna(row.get("final_rank")) else int(row["final_rank"]),
                "final_score": _safe_float(row.get("final_score")),
                "risk_regime": row["risk_regime"],
                "overlay_reason": row["overlay_reason"],
                "holdings_before": None if pd.isna(row.get("holdings_before")) else int(row["holdings_before"]),
                "effective_max_positions": None
                if pd.isna(row.get("effective_max_positions"))
                else int(row["effective_max_positions"]),
                "delayed_entry_in_slot_path": delayed_entry,
            }
        )

    baseline_holdings = baseline.holdings_before_by_execute_date.get(execute_date, [])
    slot_holdings = slot_only.holdings_before_by_execute_date.get(execute_date, [])
    delayed_entry_count = sum(1 for item in left_only_payload if item["delayed_entry_in_slot_path"] is not None)

    return {
        "execute_date": execute_date,
        "baseline_only_trade_count": int(len(left_only_payload)),
        "slot_only_trade_count": int(len(right_only)),
        "slot_reject_count": int(len(reject_payload)),
        "delayed_entry_count": delayed_entry_count,
        "permanent_miss_count": int(len(left_only_payload) - delayed_entry_count),
        "baseline_only_entry_pnl_total": float(left_only["entry_pnl_baseline"].fillna(0.0).sum()),
        "baseline_only_positive_count": int((left_only["entry_pnl_baseline"].fillna(0.0) > 0).sum()),
        "baseline_only_negative_count": int((left_only["entry_pnl_baseline"].fillna(0.0) < 0).sum()),
        "holdings_before": {
            "baseline_no_overlay": baseline_holdings,
            "only_max_positions": slot_holdings,
            "shared": sorted(set(baseline_holdings) & set(slot_holdings)),
            "baseline_only": sorted(set(baseline_holdings) - set(slot_holdings)),
            "slot_only": sorted(set(slot_holdings) - set(baseline_holdings)),
        },
        "same_day_competition": {
            "accepted": _summarize_competition_rows(accepted),
            "maxpos_rejected": reject_payload,
        },
        "baseline_only_trades": left_only_payload,
        "slot_only_trades": [
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "pattern": row["pattern"],
                "slot_quantity": int(row["quantity_slot"]),
                "slot_entry_pnl": _safe_float(row["entry_pnl_slot"]),
                "slot_entry_pnl_pct": _safe_float(row["entry_pnl_pct_slot"]),
            }
            for _, row in right_only.iterrows()
        ],
    }


def _build_sizing_date_payload(
    execute_date: str,
    slot_only: ScenarioArtifacts,
    full_overlay: ScenarioArtifacts,
) -> dict[str, object]:
    left_day = slot_only.buy_attr[slot_only.buy_attr["execute_date"] == execute_date].copy()
    right_day = full_overlay.buy_attr[full_overlay.buy_attr["execute_date"] == execute_date].copy()
    merged = left_day.merge(
        right_day,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="inner",
        suffixes=("_slot", "_full"),
    )
    changed = merged[merged["quantity_slot"] != merged["quantity_full"]].copy()

    left_context = slot_only.signal_context[
        (slot_only.signal_context["execute_date"] == execute_date)
        & (slot_only.signal_context["decision_status"] == "ACCEPTED")
    ][
        [
            "signal_id",
            "risk_regime",
            "overlay_reason",
            "effective_risk_per_trade_pct",
            "effective_max_position_pct",
        ]
    ].drop_duplicates(subset=["signal_id"])
    right_context = full_overlay.signal_context[
        (full_overlay.signal_context["execute_date"] == execute_date)
        & (full_overlay.signal_context["decision_status"] == "ACCEPTED")
    ][
        [
            "signal_id",
            "risk_regime",
            "overlay_reason",
            "effective_risk_per_trade_pct",
            "effective_max_position_pct",
        ]
    ].drop_duplicates(subset=["signal_id"])
    changed = changed.merge(left_context, on="signal_id", how="left", suffixes=("_slot_ctx", "_full_ctx"))
    changed = changed.merge(right_context, on="signal_id", how="left", suffixes=("_slot_ctx", "_full_ctx"))

    payload_rows: list[dict[str, object]] = []
    for _, row in changed.sort_values(["signal_id"], ascending=[True]).iterrows():
        payload_rows.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "pattern": row["pattern"],
                "slot_quantity": int(row["quantity_slot"]),
                "full_overlay_quantity": int(row["quantity_full"]),
                "slot_entry_pnl": _safe_float(row["entry_pnl_slot"]),
                "full_overlay_entry_pnl": _safe_float(row["entry_pnl_full"]),
                "slot_entry_pnl_pct": _safe_float(row["entry_pnl_pct_slot"]),
                "full_overlay_entry_pnl_pct": _safe_float(row["entry_pnl_pct_full"]),
                "risk_regime": row.get("risk_regime_full_ctx") or row.get("risk_regime_slot_ctx"),
                "overlay_reason": row.get("overlay_reason_full_ctx") or row.get("overlay_reason_slot_ctx"),
                "slot_effective_risk_per_trade_pct": _safe_float(row.get("effective_risk_per_trade_pct_slot_ctx")),
                "full_effective_risk_per_trade_pct": _safe_float(row.get("effective_risk_per_trade_pct_full_ctx")),
                "slot_effective_max_position_pct": _safe_float(row.get("effective_max_position_pct_slot_ctx")),
                "full_effective_max_position_pct": _safe_float(row.get("effective_max_position_pct_full_ctx")),
            }
        )

    return {
        "execute_date": execute_date,
        "quantity_changed_count": int(len(payload_rows)),
        "slot_changed_entry_pnl_total": float(changed["entry_pnl_slot"].fillna(0.0).sum()),
        "full_changed_entry_pnl_total": float(changed["entry_pnl_full"].fillna(0.0).sum()),
        "quantity_changes": payload_rows,
    }


def _aggregate_slot_summary(date_payloads: list[dict[str, object]]) -> dict[str, object]:
    delayed_entry_count = sum(int(item["delayed_entry_count"]) for item in date_payloads)
    permanent_miss_count = sum(int(item["permanent_miss_count"]) for item in date_payloads)
    return {
        "focus_date_count": len(date_payloads),
        "slot_reject_count": sum(int(item["slot_reject_count"]) for item in date_payloads),
        "baseline_only_trade_count": sum(int(item["baseline_only_trade_count"]) for item in date_payloads),
        "delayed_entry_count": delayed_entry_count,
        "permanent_miss_count": permanent_miss_count,
        "baseline_only_entry_pnl_total": float(
            sum(float(item["baseline_only_entry_pnl_total"]) for item in date_payloads)
        ),
        "conclusion": (
            "当前 BOF 默认路径下，slot scarcity 主要体现为直接删掉交易集合；"
            "若 delayed_entry_count = 0，则说明这条路径没有在后续窗口里靠延迟入场补回来。"
        ),
    }


def _aggregate_sizing_summary(date_payloads: list[dict[str, object]]) -> dict[str, object]:
    return {
        "focus_date_count": len(date_payloads),
        "quantity_changed_count": sum(int(item["quantity_changed_count"]) for item in date_payloads),
        "slot_changed_entry_pnl_total": float(
            sum(float(item["slot_changed_entry_pnl_total"]) for item in date_payloads)
        ),
        "full_changed_entry_pnl_total": float(
            sum(float(item["full_changed_entry_pnl_total"]) for item in date_payloads)
        ),
        "conclusion": "sizing path 当前只改 surviving trades 的仓位，不改交易集合。",
    }


def _run_scenario(
    db_file: Path,
    base_config: Settings,
    spec: ScenarioSpec,
    start: date,
    end: date,
    patterns: list[str],
    initial_cash: float | None,
    artifact_root: Path,
    focus_dates: list[str],
) -> ScenarioArtifacts:
    cfg = _build_scenario_config(base_config, spec)
    clear_store = Store(db_file)
    try:
        clear_runtime_tables(clear_store)
    finally:
        clear_store.close()

    meta_store = Store(db_file)
    try:
        run = start_run(
            store=meta_store,
            scope=f"mss_path_dependency_{spec.label}",
            modules=["backtest", "selector", "strategy", "broker", "report"],
            config=cfg,
            runtime_env="script",
            artifact_root=str(artifact_root),
            start=start,
            end=end,
        )
    finally:
        meta_store.close()

    error_summary: str | None = None
    try:
        run_backtest(
            db_path=db_file,
            config=cfg,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=initial_cash,
            run_id=run.run_id,
        )
        status = "COMPLETED"
    except Exception as exc:
        error_summary = str(exc)
        status = "FAILED"
        raise
    finally:
        finish_store = Store(db_file)
        try:
            finish_run(finish_store, run.run_id, status=status, error_summary=error_summary)
        finally:
            finish_store.close()

    snap_store = Store(db_file)
    try:
        overlay_trace = _read_overlay_trace(snap_store, run.run_id)
        buy_orders = _read_buy_orders(snap_store, start, end)
        rank_frame = _read_rank_frame(snap_store, run.run_id)
        buy_trades = _read_buy_trades(snap_store, start, end)
        trades = _read_trades(snap_store, start, end)
    finally:
        snap_store.close()

    buy_attr = _build_buy_attribution(buy_trades, trades)
    signal_context = _build_signal_context(overlay_trace, buy_orders, rank_frame)
    holdings_before = _build_holdings_snapshots(trades, focus_dates)
    return ScenarioArtifacts(
        label=spec.label,
        run_id=run.run_id,
        signal_context=signal_context,
        buy_attr=buy_attr,
        trades=trades,
        holdings_before_by_execute_date=holdings_before,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MSS path dependency attribution for Phase 4.1-B")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default=None, help="Comma-separated patterns; default uses current config")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--slot-dates", nargs="+", default=DEFAULT_SLOT_DATES, help="Execute dates for slot scarcity focus")
    parser.add_argument("--sizing-dates", nargs="+", default=DEFAULT_SIZING_DATES, help="Execute dates for sizing-only focus")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument("--output", default=None, help="Output JSON path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = _parse_patterns(args.patterns, cfg)
    slot_dates = _parse_date_list(args.slot_dates)
    sizing_dates = _parse_date_list(args.sizing_dates)
    focus_dates = sorted(set(slot_dates + sizing_dates))

    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"mss-path-dependency-{date.today():%Y%m%d}.duckdb"
    )
    db_file = prepare_working_db(source_db, working_db_path)
    artifact_root = (cfg.resolved_temp_path / "artifacts").resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_rebuild_l3:
        build_store = Store(db_file)
        try:
            build_layers(build_store, cfg, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    scenario_artifacts: dict[str, ScenarioArtifacts] = {}
    for spec in SCENARIOS:
        scenario_artifacts[spec.label] = _run_scenario(
            db_file=db_file,
            base_config=cfg,
            spec=spec,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=args.cash,
            artifact_root=artifact_root,
            focus_dates=focus_dates,
        )

    baseline = scenario_artifacts["baseline_no_overlay"]
    slot_only = scenario_artifacts["only_max_positions"]
    full_overlay = scenario_artifacts["full_overlay"]

    slot_payloads = [_build_slot_date_payload(item, baseline, slot_only) for item in slot_dates]
    sizing_payloads = [_build_sizing_date_payload(item, slot_only, full_overlay) for item in sizing_dates]

    summary_run_id = build_run_id(
        scope="mss_path_dependency_attribution",
        mode="dtt",
        variant="v0_01_dtt_pattern_plus_irs_mss_score",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT
        / "docs"
        / "spec"
        / "v0.01-plus"
        / "evidence"
        / build_artifact_name(summary_run_id, "mss_path_dependency_attribution", "json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(source_db),
        "working_db_path": str(db_file),
        "artifact_root": str(artifact_root),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns,
        "slot_focus_dates": slot_dates,
        "sizing_focus_dates": sizing_dates,
        "scenarios": {
            key: {
                "run_id": value.run_id,
                "buy_trade_count": int(len(value.buy_attr)),
                "signal_count": int(len(value.signal_context)),
            }
            for key, value in scenario_artifacts.items()
        },
        "slot_path_summary": _aggregate_slot_summary(slot_payloads),
        "slot_path_dates": slot_payloads,
        "sizing_path_summary": _aggregate_sizing_summary(sizing_payloads),
        "sizing_path_dates": sizing_payloads,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mss_path_dependency_attribution={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
