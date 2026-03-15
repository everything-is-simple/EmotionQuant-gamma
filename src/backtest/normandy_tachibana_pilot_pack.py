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
from src.backtest.positioning_partial_exit_family import build_positioning_partial_exit_family_digest
from src.config import Settings
from src.contracts import Signal, Trade
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import finish_run, start_run

NORMANDY_TACHIBANA_PILOT_PACK_SCOPE = "normandy_tachibana_pilot_pack"
CANONICAL_CONTROL_LABEL = "FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0"
OPERATING_PROXY_LABEL = "TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0"
FLOOR_CONTROL_LABEL = "FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL__CD0"
FLOOR_PROXY_LABEL = "TRAIL_SCALE_OUT_25_75__SINGLE_LOT_CONTROL__CD0"


@dataclass(frozen=True)
class TachibanaPilotPackScenario:
    label: str
    pilot_pack_component: str
    notes: str
    exit_control_mode: str
    partial_exit_scale_out_ratio: float
    position_sizing_mode: str
    fixed_lot_size: int
    fixed_notional_amount: float
    entry_cooldown_trade_days: int
    unit_regime_tag: str
    reduced_unit_scale: float
    experimental_segment_policy: str


class SameCodeCooldownSignalFilter:
    def __init__(self, trade_day_index: dict[date, int], cooldown_trade_days: int):
        self._trade_day_index = trade_day_index
        self.cooldown_trade_days = max(int(cooldown_trade_days), 0)
        self._last_full_exit_index_by_code: dict[str, int] = {}
        self.total_signal_count = 0
        self.allowed_signal_count = 0
        self.blocked_signal_count = 0
        self.full_exit_event_count = 0

    def __call__(
        self,
        signals: list[Signal],
        trade_day: date,
        filled_trades: list[Trade],
        broker,
        store: Store,
    ) -> list[Signal]:
        current_index = self._trade_day_index.get(trade_day)
        if current_index is None:
            self.total_signal_count += len(signals)
            self.allowed_signal_count += len(signals)
            return signals

        for trade in filled_trades:
            if trade.action != "SELL":
                continue
            if int(trade.remaining_qty_after or 0) > 0:
                continue
            self._last_full_exit_index_by_code[trade.code] = current_index
            self.full_exit_event_count += 1

        self.total_signal_count += len(signals)
        if self.cooldown_trade_days <= 0:
            self.allowed_signal_count += len(signals)
            return signals

        filtered: list[Signal] = []
        for signal in signals:
            last_exit_index = self._last_full_exit_index_by_code.get(signal.code)
            if last_exit_index is not None and (current_index - last_exit_index) < self.cooldown_trade_days:
                self.blocked_signal_count += 1
                continue
            filtered.append(signal)

        self.allowed_signal_count += len(filtered)
        return filtered

    def build_metrics(self) -> dict[str, object]:
        blocked_share = _safe_ratio(self.blocked_signal_count, self.total_signal_count)
        return {
            "entry_cooldown_trade_days": int(self.cooldown_trade_days),
            "cooldown_scope": "same_code_after_full_exit",
            "cooldown_total_signal_count": int(self.total_signal_count),
            "cooldown_allowed_signal_count": int(self.allowed_signal_count),
            "cooldown_blocked_signal_count": int(self.blocked_signal_count),
            "cooldown_blocked_signal_share": float(blocked_share or 0.0),
            "cooldown_full_exit_event_count": int(self.full_exit_event_count),
        }


def _resolve_component(position_sizing_mode: str, cooldown_trade_days: int) -> str:
    if position_sizing_mode == "single_lot":
        return "E3_unit_regime_overlay"
    if cooldown_trade_days > 0:
        return "E2_cooldown_overlay_family"
    return "E1_reduce_to_core_proxy_replay"


def build_normandy_tachibana_pilot_pack_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
    include_side_references: bool = False,
) -> list[TachibanaPilotPackScenario]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    fixed_notional_amount = float(config.fixed_notional_amount)
    if fixed_notional_amount <= 0:
        fixed_notional_amount = starting_cash * float(config.max_position_pct)

    fixed_lot_size = max(int(config.fixed_lot_size), 100)
    fixed_regime_tag = config.tachibana_unit_regime_tag.strip() or "fixed_notional_control"
    reduced_scale = float(config.tachibana_reduced_unit_scale)
    experimental_policy = (
        config.tachibana_experimental_segment_policy.strip() or "isolate_from_canonical_aggregate"
    )

    def make_scenario(
        *,
        label: str,
        notes: str,
        exit_control_mode: str,
        partial_exit_scale_out_ratio: float,
        position_sizing_mode: str,
        fixed_notional: float,
        cooldown_trade_days: int,
        unit_regime_tag: str,
        reduced_unit_scale: float,
    ) -> TachibanaPilotPackScenario:
        return TachibanaPilotPackScenario(
            label=label,
            pilot_pack_component=_resolve_component(position_sizing_mode, cooldown_trade_days),
            notes=notes,
            exit_control_mode=exit_control_mode,
            partial_exit_scale_out_ratio=float(partial_exit_scale_out_ratio),
            position_sizing_mode=position_sizing_mode,
            fixed_lot_size=fixed_lot_size,
            fixed_notional_amount=float(fixed_notional),
            entry_cooldown_trade_days=int(cooldown_trade_days),
            unit_regime_tag=unit_regime_tag,
            reduced_unit_scale=float(reduced_unit_scale),
            experimental_segment_policy=experimental_policy,
        )

    scenarios: list[TachibanaPilotPackScenario] = []
    for cooldown_trade_days in [0, 2, 5, 10]:
        scenarios.append(
            make_scenario(
                label=f"FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD{cooldown_trade_days}",
                notes="Canonical full-exit control on the operating fixed-notional baseline.",
                exit_control_mode="full_exit_control",
                partial_exit_scale_out_ratio=0.0,
                position_sizing_mode="fixed_notional",
                fixed_notional=float(fixed_notional_amount),
                cooldown_trade_days=cooldown_trade_days,
                unit_regime_tag=fixed_regime_tag,
                reduced_unit_scale=reduced_scale,
            )
        )
        scenarios.append(
            make_scenario(
                label=f"TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD{cooldown_trade_days}",
                notes="Current reduce-to-core engineering proxy on the operating fixed-notional baseline.",
                exit_control_mode="naive_trail_scale_out_50_50_control",
                partial_exit_scale_out_ratio=0.25,
                position_sizing_mode="fixed_notional",
                fixed_notional=float(fixed_notional_amount),
                cooldown_trade_days=cooldown_trade_days,
                unit_regime_tag=fixed_regime_tag,
                reduced_unit_scale=reduced_scale,
            )
        )

    scenarios.append(
        make_scenario(
            label=FLOOR_CONTROL_LABEL,
            notes="Floor sanity line for the canonical full-exit control.",
            exit_control_mode="full_exit_control",
            partial_exit_scale_out_ratio=0.0,
            position_sizing_mode="single_lot",
            fixed_notional=0.0,
            cooldown_trade_days=0,
            unit_regime_tag="single_lot_control",
            reduced_unit_scale=1.0,
        )
    )
    scenarios.append(
        make_scenario(
            label=FLOOR_PROXY_LABEL,
            notes="Floor sanity line for the current reduce-to-core engineering proxy.",
            exit_control_mode="naive_trail_scale_out_50_50_control",
            partial_exit_scale_out_ratio=0.25,
            position_sizing_mode="single_lot",
            fixed_notional=0.0,
            cooldown_trade_days=0,
            unit_regime_tag="single_lot_control",
            reduced_unit_scale=1.0,
        )
    )

    if include_side_references:
        scenarios.append(
            make_scenario(
                label="TRAIL_SCALE_OUT_33_67__FIXED_NOTIONAL_CONTROL__CD0",
                notes="Side reference only; kept for context, not promoted to the default pilot anchor.",
                exit_control_mode="naive_trail_scale_out_50_50_control",
                partial_exit_scale_out_ratio=1.0 / 3.0,
                position_sizing_mode="fixed_notional",
                fixed_notional=float(fixed_notional_amount),
                cooldown_trade_days=0,
                unit_regime_tag=fixed_regime_tag,
                reduced_unit_scale=reduced_scale,
            )
        )
        scenarios.append(
            make_scenario(
                label="TRAIL_SCALE_OUT_50_50__FIXED_NOTIONAL_CONTROL__CD0",
                notes="Side reference only; kept for context, not promoted to the default pilot anchor.",
                exit_control_mode="naive_trail_scale_out_50_50_control",
                partial_exit_scale_out_ratio=0.50,
                position_sizing_mode="fixed_notional",
                fixed_notional=float(fixed_notional_amount),
                cooldown_trade_days=0,
                unit_regime_tag=fixed_regime_tag,
                reduced_unit_scale=reduced_scale,
            )
        )

    return scenarios


def select_normandy_tachibana_pilot_pack_scenarios(
    scenarios: list[TachibanaPilotPackScenario],
    labels: list[str] | None,
) -> list[TachibanaPilotPackScenario]:
    if not labels:
        return scenarios

    normalized = {label.strip().upper() for label in labels if label.strip()}
    selected = [scenario for scenario in scenarios if scenario.label.upper() in normalized]
    missing = sorted(normalized - {scenario.label.upper() for scenario in selected})
    if missing:
        raise ValueError(f"unknown tachibana pilot-pack labels: {', '.join(missing)}")
    return selected


def _normalize_runtime_for_tachibana_pilot_pack(
    config: Settings,
    scenario: TachibanaPilotPackScenario,
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
    cfg.entry_cooldown_trade_days = int(scenario.entry_cooldown_trade_days)
    cfg.tachibana_pilot_mode = True
    cfg.tachibana_unit_regime_tag = scenario.unit_regime_tag
    cfg.tachibana_reduced_unit_scale = float(scenario.reduced_unit_scale)
    cfg.tachibana_experimental_segment_policy = scenario.experimental_segment_policy
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _load_trade_day_index(store: Store, start: date, end: date) -> dict[date, int]:
    trade_days = store.read_df(
        """
        SELECT date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE
          AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if trade_days.empty:
        return {}
    values = [item.date() if isinstance(item, pd.Timestamp) else item for item in trade_days["date"].tolist()]
    return {trade_day: idx for idx, trade_day in enumerate(values)}


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
    return f"{NORMANDY_TACHIBANA_PILOT_PACK_SCOPE}_{label.strip().lower()}"


def _build_result_payload(
    *,
    scenario: TachibanaPilotPackScenario,
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
    filter_metrics = dict(result.signal_filter_metrics or {})

    partial_exit_pair_count = int(paired_metrics.get("partial_exit_pair_count") or 0)
    paired_trade_count = int(paired_metrics.get("paired_trade_count") or 0)
    partial_exit_pair_share = _safe_ratio(partial_exit_pair_count, paired_trade_count)

    return {
        "label": scenario.label,
        "pilot_pack_component": scenario.pilot_pack_component,
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": "dtt",
        "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
        "exit_control_mode": scenario.exit_control_mode,
        "partial_exit_scale_out_ratio": float(scenario.partial_exit_scale_out_ratio),
        "position_sizing_mode": scenario.position_sizing_mode,
        "fixed_lot_size": int(scenario.fixed_lot_size),
        "fixed_notional_amount": float(scenario.fixed_notional_amount),
        "entry_cooldown_trade_days": int(scenario.entry_cooldown_trade_days),
        "unit_regime_tag": scenario.unit_regime_tag,
        "reduced_unit_scale": float(scenario.reduced_unit_scale),
        "experimental_segment_policy": scenario.experimental_segment_policy,
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
        **filter_metrics,
        "partial_exit_pair_share": partial_exit_pair_share,
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
    }


def run_normandy_tachibana_pilot_pack_matrix(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
    scenario_labels: list[str] | None = None,
    include_side_references: bool = False,
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

    calendar_store = Store(db_file)
    try:
        trade_day_index = _load_trade_day_index(calendar_store, start, end)
    finally:
        calendar_store.close()

    scenarios = select_normandy_tachibana_pilot_pack_scenarios(
        build_normandy_tachibana_pilot_pack_scenarios(
            config,
            initial_cash=starting_cash,
            include_side_references=include_side_references,
        ),
        scenario_labels,
    )

    results: list[dict[str, object]] = []
    for scenario in scenarios:
        cfg = _normalize_runtime_for_tachibana_pilot_pack(config, scenario)
        cooldown_filter = SameCodeCooldownSignalFilter(
            trade_day_index=trade_day_index,
            cooldown_trade_days=scenario.entry_cooldown_trade_days,
        )

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
                signal_filter=cooldown_filter,
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
        "research_parent": "tachibana_pilot_pack_runner",
        "research_question": (
            "Under the current BOF stack and the frozen third-lane baseline, can the Tachibana migratable subset "
            "form a credible pilot when reduce-to-core proxy replay, cooldown gating, unit-regime tags, and "
            "experimental-segment isolation are kept explicit?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "canonical_control_label": CANONICAL_CONTROL_LABEL,
        "operating_proxy_label": OPERATING_PROXY_LABEL,
        "floor_control_label": FLOOR_CONTROL_LABEL,
        "floor_proxy_label": FLOOR_PROXY_LABEL,
        "baseline_runtime": {
            "pipeline_mode": "dtt",
            "dtt_variant": POSITIONING_PARTIAL_EXIT_NULL_CONTROL_DTT_VARIANT,
            "patterns": ["bof"],
            "enable_irs_filter": False,
            "enable_mss_gate": False,
            "entry_family": "BOF control only",
            "canonical_control_baseline": "FULL_EXIT_CONTROL",
            "operating_sizing_baseline": "FIXED_NOTIONAL_CONTROL",
            "floor_sizing_baseline": "SINGLE_LOT_CONTROL",
            "experimental_segment_policy": (
                config.tachibana_experimental_segment_policy.strip()
                or "isolate_from_canonical_aggregate"
            ),
        },
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "results": results,
    }


def _normalize_to_e1_label(label: str) -> str:
    if "__FIXED_NOTIONAL_CONTROL__CD0" in label:
        return label.split("__FIXED_NOTIONAL_CONTROL__CD0", 1)[0]
    return label


def _build_e1_digest_payload(results: list[dict[str, object]]) -> dict[str, object]:
    e1_results = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if str(item.get("position_sizing_mode") or "") != "fixed_notional":
            continue
        if int(item.get("entry_cooldown_trade_days") or 0) != 0:
            continue
        cloned = dict(item)
        cloned["label"] = _normalize_to_e1_label(str(item.get("label") or ""))
        e1_results.append(cloned)

    if not e1_results:
        return {
            "matrix_status": "completed",
            "decision": "missing_e1_subset",
            "conclusion": "No cooldown-0 fixed-notional subset found for the E1 formal-entry digest.",
        }

    return build_positioning_partial_exit_family_digest(
        {
            "matrix_status": "completed",
            "research_parent": "tachibana_pilot_pack_e1_formal_entry",
            "results": e1_results,
        }
    )


def _build_cooldown_scorecard(
    results: list[dict[str, object]],
    canonical_control: dict[str, object],
) -> list[dict[str, object]]:
    control_trade_count = int(canonical_control.get("trade_count") or 0)
    control_buy_filled_count = int(canonical_control.get("buy_filled_count") or 0)
    control_ev = float(canonical_control.get("expected_value") or 0.0)
    control_pf = float(canonical_control.get("profit_factor") or 0.0)
    control_mdd = float(canonical_control.get("max_drawdown") or 0.0)
    control_net_pnl = float(canonical_control.get("net_pnl") or 0.0)

    scorecard: list[dict[str, object]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if str(item.get("position_sizing_mode") or "") != "fixed_notional":
            continue
        cooldown_trade_days = int(item.get("entry_cooldown_trade_days") or 0)
        if cooldown_trade_days <= 0:
            continue

        trade_count = int(item.get("trade_count") or 0)
        buy_filled_count = int(item.get("buy_filled_count") or 0)
        expected_value = float(item.get("expected_value") or 0.0)
        profit_factor = float(item.get("profit_factor") or 0.0)
        max_drawdown = float(item.get("max_drawdown") or 0.0)
        net_pnl = float(item.get("net_pnl") or 0.0)
        label = str(item.get("label") or "")
        scenario_kind = "proxy" if label.startswith("TRAIL_SCALE_OUT_25_75") else "control"

        scorecard.append(
            {
                "label": label,
                "scenario_kind": scenario_kind,
                "entry_cooldown_trade_days": cooldown_trade_days,
                "trade_count": trade_count,
                "trade_count_ratio_vs_canonical": _safe_ratio(trade_count, control_trade_count),
                "buy_filled_count": buy_filled_count,
                "buy_fill_ratio_vs_canonical": _safe_ratio(buy_filled_count, control_buy_filled_count),
                "expected_value": expected_value,
                "expected_value_delta_vs_canonical": expected_value - control_ev,
                "profit_factor": profit_factor,
                "profit_factor_delta_vs_canonical": profit_factor - control_pf,
                "max_drawdown": max_drawdown,
                "max_drawdown_delta_vs_canonical": max_drawdown - control_mdd,
                "net_pnl": net_pnl,
                "net_pnl_delta_vs_canonical": net_pnl - control_net_pnl,
                "cooldown_blocked_signal_count": int(item.get("cooldown_blocked_signal_count") or 0),
                "cooldown_blocked_signal_share": float(item.get("cooldown_blocked_signal_share") or 0.0),
            }
        )

    scorecard.sort(
        key=lambda item: (
            -int(item["entry_cooldown_trade_days"]),
            0 if item["scenario_kind"] == "proxy" else 1,
            float(item.get("net_pnl_delta_vs_canonical") or 0.0),
        )
    )
    return scorecard


def _build_floor_sanity_summary(
    results_by_label: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    floor_control = results_by_label.get(FLOOR_CONTROL_LABEL)
    floor_proxy = results_by_label.get(FLOOR_PROXY_LABEL)
    if floor_control is None or floor_proxy is None:
        return None

    ev_delta = float(floor_proxy.get("expected_value") or 0.0) - float(floor_control.get("expected_value") or 0.0)
    pf_delta = float(floor_proxy.get("profit_factor") or 0.0) - float(floor_control.get("profit_factor") or 0.0)
    mdd_delta = float(floor_proxy.get("max_drawdown") or 0.0) - float(floor_control.get("max_drawdown") or 0.0)
    trade_count_delta = int(floor_proxy.get("trade_count") or 0) - int(floor_control.get("trade_count") or 0)
    partial_exit_pair_count = int(floor_proxy.get("partial_exit_pair_count") or 0)
    degenerate = partial_exit_pair_count == 0 and trade_count_delta == 0 and abs(ev_delta) < 1e-9 and abs(pf_delta) < 1e-9

    return {
        "control_label": FLOOR_CONTROL_LABEL,
        "proxy_label": FLOOR_PROXY_LABEL,
        "trade_count_delta_vs_floor_control": trade_count_delta,
        "expected_value_delta_vs_floor_control": ev_delta,
        "profit_factor_delta_vs_floor_control": pf_delta,
        "max_drawdown_delta_vs_floor_control": mdd_delta,
        "partial_exit_pair_count": partial_exit_pair_count,
        "degenerate_to_full_exit": degenerate,
    }


def build_normandy_tachibana_pilot_pack_digest(matrix_payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(matrix_payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_normandy_tachibana_pilot_pack_matrix",
            "conclusion": "Tachibana pilot-pack matrix is not complete yet.",
        }

    results = matrix_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("matrix_payload.results must be a list")

    results_by_label = {
        str(item.get("label") or ""): item
        for item in results
        if isinstance(item, dict) and str(item.get("label") or "")
    }
    canonical_control = results_by_label.get(CANONICAL_CONTROL_LABEL)
    if canonical_control is None:
        raise ValueError(f"matrix_payload.results must include {CANONICAL_CONTROL_LABEL}")

    e1_digest = _build_e1_digest_payload(results)
    cooldown_scorecard = _build_cooldown_scorecard(results, canonical_control)
    floor_sanity_summary = _build_floor_sanity_summary(results_by_label)

    proxy_cooldown_rows = [item for item in cooldown_scorecard if item["scenario_kind"] == "proxy"]
    control_cooldown_rows = [item for item in cooldown_scorecard if item["scenario_kind"] == "control"]
    proxy_cooldown_leader = max(
        proxy_cooldown_rows,
        key=lambda item: (
            float(item.get("net_pnl_delta_vs_canonical") or 0.0),
            float(item.get("expected_value_delta_vs_canonical") or 0.0),
            -float(item.get("cooldown_blocked_signal_share") or 1.0),
        ),
        default=None,
    )
    control_cooldown_leader = max(
        control_cooldown_rows,
        key=lambda item: (
            float(item.get("net_pnl_delta_vs_canonical") or 0.0),
            float(item.get("expected_value_delta_vs_canonical") or 0.0),
            -float(item.get("cooldown_blocked_signal_share") or 1.0),
        ),
        default=None,
    )

    floor_line_status = "not_run"
    if floor_sanity_summary is not None:
        floor_line_status = (
            "degenerate_to_full_exit"
            if bool(floor_sanity_summary.get("degenerate_to_full_exit"))
            else "distinct_floor_readout"
        )

    conclusion_parts = [
        f"E1 formal-entry digest stays anchored on `{str((e1_digest.get('leader') or {}).get('label') or 'UNKNOWN')}`."
    ]
    if proxy_cooldown_leader is not None:
        conclusion_parts.append(
            "Proxy cooldown leader is "
            f"`{proxy_cooldown_leader['label']}` with "
            f"`cooldown_blocked_signal_share={float(proxy_cooldown_leader.get('cooldown_blocked_signal_share') or 0.0):.4f}`."
        )
    if floor_sanity_summary is not None:
        conclusion_parts.append(f"Floor line currently reads `{floor_line_status}`.")

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "research_parent": matrix_payload.get("research_parent"),
        "diagnosis": "tachibana_pilot_pack_runner_readout_ready",
        "decision": "use_normandy_tachibana_pilot_pack_runner",
        "canonical_control_label": CANONICAL_CONTROL_LABEL,
        "operating_proxy_label": OPERATING_PROXY_LABEL,
        "floor_control_label": FLOOR_CONTROL_LABEL,
        "floor_proxy_label": FLOOR_PROXY_LABEL,
        "e1_formal_entry_digest": e1_digest,
        "cooldown_scorecard": cooldown_scorecard,
        "proxy_cooldown_leader": proxy_cooldown_leader,
        "control_cooldown_leader": control_cooldown_leader,
        "floor_sanity_summary": floor_sanity_summary,
        "floor_line_status": floor_line_status,
        "conclusion": " ".join(conclusion_parts),
        "next_actions": [
            "Use the Normandy pilot-pack matrix runner as the formal E1 entry point.",
            "Inspect cooldown scorecard rows before promoting any cooldown setting beyond the current baseline.",
            "Keep unit-regime tags in the payload layer until a dedicated per-trade slicing need appears.",
        ],
    }


def read_normandy_tachibana_pilot_pack_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_normandy_tachibana_pilot_pack_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
