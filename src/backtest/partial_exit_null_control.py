from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import _pair_trades
from src.run_metadata import finish_run, start_run


POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT = "v0_01_dtt_pattern_only"
POSITIONING_PARTIAL_EXIT_NULL_CONTROL_SCOPE = "positioning_p7_partial_exit_null_control"


@dataclass(frozen=True)
class PartialExitNullControlScenario:
    label: str
    exit_control_mode: str
    position_sizing_mode: str
    fixed_lot_size: int
    fixed_notional_amount: float
    control_family: str
    notes: str


def build_partial_exit_null_control_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[PartialExitNullControlScenario]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    fixed_notional_amount = float(config.fixed_notional_amount)
    if fixed_notional_amount <= 0:
        fixed_notional_amount = starting_cash * float(config.max_position_pct)

    return [
        PartialExitNullControlScenario(
            label="FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL",
            exit_control_mode="full_exit_control",
            position_sizing_mode="fixed_notional",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=float(fixed_notional_amount),
            control_family="operating",
            notes="Current Broker full-exit semantics with the canonical operating sizing control.",
        ),
        PartialExitNullControlScenario(
            label="NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__FIXED_NOTIONAL_CONTROL",
            exit_control_mode="naive_trail_scale_out_50_50_control",
            position_sizing_mode="fixed_notional",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=float(fixed_notional_amount),
            control_family="operating",
            notes="Naive 50/50 trailing scale-out control on top of the canonical operating sizing control.",
        ),
        PartialExitNullControlScenario(
            label="FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL",
            exit_control_mode="full_exit_control",
            position_sizing_mode="single_lot",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=0.0,
            control_family="floor",
            notes="Current Broker full-exit semantics with the floor sanity sizing control.",
        ),
        PartialExitNullControlScenario(
            label="NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__SINGLE_LOT_CONTROL",
            exit_control_mode="naive_trail_scale_out_50_50_control",
            position_sizing_mode="single_lot",
            fixed_lot_size=max(int(config.fixed_lot_size), 100),
            fixed_notional_amount=0.0,
            control_family="floor",
            notes="Naive 50/50 trailing scale-out control on top of the floor sanity sizing control.",
        ),
    ]


def _normalize_runtime_for_partial_exit(
    config: Settings,
    scenario: PartialExitNullControlScenario,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = scenario.position_sizing_mode
    cfg.exit_control_mode = scenario.exit_control_mode
    cfg.partial_exit_scale_out_ratio = 0.50
    cfg.fixed_lot_size = int(scenario.fixed_lot_size)
    cfg.fixed_notional_amount = float(scenario.fixed_notional_amount)
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _query_rows(store: Store, query: str, params: tuple[object, ...]) -> pd.DataFrame:
    return store.read_df(query, params)


def _load_orders(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT
            order_id,
            signal_id,
            code,
            action,
            execute_date,
            status,
            reject_reason,
            quantity,
            position_id,
            exit_plan_id,
            exit_leg_id,
            exit_leg_seq,
            exit_leg_count,
            exit_reason_code,
            is_partial_exit,
            remaining_qty_before,
            target_qty_after
        FROM l4_orders
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, order_id ASC
        """,
        (start, end),
    )


def _load_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    return _query_rows(
        store,
        """
        SELECT
            trade_id,
            order_id,
            code,
            execute_date,
            action,
            price,
            quantity,
            fee,
            pattern,
            is_paper,
            position_id,
            exit_plan_id,
            exit_leg_id,
            exit_leg_seq,
            exit_reason_code,
            is_partial_exit,
            remaining_qty_after
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )


def _load_paired_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    trades = _load_trades(store, start, end)
    return _pair_trades(trades)


def _failure_reason_breakdown(orders: pd.DataFrame) -> dict[str, int]:
    if orders.empty:
        return {}
    failed = orders[orders["status"].isin(["REJECTED", "EXPIRED"])].copy()
    if failed.empty:
        return {}
    failed["reason_key"] = failed["reject_reason"].fillna(failed["status"]).replace("", "UNKNOWN")
    grouped = failed.groupby("reason_key").size().sort_values(ascending=False)
    return {str(key): int(value) for key, value in grouped.items()}


def _position_consistency_metrics(orders: pd.DataFrame) -> dict[str, float | int]:
    if orders.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "sell_order_count": 0,
            "sell_filled_count": 0,
            "partial_exit_order_count": 0,
            "partial_exit_filled_count": 0,
        }

    buys = orders[orders["action"] == "BUY"].copy()
    sells = orders[orders["action"] == "SELL"].copy()
    return {
        "buy_order_count": int(len(buys)),
        "buy_filled_count": int((buys["status"] == "FILLED").sum()),
        "buy_reject_count": int((buys["status"] == "REJECTED").sum()),
        "sell_order_count": int(len(sells)),
        "sell_filled_count": int((sells["status"] == "FILLED").sum()),
        "partial_exit_order_count": int(sells["is_partial_exit"].fillna(False).sum()) if not sells.empty else 0,
        "partial_exit_filled_count": int(
            ((sells["status"] == "FILLED") & sells["is_partial_exit"].fillna(False)).sum()
        )
        if not sells.empty
        else 0,
    }


def _paired_shape_metrics(paired: pd.DataFrame) -> dict[str, float | int | None]:
    if paired.empty:
        return {
            "paired_trade_count": 0,
            "partial_exit_pair_count": 0,
            "avg_hold_days": None,
            "median_hold_days": None,
            "median_pnl_pct": None,
            "avg_pnl_pct": None,
            "avg_exit_leg_seq": None,
        }

    shaped = paired.copy()
    shaped["entry_date"] = pd.to_datetime(shaped["entry_date"])
    shaped["exit_date"] = pd.to_datetime(shaped["exit_date"])
    hold_days = (shaped["exit_date"] - shaped["entry_date"]).dt.days
    return {
        "paired_trade_count": int(len(shaped)),
        "partial_exit_pair_count": int(shaped["is_partial_exit"].fillna(False).sum()),
        "avg_hold_days": float(hold_days.mean()),
        "median_hold_days": float(hold_days.median()),
        "median_pnl_pct": float(pd.to_numeric(shaped["pnl_pct"], errors="coerce").median()),
        "avg_pnl_pct": float(pd.to_numeric(shaped["pnl_pct"], errors="coerce").mean()),
        "avg_exit_leg_seq": float(pd.to_numeric(shaped["exit_leg_seq"], errors="coerce").dropna().mean())
        if shaped["exit_leg_seq"].notna().any()
        else None,
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
    return f"{POSITIONING_PARTIAL_EXIT_NULL_CONTROL_SCOPE}_{label.strip().lower()}"


def _build_result_payload(
    *,
    scenario: PartialExitNullControlScenario,
    result,
    store: Store,
    start: date,
    end: date,
    run_id: str,
) -> dict[str, object]:
    orders = _load_orders(store, start, end)
    paired = _load_paired_trades(store, start, end)
    signal_counts = _snapshot_signal_counts(store, start, end, run_id)
    position_metrics = _position_consistency_metrics(orders)
    paired_metrics = _paired_shape_metrics(paired)

    return {
        "label": scenario.label,
        "notes": scenario.notes,
        "control_family": scenario.control_family,
        "run_id": run_id,
        "pipeline_mode": "dtt",
        "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
        "exit_control_mode": scenario.exit_control_mode,
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
        **position_metrics,
        **paired_metrics,
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
    }


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def run_partial_exit_null_control_matrix(
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

    scenarios = build_partial_exit_null_control_scenarios(config, initial_cash=starting_cash)
    results: list[dict[str, object]] = []
    for scenario in scenarios:
        cfg = _normalize_runtime_for_partial_exit(config, scenario)

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
                    run_id=run.run_id,
                )
            )
        finally:
            snap_store.close()

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "positioning_partial_exit_control_baseline",
        "research_question": (
            "Under the same BOF-only / no IRS / no MSS frozen baseline, should partial-exit lane keep "
            "FULL_EXIT_CONTROL as the formal baseline, or promote the naive 50/50 trailing scale-out control?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "sizing_controls": [
                "FIXED_NOTIONAL_CONTROL",
                "SINGLE_LOT_CONTROL",
            ],
            "exit_controls": [
                "FULL_EXIT_CONTROL",
                "NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL",
            ],
        },
        "results": results,
    }


def build_partial_exit_null_control_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_partial_exit_null_control_matrix",
            "conclusion": "P7 partial-exit null control matrix 尚未完成，当前不能裁决 control baseline。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    indexed = {
        str(item.get("label")): item for item in results if isinstance(item, dict) and item.get("label") is not None
    }
    required_labels = [
        "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL",
        "NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__FIXED_NOTIONAL_CONTROL",
        "FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL",
        "NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__SINGLE_LOT_CONTROL",
    ]
    for label in required_labels:
        if label not in indexed:
            raise ValueError(f"matrix_payload.results missing {label}")

    full_operating = indexed["FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL"]
    scale_operating = indexed["NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__FIXED_NOTIONAL_CONTROL"]
    full_floor = indexed["FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL"]
    scale_floor = indexed["NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__SINGLE_LOT_CONTROL"]

    operating_buy_fill_ratio = _safe_ratio(scale_operating.get("buy_filled_count"), full_operating.get("buy_filled_count"))
    floor_buy_fill_ratio = _safe_ratio(scale_floor.get("buy_filled_count"), full_floor.get("buy_filled_count"))
    operating_partial_pair_count = int(scale_operating.get("partial_exit_pair_count") or 0)
    floor_partial_pair_count = int(scale_floor.get("partial_exit_pair_count") or 0)

    scale_out_viable = (
        operating_partial_pair_count > 0
        and floor_partial_pair_count > 0
        and (operating_buy_fill_ratio is None or operating_buy_fill_ratio >= 0.95)
        and (floor_buy_fill_ratio is None or floor_buy_fill_ratio >= 0.95)
    )
    if scale_out_viable and (
        float(scale_operating.get("expected_value") or 0.0) > float(full_operating.get("expected_value") or 0.0)
        or float(scale_operating.get("max_drawdown") or 0.0) < float(full_operating.get("max_drawdown") or 0.0)
    ):
        diagnosis = "naive_scale_out_retained_control"
        canonical_control_label = "NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL"
        decision = "promote_naive_scale_out_as_p8_control"
        conclusion = (
            "Naive 50/50 trailing scale-out 在 operating/floor 两组 control 下都能保持基本参与一致性，"
            "并且没有退化成空转控制，因此 P8 可以继续拿它做 retained partial-exit control baseline。"
        )
    else:
        diagnosis = "full_exit_retained_control"
        canonical_control_label = "FULL_EXIT_CONTROL"
        decision = "keep_full_exit_as_p8_control"
        conclusion = (
            "Naive 50/50 trailing scale-out 当前尚未在 operating/floor 两组 control 下形成足够稳的对照优势，"
            "P8 应继续以 FULL_EXIT_CONTROL 作为 formal control baseline。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": diagnosis,
        "canonical_control_label": canonical_control_label,
        "decision": decision,
        "operating_comparison": {
            "full_exit": {
                "trade_count": full_operating.get("trade_count"),
                "expected_value": full_operating.get("expected_value"),
                "profit_factor": full_operating.get("profit_factor"),
                "max_drawdown": full_operating.get("max_drawdown"),
                "buy_filled_count": full_operating.get("buy_filled_count"),
                "paired_trade_count": full_operating.get("paired_trade_count"),
                "avg_hold_days": full_operating.get("avg_hold_days"),
            },
            "naive_scale_out": {
                "trade_count": scale_operating.get("trade_count"),
                "expected_value": scale_operating.get("expected_value"),
                "profit_factor": scale_operating.get("profit_factor"),
                "max_drawdown": scale_operating.get("max_drawdown"),
                "buy_filled_count": scale_operating.get("buy_filled_count"),
                "paired_trade_count": scale_operating.get("paired_trade_count"),
                "partial_exit_pair_count": scale_operating.get("partial_exit_pair_count"),
                "avg_hold_days": scale_operating.get("avg_hold_days"),
            },
            "buy_fill_ratio_scale_out_vs_full": operating_buy_fill_ratio,
        },
        "floor_comparison": {
            "full_exit": {
                "trade_count": full_floor.get("trade_count"),
                "expected_value": full_floor.get("expected_value"),
                "profit_factor": full_floor.get("profit_factor"),
                "max_drawdown": full_floor.get("max_drawdown"),
                "buy_filled_count": full_floor.get("buy_filled_count"),
                "paired_trade_count": full_floor.get("paired_trade_count"),
                "avg_hold_days": full_floor.get("avg_hold_days"),
            },
            "naive_scale_out": {
                "trade_count": scale_floor.get("trade_count"),
                "expected_value": scale_floor.get("expected_value"),
                "profit_factor": scale_floor.get("profit_factor"),
                "max_drawdown": scale_floor.get("max_drawdown"),
                "buy_filled_count": scale_floor.get("buy_filled_count"),
                "paired_trade_count": scale_floor.get("paired_trade_count"),
                "partial_exit_pair_count": scale_floor.get("partial_exit_pair_count"),
                "avg_hold_days": scale_floor.get("avg_hold_days"),
            },
            "buy_fill_ratio_scale_out_vs_full": floor_buy_fill_ratio,
        },
        "conclusion": conclusion,
        "next_actions": [
            "把 canonical control baseline 写入 P7 formal record。",
            "后续 P8 partial-exit family replay 统一对照这条 retained control baseline。",
            "未经 P7 formal record，不提前打开 PX1 cross-exit sensitivity。",
        ],
    }


def read_partial_exit_null_control_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_partial_exit_null_control_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
