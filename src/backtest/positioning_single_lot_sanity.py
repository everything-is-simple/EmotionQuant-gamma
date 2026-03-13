from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.positioning_null_control import (
    POSITIONING_NULL_CONTROL_DTT_VARIANT,
    build_positioning_null_control_scenarios,
)
from src.backtest.positioning_sizing_family import (
    PositioningSizingScenario,
    _build_result_payload,
    _normalize_runtime_for_positioning,
    build_positioning_sizing_family_scenarios,
)
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run


POSITIONING_SINGLE_LOT_SANITY_SCOPE = "positioning_p3_single_lot_sanity"


def build_positioning_single_lot_sanity_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[PositioningSizingScenario]:
    sizing_scenarios = {
        scenario.label: scenario
        for scenario in build_positioning_sizing_family_scenarios(config, initial_cash=initial_cash)
    }
    single_lot = build_positioning_null_control_scenarios(config, initial_cash=initial_cash)[0]

    return [
        PositioningSizingScenario(
            label="SINGLE_LOT_CONTROL",
            family="control-floor",
            notes="Floor sanity control retained by P1; minimum deployment baseline.",
            runtime_overrides={
                "position_sizing_mode": "single_lot",
                "fixed_lot_size": int(single_lot.fixed_lot_size),
            },
        ),
        PositioningSizingScenario(
            label="WILLIAMS_FIXED_RISK",
            family=str(sizing_scenarios["WILLIAMS_FIXED_RISK"].family),
            notes=(
                "P2 provisional leader replayed against SINGLE_LOT_CONTROL to test whether the "
                "improvement survives the floor environment."
            ),
            runtime_overrides=dict(sizing_scenarios["WILLIAMS_FIXED_RISK"].runtime_overrides),
        ),
        PositioningSizingScenario(
            label="FIXED_RATIO",
            family=str(sizing_scenarios["FIXED_RATIO"].family),
            notes=(
                "P2 provisional candidate replayed against SINGLE_LOT_CONTROL to test whether the "
                "improvement survives the floor environment."
            ),
            runtime_overrides=dict(sizing_scenarios["FIXED_RATIO"].runtime_overrides),
        ),
    ]


def _scenario_scope(label: str) -> str:
    return f"{POSITIONING_SINGLE_LOT_SANITY_SCOPE}_{label.strip().lower()}"


def run_positioning_single_lot_sanity_matrix(
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

    scenarios = build_positioning_single_lot_sanity_scenarios(config, initial_cash=starting_cash)
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
        "research_parent": "positioning_single_lot_sanity_replay",
        "research_question": (
            "When replayed against SINGLE_LOT_CONTROL, do the P2 provisional retained sizing candidates "
            "still show a real sizing edge, or were they mainly fixed-notional low-deployment effects?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "canonical_control_label": "SINGLE_LOT_CONTROL",
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "exit_semantics": "current Broker full-exit stop-loss + trailing-stop",
            "p2_candidates_replayed": ["WILLIAMS_FIXED_RISK", "FIXED_RATIO"],
        },
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "results": results,
    }


def build_positioning_single_lot_sanity_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_positioning_single_lot_sanity_matrix",
            "conclusion": "P3 single-lot sanity replay 尚未完成，当前不能裁决候选是否真正在 floor 环境下存活。",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    control = next(
        (
            item
            for item in results
            if isinstance(item, dict) and str(item.get("label") or "") == "SINGLE_LOT_CONTROL"
        ),
        None,
    )
    if control is None:
        raise ValueError("matrix_payload.results must include SINGLE_LOT_CONTROL")

    control_ev = float(control.get("expected_value") or 0.0)
    control_pf = float(control.get("profit_factor") or 0.0)
    control_mdd = float(control.get("max_drawdown") or 0.0)
    control_trade_count = int(control.get("trade_count") or 0)
    control_cash_pressure_rate = float(control.get("cash_pressure_reject_rate") or 0.0)
    control_path_mdd = float(control.get("trade_sequence_max_drawdown") or 0.0)
    control_risk_adjusted_ev = control_ev / max(control_mdd, 1e-9)

    scorecard: list[dict[str, object]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "")
        if label == "SINGLE_LOT_CONTROL":
            continue

        trade_count = int(item.get("trade_count") or 0)
        ev = float(item.get("expected_value") or 0.0)
        pf = float(item.get("profit_factor") or 0.0)
        mdd = float(item.get("max_drawdown") or 0.0)
        cash_pressure_rate = float(item.get("cash_pressure_reject_rate") or 0.0)
        path_mdd = float(item.get("trade_sequence_max_drawdown") or 0.0)
        trade_count_ratio = trade_count / control_trade_count if control_trade_count > 0 else None
        ev_delta = ev - control_ev
        pf_delta = pf - control_pf
        mdd_delta = mdd - control_mdd
        cash_pressure_delta = cash_pressure_rate - control_cash_pressure_rate
        path_mdd_delta = path_mdd - control_path_mdd
        risk_adjusted_ev = ev / max(mdd, 1e-9)
        risk_adjusted_ev_ratio = risk_adjusted_ev / max(control_risk_adjusted_ev, 1e-9)
        total_pnl_delta = float(item.get("net_pnl") or 0.0) - float(control.get("net_pnl") or 0.0)

        survives = bool(
            trade_count_ratio is not None
            and trade_count_ratio >= 0.85
            and ev > control_ev
            and pf >= max(control_pf - 0.05, 1.0)
            and mdd <= max(control_mdd * 1.25, control_mdd + 0.01)
            and path_mdd <= max(control_path_mdd * 1.35, control_path_mdd + 0.03)
            and cash_pressure_delta <= 0.10
            and risk_adjusted_ev_ratio >= 1.10
        )
        watch = bool(
            not survives
            and (
                (trade_count_ratio is not None and trade_count_ratio >= 0.85 and risk_adjusted_ev_ratio >= 1.0)
                or (ev_delta > 0 and pf_delta >= 0)
                or (mdd_delta < 0 and path_mdd_delta < 0)
            )
        )
        verdict = (
            "sanity_survivor"
            if survives
            else "sanity_watch"
            if watch
            else "sanity_fail"
        )

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
                "trade_sequence_max_drawdown": path_mdd,
                "trade_sequence_max_drawdown_delta_vs_control": path_mdd_delta,
                "risk_adjusted_ev": risk_adjusted_ev,
                "risk_adjusted_ev_ratio_vs_control": risk_adjusted_ev_ratio,
                "net_pnl": item.get("net_pnl"),
                "net_pnl_delta_vs_control": total_pnl_delta,
                "cash_pressure_reject_rate": cash_pressure_rate,
                "cash_pressure_delta_vs_control": cash_pressure_delta,
                "runtime_overrides": item.get("runtime_overrides"),
            }
        )

    scorecard.sort(
        key=lambda item: (
            {"sanity_survivor": 2, "sanity_watch": 1, "sanity_fail": 0}[str(item["verdict"])],
            float(item.get("risk_adjusted_ev_ratio_vs_control") or 0.0),
            float(item.get("expected_value_delta_vs_control") or 0.0),
            -float(item.get("cash_pressure_delta_vs_control") or 999.0),
        ),
        reverse=True,
    )

    survivors = [item for item in scorecard if item["verdict"] == "sanity_survivor"]
    watches = [item for item in scorecard if item["verdict"] == "sanity_watch"]

    if len(survivors) >= 2:
        diagnosis = "both_provisional_candidates_survive_single_lot_sanity"
        decision = "advance_both_candidates_to_p4_retained_or_no_go"
        conclusion = (
            "P2 的两条 provisional retained candidate 在 SINGLE_LOT_CONTROL floor 环境下都保住了改善，"
            "它们更像真实 sizing edge，而不是 fixed-notional 低部署幻觉。"
        )
    elif len(survivors) == 1:
        diagnosis = "only_one_candidate_survives_single_lot_sanity"
        decision = "advance_single_survivor_to_p4_retained_or_no_go"
        conclusion = (
            f"只有 `{survivors[0]['label']}` 在 SINGLE_LOT_CONTROL floor 环境下保住了改善；"
            "另一条 candidate 更像 fixed-notional 环境产物。"
        )
    else:
        leader = watches[0]["label"] if watches else "none"
        diagnosis = "no_candidate_survives_single_lot_sanity"
        decision = "write_p3_record_and_prepare_p4_no_retained_case"
        conclusion = (
            "P2 的 provisional retained candidate 在 SINGLE_LOT_CONTROL floor 环境下未能保住改善；"
            f"当前只能把 `{leader}` 读成 residual watch 或直接写 no-retained case。"
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": diagnosis,
        "decision": decision,
        "canonical_control_label": "SINGLE_LOT_CONTROL",
        "control_summary": {
            "trade_count": control_trade_count,
            "expected_value": control_ev,
            "profit_factor": control_pf,
            "max_drawdown": control_mdd,
            "net_pnl": control.get("net_pnl"),
            "cash_pressure_reject_rate": control_cash_pressure_rate,
            "trade_sequence_max_drawdown": control_path_mdd,
            "risk_adjusted_ev": control_risk_adjusted_ev,
        },
        "scorecard": scorecard,
        "survivors": survivors,
        "watch_candidates": watches,
        "conclusion": conclusion,
        "next_actions": [
            "把 P3 scorecard 回写进 formal record。",
            "仅在存在 sanity survivor 时推进 P4 retained-or-no-go。",
            "在 P4 前不提前打开 cross-exit sensitivity。",
        ],
    }


def read_positioning_single_lot_sanity_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_positioning_single_lot_sanity_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
