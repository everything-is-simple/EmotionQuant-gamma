from __future__ import annotations

# Phase 4.1-A / MSS capacity decomposition:
# 1. 仓库根目录只放代码、文档、配置与必要脚本；正式执行库走 DATA_PATH，
#    working copy / artifact cache 走 TEMP_PATH，避免把运行副本写回仓库。
# 2. 这个脚本不负责抓数；若窗口缺数据，先按 RAW_DB_PATH / 本地旧库优先补齐，
#    再按 TUSHARE_PRIMARY_* -> TUSHARE_FALLBACK_* 的双 key 顺序补数。
# 3. 证据目标只聚焦 MSS -> Broker 三个容量杠杆：
#    max_positions / risk_per_trade_pct / max_position_pct，不重开 PAS / IRS 调参。

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
    active_knobs: tuple[str, ...]


SCENARIOS = [
    ScenarioSpec(
        label="baseline_no_overlay",
        description="固定当前 DTT 主线排序，但不启用 MSS overlay，作为 Phase 4.1 的无覆盖对照。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_score",
        active_knobs=(),
    ),
    ScenarioSpec(
        label="full_overlay",
        description="启用正式 MSS overlay，三类容量杠杆全部生效。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("max_positions", "risk_per_trade", "max_position_pct"),
    ),
    ScenarioSpec(
        label="only_max_positions",
        description="只保留 slot 缩容，risk_per_trade / max_position_pct 固定为基线。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("max_positions",),
    ),
    ScenarioSpec(
        label="only_risk_per_trade",
        description="只保留 risk budget 缩放，max_positions / max_position_pct 固定为基线。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("risk_per_trade",),
    ),
    ScenarioSpec(
        label="only_max_position_pct",
        description="只保留单票容量缩放，max_positions / risk_per_trade 固定为基线。",
        dtt_variant="v0_01_dtt_pattern_plus_irs_mss_score",
        active_knobs=("max_position_pct",),
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


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MSS capacity decomposition for Phase 4.1-A")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default=None, help="Comma-separated patterns; default uses current config")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--dtt-top-n", type=int, default=None, help="Override DTT_TOP_N for this run")
    parser.add_argument("--max-positions", type=int, default=None, help="Override MAX_POSITIONS for this run")
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
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__mss_capacity_decomposition.json",
    )
    return parser


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


def _read_buy_trade_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            o.signal_id,
            t.execute_date,
            t.code,
            t.pattern,
            t.quantity,
            t.price
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


def _read_rejected_buy_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            signal_id,
            execute_date,
            code,
            reject_reason
        FROM l4_orders
        WHERE action = 'BUY'
          AND status = 'REJECTED'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, code ASC, signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


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
                "avg_effective_max_positions": _finite_or_none(group["effective_max_positions"].mean()),
                "avg_effective_risk_per_trade_pct": _finite_or_none(
                    group["effective_risk_per_trade_pct"].mean()
                ),
                "avg_effective_max_position_pct": _finite_or_none(
                    group["effective_max_position_pct"].mean()
                ),
                "overlay_reasons": sorted({str(value) for value in group["overlay_reason"].dropna().astype(str)}),
            }
        )
    return rows


def _summarize_trace_by_column(trace: pd.DataFrame, column: str) -> list[dict[str, object]]:
    if trace.empty:
        return []
    rows: list[dict[str, object]] = []
    for key, group in trace.groupby(column, dropna=False):
        label = "UNKNOWN" if key is None or pd.isna(key) else str(key)
        rows.append(
            {
                column: label,
                "signal_count": int(group["signal_id"].nunique()),
                "accepted_count": int((group["decision_status"] == "ACCEPTED").sum()),
                "rejected_count": int((group["decision_status"] == "REJECTED").sum()),
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


def _run_scenario(
    db_file: Path,
    base_config: Settings,
    spec: ScenarioSpec,
    start: date,
    end: date,
    patterns: list[str],
    initial_cash: float | None,
    artifact_root: Path,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    cfg = _build_scenario_config(base_config, spec)
    clear_store = Store(db_file)
    try:
        clear_runtime_tables(clear_store)
    finally:
        clear_store.close()

    meta_store = Store(db_file)
    try:
        # 同一个 dtt_variant 会重复运行多个场景；scope 必须带 scenario label，
        # 否则同秒启动会发生 run_id 冲突。
        run = start_run(
            store=meta_store,
            scope=f"mss_capacity_decomp_{spec.label}",
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
        trace = _read_overlay_trace(snap_store, run.run_id)
        buy_trade_frame = _read_buy_trade_frame(snap_store, start, end)
        rejected_buy_frame = _read_rejected_buy_frame(snap_store, start, end)
        metrics = _snapshot_metrics(snap_store, start, end, run.run_id)
    finally:
        snap_store.close()

    summary = {
        "label": spec.label,
        "description": spec.description,
        "run_id": run.run_id,
        "dtt_variant": spec.dtt_variant,
        "overlay_enabled": bool(cfg.mss_risk_overlay_enabled),
        "active_knobs": list(spec.active_knobs),
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
        "buy_trade_count": int(len(buy_trade_frame)),
        "buy_reject_count": int(len(rejected_buy_frame)),
        "buy_reject_maxpos_count": int((rejected_buy_frame["reject_reason"] == "MAX_POSITIONS_REACHED").sum())
        if not rejected_buy_frame.empty
        else 0,
        "trace_count": int(len(trace)),
        "scenario_multipliers": _scenario_multiplier_snapshot(cfg),
        "regime_trace_summary": _summarize_trace_by_regime(trace),
        "regime_source_summary": _summarize_trace_by_column(trace, "regime_source"),
        "overlay_reason_summary": _summarize_trace_by_column(trace, "overlay_reason"),
        "decision_bucket_summary": _summarize_trace_by_column(trace, "decision_bucket"),
    }
    return summary, buy_trade_frame, rejected_buy_frame


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = _parse_patterns(args.patterns, cfg)
    if args.dtt_top_n is not None:
        cfg.dtt_top_n = int(args.dtt_top_n)
    if args.max_positions is not None:
        cfg.max_positions = int(args.max_positions)

    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"mss-capacity-decomposition-{date.today():%Y%m%d}.duckdb"
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

    scenario_summaries: list[dict[str, object]] = []
    buy_trade_frames: dict[str, pd.DataFrame] = {}
    rejected_buy_frames: dict[str, pd.DataFrame] = {}
    for spec in SCENARIOS:
        summary, buy_trade_frame, rejected_buy_frame = _run_scenario(
            db_file=db_file,
            base_config=cfg,
            spec=spec,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=args.cash,
            artifact_root=artifact_root,
        )
        scenario_summaries.append(summary)
        buy_trade_frames[spec.label] = buy_trade_frame
        rejected_buy_frames[spec.label] = rejected_buy_frame

    comparisons: dict[str, dict[str, object]] = {}
    for left_label, right_label in [
        ("baseline_no_overlay", "full_overlay"),
        ("baseline_no_overlay", "only_max_positions"),
        ("baseline_no_overlay", "only_risk_per_trade"),
        ("baseline_no_overlay", "only_max_position_pct"),
        ("full_overlay", "only_max_positions"),
        ("full_overlay", "only_risk_per_trade"),
        ("full_overlay", "only_max_position_pct"),
    ]:
        comparisons[f"{left_label}_vs_{right_label}"] = {
            "buy_trade_impact": _compare_buy_trade_pair(
                left_label,
                buy_trade_frames[left_label],
                right_label,
                buy_trade_frames[right_label],
            ),
            "capacity_reject_impact": _compare_capacity_reject_pair(
                left_label,
                rejected_buy_frames[left_label],
                right_label,
                rejected_buy_frames[right_label],
            ),
        }

    summary_run_id = build_run_id(
        scope="mss_capacity_decomposition",
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
        / build_artifact_name(summary_run_id, "mss_capacity_decomposition", "json")
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
        "dtt_top_n": int(cfg.dtt_top_n),
        "max_positions_base": int(cfg.max_positions),
        "scenarios": scenario_summaries,
        "comparisons": comparisons,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mss_capacity_decomposition={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
