from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.replay_variants import LEGACY_BASELINE_VARIANT
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import generate_backtest_report
from src.run_metadata import finish_run, start_run

PHASE6_INTEGRATED_VALIDATION_SCOPE = "phase6_integrated_validation"
RAW_LEGACY_BASELINE_CONTROL = "RAW_LEGACY_BASELINE_CONTROL"
PHASE6_UNIFIED_DEFAULT_CANDIDATE = "PHASE6_UNIFIED_DEFAULT_CANDIDATE"

GENE_BOUNDARY_TOKENS = (
    "l3_stock_gene",
    "l3_gene_mirror",
    "l3_gene_conditioning_eval",
    "l3_gene_validation_eval",
)


@dataclass(frozen=True)
class Phase6IntegratedScenario:
    label: str
    pipeline_mode: str
    enable_mss_gate: bool
    enable_irs_filter: bool
    position_sizing_mode: str
    fixed_notional_amount: float
    exit_control_mode: str
    notes: str


@dataclass(frozen=True)
class Phase6ValidationWindow:
    label: str
    start: date
    end: date


def _resolve_fixed_notional_amount(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> float:
    amount = float(config.fixed_notional_amount)
    if amount > 0:
        return amount
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    return starting_cash * float(config.max_position_pct)


def build_phase6_integrated_scenarios(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> list[Phase6IntegratedScenario]:
    fixed_notional_amount = _resolve_fixed_notional_amount(config, initial_cash=initial_cash)
    return [
        Phase6IntegratedScenario(
            label=RAW_LEGACY_BASELINE_CONTROL,
            pipeline_mode="legacy",
            enable_mss_gate=True,
            enable_irs_filter=True,
            position_sizing_mode="risk_budget",
            fixed_notional_amount=0.0,
            exit_control_mode="full_exit_control",
            notes=(
                "Diagnostic control only. Replays the raw legacy runtime path as currently implemented in replay "
                "variants, including legacy IRS and MSS runtime semantics."
            ),
        ),
        Phase6IntegratedScenario(
            label=PHASE6_UNIFIED_DEFAULT_CANDIDATE,
            pipeline_mode="legacy",
            enable_mss_gate=False,
            enable_irs_filter=False,
            position_sizing_mode="fixed_notional",
            fixed_notional_amount=float(fixed_notional_amount),
            exit_control_mode="full_exit_control",
            notes=(
                "Frozen Phase 6 candidate: legacy BOF entry backbone, retired IRS/MSS runtime, "
                "FIXED_NOTIONAL_CONTROL, FULL_EXIT_CONTROL, and Gene as shadow-only sidecar."
            ),
        ),
    ]


def _iter_trade_days(store: Store, start: date, end: date) -> list[date]:
    rows = store.read_df(
        """
        SELECT date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE
          AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if rows.empty:
        return []
    return [item.date() if isinstance(item, pd.Timestamp) else item for item in rows["date"].tolist()]


def build_phase6_validation_windows(
    store: Store,
    *,
    start: date,
    end: date,
) -> list[Phase6ValidationWindow]:
    trade_days = _iter_trade_days(store, start, end)
    if not trade_days:
        raise RuntimeError("No trade days available for Phase 6B validation window.")
    if len(trade_days) < 2:
        return [Phase6ValidationWindow(label="full_window", start=start, end=end)]

    midpoint = len(trade_days) // 2
    front_end = trade_days[max(midpoint - 1, 0)]
    back_start = trade_days[midpoint]
    windows = [Phase6ValidationWindow(label="full_window", start=start, end=end)]
    if front_end >= start:
        windows.append(Phase6ValidationWindow(label="front_half_window", start=start, end=front_end))
    if back_start <= end:
        windows.append(Phase6ValidationWindow(label="back_half_window", start=back_start, end=end))
    return windows


def _normalize_runtime_for_phase6(
    config: Settings,
    scenario: Phase6IntegratedScenario,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.pipeline_mode = scenario.pipeline_mode
    cfg.enable_dtt_mode = False
    cfg.dtt_variant = LEGACY_BASELINE_VARIANT
    cfg.enable_mss_gate = scenario.enable_mss_gate
    cfg.enable_irs_filter = scenario.enable_irs_filter
    cfg.enable_gene_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = scenario.position_sizing_mode
    cfg.fixed_notional_amount = float(scenario.fixed_notional_amount)
    cfg.exit_control_mode = scenario.exit_control_mode
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def _query_rows(store: Store, query: str, params: tuple[object, ...]) -> pd.DataFrame:
    return store.read_df(query, params)


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


def _load_trace_counts(store: Store, run_id: str) -> dict[str, int]:
    return {
        "selector_candidate_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM selector_candidate_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "pas_trigger_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM pas_trigger_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "broker_lifecycle_trace_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM broker_order_lifecycle_trace_exp WHERE run_id = ?",
                (run_id,),
            )
            or 0
        ),
        "mss_overlay_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM mss_risk_overlay_trace_exp WHERE run_id = ?", (run_id,)) or 0
        ),
        "rank_trace_count": int(
            store.read_scalar("SELECT COUNT(*) FROM l3_signal_rank_exp WHERE run_id = ?", (run_id,)) or 0
        ),
    }


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
            "buy_reject_rate": 0.0,
        }
    buys = orders[orders["action"] == "BUY"].copy()
    if buys.empty:
        return {
            "buy_order_count": 0,
            "buy_filled_count": 0,
            "buy_reject_count": 0,
            "buy_reject_rate": 0.0,
        }
    buy_order_count = int(len(buys))
    buy_filled_count = int((buys["status"] == "FILLED").sum())
    buy_reject_count = int((buys["status"] == "REJECTED").sum())
    return {
        "buy_order_count": buy_order_count,
        "buy_filled_count": buy_filled_count,
        "buy_reject_count": buy_reject_count,
        "buy_reject_rate": 0.0 if buy_order_count <= 0 else float(buy_reject_count / buy_order_count),
    }


def _buy_trade_metrics(buys: pd.DataFrame, initial_cash: float) -> dict[str, float | int | None]:
    if buys.empty:
        return {
            "buy_trade_count": 0,
            "avg_entry_quantity": None,
            "avg_entry_notional": None,
            "max_entry_notional_pct_initial_cash": None,
        }
    metrics = buys.copy()
    metrics["entry_notional"] = pd.to_numeric(metrics["price"], errors="coerce").fillna(0.0) * pd.to_numeric(
        metrics["quantity"], errors="coerce"
    ).fillna(0)
    max_entry_notional = float(metrics["entry_notional"].max())
    return {
        "buy_trade_count": int(len(metrics)),
        "avg_entry_quantity": float(pd.to_numeric(metrics["quantity"], errors="coerce").mean()),
        "avg_entry_notional": float(metrics["entry_notional"].mean()),
        "max_entry_notional_pct_initial_cash": 0.0
        if initial_cash <= 0
        else float(max_entry_notional / initial_cash),
    }


def _snapshot_signal_counts(store: Store, start: date, end: date) -> dict[str, int]:
    return {
        "signals_count": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        )
    }


def _hash_buy_trade_set(buys: pd.DataFrame) -> str:
    if buys.empty:
        return sha256(b"[]").hexdigest()
    payload = buys.loc[:, ["execute_date", "code", "quantity", "price"]].copy()
    payload["execute_date"] = payload["execute_date"].astype(str)
    body = json.dumps(payload.to_dict(orient="records"), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return sha256(body).hexdigest()


def _build_window_result_payload(
    *,
    scenario: Phase6IntegratedScenario,
    window: Phase6ValidationWindow,
    metrics: dict[str, object],
    trade_days: int,
    store: Store,
    initial_cash: float,
    run_id: str,
) -> dict[str, object]:
    orders = _load_orders(store, window.start, window.end)
    buys = _load_buy_trades(store, window.start, window.end)
    return {
        "scenario_label": scenario.label,
        "window_label": window.label,
        "window_start": window.start.isoformat(),
        "window_end": window.end.isoformat(),
        "notes": scenario.notes,
        "run_id": run_id,
        "pipeline_mode": scenario.pipeline_mode,
        "dtt_variant": LEGACY_BASELINE_VARIANT,
        "enable_mss_gate": scenario.enable_mss_gate,
        "enable_irs_filter": scenario.enable_irs_filter,
        "position_sizing_mode": scenario.position_sizing_mode,
        "fixed_notional_amount": float(scenario.fixed_notional_amount),
        "exit_control_mode": scenario.exit_control_mode,
        "trade_days": int(trade_days),
        "trade_count": int(float(metrics["trade_count"])),
        "win_rate": float(metrics["win_rate"]),
        "avg_win": float(metrics["avg_win"]),
        "avg_loss": float(metrics["avg_loss"]),
        "expected_value": float(metrics["expected_value"]),
        "profit_factor": float(metrics["profit_factor"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "reject_rate": float(metrics["reject_rate"]),
        "missing_rate": float(metrics["missing_rate"]),
        "exposure_rate": float(metrics["exposure_rate"]),
        "opportunity_count": float(metrics["opportunity_count"]),
        "filled_count": float(metrics["filled_count"]),
        "skip_cash_count": float(metrics["skip_cash_count"]),
        "skip_maxpos_count": float(metrics["skip_maxpos_count"]),
        "participation_rate": float(metrics["participation_rate"]),
        "environment_breakdown": dict(metrics["environment_breakdown"]),
        "buy_trade_signature": _hash_buy_trade_set(buys),
        "trace_counts": _load_trace_counts(store, run_id),
        "failure_reason_breakdown": _failure_reason_breakdown(orders),
        **_snapshot_signal_counts(store, window.start, window.end),
        **_buy_order_diagnostics(orders),
        **_buy_trade_metrics(buys, initial_cash),
    }


def _scenario_scope(scenario_label: str, window_label: str) -> str:
    return f"{PHASE6_INTEGRATED_VALIDATION_SCOPE}_{scenario_label.strip().lower()}_{window_label.strip().lower()}"


def _find_line_hits(path: Path, token: str) -> list[int]:
    hits: list[int] = []
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="ignore")
    for line_no, line in enumerate(content.splitlines(), start=1):
        if token in line:
            hits.append(line_no)
    return hits


def audit_gene_runtime_boundary(repo_root: str | Path) -> dict[str, object]:
    root = Path(repo_root).expanduser().resolve()
    src_root = root / "src"
    allowed_files = {
        src_root / "config.py",
        src_root / "data" / "builder.py",
        src_root / "data" / "store.py",
        src_root / "selector" / "gene.py",
    }
    unexpected_hits: list[dict[str, object]] = []
    enable_gene_filter_runtime_hits: list[dict[str, object]] = []

    for path in sorted(src_root.rglob("*.py")):
        if path in allowed_files:
            continue
        for token in GENE_BOUNDARY_TOKENS:
            line_hits = _find_line_hits(path, token)
            if line_hits:
                unexpected_hits.append(
                    {
                        "path": str(path),
                        "token": token,
                        "lines": line_hits,
                    }
                )
        if path.name != "config.py":
            line_hits = _find_line_hits(path, "enable_gene_filter")
            if line_hits:
                enable_gene_filter_runtime_hits.append(
                    {
                        "path": str(path),
                        "lines": line_hits,
                    }
                )

    return {
        "audit_scope": "src runtime boundary scan",
        "audit_passed": not unexpected_hits and not enable_gene_filter_runtime_hits,
        "unexpected_source_hits": unexpected_hits,
        "enable_gene_filter_runtime_hits": enable_gene_filter_runtime_hits,
    }


def snapshot_gene_sidecar(store: Store, *, start: date, end: date) -> dict[str, object]:
    latest_stock_gene_date = store.get_max_date("l3_stock_gene", date_col="calc_date")
    return {
        "stock_gene_rows": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_stock_gene WHERE calc_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
        "stock_gene_distinct_dates": int(
            store.read_scalar(
                "SELECT COUNT(DISTINCT calc_date) FROM l3_stock_gene WHERE calc_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
        "gene_validation_rows": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_gene_validation_eval WHERE calc_date BETWEEN ? AND ?",
                (start, end),
            )
            or 0
        ),
        "gene_mirror_rows": int(
            store.read_scalar("SELECT COUNT(*) FROM l3_gene_mirror WHERE calc_date = ?", (end,)) or 0
        ),
        "gene_conditioning_rows": int(
            store.read_scalar(
                "SELECT COUNT(*) FROM l3_gene_conditioning_eval WHERE calc_date = ?",
                (end,),
            )
            or 0
        ),
        "latest_stock_gene_date": None if latest_stock_gene_date is None else latest_stock_gene_date.isoformat(),
    }


def _find_result(
    results: list[dict[str, object]],
    *,
    scenario_label: str,
    window_label: str,
) -> dict[str, object]:
    for item in results:
        if (
            str(item.get("scenario_label") or "") == scenario_label
            and str(item.get("window_label") or "") == window_label
        ):
            return item
    raise ValueError(f"Missing result for scenario={scenario_label}, window={window_label}")


def build_phase6_integrated_validation_digest(payload: dict[str, object]) -> dict[str, object]:
    matrix_status = str(payload.get("matrix_status") or "completed")
    if matrix_status != "completed":
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "matrix_status": matrix_status,
            "decision": "rerun_phase6_integrated_validation",
            "conclusion": "Phase 6B integrated validation is incomplete; no promotion judgment is allowed.",
        }

    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("payload.results must be a list")

    raw_legacy = _find_result(
        results,
        scenario_label=RAW_LEGACY_BASELINE_CONTROL,
        window_label="full_window",
    )
    candidate = _find_result(
        results,
        scenario_label=PHASE6_UNIFIED_DEFAULT_CANDIDATE,
        window_label="full_window",
    )
    front_candidate = _find_result(
        results,
        scenario_label=PHASE6_UNIFIED_DEFAULT_CANDIDATE,
        window_label="front_half_window",
    )
    back_candidate = _find_result(
        results,
        scenario_label=PHASE6_UNIFIED_DEFAULT_CANDIDATE,
        window_label="back_half_window",
    )

    gene_sidecar = payload.get("gene_sidecar")
    if not isinstance(gene_sidecar, dict):
        raise ValueError("payload.gene_sidecar must be a dict")
    boundary_audit = payload.get("boundary_audit")
    if not isinstance(boundary_audit, dict):
        raise ValueError("payload.boundary_audit must be a dict")

    trade_count_ratio = _safe_ratio(candidate.get("trade_count"), raw_legacy.get("trade_count"))
    filled_count_ratio = _safe_ratio(candidate.get("buy_filled_count"), raw_legacy.get("buy_filled_count"))
    exposure_rate_delta = float(candidate.get("exposure_rate") or 0.0) - float(raw_legacy.get("exposure_rate") or 0.0)
    expected_value_delta = float(candidate.get("expected_value") or 0.0) - float(raw_legacy.get("expected_value") or 0.0)
    profit_factor_delta = float(candidate.get("profit_factor") or 0.0) - float(raw_legacy.get("profit_factor") or 0.0)
    max_drawdown_delta = float(candidate.get("max_drawdown") or 0.0) - float(raw_legacy.get("max_drawdown") or 0.0)

    trace_complete = all(
        int(entry.get("trace_counts", {}).get("selector_candidate_trace_count", 0)) > 0
        and int(entry.get("trace_counts", {}).get("pas_trigger_trace_count", 0)) > 0
        and int(entry.get("trace_counts", {}).get("broker_lifecycle_trace_count", 0)) > 0
        for entry in (candidate, front_candidate, back_candidate)
    )
    window_slice_complete = all(int(entry.get("trade_days") or 0) > 0 for entry in (front_candidate, back_candidate))
    gene_sidecar_ready = (
        int(gene_sidecar.get("stock_gene_rows", 0)) > 0
        and int(gene_sidecar.get("gene_validation_rows", 0)) > 0
        and int(gene_sidecar.get("gene_mirror_rows", 0)) > 0
        and int(gene_sidecar.get("gene_conditioning_rows", 0)) > 0
    )
    retired_runtime_boundary_held = not bool(candidate.get("enable_irs_filter")) and not bool(
        candidate.get("enable_mss_gate")
    )
    boundary_audit_passed = bool(boundary_audit.get("audit_passed"))
    candidate_runtime_stable = (
        int(candidate.get("trade_count") or 0) > 0
        and int(candidate.get("buy_filled_count") or 0) > 0
        and float(candidate.get("reject_rate") or 0.0) < 0.99
        and float(candidate.get("max_drawdown") or 0.0) <= float(raw_legacy.get("max_drawdown") or 0.0) + 0.20
    )

    if not boundary_audit_passed or not gene_sidecar_ready or not retired_runtime_boundary_held:
        decision = "no_go"
        diagnosis = "boundary_violation"
        conclusion = (
            "Phase 6 frozen boundary is not yet credible: either Gene sidecar is incomplete, "
            "runtime retirement boundaries leaked, or source-level boundary audit failed."
        )
    elif not trace_complete or not window_slice_complete or not candidate_runtime_stable:
        decision = "hold"
        diagnosis = "integration_not_stable_enough"
        conclusion = (
            "Phase 6 candidate is formalized, but integrated replay still lacks stable runtime/trace behavior "
            "across the full window and split windows."
        )
    else:
        decision = "go_to_phase_6c"
        diagnosis = "candidate_boundary_and_runtime_validated"
        conclusion = (
            "Phase 6 candidate has a clear delta versus raw legacy runtime, keeps the shadow-only Gene boundary, "
            "and holds integrated trace/runtime stability across the long window and split windows."
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": matrix_status,
        "diagnosis": diagnosis,
        "decision": decision,
        "full_window_comparison": {
            "trade_count_ratio_candidate_vs_raw_legacy": trade_count_ratio,
            "buy_filled_count_ratio_candidate_vs_raw_legacy": filled_count_ratio,
            "exposure_rate_delta_candidate_minus_raw_legacy": exposure_rate_delta,
            "expected_value_delta_candidate_minus_raw_legacy": expected_value_delta,
            "profit_factor_delta_candidate_minus_raw_legacy": profit_factor_delta,
            "max_drawdown_delta_candidate_minus_raw_legacy": max_drawdown_delta,
        },
        "candidate_window_summary": {
            "front_half_trade_count": front_candidate.get("trade_count"),
            "front_half_expected_value": front_candidate.get("expected_value"),
            "back_half_trade_count": back_candidate.get("trade_count"),
            "back_half_expected_value": back_candidate.get("expected_value"),
        },
        "gate_checks": {
            "trace_complete": trace_complete,
            "window_slice_complete": window_slice_complete,
            "gene_sidecar_ready": gene_sidecar_ready,
            "retired_runtime_boundary_held": retired_runtime_boundary_held,
            "boundary_audit_passed": boundary_audit_passed,
            "candidate_runtime_stable": candidate_runtime_stable,
        },
        "conclusion": conclusion,
        "next_actions": [
            "Write the formal Phase 6B record and update development status.",
            "Activate Phase 6C only if the Phase 6B gate remains GO_TO_PHASE_6C.",
            "Keep Gene as shadow-only sidecar; do not translate it into a runtime hard gate.",
        ],
    }


def run_phase6_integrated_validation(
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

    window_store = Store(db_file)
    try:
        windows = build_phase6_validation_windows(window_store, start=start, end=end)
        gene_sidecar = snapshot_gene_sidecar(window_store, start=start, end=end)
    finally:
        window_store.close()

    boundary_audit = audit_gene_runtime_boundary(Path(__file__).resolve().parents[2])
    scenarios = build_phase6_integrated_scenarios(config, initial_cash=starting_cash)
    results: list[dict[str, object]] = []

    for scenario in scenarios:
        cfg = _normalize_runtime_for_phase6(config, scenario)
        full_window = windows[0]
        meta_store = Store(db_file)
        run = start_run(
            store=meta_store,
            scope=_scenario_scope(scenario.label, full_window.label),
            modules=["backtest", "selector", "strategy", "broker", "report"],
            config=cfg,
            runtime_env="script",
            artifact_root=str(artifact_root_path),
            start=full_window.start,
            end=full_window.end,
        )
        meta_store.close()

        clear_store = Store(db_file)
        try:
            clear_runtime_tables(clear_store, run_id=run.run_id)
        finally:
            clear_store.close()

        try:
            run_backtest(
                db_path=db_file,
                config=cfg,
                start=full_window.start,
                end=full_window.end,
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
            for window in windows:
                metrics = generate_backtest_report(
                    snap_store,
                    cfg,
                    window.start,
                    window.end,
                    starting_cash,
                )
                results.append(
                    _build_window_result_payload(
                        scenario=scenario,
                        window=window,
                        metrics=metrics,
                        trade_days=len(_iter_trade_days(snap_store, window.start, window.end)),
                        store=snap_store,
                        initial_cash=starting_cash,
                        run_id=run.run_id,
                    )
                )
        finally:
            snap_store.close()

    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "matrix_status": "completed",
        "research_parent": "phase6_unified_default_system_migration_package",
        "research_question": (
            "Does the frozen Phase 6 unified default candidate materially clarify the operating system boundary "
            "without breaking long-window runtime stability, trace completeness, or the Gene shadow-only contract?"
        ),
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "initial_cash": starting_cash,
        "windows": [asdict(window) for window in windows],
        "scenarios": [asdict(scenario) for scenario in scenarios],
        "gene_sidecar": gene_sidecar,
        "boundary_audit": boundary_audit,
        "results": results,
    }
    payload["digest"] = build_phase6_integrated_validation_digest(payload)
    return payload


def read_phase6_integrated_validation_payload(path: str | Path) -> dict[str, object]:
    payload_path = Path(path).expanduser().resolve()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def write_phase6_integrated_validation_evidence(output_path: str | Path, payload: dict[str, object]) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
