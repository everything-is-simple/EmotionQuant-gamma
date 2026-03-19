from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.backtest.phase9_duration_percentile_validation import build_phase9_validation_windows
from src.config import Settings
from src.data.store import Store
from src.report.reporter import _load_trades, _pair_trades, generate_backtest_report
from src.run_metadata import build_artifact_name, build_run_id, finish_run, sanitize_label, start_run
from src.selector.gene import compute_gene_snapshots_for_dates

PHASE9E_DURATION_LIFESPAN_SCOPE = "phase9e_duration_lifespan_distribution"
PHASE9E_BASELINE_CONTROL = "PHASE9E_BASELINE_CONTROL"
QUARTILE_BAND_ORDER = (
    "FIRST_QUARTER",
    "SECOND_QUARTER",
    "THIRD_QUARTER",
    "FOURTH_QUARTER",
    "UNSCALED",
)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def _normalize_runtime_for_phase9(
    config: Settings,
    *,
    initial_cash: float | None = None,
) -> Settings:
    cfg = config.model_copy(deep=True)
    cfg.history_start = date(2020, 1, 1)
    cfg.pipeline_mode = "legacy"
    cfg.enable_dtt_mode = False
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.enable_gene_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = "fixed_notional"
    if float(cfg.fixed_notional_amount) <= 0:
        starting_cash = float(initial_cash if initial_cash is not None else cfg.backtest_initial_cash)
        cfg.fixed_notional_amount = starting_cash * float(cfg.max_position_pct)
    cfg.exit_control_mode = "full_exit_control"
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


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
    dates = pd.to_datetime(rows["date"], errors="coerce")
    return [item.date() for item in dates if not pd.isna(item)]


def _window_scope(window_label: str) -> str:
    return f"{PHASE9E_DURATION_LIFESPAN_SCOPE}_{window_label.strip().lower()}"


def _load_entry_context(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            t.trade_id AS entry_trade_id,
            t.order_id,
            COALESCE(o.signal_id, s.signal_id) AS signal_id,
            COALESCE(s.signal_date, o.execute_date) AS entry_signal_date,
            t.execute_date AS entry_execute_date,
            t.code,
            t.position_id,
            s.pattern,
            g.current_wave_direction AS entry_wave_direction,
            g.current_wave_age_trade_days AS entry_wave_age_trade_days,
            g.current_wave_duration_percentile AS entry_duration_percentile,
            g.current_wave_duration_band AS entry_duration_band,
            g.current_wave_age_band AS entry_age_band,
            g.current_wave_magnitude_percentile AS entry_magnitude_percentile,
            g.current_wave_magnitude_band AS entry_magnitude_band,
            g.current_wave_lifespan_joint_percentile AS entry_lifespan_joint_percentile,
            g.current_wave_lifespan_joint_band AS entry_lifespan_joint_band,
            g.current_wave_magnitude_remaining_prob AS entry_magnitude_remaining_prob,
            g.current_wave_duration_remaining_prob AS entry_duration_remaining_prob,
            g.current_wave_lifespan_average_remaining_prob AS entry_average_remaining_prob,
            g.current_wave_lifespan_average_aged_prob AS entry_average_aged_prob,
            g.current_wave_lifespan_remaining_vs_aged_odds AS entry_remaining_vs_aged_odds,
            g.current_wave_lifespan_aged_vs_remaining_odds AS entry_aged_vs_remaining_odds
        FROM l4_trades t
        LEFT JOIN l4_orders o
          ON o.order_id = t.order_id
        LEFT JOIN l3_signals s
          ON s.signal_id = o.signal_id
        LEFT JOIN l3_stock_gene g
          ON g.code = t.code
         AND g.calc_date = COALESCE(s.signal_date, o.execute_date)
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date, t.trade_id
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["entry_signal_date"] = pd.to_datetime(frame["entry_signal_date"], errors="coerce").dt.date
    frame["entry_execute_date"] = pd.to_datetime(frame["entry_execute_date"], errors="coerce").dt.date
    return frame


def _load_entry_signal_dates(store: Store, start: date, end: date) -> list[date]:
    frame = store.read_df(
        """
        SELECT DISTINCT COALESCE(s.signal_date, o.execute_date) AS signal_date
        FROM l4_trades t
        LEFT JOIN l4_orders o
          ON o.order_id = t.order_id
        LEFT JOIN l3_signals s
          ON s.signal_id = o.signal_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
          AND COALESCE(s.signal_date, o.execute_date) IS NOT NULL
        ORDER BY 1
        """,
        (start, end),
    )
    if frame.empty:
        return []
    dates = pd.to_datetime(frame["signal_date"], errors="coerce")
    return [item.date() for item in dates if not pd.isna(item)]


def _build_roundtrip_ledger(store: Store, start: date, end: date, entry_context: pd.DataFrame) -> pd.DataFrame:
    trades = _load_trades(store, start, end)
    if trades.empty or entry_context.empty:
        return pd.DataFrame()
    paired = _pair_trades(trades)
    if paired.empty:
        return pd.DataFrame()
    entry_lookup = entry_context.drop_duplicates(subset=["entry_trade_id"]).copy()
    out = paired.merge(entry_lookup, on="entry_trade_id", how="left", suffixes=("", "_entry"))
    if out.empty:
        return out
    out["entry_date"] = pd.to_datetime(out["entry_date"], errors="coerce").dt.date
    out["exit_date"] = pd.to_datetime(out["exit_date"], errors="coerce").dt.date
    out["holding_days"] = (
        pd.to_datetime(out["exit_date"], errors="coerce") - pd.to_datetime(out["entry_date"], errors="coerce")
    ).dt.days
    return out.sort_values(["exit_date", "entry_date", "code"]).reset_index(drop=True)


def _band_label(value: Any) -> str:
    token = str(value or "").strip().upper()
    return token if token else "UNSCALED"


def _band_count_rows(entries_df: pd.DataFrame, band_col: str) -> list[dict[str, object]]:
    normalized = entries_df.copy()
    if normalized.empty or band_col not in normalized.columns:
        return []
    normalized[band_col] = normalized[band_col].map(_band_label)
    grouped = normalized.groupby(band_col).size().to_dict()
    rows = [
        {"band_label": label, "entry_count": int(grouped.get(label, 0))}
        for label in QUARTILE_BAND_ORDER
        if label in grouped or label != "UNSCALED"
    ]
    if "UNSCALED" in grouped and all(row["band_label"] != "UNSCALED" for row in rows):
        rows.append({"band_label": "UNSCALED", "entry_count": int(grouped["UNSCALED"])})
    return rows


def _profit_factor(values: pd.Series) -> float | None:
    if values.empty:
        return None
    wins = values[values > 0]
    losses = values[values <= 0]
    if losses.empty:
        return None if wins.empty else float("inf")
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(abs(losses.mean()))
    if math.isclose(avg_loss, 0.0):
        return None
    return float(avg_win / avg_loss)


def _payoff_summary(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty:
        return {
            "paired_trade_count": 0,
            "win_rate": None,
            "avg_pnl_pct": None,
            "median_pnl_pct": None,
            "profit_factor": None,
            "avg_holding_days": None,
            "avg_average_aged_prob": None,
            "median_average_aged_prob": None,
            "avg_remaining_vs_aged_odds": None,
            "median_remaining_vs_aged_odds": None,
        }
    pnl = pd.to_numeric(frame["pnl_pct"], errors="coerce").dropna()
    aged = pd.to_numeric(frame.get("entry_average_aged_prob"), errors="coerce")
    odds = pd.to_numeric(frame.get("entry_remaining_vs_aged_odds"), errors="coerce")
    holding = pd.to_numeric(frame.get("holding_days"), errors="coerce")
    return {
        "paired_trade_count": int(len(frame)),
        "win_rate": float((pnl > 0).mean()) if not pnl.empty else None,
        "avg_pnl_pct": float(pnl.mean()) if not pnl.empty else None,
        "median_pnl_pct": float(pnl.median()) if not pnl.empty else None,
        "profit_factor": _profit_factor(pnl),
        "avg_holding_days": float(holding.mean()) if not holding.dropna().empty else None,
        "avg_average_aged_prob": float(aged.mean()) if not aged.dropna().empty else None,
        "median_average_aged_prob": float(aged.median()) if not aged.dropna().empty else None,
        "avg_remaining_vs_aged_odds": float(odds.mean()) if not odds.dropna().empty else None,
        "median_remaining_vs_aged_odds": float(odds.median()) if not odds.dropna().empty else None,
    }


def _band_payoff_rows(roundtrip_df: pd.DataFrame, band_col: str) -> list[dict[str, object]]:
    if roundtrip_df.empty or band_col not in roundtrip_df.columns:
        return []
    normalized = roundtrip_df.copy()
    normalized[band_col] = normalized[band_col].map(_band_label)
    grouped = {key: value.copy() for key, value in normalized.groupby(band_col)}
    labels = [label for label in QUARTILE_BAND_ORDER if label in grouped]
    extra = sorted(key for key in grouped if key not in labels)
    rows: list[dict[str, object]] = []
    for label in [*labels, *extra]:
        rows.append({"band_label": label, **_payoff_summary(grouped[label])})
    return rows


def _bucket_label(lower: float, upper: float) -> str:
    return f"{lower:.2f}_{upper:.2f}"


def _bucket_payoff_rows(
    roundtrip_df: pd.DataFrame,
    value_col: str,
    *,
    bucket_edges: list[float],
) -> list[dict[str, object]]:
    if roundtrip_df.empty or value_col not in roundtrip_df.columns:
        return []
    values = pd.to_numeric(roundtrip_df[value_col], errors="coerce")
    valid = roundtrip_df.loc[values.notna()].copy()
    if valid.empty:
        return []
    valid[value_col] = pd.to_numeric(valid[value_col], errors="coerce")
    rows: list[dict[str, object]] = []
    for idx in range(len(bucket_edges) - 1):
        lower = float(bucket_edges[idx])
        upper = float(bucket_edges[idx + 1])
        if idx == len(bucket_edges) - 2:
            part = valid[(valid[value_col] >= lower) & (valid[value_col] <= upper)].copy()
        else:
            part = valid[(valid[value_col] >= lower) & (valid[value_col] < upper)].copy()
        rows.append(
            {
                "bucket_label": _bucket_label(lower, upper),
                "bucket_start": lower,
                "bucket_end": upper,
                **_payoff_summary(part),
            }
        )
    return rows


def _spearman_corr(frame: pd.DataFrame, value_col: str, target_col: str) -> float | None:
    if frame.empty or value_col not in frame.columns or target_col not in frame.columns:
        return None
    pair = frame[[value_col, target_col]].copy()
    pair[value_col] = pd.to_numeric(pair[value_col], errors="coerce")
    pair[target_col] = pd.to_numeric(pair[target_col], errors="coerce")
    pair = pair.dropna()
    if len(pair) < 3:
        return None
    corr = pair[value_col].rank().corr(pair[target_col].rank())
    return None if corr is None or not math.isfinite(float(corr)) else float(corr)


def build_phase9_duration_lifespan_window_summary(
    *,
    window_label: str,
    window_start: date,
    window_end: date,
    backtest_metrics: dict[str, object],
    entry_df: pd.DataFrame,
    roundtrip_df: pd.DataFrame,
) -> dict[str, object]:
    return {
        "window_label": window_label,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "entry_count": int(len(entry_df)),
        "paired_trade_count": int(len(roundtrip_df)),
        "overall_payoff_summary": _payoff_summary(roundtrip_df),
        "official_backtest_metrics": {
            "trade_count": _safe_int(backtest_metrics.get("trade_count")),
            "win_rate": _safe_float(backtest_metrics.get("win_rate")),
            "expected_value": _safe_float(backtest_metrics.get("expected_value")),
            "profit_factor": _safe_float(backtest_metrics.get("profit_factor")),
            "max_drawdown": _safe_float(backtest_metrics.get("max_drawdown")),
            "filled_count": _safe_float(backtest_metrics.get("filled_count")),
            "participation_rate": _safe_float(backtest_metrics.get("participation_rate")),
        },
        "duration_quartile_counts": _band_count_rows(entry_df, "entry_duration_band"),
        "magnitude_quartile_counts": _band_count_rows(entry_df, "entry_magnitude_band"),
        "joint_quartile_counts": _band_count_rows(entry_df, "entry_lifespan_joint_band"),
        "duration_quartile_payoff": _band_payoff_rows(roundtrip_df, "entry_duration_band"),
        "magnitude_quartile_payoff": _band_payoff_rows(roundtrip_df, "entry_magnitude_band"),
        "joint_quartile_payoff": _band_payoff_rows(roundtrip_df, "entry_lifespan_joint_band"),
        "continuous_relationships": {
            "duration_percentile_vs_pnl_pct_spearman": _spearman_corr(
                roundtrip_df,
                "entry_duration_percentile",
                "pnl_pct",
            ),
            "magnitude_percentile_vs_pnl_pct_spearman": _spearman_corr(
                roundtrip_df,
                "entry_magnitude_percentile",
                "pnl_pct",
            ),
            "joint_percentile_vs_pnl_pct_spearman": _spearman_corr(
                roundtrip_df,
                "entry_lifespan_joint_percentile",
                "pnl_pct",
            ),
            "average_aged_prob_vs_pnl_pct_spearman": _spearman_corr(
                roundtrip_df,
                "entry_average_aged_prob",
                "pnl_pct",
            ),
            "joint_percentile_bucket_payoff": _bucket_payoff_rows(
                roundtrip_df,
                "entry_lifespan_joint_percentile",
                bucket_edges=[0.0, 25.0, 50.0, 75.0, 100.0],
            ),
            "average_aged_prob_bucket_payoff": _bucket_payoff_rows(
                roundtrip_df,
                "entry_average_aged_prob",
                bucket_edges=[0.0, 0.25, 0.50, 0.75, 1.0],
            ),
        },
    }


def build_phase9_duration_lifespan_digest(payload: dict[str, Any]) -> dict[str, Any]:
    windows = payload.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("payload.windows must be a non-empty list")
    full_window = next(
        (item for item in windows if str(item.get("window_label") or "") == "full_window"),
        None,
    )
    if not isinstance(full_window, dict):
        raise ValueError("Missing full_window summary")

    overall = full_window.get("overall_payoff_summary") or {}
    duration_rows = full_window.get("duration_quartile_payoff") or []
    joint_rows = full_window.get("joint_quartile_payoff") or []
    if not isinstance(overall, dict) or not isinstance(duration_rows, list) or not isinstance(joint_rows, list):
        raise ValueError("Invalid full_window shape")

    duration_by_band = {str(row.get("band_label") or ""): row for row in duration_rows if isinstance(row, dict)}
    joint_by_band = {str(row.get("band_label") or ""): row for row in joint_rows if isinstance(row, dict)}
    fourth_duration = duration_by_band.get("FOURTH_QUARTER") or {}
    fourth_joint = joint_by_band.get("FOURTH_QUARTER") or {}

    overall_avg = _safe_float(overall.get("avg_pnl_pct"))
    overall_win_rate = _safe_float(overall.get("win_rate"))
    fourth_avg = _safe_float(fourth_duration.get("avg_pnl_pct"))
    fourth_win_rate = _safe_float(fourth_duration.get("win_rate"))
    fourth_count = _safe_int(fourth_duration.get("paired_trade_count")) or 0
    fourth_aged = _safe_float(fourth_duration.get("avg_average_aged_prob"))
    joint_fourth_avg = _safe_float(fourth_joint.get("avg_pnl_pct"))
    joint_fourth_count = _safe_int(fourth_joint.get("paired_trade_count")) or 0

    support_runtime = (
        fourth_count >= 5
        and joint_fourth_count >= 5
        and overall_avg is not None
        and overall_win_rate is not None
        and fourth_avg is not None
        and fourth_win_rate is not None
        and joint_fourth_avg is not None
        and fourth_avg < overall_avg
        and fourth_win_rate < overall_win_rate
        and joint_fourth_avg < overall_avg
        and (fourth_aged is None or fourth_aged >= 0.65)
    )

    if support_runtime:
        decision = "duration_runtime_candidate_survives_quartile_surface"
        diagnosis = "fourth_quarter_and_joint_aged_buckets_underperform"
        phase9f_hint = "use_duration_band_fourth_quarter_only_if_duration_is_carried_forward"
        conclusion = (
            "The remediated quartile surface now shows that late-life entries cluster in the fourth quarter and "
            "underperform the full-window baseline, so duration can remain a narrow negative-guard candidate."
        )
    else:
        decision = "duration_should_return_to_sidecar_only_distribution_reading"
        diagnosis = "quartile_surface_is_mixed_or_under-sampled"
        phase9f_hint = "do_not_carry_duration_into_phase9f_until_stronger_quartile_evidence_exists"
        conclusion = (
            "The remediated quartile surface is still mixed or too thin in the late-life buckets, so duration should "
            "stay as a sidecar distribution reading rather than a truthful runtime guard for now."
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "decision": decision,
        "diagnosis": diagnosis,
        "phase9f_duration_operand_recommendation": phase9f_hint,
        "legacy_threshold_archive_status": "p65_and_p95_are_legacy_archive_only",
        "full_window_overall_avg_pnl_pct": overall_avg,
        "full_window_overall_win_rate": overall_win_rate,
        "full_window_fourth_quarter_avg_pnl_pct": fourth_avg,
        "full_window_fourth_quarter_win_rate": fourth_win_rate,
        "full_window_fourth_quarter_trade_count": fourth_count,
        "full_window_fourth_quarter_avg_aged_prob": fourth_aged,
        "full_window_joint_fourth_quarter_avg_pnl_pct": joint_fourth_avg,
        "full_window_joint_fourth_quarter_trade_count": joint_fourth_count,
        "conclusion": conclusion,
    }


def _window_metrics_from_result(result: Any) -> dict[str, object]:
    return {
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
        "environment_breakdown": dict(result.environment_breakdown),
    }


def run_phase9_duration_lifespan_distribution(
    *,
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, Any]:
    starting_cash = float(initial_cash if initial_cash is not None else config.backtest_initial_cash)
    source_db = Path(db_path).expanduser().resolve()
    db_file = prepare_working_db(source_db, working_db_path) if working_db_path is not None else source_db
    artifact_root_path = Path(artifact_root).expanduser().resolve() if artifact_root is not None else db_file.parent
    artifact_root_path.mkdir(parents=True, exist_ok=True)

    window_store = Store(db_file)
    try:
        windows = build_phase9_validation_windows(window_store, start=start, end=end)
    finally:
        window_store.close()
    if not windows:
        raise RuntimeError("No validation windows available for Phase 9E lifespan distribution.")

    cfg = _normalize_runtime_for_phase9(config, initial_cash=starting_cash)
    full_window = windows[0]
    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope=_window_scope(full_window.label),
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
        backtest_result = run_backtest(
            db_path=db_file,
            config=cfg,
            start=full_window.start,
            end=full_window.end,
            patterns=["bof"],
            initial_cash=starting_cash,
            run_id=run.run_id,
            signal_filter=None,
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

    store = Store(db_file)
    try:
        entry_signal_dates: list[date] = []
        if rebuild_l3:
            entry_signal_dates = _load_entry_signal_dates(store, full_window.start, full_window.end)
            if entry_signal_dates:
                compute_gene_snapshots_for_dates(store, entry_signal_dates)
        entry_context = _load_entry_context(store, full_window.start, full_window.end)
        roundtrip_ledger = _build_roundtrip_ledger(store, full_window.start, full_window.end, entry_context)
        window_summaries: list[dict[str, object]] = []
        trade_days_map = {
            window.label: len(_iter_trade_days(store, window.start, window.end))
            for window in windows
        }
        for window in windows:
            if window.label == "full_window":
                metrics = _window_metrics_from_result(backtest_result)
            else:
                metrics = generate_backtest_report(store, cfg, window.start, window.end, starting_cash)
            window_entry_df = entry_context.loc[
                (entry_context["entry_signal_date"] >= window.start) & (entry_context["entry_signal_date"] <= window.end)
            ].copy()
            window_roundtrip_df = roundtrip_ledger.loc[
                (roundtrip_ledger["entry_signal_date"] >= window.start)
                & (roundtrip_ledger["entry_signal_date"] <= window.end)
            ].copy()
            summary = build_phase9_duration_lifespan_window_summary(
                window_label=window.label,
                window_start=window.start,
                window_end=window.end,
                backtest_metrics=metrics,
                entry_df=window_entry_df,
                roundtrip_df=window_roundtrip_df,
            )
            summary["trade_days"] = int(trade_days_map.get(window.label) or 0)
            summary["run_id"] = run.run_id
            window_summaries.append(summary)

        payload = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "research_parent": "phase9_gene_mainline_integration_package",
            "research_question": (
                "If duration is reopened on the remediated book-aligned lifespan surface, does the quartile + average "
                "lifespan odds evidence still justify any truthful runtime follow-up?"
            ),
            "scope": PHASE9E_DURATION_LIFESPAN_SCOPE,
            "baseline_contract": (
                "legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only"
            ),
            "source_db": str(source_db),
            "working_db": str(db_file),
            "window_run_id": run.run_id,
            "entry_signal_dates": [item.isoformat() for item in entry_signal_dates],
            "start": start.isoformat(),
            "end": end.isoformat(),
            "windows": window_summaries,
            "final_snapshot": {
                "signal_date": end.isoformat(),
                "entry_count": int(
                    len(entry_context.loc[entry_context["entry_signal_date"] == end].copy())
                ),
                "duration_quartile_counts": _band_count_rows(
                    entry_context.loc[entry_context["entry_signal_date"] == end].copy(),
                    "entry_duration_band",
                ),
                "joint_quartile_counts": _band_count_rows(
                    entry_context.loc[entry_context["entry_signal_date"] == end].copy(),
                    "entry_lifespan_joint_band",
                ),
            },
            "legacy_archive": {
                "phase9b_duration_percentile_isolated_p95": "legacy_archive_only",
                "phase9b_duration_percentile_isolated_p65": "legacy_archive_only",
            },
        }
        payload["digest"] = build_phase9_duration_lifespan_digest(payload)
        return payload
    finally:
        store.close()


def build_phase9_duration_lifespan_variant() -> str:
    return sanitize_label("book_aligned_quartile_and_average_lifespan_odds")


def write_phase9_duration_lifespan_evidence(
    output_path: str | Path,
    payload: dict[str, Any],
) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def default_phase9_duration_lifespan_output_path(
    *,
    repo_root: str | Path,
    start: date,
    end: date,
) -> Path:
    run_id = build_run_id(
        scope=PHASE9E_DURATION_LIFESPAN_SCOPE,
        mode="legacy",
        variant=build_phase9_duration_lifespan_variant(),
        start=start,
        end=end,
    )
    return Path(repo_root).expanduser().resolve() / "docs" / "spec" / "v0.01-plus" / "evidence" / build_artifact_name(
        run_id,
        "phase9_duration_lifespan_distribution",
        "json",
    )
