from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.positioning_null_control import (
    POSITIONING_NULL_CONTROL_DTT_VARIANT,
    _buy_order_diagnostics,
    _buy_trade_metrics,
    _failure_reason_breakdown,
    _load_orders,
    _load_overlay_trace,
    _overlay_diagnostics,
    _query_rows,
    _safe_ratio,
    _snapshot_signal_counts,
)
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import _load_trades, _pair_trades
from src.run_metadata import finish_run, start_run


POSITIONING_SIZING_FAMILY_SCOPE = "positioning_p2_sizing_family"


@dataclass(frozen=True)
class PositioningSizingScenario:
    label: str
    family: str
    notes: str
    runtime_overrides: dict[str, Any] = field(default_factory=dict)


def build_positioning_sizing_family_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[PositioningSizingScenario]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    fixed_notional_amount = float(config.fixed_notional_amount)
    if fixed_notional_amount <= 0:
        fixed_notional_amount = starting_cash * float(config.max_position_pct)

    return [
        PositioningSizingScenario(
            label="FIXED_NOTIONAL_CONTROL",
            family="control",
            notes="Canonical operating control retained by P1.",
            runtime_overrides={
                "position_sizing_mode": "fixed_notional",
                "fixed_notional_amount": float(fixed_notional_amount),
            },
        ),
        PositioningSizingScenario(
            label="FIXED_RISK",
            family="fixed-risk",
            notes="Fixed per-trade risk budget with stop-width anchor.",
            runtime_overrides={
                "position_sizing_mode": "fixed_risk",
                "risk_per_trade_pct": 0.004,
            },
        ),
        PositioningSizingScenario(
            label="FIXED_CAPITAL",
            family="fixed-capital",
            notes="Fixed nominal capital allocation, independent from current NAV drift.",
            runtime_overrides={
                "position_sizing_mode": "fixed_capital",
                "fixed_capital_amount": starting_cash * 0.075,
            },
        ),
        PositioningSizingScenario(
            label="FIXED_RATIO",
            family="fixed-ratio",
            notes="Stepwise unit expansion as account equity rises above the baseline.",
            runtime_overrides={
                "position_sizing_mode": "fixed_ratio",
                "fixed_ratio_base_amount": starting_cash * 0.05,
                "fixed_ratio_delta_amount": 250_000.0,
            },
        ),
        PositioningSizingScenario(
            label="FIXED_UNIT",
            family="fixed-unit",
            notes="Fixed number of A-share lots per accepted BUY signal.",
            runtime_overrides={
                "position_sizing_mode": "fixed_unit",
                "fixed_unit_quantity": 1_000,
            },
        ),
        PositioningSizingScenario(
            label="WILLIAMS_FIXED_RISK",
            family="williams-fixed-risk",
            notes="Williams-style fixed risk using a wider loss reference than the current hard stop.",
            runtime_overrides={
                "position_sizing_mode": "williams_fixed_risk",
                "williams_risk_per_trade_pct": 0.005,
                "williams_loss_reference_pct": 0.10,
            },
        ),
        PositioningSizingScenario(
            label="FIXED_PERCENTAGE",
            family="fixed-percentage",
            notes="Fixed account percentage allocated to each BUY signal.",
            runtime_overrides={
                "position_sizing_mode": "fixed_percentage",
                "fixed_percentage_position_pct": 0.08,
            },
        ),
        PositioningSizingScenario(
            label="FIXED_VOLATILITY",
            family="fixed-volatility",
            notes="Position size inversely scales with recent realized volatility.",
            runtime_overrides={
                "position_sizing_mode": "fixed_volatility",
                "fixed_volatility_lookback_days": 20,
                "fixed_volatility_target_pct": 0.003,
                "fixed_volatility_min_position_pct": 0.03,
                "fixed_volatility_max_position_pct": float(config.max_position_pct),
            },
        ),
    ]


def _normalize_runtime_for_positioning(
    config: Settings,
    scenario: PositioningSizingScenario,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = POSITIONING_NULL_CONTROL_DTT_VARIANT
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.pas_patterns = "bof"
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    for key, value in scenario.runtime_overrides.items():
        setattr(cfg, key, value)
    return cfg


def _load_trades_for_path_metrics(store: Store, start: date, end: date) -> pd.DataFrame:
    return _load_trades(store, start, end)


def _build_trade_path_metrics(store: Store, start: date, end: date) -> dict[str, float | int | None]:
    trades = _load_trades_for_path_metrics(store, start, end)
    paired = _pair_trades(trades)
    if paired.empty:
        return {
            "net_pnl": 0.0,
            "trade_sequence_max_drawdown": None,
            "max_consecutive_loss_count": 0,
            "worst_trade_pnl_pct": None,
            "p05_trade_pnl_pct": None,
            "loss_trade_share": None,
        }

    ordered = paired.sort_values(["exit_date", "code", "entry_date"])
    curve = ordered["pnl"].cumsum()
    running_peak = curve.cummax()
    drawdown = (running_peak - curve) / running_peak.replace(0, pd.NA)
    drawdown = drawdown.fillna(0.0)

    max_consecutive_loss_count = 0
    current_loss_streak = 0
    for pnl_pct in ordered["pnl_pct"].tolist():
        if float(pnl_pct) <= 0:
            current_loss_streak += 1
            max_consecutive_loss_count = max(max_consecutive_loss_count, current_loss_streak)
        else:
            current_loss_streak = 0

    losses = ordered[ordered["pnl_pct"] <= 0]
    return {
        "net_pnl": float(ordered["pnl"].sum()),
        "trade_sequence_max_drawdown": float(drawdown.max()),
        "max_consecutive_loss_count": int(max_consecutive_loss_count),
        "worst_trade_pnl_pct": float(ordered["pnl_pct"].min()),
        "p05_trade_pnl_pct": float(ordered["pnl_pct"].quantile(0.05)),
        "loss_trade_share": float(len(losses) / len(ordered)),
    }


def _scenario_scope(label: str) -> str:
    return f"{POSITIONING_SIZING_FAMILY_SCOPE}_{label.strip().lower()}"


def _build_result_payload(
    *,
    scenario: PositioningSizingScenario,
    result,
    store: Store,
    start: date,
    end: date,
    initial_cash: float,
    run_id: str,
) -> dict[str, object]:
    orders = _load_orders(store, start, end)
    buys = _query_rows(
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
    trace = _load_overlay_trace(store, run_id)
    signal_counts = _snapshot_signal_counts(store, start, end, run_id)
    order_metrics = _buy_order_diagnostics(orders)
    buy_metrics = _buy_trade_metrics(buys, initial_cash)
    trace_metrics = _overlay_diagnostics(trace)
    path_metrics = _build_trade_path_metrics(store, start, end)

    avg_entry_notional_pct_initial_cash = buy_metrics.get("avg_entry_notional_pct_initial_cash")
    exposure_utilization = None
    if avg_entry_notional_pct_initial_cash is not None and float(initial_cash) > 0:
        denom = max(float(result.exposure_rate), 0.000001)
        exposure_utilization = float(avg_entry_notional_pct_initial_cash) / denom

    return {
        "label": scenario.label,
        "family": scenario.family,
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": "dtt",
        "dtt_variant": POSITIONING_NULL_CONTROL_DTT_VARIANT,
        "position_sizing_mode": str(scenario.runtime_overrides.get("position_sizing_mode") or ""),
        "runtime_overrides": dict(scenario.runtime_overrides),
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
        **path_metrics,
        "avg_position_size": buy_metrics.get("avg_entry_notional"),
        "exposure_utilization": exposure_utilization,
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
    }


def run_positioning_sizing_family_matrix(
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

    scenarios = build_positioning_sizing_family_scenarios(config, initial_cash=starting_cash)
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
        "research_parent": "positioning_sizing_family_replay",
        "research_question": (
            "Under the same BOF-only / no IRS / no MSS frozen baseline, which first-batch sizing "
            "family improves on FIXED_NOTIONAL_CONTROL without merely amplifying cash pressure or path risk?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "canonical_control_label": "FIXED_NOTIONAL_CONTROL",
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "exit_semantics": "current Broker full-exit stop-loss + trailing-stop",
            "single_lot_role": "retained-candidate floor sanity line only",
        },
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "results": results,
    }


def build_positioning_sizing_family_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_positioning_sizing_family_matrix",
            "conclusion": "P2 sizing family matrix 尚未完成，当前不能裁决 retained-or-no-go。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (
            item
            for item in results
            if isinstance(item, dict) and str(item.get("label") or "") == "FIXED_NOTIONAL_CONTROL"
        ),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include FIXED_NOTIONAL_CONTROL")

    control_ev = float(control.get("expected_value") or 0.0)
    control_pf = float(control.get("profit_factor") or 0.0)
    control_mdd = float(control.get("max_drawdown") or 0.0)
    control_trade_count = int(control.get("trade_count") or 0)
    control_cash_pressure_rate = float(control.get("cash_pressure_reject_rate") or 0.0)
    control_path_mdd = float(control.get("trade_sequence_max_drawdown") or 0.0)

    scorecard: list[dict[str, object]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "")
        if label == "FIXED_NOTIONAL_CONTROL":
            continue

        trade_count = int(item.get("trade_count") or 0)
        ev = float(item.get("expected_value") or 0.0)
        pf = float(item.get("profit_factor") or 0.0)
        mdd = float(item.get("max_drawdown") or 0.0)
        cash_pressure_rate = float(item.get("cash_pressure_reject_rate") or 0.0)
        path_mdd = float(item.get("trade_sequence_max_drawdown") or 0.0)
        trade_count_ratio = _safe_ratio(trade_count, control_trade_count)
        cash_pressure_delta = cash_pressure_rate - control_cash_pressure_rate
        ev_delta = ev - control_ev
        pf_delta = pf - control_pf
        mdd_delta = mdd - control_mdd
        path_mdd_delta = path_mdd - control_path_mdd
        total_pnl_delta = float(item.get("net_pnl") or 0.0) - float(control.get("net_pnl") or 0.0)

        retained_candidate = bool(
            ev_delta >= 0.001
            and pf >= max(control_pf - 0.05, 1.0)
            and mdd <= max(control_mdd * 1.15, control_mdd + 0.02)
            and (trade_count_ratio is not None and trade_count_ratio >= 0.85)
            and cash_pressure_delta <= 0.10
        )
        watch_candidate = bool(
            not retained_candidate
            and (
                (total_pnl_delta > 0 and cash_pressure_delta <= 0.15)
                or (ev_delta > 0 and pf_delta >= -0.05)
                or (mdd_delta < 0 and trade_count_ratio is not None and trade_count_ratio >= 0.80)
            )
        )
        if retained_candidate:
            verdict = "provisional_retained_candidate"
        elif watch_candidate:
            verdict = "watch_candidate"
        else:
            verdict = "no_go"

        scorecard.append(
            {
                "label": label,
                "family": item.get("family"),
                "verdict": verdict,
                "trade_count": trade_count,
                "trade_count_ratio_vs_control": trade_count_ratio,
                "expected_value": ev,
                "expected_value_delta_vs_control": ev_delta,
                "profit_factor": pf,
                "profit_factor_delta_vs_control": pf_delta,
                "max_drawdown": mdd,
                "max_drawdown_delta_vs_control": mdd_delta,
                "net_pnl": item.get("net_pnl"),
                "net_pnl_delta_vs_control": total_pnl_delta,
                "cash_pressure_reject_rate": cash_pressure_rate,
                "cash_pressure_delta_vs_control": cash_pressure_delta,
                "trade_sequence_max_drawdown": path_mdd,
                "trade_sequence_max_drawdown_delta_vs_control": path_mdd_delta,
                "max_consecutive_loss_count": item.get("max_consecutive_loss_count"),
                "runtime_overrides": item.get("runtime_overrides"),
            }
        )

    scorecard.sort(
        key=lambda item: (
            {"provisional_retained_candidate": 2, "watch_candidate": 1, "no_go": 0}[str(item["verdict"])],
            float(item.get("net_pnl_delta_vs_control") or 0.0),
            float(item.get("expected_value_delta_vs_control") or 0.0),
            -float(item.get("max_drawdown") or 999.0),
        ),
        reverse=True,
    )
    provisional_retained = [item for item in scorecard if item["verdict"] == "provisional_retained_candidate"]
    watch_candidates = [item for item in scorecard if item["verdict"] == "watch_candidate"]

    if provisional_retained:
        leader = provisional_retained[0]
        diagnosis = "provisional_retained_sizing_candidate_found"
        decision = "advance_retained_candidate_to_single_lot_sanity_replay"
        conclusion = (
            f"当前首批 sizing family 中，`{leader['label']}` 在 FIXED_NOTIONAL_CONTROL 基线下交出了"
            "可继续推进的 provisional retained readout，但仍需先补做 single-lot sanity replay。"
        )
        next_actions = [
            "为 provisional retained candidate 补做 single-lot sanity replay。",
            "在 sanity replay 通过前，不提前打开 cross-exit sensitivity。",
            "把 P2 scorecard 回写进 formal record。",
        ]
    elif watch_candidates:
        leader = watch_candidates[0]
        diagnosis = "watch_only_no_retained_candidate_yet"
        decision = "write_p2_record_and_hold_retained_gate"
        conclusion = (
            f"当前首批 sizing family 尚未产出 provisional retained candidate，`{leader['label']}` 只保留为 watch；"
            "P2 当前更像是排除式读数，而不是已经找到可升格的 sizing 主体。"
        )
        next_actions = [
            "把 watch / no-go 裁决写入 P2 formal record。",
            "继续保持 FIXED_NOTIONAL_CONTROL 为当前正式对照尺子。",
            "在没有 retained candidate 前，不打开 single-lot sanity replay。",
        ]
    else:
        leader = scorecard[0] if scorecard else None
        diagnosis = "no_retained_sizing_candidate_yet"
        decision = "write_p2_record_and_continue_family_program"
        conclusion = (
            "当前首批 sizing family 全部未达到 provisional retained 标准，P2 当前结论应优先读成"
            "排除矩阵与后续缩窄依据，而不是默认仓位升级依据。"
        )
        next_actions = [
            "把 no-go 主体和 residual watch 写入 P2 formal record。",
            "在 P9 前不宣布任何 sizing family 成为默认主线仓位。",
            "如需继续，只允许沿新的 targeted sizing hypothesis 缩窄。",
        ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": diagnosis,
        "decision": decision,
        "canonical_control_label": "FIXED_NOTIONAL_CONTROL",
        "control_summary": {
            "trade_count": control_trade_count,
            "expected_value": control_ev,
            "profit_factor": control_pf,
            "max_drawdown": control_mdd,
            "net_pnl": control.get("net_pnl"),
            "cash_pressure_reject_rate": control_cash_pressure_rate,
            "trade_sequence_max_drawdown": control.get("trade_sequence_max_drawdown"),
        },
        "scorecard": scorecard,
        "provisional_retained_candidates": provisional_retained,
        "watch_candidates": watch_candidates,
        "leader": leader,
        "conclusion": conclusion,
        "next_actions": next_actions,
    }


def read_positioning_sizing_family_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_positioning_sizing_family_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
