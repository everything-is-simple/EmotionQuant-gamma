from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run


POSITIONING_NULL_CONTROL_DTT_VARIANT = "v0_01_dtt_pattern_only"
POSITIONING_NULL_CONTROL_SCOPE = "positioning_p1_null_control"


@dataclass(frozen=True)
class PositioningNullControlScenario:
    label: str
    position_sizing_mode: str
    fixed_lot_size: int
    fixed_notional_amount: float
    notes: str


def build_positioning_null_control_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[PositioningNullControlScenario]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    fixed_notional_amount = float(config.fixed_notional_amount)
    if fixed_notional_amount <= 0:
        fixed_notional_amount = starting_cash * float(config.max_position_pct)

    return [
        PositioningNullControlScenario(
            label="SINGLE_LOT_CONTROL",
            position_sizing_mode="single_lot",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=0.0,
            notes="One A-share lot per accepted BUY signal; control floor for minimum tradable participation.",
        ),
        PositioningNullControlScenario(
            label="FIXED_NOTIONAL_CONTROL",
            position_sizing_mode="fixed_notional",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=float(fixed_notional_amount),
            notes=(
                "Fixed nominal BUY notional anchored to initial cash * max_position_pct unless explicitly overridden."
            ),
        ),
    ]


def _normalize_runtime_for_positioning(
    config: Settings,
    scenario: PositioningNullControlScenario,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = POSITIONING_NULL_CONTROL_DTT_VARIANT
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = scenario.position_sizing_mode
    cfg.fixed_lot_size = int(scenario.fixed_lot_size)
    cfg.fixed_notional_amount = float(scenario.fixed_notional_amount)
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _query_rows(store: Store, query: str, params: tuple[object, ...]) -> pd.DataFrame:
    return store.read_df(query, params)


def _load_buy_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT trade_id, order_id, code, execute_date, price, quantity, fee
        FROM l4_trades
        WHERE action = 'BUY'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )


def _load_orders(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT order_id, signal_id, code, action, execute_date, status, reject_reason, quantity
        FROM l4_orders
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, order_id ASC
        """,
        (start, end),
    )


def _load_overlay_trace(store: Store, run_id: str) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT
            signal_id,
            signal_date,
            code,
            decision_status,
            decision_bucket,
            decision_reason,
            available_cash,
            reserved_cash,
            holdings_before,
            effective_max_positions
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ?
        ORDER BY signal_date ASC, signal_id ASC
        """,
        (run_id,),
    )


def _failure_reason_breakdown(orders: pd.DataFrame) -> dict[str, int]:
    if orders.empty:
        return {}
    failed = orders[orders["status"].isin(["REJECTED", "EXPIRED"])].copy()
    if failed.empty:
        return {}
    failed["reason_key"] = failed["reject_reason"].fillna(failed["status"]).replace("", "UNKNOWN")
    grouped = failed.groupby("reason_key").size().sort_values(ascending=False)
    return {str(key): int(value) for key, value in grouped.items()}


def _buy_order_diagnostics(orders: pd.DataFrame) -> dict[str, float | int]:
    if orders.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "cash_pressure_reject_count": 0,
            "max_position_reject_count": 0,
            "buy_reject_rate": 0.0,
            "cash_pressure_reject_rate": 0.0,
            "max_position_reject_rate": 0.0,
        }

    buys = orders[orders["action"] == "BUY"].copy()
    if buys.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "cash_pressure_reject_count": 0,
            "max_position_reject_count": 0,
            "buy_reject_rate": 0.0,
            "cash_pressure_reject_rate": 0.0,
            "max_position_reject_rate": 0.0,
        }

    filled_count = int((buys["status"] == "FILLED").sum())
    reject_count = int((buys["status"] == "REJECTED").sum())
    cash_pressure_reject_count = int(
        (
            (buys["status"] == "REJECTED")
            & buys["reject_reason"].isin(
                ["INSUFFICIENT_CASH", "INSUFFICIENT_CASH_AT_EXECUTION", "SIZE_BELOW_MIN_LOT"]
            )
        ).sum()
    )
    max_position_reject_count = int(
        ((buys["status"] == "REJECTED") & (buys["reject_reason"] == "MAX_POSITIONS_REACHED")).sum()
    )
    order_count = int(len(buys))
    return {
        "buy_order_count": order_count,
        "buy_filled_count": filled_count,
        "buy_reject_count": reject_count,
        "cash_pressure_reject_count": cash_pressure_reject_count,
        "max_position_reject_count": max_position_reject_count,
        "buy_reject_rate": 0.0 if order_count <= 0 else float(reject_count / order_count),
        "cash_pressure_reject_rate": 0.0
        if order_count <= 0
        else float(cash_pressure_reject_count / order_count),
        "max_position_reject_rate": 0.0
        if order_count <= 0
        else float(max_position_reject_count / order_count),
    }


def _buy_trade_metrics(buys: pd.DataFrame, initial_cash: float) -> dict[str, float | int | None]:
    if buys.empty:
        return {
            "buy_trade_count": 0,
            "avg_entry_quantity": None,
            "median_entry_quantity": None,
            "avg_entry_notional": None,
            "median_entry_notional": None,
            "avg_entry_notional_pct_initial_cash": None,
            "max_entry_notional_pct_initial_cash": None,
        }

    metrics = buys.copy()
    metrics["entry_notional"] = pd.to_numeric(metrics["price"], errors="coerce").fillna(0.0) * pd.to_numeric(
        metrics["quantity"], errors="coerce"
    ).fillna(0)
    avg_entry_notional = float(metrics["entry_notional"].mean())
    max_entry_notional = float(metrics["entry_notional"].max())
    return {
        "buy_trade_count": int(len(metrics)),
        "avg_entry_quantity": float(pd.to_numeric(metrics["quantity"], errors="coerce").mean()),
        "median_entry_quantity": float(pd.to_numeric(metrics["quantity"], errors="coerce").median()),
        "avg_entry_notional": avg_entry_notional,
        "median_entry_notional": float(metrics["entry_notional"].median()),
        "avg_entry_notional_pct_initial_cash": 0.0
        if initial_cash <= 0
        else float(avg_entry_notional / initial_cash),
        "max_entry_notional_pct_initial_cash": 0.0
        if initial_cash <= 0
        else float(max_entry_notional / initial_cash),
    }


def _overlay_diagnostics(trace: pd.DataFrame) -> dict[str, float | int | None]:
    if trace.empty:
        return {
            "decision_count": 0,
            "accepted_decision_count": 0,
            "avg_reserved_cash_on_accept": None,
            "avg_reserved_cash_pct_available_cash": None,
            "avg_holdings_before_decision": None,
            "avg_effective_max_positions": None,
        }

    accepted = trace[trace["decision_status"] == "ACCEPTED"].copy()
    ratio_series = pd.Series(dtype="float64")
    if not accepted.empty:
        safe = accepted[pd.to_numeric(accepted["available_cash"], errors="coerce") > 0].copy()
        if not safe.empty:
            ratio_series = pd.to_numeric(safe["reserved_cash"], errors="coerce").fillna(0.0) / pd.to_numeric(
                safe["available_cash"], errors="coerce"
            ).replace(0, pd.NA)

    return {
        "decision_count": int(len(trace)),
        "accepted_decision_count": int(len(accepted)),
        "avg_reserved_cash_on_accept": None
        if accepted.empty
        else float(pd.to_numeric(accepted["reserved_cash"], errors="coerce").fillna(0.0).mean()),
        "avg_reserved_cash_pct_available_cash": None
        if ratio_series.empty
        else float(ratio_series.fillna(0.0).mean()),
        "avg_holdings_before_decision": float(
            pd.to_numeric(trace["holdings_before"], errors="coerce").fillna(0.0).mean()
        ),
        "avg_effective_max_positions": float(
            pd.to_numeric(trace["effective_max_positions"], errors="coerce").fillna(0.0).mean()
        ),
    }


def _snapshot_signal_counts(store: Store, start: date, end: date, run_id: str) -> dict[str, int]:
    signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    ranked_signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signal_rank_exp WHERE run_id = ? AND signal_date BETWEEN ? AND ?",
            (run_id, start, end),
        )
        or 0
    )
    return {
        "signals_count": signals_count,
        "ranked_signals_count": ranked_signals_count,
    }


def _scenario_scope(label: str) -> str:
    return f"{POSITIONING_NULL_CONTROL_SCOPE}_{label.strip().lower()}"


def _build_result_payload(
    *,
    scenario: PositioningNullControlScenario,
    result,
    store: Store,
    start: date,
    end: date,
    initial_cash: float,
    run_id: str,
) -> dict[str, object]:
    orders = _load_orders(store, start, end)
    buys = _load_buy_trades(store, start, end)
    trace = _load_overlay_trace(store, run_id)
    signal_counts = _snapshot_signal_counts(store, start, end, run_id)

    order_metrics = _buy_order_diagnostics(orders)
    buy_metrics = _buy_trade_metrics(buys, initial_cash)
    trace_metrics = _overlay_diagnostics(trace)

    return {
        "label": scenario.label,
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": "dtt",
        "dtt_variant": POSITIONING_NULL_CONTROL_DTT_VARIANT,
        "position_sizing_mode": scenario.position_sizing_mode,
        "fixed_lot_size": int(scenario.fixed_lot_size),
        "fixed_notional_amount": float(scenario.fixed_notional_amount),
        "trade_days": int(result.trade_days),
        "trade_count": int(result.trade_count),
        "win_rate": float(result.win_rate),
        "avg_win": float(result.avg_win),
        "avg_loss": float(result.avg_loss),
        "expected_value": float(result.expected_value),
        "profit_factor": float(result.profit_factor),
        "max_drawdown": float(result.max_drawdown),
        "reject_rate": float(result.reject_rate),
        "missing_rate": float(result.missing_rate),
        "exposure_rate": float(result.exposure_rate),
        "opportunity_count": float(result.opportunity_count),
        "filled_count": float(result.filled_count),
        "skip_cash_count": float(result.skip_cash_count),
        "skip_maxpos_count": float(result.skip_maxpos_count),
        "participation_rate": float(result.participation_rate),
        "environment_breakdown": result.environment_breakdown,
        **signal_counts,
        **order_metrics,
        **buy_metrics,
        **trace_metrics,
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
    }


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def run_positioning_null_control_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, object]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    source_db = Path(db_path).expanduser().resolve()
    db_file = prepare_working_db(source_db, working_db_path) if working_db_path is not None else source_db
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    artifact_root_path.mkdir(parents=True, exist_ok=True)

    if rebuild_l3:
        build_store = Store(db_file)
        try:
            build_layers(build_store, config, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    scenarios = build_positioning_null_control_scenarios(config, initial_cash=starting_cash)
    results: list[dict[str, object]] = []
    for scenario in scenarios:
        cfg = _normalize_runtime_for_positioning(config, scenario)

        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope=_scenario_scope(scenario.label),
            modules=["backtest", "selector", "strategy", "broker", "report"],
            config=cfg,
            runtime_env="script",
            artifact_root=str(artifact_root_path),
            start=start,
            end=end,
        )
        meta_store.close()

        clear_store = Store(db_file)
        try:
            clear_runtime_tables(clear_store, run_id=run.run_id)
        finally:
            clear_store.close()

        try:
            result = run_backtest(
                db_path=db_file,
                config=cfg,
                start=start,
                end=end,
                patterns=["bof"],
                initial_cash=starting_cash,
                run_id=run.run_id,
            )
            finish_store = Store(db_file)
            try:
                finish_run(finish_store, run.run_id, "SUCCESS")
            finally:
                finish_store.close()
        except Exception as exc:
            finish_store = Store(db_file)
            try:
                finish_run(finish_store, run.run_id, "FAILED", str(exc))
            finally:
                finish_store.close()
            raise

        snap_store = Store(db_file)
        try:
            results.append(
                _build_result_payload(
                    scenario=scenario,
                    result=result,
                    store=snap_store,
                    start=start,
                    end=end,
                    initial_cash=starting_cash,
                    run_id=run.run_id,
                )
            )
        finally:
            snap_store.close()

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "positioning_control_baseline",
        "research_question": (
            "Under the same BOF-only / no IRS / no MSS frozen baseline, which null control should become the "
            "canonical sizing comparator for later positioning families?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "exit_semantics": "current Broker full-exit stop-loss + trailing-stop",
        },
        "results": results,
    }


def build_positioning_null_control_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_positioning_null_control_matrix",
            "conclusion": "P1 null control matrix 尚未完成，当前不能裁决 canonical control baseline。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    single_lot = next(
        (item for item in results if isinstance(item, dict) and str(item.get("label") or "") == "SINGLE_LOT_CONTROL"),
        None,
    )
    fixed_notional = next(
        (
            item
            for item in results
            if isinstance(item, dict) and str(item.get("label") or "") == "FIXED_NOTIONAL_CONTROL"
        ),
        None,
    )
    if single_lot is None or fixed_notional is None:
        raise ValueError("matrix_payload.results must include SINGLE_LOT_CONTROL and FIXED_NOTIONAL_CONTROL")

    trade_count_ratio = _safe_ratio(fixed_notional.get("trade_count"), single_lot.get("trade_count"))
    filled_count_ratio = _safe_ratio(fixed_notional.get("buy_filled_count"), single_lot.get("buy_filled_count"))
    avg_notional_scale_ratio = _safe_ratio(
        fixed_notional.get("avg_entry_notional"),
        single_lot.get("avg_entry_notional"),
    )
    exposure_delta = float(fixed_notional.get("exposure_rate") or 0.0) - float(single_lot.get("exposure_rate") or 0.0)
    fixed_cash_pressure_rate = float(fixed_notional.get("cash_pressure_reject_rate") or 0.0)

    fixed_notional_is_viable = (
        trade_count_ratio is not None
        and trade_count_ratio >= 0.80
        and filled_count_ratio is not None
        and filled_count_ratio >= 0.80
        and fixed_cash_pressure_rate <= 0.25
    )
    if fixed_notional_is_viable:
        diagnosis = "fixed_notional_canonical_control"
        canonical_label = "FIXED_NOTIONAL_CONTROL"
        decision = "promote_fixed_notional_as_p2_p8_control"
        conclusion = (
            "FIXED_NOTIONAL_CONTROL 在保持交易参与一致性的同时，提供了比 SINGLE_LOT_CONTROL 更有代表性的"
            "资金暴露尺度，适合作为后续 sizing family replay 的 canonical control baseline。"
        )
    else:
        diagnosis = "single_lot_canonical_control"
        canonical_label = "SINGLE_LOT_CONTROL"
        decision = "keep_single_lot_as_p2_p8_control"
        conclusion = (
            "FIXED_NOTIONAL_CONTROL 当前带来的现金压力或交易参与折损过高，P2~P8 暂时应继续以"
            "SINGLE_LOT_CONTROL 作为最稳妥的 canonical control baseline。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": diagnosis,
        "canonical_control_label": canonical_label,
        "decision": decision,
        "comparison_summary": {
            "trade_count_ratio_fixed_notional_vs_single_lot": trade_count_ratio,
            "filled_count_ratio_fixed_notional_vs_single_lot": filled_count_ratio,
            "avg_notional_scale_ratio_fixed_notional_vs_single_lot": avg_notional_scale_ratio,
            "exposure_rate_delta_fixed_notional_vs_single_lot": exposure_delta,
            "fixed_notional_cash_pressure_reject_rate": fixed_cash_pressure_rate,
        },
        "single_lot_summary": {
            "trade_count": single_lot.get("trade_count"),
            "expected_value": single_lot.get("expected_value"),
            "profit_factor": single_lot.get("profit_factor"),
            "max_drawdown": single_lot.get("max_drawdown"),
            "avg_entry_notional": single_lot.get("avg_entry_notional"),
            "exposure_rate": single_lot.get("exposure_rate"),
            "cash_pressure_reject_rate": single_lot.get("cash_pressure_reject_rate"),
        },
        "fixed_notional_summary": {
            "trade_count": fixed_notional.get("trade_count"),
            "expected_value": fixed_notional.get("expected_value"),
            "profit_factor": fixed_notional.get("profit_factor"),
            "max_drawdown": fixed_notional.get("max_drawdown"),
            "avg_entry_notional": fixed_notional.get("avg_entry_notional"),
            "exposure_rate": fixed_notional.get("exposure_rate"),
            "cash_pressure_reject_rate": fixed_notional.get("cash_pressure_reject_rate"),
            "configured_fixed_notional_amount": fixed_notional.get("fixed_notional_amount"),
        },
        "conclusion": conclusion,
        "next_actions": [
            "把 canonical control baseline 写入 P1 formal record。",
            "后续 P2~P8 sizing family replay 统一对照这条 retained control baseline。",
            "在 P1 完成前，不提前打开 partial-exit lane。",
        ],
    }


def read_positioning_null_control_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_positioning_null_control_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
