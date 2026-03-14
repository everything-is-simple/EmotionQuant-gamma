from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.partial_exit_null_control import (
    POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
    _failure_reason_breakdown,
    _load_orders,
    _load_paired_trades,
    _paired_shape_metrics,
    _position_consistency_metrics,
    _safe_ratio,
    _snapshot_signal_counts,
)
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run


POSITIONING_PARTIAL_EXIT_FAMILY_SCOPE = "positioning_p8_partial_exit_family"


@dataclass(frozen=True)
class PartialExitFamilyScenario:
    label: str
    family: str
    notes: str
    exit_control_mode: str
    partial_exit_scale_out_ratio: float
    position_sizing_mode: str
    fixed_lot_size: int
    fixed_notional_amount: float


def build_positioning_partial_exit_family_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[PartialExitFamilyScenario]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    fixed_notional_amount = float(config.fixed_notional_amount)
    if fixed_notional_amount <= 0:
        fixed_notional_amount = starting_cash * float(config.max_position_pct)

    fixed_lot_size = max(int(config.fixed_lot_size), 100)
    control = PartialExitFamilyScenario(
        label="FULL_EXIT_CONTROL",
        family="control",
        notes="Canonical control baseline retained by P7.",
        exit_control_mode="full_exit_control",
        partial_exit_scale_out_ratio=0.0,
        position_sizing_mode="fixed_notional",
        fixed_lot_size=fixed_lot_size,
        fixed_notional_amount=float(fixed_notional_amount),
    )
    ratios = [
        ("TRAIL_SCALE_OUT_25_75", 0.25, "Sell 25% on the first trailing-stop leg and keep 75% for the terminal leg."),
        ("TRAIL_SCALE_OUT_33_67", 1.0 / 3.0, "Sell one-third on the first trailing-stop leg and keep two-thirds for the terminal leg."),
        ("TRAIL_SCALE_OUT_50_50", 0.50, "Sell 50% on the first trailing-stop leg and keep 50% for the terminal leg."),
        ("TRAIL_SCALE_OUT_67_33", 2.0 / 3.0, "Sell two-thirds on the first trailing-stop leg and keep one-third for the terminal leg."),
        ("TRAIL_SCALE_OUT_75_25", 0.75, "Sell 75% on the first trailing-stop leg and keep 25% for the terminal leg."),
    ]
    families = [
        PartialExitFamilyScenario(
            label=label,
            family="naive-trailing-scale-out",
            notes=notes,
            exit_control_mode="naive_trail_scale_out_50_50_control",
            partial_exit_scale_out_ratio=ratio,
            position_sizing_mode="fixed_notional",
            fixed_lot_size=fixed_lot_size,
            fixed_notional_amount=float(fixed_notional_amount),
        )
        for label, ratio, notes in ratios
    ]
    return [control, *families]


def _normalize_runtime_for_partial_exit_family(
    config: Settings,
    scenario: PartialExitFamilyScenario,
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
    cfg.partial_exit_scale_out_ratio = float(scenario.partial_exit_scale_out_ratio)
    cfg.fixed_lot_size = int(scenario.fixed_lot_size)
    cfg.fixed_notional_amount = float(scenario.fixed_notional_amount)
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _build_trade_path_metrics(
    paired: pd.DataFrame,
    *,
    initial_cash: float,
) -> dict[str, float | int | None]:
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
    equity_curve = float(initial_cash) + ordered["pnl"].cumsum()
    running_peak = equity_curve.cummax()
    drawdown = (running_peak - equity_curve) / running_peak.replace(0, pd.NA)
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
    return f"{POSITIONING_PARTIAL_EXIT_FAMILY_SCOPE}_{label.strip().lower()}"


def _build_result_payload(
    *,
    scenario: PartialExitFamilyScenario,
    result,
    store: Store,
    start: date,
    end: date,
    initial_cash: float,
    run_id: str,
) -> dict[str, object]:
    orders = _load_orders(store, start, end)
    paired = _load_paired_trades(store, start, end)
    signal_counts = _snapshot_signal_counts(store, start, end, run_id)
    position_metrics = _position_consistency_metrics(orders)
    paired_metrics = _paired_shape_metrics(paired)
    path_metrics = _build_trade_path_metrics(paired, initial_cash=initial_cash)

    partial_exit_pair_count = int(paired_metrics.get("partial_exit_pair_count") or 0)
    paired_trade_count = int(paired_metrics.get("paired_trade_count") or 0)
    partial_exit_pair_share = _safe_ratio(partial_exit_pair_count, paired_trade_count)

    return {
        "label": scenario.label,
        "family": scenario.family,
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": "dtt",
        "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
        "exit_control_mode": scenario.exit_control_mode,
        "partial_exit_scale_out_ratio": float(scenario.partial_exit_scale_out_ratio),
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
        **path_metrics,
        "partial_exit_pair_share": partial_exit_pair_share,
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
    }


def run_positioning_partial_exit_family_matrix(
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

    scenarios = build_positioning_partial_exit_family_scenarios(config, initial_cash=starting_cash)
    results: list[dict[str, object]] = []
    for scenario in scenarios:
        cfg = _normalize_runtime_for_partial_exit_family(config, scenario)
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
        "research_parent": "positioning_partial_exit_family_replay",
        "research_question": (
            "Under the same BOF-only / no IRS / no MSS frozen baseline and with FULL_EXIT_CONTROL kept as the "
            "canonical control, which first-batch trailing partial-exit ratio family improves on the control "
            "without merely inflating pair count or degrading entry participation?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "canonical_control_label": "FULL_EXIT_CONTROL",
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "sizing_baseline": "FIXED_NOTIONAL_CONTROL",
            "control_baseline": "FULL_EXIT_CONTROL",
            "family_shape": "single trailing-stop partial-exit leg plus terminal liquidation leg",
        },
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "results": results,
    }


def build_positioning_partial_exit_family_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_positioning_partial_exit_family_matrix",
            "conclusion": "P8 partial-exit family matrix 尚未完成，当前不能裁定 retained-or-no-go。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (
            item
            for item in results
            if isinstance(item, dict) and str(item.get("label") or "") == "FULL_EXIT_CONTROL"
        ),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include FULL_EXIT_CONTROL")

    control_trade_count = int(control.get("trade_count") or 0)
    control_buy_filled_count = int(control.get("buy_filled_count") or 0)
    control_ev = float(control.get("expected_value") or 0.0)
    control_pf = float(control.get("profit_factor") or 0.0)
    control_mdd = float(control.get("max_drawdown") or 0.0)
    control_net_pnl = float(control.get("net_pnl") or 0.0)
    control_path_mdd = float(control.get("trade_sequence_max_drawdown") or 0.0)

    scorecard: list[dict[str, object]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "")
        if label == "FULL_EXIT_CONTROL":
            continue

        trade_count = int(item.get("trade_count") or 0)
        buy_filled_count = int(item.get("buy_filled_count") or 0)
        expected_value = float(item.get("expected_value") or 0.0)
        profit_factor = float(item.get("profit_factor") or 0.0)
        max_drawdown = float(item.get("max_drawdown") or 0.0)
        net_pnl = float(item.get("net_pnl") or 0.0)
        path_mdd = float(item.get("trade_sequence_max_drawdown") or 0.0)
        partial_exit_pair_count = int(item.get("partial_exit_pair_count") or 0)

        buy_fill_ratio = _safe_ratio(buy_filled_count, control_buy_filled_count)
        trade_count_ratio = _safe_ratio(trade_count, control_trade_count)
        ev_delta = expected_value - control_ev
        pf_delta = profit_factor - control_pf
        mdd_delta = max_drawdown - control_mdd
        net_pnl_delta = net_pnl - control_net_pnl
        path_mdd_delta = path_mdd - control_path_mdd

        retained_candidate = bool(
            partial_exit_pair_count >= 100
            and buy_fill_ratio is not None
            and buy_fill_ratio >= 0.95
            and ev_delta >= 0.002
            and profit_factor >= max(control_pf - 0.05, 1.0)
            and max_drawdown <= max(control_mdd * 1.05, control_mdd + 0.01)
            and path_mdd <= max(control_path_mdd * 1.10, control_path_mdd + 0.02)
            and net_pnl_delta >= 0.0
        )
        watch_candidate = bool(
            not retained_candidate
            and partial_exit_pair_count > 0
            and buy_fill_ratio is not None
            and buy_fill_ratio >= 0.90
            and (ev_delta > 0 or pf_delta > 0 or mdd_delta < 0 or net_pnl_delta > 0)
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
                "partial_exit_scale_out_ratio": item.get("partial_exit_scale_out_ratio"),
                "trade_count": trade_count,
                "trade_count_ratio_vs_control": trade_count_ratio,
                "buy_filled_count": buy_filled_count,
                "buy_fill_ratio_vs_control": buy_fill_ratio,
                "partial_exit_pair_count": partial_exit_pair_count,
                "partial_exit_pair_share": item.get("partial_exit_pair_share"),
                "expected_value": expected_value,
                "expected_value_delta_vs_control": ev_delta,
                "profit_factor": profit_factor,
                "profit_factor_delta_vs_control": pf_delta,
                "max_drawdown": max_drawdown,
                "max_drawdown_delta_vs_control": mdd_delta,
                "net_pnl": net_pnl,
                "net_pnl_delta_vs_control": net_pnl_delta,
                "trade_sequence_max_drawdown": item.get("trade_sequence_max_drawdown"),
                "trade_sequence_max_drawdown_delta_vs_control": path_mdd_delta,
                "avg_hold_days": item.get("avg_hold_days"),
                "avg_hold_days_delta_vs_control": (
                    float(item.get("avg_hold_days") or 0.0) - float(control.get("avg_hold_days") or 0.0)
                    if item.get("avg_hold_days") is not None and control.get("avg_hold_days") is not None
                    else None
                ),
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
    no_go = [item for item in scorecard if item["verdict"] == "no_go"]

    if provisional_retained:
        leader = provisional_retained[0]
        diagnosis = "provisional_retained_partial_exit_candidate_found"
        decision = "write_p8_record_with_retained_queue"
        conclusion = (
            f"首批 partial-exit family 中，`{leader['label']}` 已在 FULL_EXIT_CONTROL 基线下交出可以继续保留的 "
            "provisional retained readout，但当前仍只允许把它写进 P8 formal record，不提前打开 PX2。"
        )
        next_actions = [
            "把 retained / watch / no-go 裁决写入 P8 formal record。",
            "P9 只收口 partial-exit lane 结果，不在 closeout 卡重开 replay。",
            "只有当 retained leader 形成明确 targeted mechanism hypothesis 时，PX2 才允许打开。",
        ]
    elif watch_candidates:
        leader = watch_candidates[0]
        diagnosis = "watch_only_partial_exit_family"
        decision = "write_p8_record_and_hold_px2_conditional"
        conclusion = (
            f"首批 partial-exit family 当前尚未产出 provisional retained candidate，`{leader['label']}` 只保留为 "
            "watch candidate。它可以支撑后续 targeted hypothesis，但还不构成默认 exit 升格依据。"
        )
        next_actions = [
            "把 watch / no-go 裁决写入 P8 formal record。",
            "P9 继续以 FULL_EXIT_CONTROL 作为 canonical baseline 做战役收官。",
            "只有当 watch leader 能压缩成单一 targeted mechanism hypothesis 时，PX2 才允许打开。",
        ]
    else:
        leader = scorecard[0] if scorecard else None
        diagnosis = "no_retained_partial_exit_family_yet"
        decision = "write_p8_record_and_close_to_p9"
        conclusion = (
            "首批 partial-exit family 当前没有产生 provisional retained candidate，也没有形成足够干净的 watch object；"
            "P8 应把结果读成排除式矩阵，而不是默认 exit 升格依据。"
        )
        next_actions = [
            "把 no-go 结果写入 P8 formal record。",
            "P9 继续保持 FULL_EXIT_CONTROL 为 partial-exit lane 的 formal baseline。",
            "未经新的 targeted hypothesis package，不重开 partial-exit family 全矩阵。",
        ]

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": diagnosis,
        "decision": decision,
        "canonical_control_label": "FULL_EXIT_CONTROL",
        "control_summary": {
            "trade_count": control_trade_count,
            "buy_filled_count": control_buy_filled_count,
            "expected_value": control_ev,
            "profit_factor": control_pf,
            "max_drawdown": control_mdd,
            "net_pnl": control_net_pnl,
            "trade_sequence_max_drawdown": control.get("trade_sequence_max_drawdown"),
        },
        "scorecard": scorecard,
        "provisional_retained_candidates": provisional_retained,
        "watch_candidates": watch_candidates,
        "no_go": no_go,
        "leader": leader,
        "conclusion": conclusion,
        "next_actions": next_actions,
    }


def read_positioning_partial_exit_family_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_positioning_partial_exit_family_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
