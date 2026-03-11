from __future__ import annotations

# Phase 4.1-C / MSS remediation candidate freeze:
# 1. 仓库根目录只放代码、文档、配置与最终 evidence；正式执行库固定走 DATA_PATH，
#    working copy / artifact cache 固定走 TEMP_PATH，避免把运行副本写回仓库。
# 2. 这个脚本不负责抓数；若窗口缺数据，先看 RAW_DB_PATH / 本地旧库，
#    再按 TUSHARE_PRIMARY_* -> TUSHARE_FALLBACK_* 的双 key 顺序补数。
# 3. 当前只冻结一条 MSS -> Broker 候选：
#    不动 PAS / IRS，不动 risk_per_trade / max_position_pct，只改 max_positions shrink / carryover 语义。

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

CAPACITY_REJECT_REASONS = {
    "MAX_POSITIONS_REACHED",
    "INSUFFICIENT_CASH",
    "SIZE_BELOW_MIN_LOT",
}
EPSILON = 1e-9


@dataclass(frozen=True)
class ScenarioSpec:
    label: str
    description: str
    dtt_variant: str
    max_positions_mode: str
    max_positions_buffer_slots: int


@dataclass(frozen=True)
class ScenarioArtifacts:
    label: str
    run_id: str
    summary: dict[str, object]
    buy_attr: pd.DataFrame
    rejected_buy_orders: pd.DataFrame
    signal_context: pd.DataFrame


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


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _safe_float(value: object | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MSS remediation candidate freeze for Phase 4.1-C")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default=None, help="Comma-separated patterns; default uses current config")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument(
        "--candidate-mode",
        default="carryover_buffer",
        help="Candidate max_positions mode; default freezes carryover_buffer",
    )
    parser.add_argument(
        "--candidate-buffer-slots",
        type=int,
        default=1,
        help="Fresh slots reserved for the candidate carryover mode; default=1",
    )
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


def _parse_patterns(raw: str | None, cfg: Settings) -> list[str]:
    source = raw if raw is not None else cfg.pas_patterns
    patterns = [item.strip().lower() for item in source.split(",") if item.strip()]
    return patterns or ["bof"]


def _build_scenario_config(base: Settings, spec: ScenarioSpec) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.dtt_variant = spec.dtt_variant
    cfg.mss_max_positions_mode = spec.max_positions_mode
    cfg.mss_max_positions_buffer_slots = int(spec.max_positions_buffer_slots)
    return cfg


def _scenario_multiplier_snapshot(cfg: Settings) -> dict[str, dict[str, float]]:
    return {
        "RISK_ON": {
            "max_positions_mult": float(cfg.mss_bullish_max_positions_mult),
            "risk_per_trade_mult": float(cfg.mss_bullish_risk_per_trade_mult),
            "max_position_mult": float(cfg.mss_bullish_max_position_mult),
        },
        "RISK_NEUTRAL": {
            "max_positions_mult": float(cfg.mss_neutral_max_positions_mult),
            "risk_per_trade_mult": float(cfg.mss_neutral_risk_per_trade_mult),
            "max_position_mult": float(cfg.mss_neutral_max_position_mult),
        },
        "RISK_OFF": {
            "max_positions_mult": float(cfg.mss_bearish_max_positions_mult),
            "risk_per_trade_mult": float(cfg.mss_bearish_risk_per_trade_mult),
            "max_position_mult": float(cfg.mss_bearish_max_position_mult),
        },
    }


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
            max_positions_mult,
            target_max_positions,
            effective_max_positions,
            max_positions_mode,
            max_positions_buffer_slots,
            effective_risk_per_trade_pct,
            effective_max_position_pct,
            holdings_before,
            decision_status,
            decision_bucket,
            decision_reason
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
    frame["selected"] = frame["selected"].astype(bool)
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
            columns=[
                "signal_id",
                "execute_date",
                "code",
                "pattern",
                "quantity",
                "price",
                "fee",
                "entry_pnl",
                "entry_pnl_pct",
            ]
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
        lambda row: 0.0
        if float(row["entry_notional"] or 0.0) <= 0
        else float(row["entry_pnl"]) / float(row["entry_notional"]),
        axis=1,
    )
    return merged[
        ["signal_id", "execute_date", "code", "pattern", "quantity", "price", "fee", "entry_pnl", "entry_pnl_pct"]
    ]


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


def _snapshot_metrics(store: Store, start: date, end: date, run_id: str) -> dict[str, float | int | None]:
    report = store.read_df(
        """
        SELECT
            expected_value,
            profit_factor,
            max_drawdown,
            trades_count,
            reject_rate,
            missing_rate,
            exposure_rate,
            opportunity_count,
            filled_count,
            skip_cash_count,
            skip_maxpos_count,
            participation_rate
        FROM l4_daily_report
        WHERE date = ?
        LIMIT 1
        """,
        (end,),
    )
    signal_count = int(store.read_scalar("SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?", (start, end)) or 0)
    ranked_signal_count = int(
        store.read_scalar("SELECT COUNT(*) FROM l3_signal_rank_exp WHERE run_id = ?", (run_id,)) or 0
    )
    if report.empty:
        return {
            "signals_count": signal_count,
            "ranked_signals_count": ranked_signal_count,
        }
    row = report.iloc[0]
    return {
        "signals_count": signal_count,
        "ranked_signals_count": ranked_signal_count,
        "expected_value": _finite_or_none(row["expected_value"]),
        "profit_factor": _finite_or_none(row["profit_factor"]),
        "max_drawdown": _finite_or_none(row["max_drawdown"]),
        "trades_count": int(row["trades_count"] or 0),
        "reject_rate": _finite_or_none(row.get("reject_rate")),
        "missing_rate": _finite_or_none(row.get("missing_rate")),
        "exposure_rate": _finite_or_none(row.get("exposure_rate")),
        "opportunity_count": _finite_or_none(row.get("opportunity_count")),
        "filled_count": _finite_or_none(row.get("filled_count")),
        "skip_cash_count": _finite_or_none(row.get("skip_cash_count")),
        "skip_maxpos_count": _finite_or_none(row.get("skip_maxpos_count")),
        "participation_rate": _finite_or_none(row.get("participation_rate")),
    }


def _summarize_trace_by_regime(trace: pd.DataFrame) -> list[dict[str, object]]:
    if trace.empty:
        return []
    rows: list[dict[str, object]] = []
    for risk_regime, group in trace.groupby("risk_regime", dropna=False):
        label = "UNKNOWN" if risk_regime is None or pd.isna(risk_regime) else str(risk_regime)
        rows.append(
            {
                "risk_regime": label,
                "signal_count": int(group["signal_id"].nunique()),
                "accepted_count": int((group["decision_status"] == "ACCEPTED").sum()),
                "rejected_count": int((group["decision_status"] == "REJECTED").sum()),
                "avg_target_max_positions": _finite_or_none(group["target_max_positions"].mean()),
                "avg_effective_max_positions": _finite_or_none(group["effective_max_positions"].mean()),
                "overlay_reasons": sorted({str(value) for value in group["overlay_reason"].dropna().astype(str)}),
            }
        )
    return rows


def _build_execution_samples(
    frame: pd.DataFrame,
    left_label: str,
    right_label: str,
    *,
    quantity_column: str | None = None,
) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for _, row in frame.head(5).iterrows():
        payload = {
            "execute_date": row["execute_date"],
            "code": row["code"],
            "signal_id": row["signal_id"],
            f"present_{left_label}": bool(row[f"present_{left_label}"]),
            f"present_{right_label}": bool(row[f"present_{right_label}"]),
        }
        if quantity_column is not None:
            payload[f"{left_label}_{quantity_column}"] = (
                None if pd.isna(row[f"{quantity_column}_{left_label}"]) else float(row[f"{quantity_column}_{left_label}"])
            )
            payload[f"{right_label}_{quantity_column}"] = (
                None if pd.isna(row[f"{quantity_column}_{right_label}"]) else float(row[f"{quantity_column}_{right_label}"])
            )
        if f"reject_reason_{left_label}" in row.index:
            payload[f"{left_label}_reject_reason"] = row.get(f"reject_reason_{left_label}")
        if f"reject_reason_{right_label}" in row.index:
            payload[f"{right_label}_reject_reason"] = row.get(f"reject_reason_{right_label}")
        samples.append(payload)
    return samples


def _compare_buy_trade_pair(left_label: str, left_frame: pd.DataFrame, right_label: str, right_frame: pd.DataFrame) -> dict[str, object]:
    left = left_frame.rename(
        columns={
            "quantity": f"quantity_{left_label}",
            "price": f"price_{left_label}",
        }
    )
    right = right_frame.rename(
        columns={
            "quantity": f"quantity_{right_label}",
            "price": f"price_{right_label}",
        }
    )
    merged = left.merge(
        right,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="outer",
        indicator=True,
    ).sort_values(["execute_date", "signal_id"], ascending=[True, True])
    merged[f"present_{left_label}"] = merged["_merge"].isin(["both", "left_only"])
    merged[f"present_{right_label}"] = merged["_merge"].isin(["both", "right_only"])
    shared_mask = merged["_merge"] == "both"
    quantity_changed_mask = shared_mask & (
        merged[f"quantity_{left_label}"] != merged[f"quantity_{right_label}"]
    )
    price_changed_mask = shared_mask & (
        (merged[f"price_{left_label}"] - merged[f"price_{right_label}"]).abs() > EPSILON
    )
    merged = merged.assign(quantity_changed=quantity_changed_mask, price_changed=price_changed_mask)

    per_execute_date: list[dict[str, object]] = []
    for execute_date, group in merged.groupby("execute_date", dropna=False):
        payload: dict[str, object] = {
            "execute_date": str(execute_date),
            "shared_buy_trade_count": int((group["_merge"] == "both").sum()),
            "left_only_count": int((group["_merge"] == "left_only").sum()),
            "right_only_count": int((group["_merge"] == "right_only").sum()),
            "quantity_changed_count": int(group["quantity_changed"].sum()),
            "price_changed_count": int(group["price_changed"].sum()),
        }
        changed_rows = group[
            (group["quantity_changed"]) | (group["price_changed"]) | (group["_merge"] != "both")
        ]
        if not changed_rows.empty:
            payload["sample_changes"] = _build_execution_samples(
                changed_rows,
                left_label,
                right_label,
                quantity_column="quantity",
            )
        per_execute_date.append(payload)

    return {
        "left_scenario": left_label,
        "right_scenario": right_label,
        "shared_buy_trade_count": int(shared_mask.sum()),
        "left_only_count": int((merged["_merge"] == "left_only").sum()),
        "right_only_count": int((merged["_merge"] == "right_only").sum()),
        "trade_set_changed_count": int((merged["_merge"] != "both").sum()),
        "quantity_changed_count": int(quantity_changed_mask.sum()),
        "price_changed_count": int(price_changed_mask.sum()),
        "dates_with_trade_set_change": [
            item["execute_date"]
            for item in per_execute_date
            if int(item["left_only_count"]) > 0 or int(item["right_only_count"]) > 0
        ],
        "dates_with_quantity_change": [
            item["execute_date"] for item in per_execute_date if int(item["quantity_changed_count"]) > 0
        ],
        "per_execute_date": per_execute_date,
    }


def _compare_capacity_reject_pair(
    left_label: str,
    left_frame: pd.DataFrame,
    right_label: str,
    right_frame: pd.DataFrame,
) -> dict[str, object]:
    left_capacity = left_frame[left_frame["reject_reason"].isin(CAPACITY_REJECT_REASONS)].copy()
    right_capacity = right_frame[right_frame["reject_reason"].isin(CAPACITY_REJECT_REASONS)].copy()
    left = left_capacity.rename(columns={"reject_reason": f"reject_reason_{left_label}"})
    right = right_capacity.rename(columns={"reject_reason": f"reject_reason_{right_label}"})
    merged = left.merge(
        right,
        on=["signal_id", "execute_date", "code"],
        how="outer",
        indicator=True,
    ).sort_values(["execute_date", "signal_id"], ascending=[True, True])
    merged[f"present_{left_label}"] = merged["_merge"].isin(["both", "left_only"])
    merged[f"present_{right_label}"] = merged["_merge"].isin(["both", "right_only"])

    per_execute_date: list[dict[str, object]] = []
    for execute_date, group in merged.groupby("execute_date", dropna=False):
        payload: dict[str, object] = {
            "execute_date": str(execute_date),
            "shared_reject_count": int((group["_merge"] == "both").sum()),
            "left_only_count": int((group["_merge"] == "left_only").sum()),
            "right_only_count": int((group["_merge"] == "right_only").sum()),
        }
        changed_rows = group[group["_merge"] != "both"]
        if not changed_rows.empty:
            payload["sample_changes"] = _build_execution_samples(changed_rows, left_label, right_label)
        per_execute_date.append(payload)

    return {
        "left_scenario": left_label,
        "right_scenario": right_label,
        "shared_reject_count": int((merged["_merge"] == "both").sum()),
        "left_only_count": int((merged["_merge"] == "left_only").sum()),
        "right_only_count": int((merged["_merge"] == "right_only").sum()),
        "reject_set_changed_count": int((merged["_merge"] != "both").sum()),
        "dates_with_reject_change": [
            item["execute_date"]
            for item in per_execute_date
            if int(item["left_only_count"]) > 0 or int(item["right_only_count"]) > 0
        ],
        "per_execute_date": per_execute_date,
    }


def _summarize_side_only_trades(
    side: str,
    frame: pd.DataFrame,
    signal_context: pd.DataFrame,
    *,
    quantity_col: str,
    entry_pnl_col: str,
    entry_pnl_pct_col: str,
) -> dict[str, object]:
    if frame.empty:
        return {
            "side": side,
            "trade_count": 0,
            "entry_pnl_total": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "dates": [],
            "samples": [],
        }

    context_columns = [
        "signal_id",
        "final_rank",
        "final_score",
        "risk_regime",
        "overlay_reason",
        "holdings_before",
        "target_max_positions",
        "effective_max_positions",
        "decision_bucket",
        "decision_reason",
    ]
    # current_only / candidate_only 是 merge 后的 side-only 子集，成交列会带 suffix；
    # 这里显式接收列名，避免把 current/candidate 两侧再错误地折回成同一个 schema。
    merged = frame.merge(signal_context[context_columns], on="signal_id", how="left").sort_values(
        ["execute_date", "final_rank", "signal_id"],
        ascending=[True, True, True],
    )
    samples: list[dict[str, object]] = []
    for _, row in merged.head(8).iterrows():
        samples.append(
            {
                "execute_date": row["execute_date"],
                "code": row["code"],
                "signal_id": row["signal_id"],
                "pattern": row["pattern"],
                "quantity": int(row[quantity_col]),
                "entry_pnl": _safe_float(row[entry_pnl_col]),
                "entry_pnl_pct": _safe_float(row[entry_pnl_pct_col]),
                "final_rank": None if pd.isna(row.get("final_rank")) else int(row["final_rank"]),
                "risk_regime": row.get("risk_regime"),
                "overlay_reason": row.get("overlay_reason"),
                "holdings_before": None if pd.isna(row.get("holdings_before")) else int(row["holdings_before"]),
                "target_max_positions": None
                if pd.isna(row.get("target_max_positions"))
                else int(row["target_max_positions"]),
                "effective_max_positions": None
                if pd.isna(row.get("effective_max_positions"))
                else int(row["effective_max_positions"]),
            }
        )

    return {
        "side": side,
        "trade_count": int(len(merged)),
        "entry_pnl_total": float(merged[entry_pnl_col].fillna(0.0).sum()),
        "positive_count": int((merged[entry_pnl_col].fillna(0.0) > 0).sum()),
        "negative_count": int((merged[entry_pnl_col].fillna(0.0) < 0).sum()),
        "dates": sorted(set(merged["execute_date"].astype(str).tolist())),
        "samples": samples,
    }


def _summarize_relieved_maxpos_rejects(current: ScenarioArtifacts, candidate: ScenarioArtifacts) -> dict[str, object]:
    if current.signal_context.empty or candidate.signal_context.empty:
        return {"count": 0, "dates": [], "samples": []}

    left = current.signal_context[
        [
            "signal_id",
            "code",
            "execute_date",
            "decision_reason",
            "decision_status",
            "final_rank",
            "holdings_before",
            "target_max_positions",
            "effective_max_positions",
        ]
    ].rename(
        columns={
            "decision_reason": "decision_reason_current",
            "decision_status": "decision_status_current",
            "final_rank": "final_rank_current",
            "holdings_before": "holdings_before_current",
            "target_max_positions": "target_max_positions_current",
            "effective_max_positions": "effective_max_positions_current",
        }
    )
    right = candidate.signal_context[
        [
            "signal_id",
            "code",
            "execute_date",
            "decision_reason",
            "decision_status",
            "final_rank",
            "holdings_before",
            "target_max_positions",
            "effective_max_positions",
        ]
    ].rename(
        columns={
            "decision_reason": "decision_reason_candidate",
            "decision_status": "decision_status_candidate",
            "final_rank": "final_rank_candidate",
            "holdings_before": "holdings_before_candidate",
            "target_max_positions": "target_max_positions_candidate",
            "effective_max_positions": "effective_max_positions_candidate",
        }
    )
    merged = left.merge(right, on=["signal_id", "code", "execute_date"], how="inner")
    relieved = merged[
        (merged["decision_reason_current"] == "MAX_POSITIONS_REACHED")
        & (merged["decision_status_candidate"] == "ACCEPTED")
    ].sort_values(["execute_date", "final_rank_candidate", "signal_id"], ascending=[True, True, True])

    samples: list[dict[str, object]] = []
    for _, row in relieved.head(8).iterrows():
        samples.append(
            {
                "execute_date": row["execute_date"],
                "code": row["code"],
                "signal_id": row["signal_id"],
                "final_rank": None if pd.isna(row["final_rank_candidate"]) else int(row["final_rank_candidate"]),
                "holdings_before_current": int(row["holdings_before_current"]),
                "holdings_before_candidate": int(row["holdings_before_candidate"]),
                "target_max_positions_current": int(row["target_max_positions_current"]),
                "effective_max_positions_current": int(row["effective_max_positions_current"]),
                "target_max_positions_candidate": int(row["target_max_positions_candidate"]),
                "effective_max_positions_candidate": int(row["effective_max_positions_candidate"]),
            }
        )

    return {
        "count": int(len(relieved)),
        "dates": sorted(set(relieved["execute_date"].astype(str).tolist())),
        "samples": samples,
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
            scope=f"mss_remediation_candidate_{spec.label}",
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
        result = run_backtest(
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
        metrics = _snapshot_metrics(snap_store, start, end, run.run_id)
    finally:
        snap_store.close()

    buy_attr = _build_buy_attribution(buy_trades, trades)
    rejected_buy_orders = buy_orders[buy_orders["status"] == "REJECTED"].copy() if not buy_orders.empty else pd.DataFrame()
    signal_context = _build_signal_context(overlay_trace, buy_orders, rank_frame)
    summary = {
        "label": spec.label,
        "description": spec.description,
        "run_id": run.run_id,
        "dtt_variant": spec.dtt_variant,
        "max_positions_mode": spec.max_positions_mode,
        "max_positions_buffer_slots": int(spec.max_positions_buffer_slots),
        "overlay_enabled": bool(cfg.mss_risk_overlay_enabled),
        "trade_days": result.trade_days,
        "trade_count": result.trade_count,
        "win_rate": _finite_or_none(result.win_rate),
        "avg_win": _finite_or_none(result.avg_win),
        "avg_loss": _finite_or_none(result.avg_loss),
        "expected_value": _finite_or_none(result.expected_value),
        "profit_factor": _finite_or_none(result.profit_factor),
        "max_drawdown": _finite_or_none(result.max_drawdown),
        "reject_rate": _finite_or_none(result.reject_rate),
        "missing_rate": _finite_or_none(result.missing_rate),
        "exposure_rate": _finite_or_none(result.exposure_rate),
        "opportunity_count": _finite_or_none(result.opportunity_count),
        "filled_count": _finite_or_none(result.filled_count),
        "skip_cash_count": _finite_or_none(result.skip_cash_count),
        "skip_maxpos_count": _finite_or_none(result.skip_maxpos_count),
        "participation_rate": _finite_or_none(result.participation_rate),
        "signals_count": int(metrics.get("signals_count") or 0),
        "ranked_signals_count": int(metrics.get("ranked_signals_count") or 0),
        "trades_count": int(metrics.get("trades_count") or 0),
        "buy_trade_count": int(len(buy_attr)),
        "buy_reject_count": int(len(rejected_buy_orders)),
        "buy_reject_maxpos_count": int((rejected_buy_orders["reject_reason"] == "MAX_POSITIONS_REACHED").sum())
        if not rejected_buy_orders.empty
        else 0,
        "scenario_multipliers": _scenario_multiplier_snapshot(cfg),
        "regime_trace_summary": _summarize_trace_by_regime(overlay_trace),
    }
    return ScenarioArtifacts(
        label=spec.label,
        run_id=run.run_id,
        summary=summary,
        buy_attr=buy_attr,
        rejected_buy_orders=rejected_buy_orders,
        signal_context=signal_context,
    )


def _build_candidate_comparison(current: ScenarioArtifacts, candidate: ScenarioArtifacts) -> dict[str, object]:
    buy_trade_impact = _compare_buy_trade_pair(
        current.label,
        current.buy_attr,
        candidate.label,
        candidate.buy_attr,
    )
    capacity_reject_impact = _compare_capacity_reject_pair(
        current.label,
        current.rejected_buy_orders,
        candidate.label,
        candidate.rejected_buy_orders,
    )

    merged = current.buy_attr.merge(
        candidate.buy_attr,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="outer",
        indicator=True,
        suffixes=("_current", "_candidate"),
    )
    current_only = merged[merged["_merge"] == "left_only"].copy()
    candidate_only = merged[merged["_merge"] == "right_only"].copy()

    current_only_summary = _summarize_side_only_trades(
        current.label,
        current_only,
        current.signal_context,
        quantity_col="quantity_current",
        entry_pnl_col="entry_pnl_current",
        entry_pnl_pct_col="entry_pnl_pct_current",
    )
    candidate_only_summary = _summarize_side_only_trades(
        candidate.label,
        candidate_only,
        candidate.signal_context,
        quantity_col="quantity_candidate",
        entry_pnl_col="entry_pnl_candidate",
        entry_pnl_pct_col="entry_pnl_pct_candidate",
    )
    relieved_rejects = _summarize_relieved_maxpos_rejects(current, candidate)

    current_ev = _safe_float(current.summary.get("expected_value"))
    candidate_ev = _safe_float(candidate.summary.get("expected_value"))
    current_pf = _safe_float(current.summary.get("profit_factor"))
    candidate_pf = _safe_float(candidate.summary.get("profit_factor"))
    current_mdd = _safe_float(current.summary.get("max_drawdown"))
    candidate_mdd = _safe_float(candidate.summary.get("max_drawdown"))

    conclusion = (
        "候选只动 max_positions shrink / carryover 语义；若 relieved_maxpos_reject_count > 0 且 EV/PF 改善，"
        "则说明当前 NO-GO 主因可以先沿这个方向进入 Gate replay。"
    )
    if (
        current_ev is not None
        and candidate_ev is not None
        and current_pf is not None
        and candidate_pf is not None
        and current_mdd is not None
        and candidate_mdd is not None
        and candidate_ev >= current_ev
        and candidate_pf >= current_pf
        and candidate_mdd <= current_mdd
    ):
        conclusion = (
            "候选相对当前 hard_cap 路径已同时改善 EV/PF/MDD，"
            "且 trade/reject 变化集中在 max_positions 释放出来的 fresh slot。"
        )

    return {
        "buy_trade_impact": buy_trade_impact,
        "capacity_reject_impact": capacity_reject_impact,
        "current_only_trade_summary": current_only_summary,
        "candidate_only_trade_summary": candidate_only_summary,
        "relieved_maxpos_reject_summary": relieved_rejects,
        "conclusion": conclusion,
    }


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = _parse_patterns(args.patterns, cfg)
    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"mss-remediation-candidate-{date.today():%Y%m%d}.duckdb"
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

    scenarios = [
        ScenarioSpec(
            label="baseline_no_overlay",
            description="当前 DTT 排序链路，不启用 MSS overlay，保留为整改候选的无覆盖对照。",
            dtt_variant="v0_01_dtt_pattern_plus_irs_score",
            max_positions_mode="hard_cap",
            max_positions_buffer_slots=0,
        ),
        ScenarioSpec(
            label="current_full_overlay_hard_cap",
            description="当前正式 NO-GO 路径，保留 hard_cap 语义作为候选比较基线。",
            dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
            max_positions_mode="hard_cap",
            max_positions_buffer_slots=0,
        ),
        ScenarioSpec(
            label="candidate_full_overlay_carryover_buffer",
            description="候选：只在 shrink + carryover 已经压满时保留有限 fresh slot；不动 sizing 与 PAS/IRS。",
            dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
            max_positions_mode=args.candidate_mode,
            max_positions_buffer_slots=max(int(args.candidate_buffer_slots), 0),
        ),
    ]

    artifacts: dict[str, ScenarioArtifacts] = {}
    for spec in scenarios:
        artifacts[spec.label] = _run_scenario(
            db_file=db_file,
            base_config=cfg,
            spec=spec,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=args.cash,
            artifact_root=artifact_root,
        )

    current = artifacts["current_full_overlay_hard_cap"]
    candidate = artifacts["candidate_full_overlay_carryover_buffer"]
    baseline = artifacts["baseline_no_overlay"]

    summary_run_id = build_run_id(
        scope="mss_remediation_candidate_freeze",
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
        / build_artifact_name(summary_run_id, "mss_remediation_candidate_freeze", "json")
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
        "candidate": {
            "max_positions_mode": args.candidate_mode,
            "max_positions_buffer_slots": max(int(args.candidate_buffer_slots), 0),
        },
        "scenarios": [
            baseline.summary,
            current.summary,
            candidate.summary,
        ],
        "comparisons": {
            "current_full_overlay_hard_cap_vs_candidate": _build_candidate_comparison(current, candidate),
            "baseline_no_overlay_vs_candidate": _build_candidate_comparison(baseline, candidate),
        },
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mss_remediation_candidate_freeze={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
