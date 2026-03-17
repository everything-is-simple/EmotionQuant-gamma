from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings, get_settings
from src.data.builder import build_layers
from src.data.fetcher import bootstrap_l1_from_raw_duckdb
from src.data.store import Store
from src.report.reporter import _load_orders, _load_trades, _pair_trades
from src.run_metadata import finish_run, start_run
from src.strategy.ranker import MSS_SIZE_ONLY_VARIANT, apply_dtt_variant_runtime


WINDOW_ENCODING = "utf-8-sig"


@dataclass(frozen=True)
class YearWindow:
    year: int
    start: date
    end: date
    note: str


@dataclass(frozen=True)
class ScenarioSpec:
    slug: str
    title: str
    notes: str
    config_kind: str


class GeneContextSignalFilter:
    def __init__(self) -> None:
        self.total_signal_count = 0
        self.allowed_signal_count = 0
        self.blocked_signal_count = 0
        self.blocked_rows: list[dict[str, object]] = []

    def __call__(self, signals, trade_day: date, filled_trades, broker, store: Store):
        self.total_signal_count += len(signals)
        if not signals:
            return []

        codes = sorted({str(signal.code) for signal in signals})
        context = _load_signal_context_batch(store, trade_day, codes)
        context_by_code = {str(row["code"]): row for row in context.to_dict(orient="records")}

        kept = []
        for signal in signals:
            row = context_by_code.get(str(signal.code), {})
            reasons = _gene_block_reasons(row)
            if reasons:
                self.blocked_signal_count += 1
                self.blocked_rows.append(
                    {
                        "signal_date": trade_day.isoformat(),
                        "code": str(signal.code),
                        "pattern": str(signal.pattern),
                        "industry": row.get("industry"),
                        "block_reasons": ";".join(reasons),
                        "current_wave_direction": row.get("current_wave_direction"),
                        "current_wave_age_band": row.get("current_wave_age_band"),
                        "current_wave_duration_percentile": row.get("current_wave_duration_percentile"),
                        "current_wave_magnitude_band": row.get("current_wave_magnitude_band"),
                        "latest_confirmed_turn_type": row.get("latest_confirmed_turn_type"),
                        "latest_two_b_confirm_type": row.get("latest_two_b_confirm_type"),
                        "gene_score": row.get("gene_score"),
                        "market_signal": row.get("market_signal"),
                        "market_score": row.get("market_score"),
                        "industry_rank": row.get("industry_rank"),
                        "industry_score": row.get("industry_score"),
                    }
                )
                continue
            kept.append(signal)

        self.allowed_signal_count += len(kept)
        return kept

    def build_metrics(self) -> dict[str, object]:
        blocked_share = _safe_ratio(self.blocked_signal_count, self.total_signal_count)
        return {
            "gene_filter_total_signal_count": int(self.total_signal_count),
            "gene_filter_allowed_signal_count": int(self.allowed_signal_count),
            "gene_filter_blocked_signal_count": int(self.blocked_signal_count),
            "gene_filter_blocked_signal_share": float(blocked_share or 0.0),
            "gene_filter_rule": (
                "block when current_wave_age_band=EXTREME or current_wave_direction=UP "
                "or latest_two_b_confirm_type=2B_TOP"
            ),
        }


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    denom = float(denominator)
    if math.isclose(denom, 0.0):
        return None
    return float(float(numerator) / denom)


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _format_num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.{digits}f}"


def _format_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.3f}"


def _resolve_fixed_notional_amount(config: Settings, initial_cash: float) -> float:
    amount = float(config.fixed_notional_amount)
    if amount > 0:
        return amount
    return float(initial_cash * float(config.max_position_pct))


def _build_year_windows(
    *,
    start_year: int,
    end_year: int,
    available_start: date,
    available_end: date,
) -> list[YearWindow]:
    windows: list[YearWindow] = []
    for year in range(start_year, end_year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        start = max(year_start, available_start)
        end = min(year_end, available_end)
        if start > end:
            continue
        if start == year_start and end == year_end:
            note = "Full calendar-year backtest window."
        elif start == year_start:
            note = f"Partial year: data currently ends at {end.isoformat()}."
        elif end == year_end:
            note = f"Partial year: data currently starts at {start.isoformat()}."
        else:
            note = f"Partial year: data covers {start.isoformat()} to {end.isoformat()}."
        windows.append(YearWindow(year=year, start=start, end=end, note=note))
    return windows


def _detect_available_end(raw_db: Path) -> date:
    store = Store(raw_db)
    try:
        value = store.read_scalar("SELECT MAX(STRPTIME(trade_date, '%Y%m%d')::DATE) FROM raw_daily")
    finally:
        store.close()
    if value is None:
        raise RuntimeError("raw_daily has no coverage in raw DuckDB.")
    if isinstance(value, pd.Timestamp):
        return value.date()
    return value


def _build_long_window_execution_db(
    *,
    exec_source_db: Path,
    raw_source_db: Path,
    working_db_path: Path,
    start: date,
    end: date,
    initial_cash: float,
) -> Path:
    db_file = prepare_working_db(exec_source_db, working_db_path)
    cfg = get_settings().model_copy(deep=True)
    cfg.history_start = start
    cfg.backtest_initial_cash = initial_cash

    store = Store(db_file)
    try:
        print(f"[build] bootstrap L1 from raw db: {start} -> {end}")
        bootstrap_l1_from_raw_duckdb(
            store=store,
            source_db=raw_source_db,
            start=start,
            end=end,
            refresh_stock_info_only=False,
        )
        print("[build] build L2")
        build_layers(store, cfg, layers=["l2"], start=start, end=end, force=True)
        print("[build] build L3")
        build_layers(store, cfg, layers=["l3"], start=start, end=end, force=True)
    finally:
        store.close()
    return db_file


def _reference_mainline_config(base_cfg: Settings, initial_cash: float) -> Settings:
    cfg = base_cfg.model_copy(deep=True)
    cfg.history_start = date(2020, 1, 1)
    cfg.pipeline_mode = "legacy"
    cfg.enable_dtt_mode = False
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.enable_gene_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = "fixed_notional"
    cfg.fixed_notional_amount = _resolve_fixed_notional_amount(cfg, initial_cash)
    cfg.exit_control_mode = "full_exit_control"
    cfg.mss_max_positions_mode = "hard_cap"
    cfg.mss_max_positions_buffer_slots = 0
    return cfg


def _combo_fixed_notional_config(base_cfg: Settings, initial_cash: float) -> Settings:
    cfg = base_cfg.model_copy(deep=True)
    cfg.history_start = date(2020, 1, 1)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    cfg.enable_gene_filter = False
    cfg.pas_patterns = "bof"
    cfg.position_sizing_mode = "fixed_notional"
    cfg.fixed_notional_amount = _resolve_fixed_notional_amount(cfg, initial_cash)
    cfg.exit_control_mode = "naive_trail_scale_out_50_50_control"
    cfg.partial_exit_scale_out_ratio = 0.25
    cfg = apply_dtt_variant_runtime(cfg, MSS_SIZE_ONLY_VARIANT)
    return cfg


def _combo_williams_config(base_cfg: Settings, initial_cash: float) -> Settings:
    cfg = _combo_fixed_notional_config(base_cfg, initial_cash)
    cfg.position_sizing_mode = "williams_fixed_risk"
    cfg.williams_risk_per_trade_pct = 0.007
    cfg.williams_loss_reference_pct = 0.20
    return cfg


def _build_scenarios() -> list[ScenarioSpec]:
    return [
        ScenarioSpec(
            slug="01-reference-frozen-mainline",
            title="Reference Frozen Mainline",
            notes=(
                "Current frozen mainline reference. BOF only, fixed notional, full exit, "
                "no runtime IRS, no runtime MSS, no Gene hard gate."
            ),
            config_kind="reference_mainline",
        ),
        ScenarioSpec(
            slug="02-dtt-gene-fixed-notional-25_75",
            title="Experimental DTT + Gene + Fixed Notional + 25/75",
            notes=(
                "Experimental combo. BOF only, DTT ranking with IRS plus MSS size-only overlay, "
                "Gene negative filter, fixed notional sizing, 25/75 trailing scale-out."
            ),
            config_kind="combo_fixed_notional",
        ),
        ScenarioSpec(
            slug="03-dtt-gene-williams-25_75",
            title="Experimental DTT + Gene + Williams + 25/75",
            notes=(
                "Experimental combo. BOF only, DTT ranking with IRS plus MSS size-only overlay, "
                "Gene negative filter, Williams fixed-risk sizing, 25/75 trailing scale-out."
            ),
            config_kind="combo_williams",
        ),
    ]


def _make_config(base_cfg: Settings, scenario: ScenarioSpec, initial_cash: float) -> Settings:
    if scenario.config_kind == "reference_mainline":
        return _reference_mainline_config(base_cfg, initial_cash)
    if scenario.config_kind == "combo_fixed_notional":
        return _combo_fixed_notional_config(base_cfg, initial_cash)
    if scenario.config_kind == "combo_williams":
        return _combo_williams_config(base_cfg, initial_cash)
    raise ValueError(f"Unsupported scenario kind: {scenario.config_kind}")


def _maybe_make_signal_filter(scenario: ScenarioSpec):
    if scenario.config_kind == "reference_mainline":
        return None
    return GeneContextSignalFilter()


def _query_df(store: Store, query: str, params: tuple[object, ...] = ()) -> pd.DataFrame:
    return store.read_df(query, params)


def _load_signal_context_batch(store: Store, signal_date: date, codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame()
    placeholders = ", ".join(["?"] * len(codes))
    params: tuple[object, ...] = tuple(codes) + (signal_date, signal_date, signal_date)
    return store.read_df(
        f"""
        WITH base AS (
            SELECT
                l2.code,
                COALESCE(
                    (
                        SELECT info.industry
                        FROM l1_stock_info info
                        WHERE info.ts_code = l2.code
                          AND info.effective_from <= l2.date
                        ORDER BY info.effective_from DESC
                        LIMIT 1
                    ),
                    '未知'
                ) AS industry,
                g.current_wave_direction,
                g.current_wave_age_band,
                g.current_wave_duration_percentile,
                g.current_wave_magnitude_band,
                g.current_wave_magnitude_percentile,
                g.latest_confirmed_turn_type,
                g.latest_two_b_confirm_type,
                g.gene_score
            FROM l2_stock_adj_daily l2
            LEFT JOIN l3_stock_gene g
              ON g.code = l2.code
             AND g.calc_date = l2.date
            WHERE l2.code IN ({placeholders})
              AND l2.date = ?
        )
        SELECT
            b.*,
            m.signal AS market_signal,
            m.score AS market_score,
            i.rank AS industry_rank,
            i.score AS industry_score
        FROM base b
        LEFT JOIN l3_mss_daily m
          ON m.date = ?
        LEFT JOIN l3_irs_daily i
          ON i.date = ?
         AND i.industry = b.industry
        """,
        params,
    )


def _gene_block_reasons(row: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if str(row.get("current_wave_age_band") or "").upper() == "EXTREME":
        reasons.append("GENE_AGE_EXTREME")
    if str(row.get("current_wave_direction") or "").upper() == "UP":
        reasons.append("GENE_WAVE_UP")
    if str(row.get("latest_two_b_confirm_type") or "").upper() == "2B_TOP":
        reasons.append("GENE_2B_TOP")
    return reasons


def _load_run_frames(store: Store, run_id: str, start: date, end: date) -> dict[str, pd.DataFrame]:
    trades = _load_trades(store, start, end)
    orders = _query_df(
        store,
        """
        SELECT
            order_id,
            signal_id,
            code,
            action,
            pattern,
            quantity,
            execute_date,
            status,
            reject_reason,
            position_id,
            is_partial_exit
        FROM l4_orders
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date, order_id
        """,
        (start, end),
    )
    signals = _query_df(
        store,
        """
        SELECT signal_id, code, signal_date, action, strength, pattern, reason_code
        FROM l3_signals
        WHERE signal_date BETWEEN ? AND ?
        ORDER BY signal_date, signal_id
        """,
        (start, end),
    )
    rank_exp = _query_df(
        store,
        """
        SELECT run_id, signal_id, signal_date, code, industry, variant, pattern_strength, irs_score,
               mss_score, final_score, final_rank, selected
        FROM l3_signal_rank_exp
        WHERE run_id = ?
        ORDER BY signal_date, final_rank, signal_id
        """,
        (run_id,),
    )
    selector_trace = _query_df(
        store,
        """
        SELECT run_id, signal_date, code, industry, preselect_score, final_score AS selector_final_score,
               candidate_rank, candidate_top_n, liquidity_tag, selected
        FROM selector_candidate_trace_exp
        WHERE run_id = ?
        ORDER BY signal_date, candidate_rank, code
        """,
        (run_id,),
    )
    pas_trace = _query_df(
        store,
        """
        SELECT run_id, signal_date, code, detector, signal_id, pattern, candidate_rank,
               selected_pattern, detect_reason, reason_code, strength, pattern_strength,
               pattern_quality_score, quality_status, entry_ref, stop_ref, target_ref,
               risk_reward_ref, volume_ratio, trace_payload_json, pattern_context_json
        FROM pas_trigger_trace_exp
        WHERE run_id = ?
          AND signal_id IS NOT NULL
        ORDER BY signal_date, code, detector
        """,
        (run_id,),
    )
    stock_gene = _query_df(
        store,
        """
        SELECT code, calc_date AS signal_date, current_wave_direction, current_wave_age_trade_days,
               current_wave_age_band, current_wave_duration_percentile,
               current_wave_magnitude_percentile, current_wave_magnitude_band,
               latest_confirmed_turn_type, latest_two_b_confirm_type, gene_score
        FROM l3_stock_gene
        WHERE calc_date BETWEEN ? AND ?
        """,
        (start, end),
    )
    mss = _query_df(
        store,
        """
        SELECT date AS signal_date, score AS market_score, signal AS market_signal
        FROM l3_mss_daily
        WHERE date BETWEEN ? AND ?
        """,
        (start, end),
    )
    irs = _query_df(
        store,
        """
        SELECT date AS signal_date, industry, score AS industry_score, rank AS industry_rank
        FROM l3_irs_daily
        WHERE date BETWEEN ? AND ?
        """,
        (start, end),
    )
    l2_snapshot = _query_df(
        store,
        """
        SELECT code, date AS signal_date, amount, volume_ratio, pct_chg, adj_close
        FROM l2_stock_adj_daily
        WHERE date BETWEEN ? AND ?
        """,
        (start, end),
    )
    return {
        "trades": trades,
        "orders": orders,
        "signals": signals,
        "rank_exp": rank_exp,
        "selector_trace": selector_trace,
        "pas_trace": pas_trace,
        "stock_gene": stock_gene,
        "mss": mss,
        "irs": irs,
        "l2_snapshot": l2_snapshot,
    }


def _build_signal_context_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    signals = frames["signals"].copy()
    if signals.empty:
        return signals

    out = signals.merge(
        frames["rank_exp"],
        on=["signal_id", "signal_date", "code"],
        how="left",
        suffixes=("", "_rank"),
    )
    out = out.merge(
        frames["selector_trace"][["signal_date", "code", "preselect_score", "candidate_rank", "liquidity_tag"]],
        on=["signal_date", "code"],
        how="left",
    )
    selected_pas = frames["pas_trace"].copy()
    if not selected_pas.empty:
        selected_pas = selected_pas[
            (selected_pas["pattern"].astype(str) == selected_pas["selected_pattern"].astype(str))
            | (selected_pas["detector"].astype(str) == selected_pas["pattern"].astype(str))
        ].copy()
        selected_pas = selected_pas.sort_values(["signal_date", "code", "detector"]).drop_duplicates(
            subset=["signal_id"], keep="first"
        )
        out = out.merge(
            selected_pas[
                [
                    "signal_id",
                    "detector",
                    "detect_reason",
                    "pattern_quality_score",
                    "quality_status",
                    "entry_ref",
                    "stop_ref",
                    "target_ref",
                    "risk_reward_ref",
                    "volume_ratio",
                    "trace_payload_json",
                    "pattern_context_json",
                ]
            ].rename(columns={"detector": "trigger_detector", "volume_ratio": "trigger_volume_ratio"}),
            on="signal_id",
            how="left",
        )

    out = out.merge(frames["stock_gene"], on=["signal_date", "code"], how="left")
    out = out.merge(frames["mss"], on="signal_date", how="left")
    out = out.merge(
        frames["irs"][["signal_date", "industry", "industry_score", "industry_rank"]],
        on=["signal_date", "industry"],
        how="left",
    )
    out = out.merge(
        frames["l2_snapshot"][["signal_date", "code", "amount", "volume_ratio", "pct_chg", "adj_close"]],
        on=["signal_date", "code"],
        how="left",
        suffixes=("", "_l2"),
    )
    return out


def _build_trade_leg_ledger(frames: dict[str, pd.DataFrame], signal_context: pd.DataFrame) -> pd.DataFrame:
    trades = frames["trades"].copy()
    orders = frames["orders"].copy()
    if trades.empty:
        return pd.DataFrame()

    orders = orders.rename(
        columns={
            "execute_date": "order_execute_date",
            "quantity": "order_quantity",
            "pattern": "order_pattern",
            "status": "order_status",
            "reject_reason": "order_reject_reason",
        }
    )
    ledger = trades.merge(
        orders[
            [
                "order_id",
                "signal_id",
                "order_execute_date",
                "order_quantity",
                "order_pattern",
                "order_status",
                "order_reject_reason",
                "position_id",
            ]
        ],
        on=["order_id", "position_id"],
        how="left",
    )

    signal_cols = [
        "signal_id",
        "signal_date",
        "pattern",
        "reason_code",
        "industry",
        "variant",
        "preselect_score",
        "candidate_rank",
        "liquidity_tag",
        "pattern_strength",
        "irs_score",
        "mss_score",
        "final_score",
        "final_rank",
        "trigger_detector",
        "detect_reason",
        "pattern_quality_score",
        "quality_status",
        "entry_ref",
        "stop_ref",
        "target_ref",
        "risk_reward_ref",
        "current_wave_direction",
        "current_wave_age_trade_days",
        "current_wave_age_band",
        "current_wave_duration_percentile",
        "current_wave_magnitude_percentile",
        "current_wave_magnitude_band",
        "latest_confirmed_turn_type",
        "latest_two_b_confirm_type",
        "gene_score",
        "market_signal",
        "market_score",
        "industry_score",
        "industry_rank",
        "amount",
        "volume_ratio",
        "pct_chg",
        "adj_close",
    ]
    signal_ctx = signal_context[signal_cols].copy()
    ledger = ledger.merge(signal_ctx, on="signal_id", how="left", suffixes=("", "_signal"))

    buy_context = ledger.loc[ledger["action"] == "BUY"].copy()
    buy_context = buy_context.sort_values(["execute_date", "trade_id"]).drop_duplicates(subset=["position_id"], keep="first")
    buy_context = buy_context[
        [
            "position_id",
            "signal_id",
            "signal_date",
            "pattern",
            "reason_code",
            "industry",
            "variant",
            "preselect_score",
            "candidate_rank",
            "pattern_strength",
            "irs_score",
            "mss_score",
            "final_score",
            "final_rank",
            "trigger_detector",
            "detect_reason",
            "pattern_quality_score",
            "entry_ref",
            "stop_ref",
            "target_ref",
            "risk_reward_ref",
            "current_wave_direction",
            "current_wave_age_trade_days",
            "current_wave_age_band",
            "current_wave_duration_percentile",
            "current_wave_magnitude_percentile",
            "current_wave_magnitude_band",
            "latest_confirmed_turn_type",
            "latest_two_b_confirm_type",
            "gene_score",
            "market_signal",
            "market_score",
            "industry_score",
            "industry_rank",
        ]
    ].rename(
        columns={
            "signal_id": "entry_signal_id",
            "signal_date": "entry_signal_date",
            "pattern": "entry_pattern",
            "reason_code": "entry_reason_code",
            "industry": "entry_industry",
            "variant": "entry_variant",
            "preselect_score": "entry_preselect_score",
            "candidate_rank": "entry_candidate_rank",
            "pattern_strength": "entry_pattern_strength",
            "irs_score": "entry_irs_score",
            "mss_score": "entry_mss_score",
            "final_score": "entry_final_score",
            "final_rank": "entry_final_rank",
            "trigger_detector": "entry_trigger_detector",
            "detect_reason": "entry_detect_reason",
            "pattern_quality_score": "entry_pattern_quality_score",
            "entry_ref": "entry_ref_price",
            "stop_ref": "entry_stop_ref_price",
            "target_ref": "entry_target_ref_price",
            "risk_reward_ref": "entry_risk_reward_ref",
            "current_wave_direction": "entry_wave_direction",
            "current_wave_age_trade_days": "entry_wave_age_trade_days",
            "current_wave_age_band": "entry_wave_age_band",
            "current_wave_duration_percentile": "entry_duration_percentile",
            "current_wave_magnitude_percentile": "entry_magnitude_percentile",
            "current_wave_magnitude_band": "entry_magnitude_band",
            "latest_confirmed_turn_type": "entry_latest_confirmed_turn_type",
            "latest_two_b_confirm_type": "entry_latest_two_b_confirm_type",
            "gene_score": "entry_gene_score",
            "market_signal": "entry_market_signal",
            "market_score": "entry_market_score",
            "industry_score": "entry_industry_score",
            "industry_rank": "entry_industry_rank",
        }
    )
    ledger = ledger.merge(buy_context, on="position_id", how="left")
    ledger["holding_trade_days_hint"] = (
        pd.to_datetime(ledger["execute_date"]) - pd.to_datetime(ledger["entry_signal_date"])
    ).dt.days
    return ledger.sort_values(["execute_date", "action", "trade_id"]).reset_index(drop=True)


def _build_roundtrip_ledger(frames: dict[str, pd.DataFrame], trade_ledger: pd.DataFrame) -> pd.DataFrame:
    paired = _pair_trades(frames["trades"])
    if paired.empty:
        return pd.DataFrame()

    trade_lookup = trade_ledger.set_index("trade_id", drop=False)
    rows: list[dict[str, object]] = []
    for row in paired.itertuples(index=False):
        entry = trade_lookup.loc[row.entry_trade_id] if row.entry_trade_id in trade_lookup.index else None
        exit_trade = trade_lookup.loc[row.exit_trade_id] if row.exit_trade_id in trade_lookup.index else None
        entry_date = pd.Timestamp(row.entry_date)
        exit_date = pd.Timestamp(row.exit_date)
        rows.append(
            {
                "code": row.code,
                "entry_signal_id": None if entry is None else entry.get("entry_signal_id") or entry.get("signal_id"),
                "entry_signal_date": None if entry is None else entry.get("entry_signal_date") or entry.get("signal_date"),
                "entry_date": row.entry_date,
                "exit_date": row.exit_date,
                "holding_days": int((exit_date - entry_date).days),
                "pattern": row.pattern,
                "quantity": int(row.quantity),
                "entry_trade_id": row.entry_trade_id,
                "exit_trade_id": row.exit_trade_id,
                "entry_price": None if entry is None else entry.get("price"),
                "exit_price": None if exit_trade is None else exit_trade.get("price"),
                "pnl": float(row.pnl),
                "pnl_pct": float(row.pnl_pct),
                "position_id": row.position_id,
                "exit_reason": row.exit_reason,
                "is_partial_exit": bool(row.is_partial_exit),
                "industry": None if entry is None else entry.get("entry_industry") or entry.get("industry"),
                "entry_variant": None if entry is None else entry.get("entry_variant") or entry.get("variant"),
                "entry_candidate_rank": None if entry is None else entry.get("entry_candidate_rank"),
                "entry_final_rank": None if entry is None else entry.get("entry_final_rank"),
                "entry_final_score": None if entry is None else entry.get("entry_final_score"),
                "entry_trigger_detector": None if entry is None else entry.get("entry_trigger_detector"),
                "entry_detect_reason": None if entry is None else entry.get("entry_detect_reason"),
                "entry_pattern_quality_score": None if entry is None else entry.get("entry_pattern_quality_score"),
                "entry_ref_price": None if entry is None else entry.get("entry_ref_price"),
                "entry_stop_ref_price": None if entry is None else entry.get("entry_stop_ref_price"),
                "entry_target_ref_price": None if entry is None else entry.get("entry_target_ref_price"),
                "entry_risk_reward_ref": None if entry is None else entry.get("entry_risk_reward_ref"),
                "entry_wave_direction": None if entry is None else entry.get("entry_wave_direction"),
                "entry_wave_age_trade_days": None if entry is None else entry.get("entry_wave_age_trade_days"),
                "entry_wave_age_band": None if entry is None else entry.get("entry_wave_age_band"),
                "entry_duration_percentile": None if entry is None else entry.get("entry_duration_percentile"),
                "entry_magnitude_percentile": None if entry is None else entry.get("entry_magnitude_percentile"),
                "entry_magnitude_band": None if entry is None else entry.get("entry_magnitude_band"),
                "entry_latest_confirmed_turn_type": None if entry is None else entry.get("entry_latest_confirmed_turn_type"),
                "entry_latest_two_b_confirm_type": None if entry is None else entry.get("entry_latest_two_b_confirm_type"),
                "entry_gene_score": None if entry is None else entry.get("entry_gene_score"),
                "entry_market_signal": None if entry is None else entry.get("entry_market_signal"),
                "entry_market_score": None if entry is None else entry.get("entry_market_score"),
                "entry_industry_score": None if entry is None else entry.get("entry_industry_score"),
                "entry_industry_rank": None if entry is None else entry.get("entry_industry_rank"),
            }
        )
    return pd.DataFrame(rows).sort_values(["exit_date", "entry_date", "code"]).reset_index(drop=True)


def _build_rejection_ledger(frames: dict[str, pd.DataFrame], signal_context: pd.DataFrame) -> pd.DataFrame:
    orders = frames["orders"].copy()
    if orders.empty:
        return pd.DataFrame()
    rejected = orders[orders["status"].isin(["REJECTED", "EXPIRED"])].copy()
    if rejected.empty:
        return rejected
    ctx = signal_context.copy()
    ledger = rejected.merge(
        ctx[
            [
                "signal_id",
                "signal_date",
                "code",
                "pattern",
                "reason_code",
                "industry",
                "variant",
                "candidate_rank",
                "final_rank",
                "final_score",
                "current_wave_direction",
                "current_wave_age_band",
                "current_wave_duration_percentile",
                "latest_two_b_confirm_type",
                "gene_score",
                "market_signal",
                "market_score",
                "industry_score",
                "industry_rank",
            ]
        ],
        on="signal_id",
        how="left",
    )
    return ledger.sort_values(["execute_date", "order_id"]).reset_index(drop=True)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding=WINDOW_ENCODING)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=WINDOW_ENCODING)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding=WINDOW_ENCODING)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding=WINDOW_ENCODING))


def _metrics_path(year_dir: Path, year: int) -> Path:
    return year_dir / f"{year}-metrics.json"


def _build_one_line_conclusion(total_return: float, trade_count: int, max_drawdown: float, profit_factor: float) -> str:
    if total_return > 0.10:
        perf = "这一年明显赚钱"
    elif total_return > 0:
        perf = "这一年小幅赚钱"
    elif total_return > -0.03:
        perf = "这一年小亏，接近打平"
    else:
        perf = "这一年亏损比较明显"

    if trade_count >= 100:
        activity = "出手频率偏高"
    elif trade_count >= 30:
        activity = "出手频率中等"
    else:
        activity = "出手频率偏低"

    risk = f"PF {_format_ratio(profit_factor)}，MDD {_format_pct(max_drawdown)}"
    return f"{perf}，{activity}，{risk}。"


def _build_summary_markdown(
    *,
    scenario: ScenarioSpec,
    year_window: YearWindow,
    result,
    roundtrip_ledger: pd.DataFrame,
    trade_ledger: pd.DataFrame,
    rejection_ledger: pd.DataFrame,
    filter_metrics: dict[str, object] | None,
    output_year_dir: Path,
    initial_cash: float,
) -> str:
    net_pnl = float(roundtrip_ledger["pnl"].sum()) if not roundtrip_ledger.empty else 0.0
    total_return = net_pnl / initial_cash if initial_cash > 0 else 0.0
    total_fees = float(pd.to_numeric(trade_ledger.get("fee"), errors="coerce").fillna(0.0).sum()) if not trade_ledger.empty else 0.0
    avg_holding_days = float(roundtrip_ledger["holding_days"].mean()) if not roundtrip_ledger.empty else None
    best_trade = roundtrip_ledger.sort_values("pnl_pct", ascending=False).head(1) if not roundtrip_ledger.empty else pd.DataFrame()
    worst_trade = roundtrip_ledger.sort_values("pnl_pct", ascending=True).head(1) if not roundtrip_ledger.empty else pd.DataFrame()
    exit_breakdown = (
        roundtrip_ledger["exit_reason"].fillna("UNKNOWN").value_counts().sort_values(ascending=False).to_dict()
        if not roundtrip_ledger.empty
        else {}
    )
    reject_breakdown = (
        rejection_ledger["reject_reason"].fillna("UNKNOWN").value_counts().sort_values(ascending=False).to_dict()
        if not rejection_ledger.empty
        else {}
    )
    lines = [
        f"# {year_window.year} {scenario.title} Summary",
        "",
        "## 一句话结论",
        "",
        _build_one_line_conclusion(
            total_return=total_return,
            trade_count=int(result.trade_count),
            max_drawdown=float(result.max_drawdown),
            profit_factor=float(result.profit_factor),
        ),
        "",
        "## 回测口径",
        "",
        f"- 年份窗口: `{year_window.start.isoformat()} ~ {year_window.end.isoformat()}`",
        f"- 说明: {year_window.note}",
        f"- 场景: `{scenario.slug}`",
        f"- 场景说明: {scenario.notes}",
        f"- 初始资金: `{_format_num(initial_cash, 0)}`",
        f"- 逐笔交易台账: `{(output_year_dir / f'{year_window.year}-trade-legs.csv').name}`",
        f"- 配对回合台账: `{(output_year_dir / f'{year_window.year}-roundtrip-trades.csv').name}`",
        f"- 拒单与错过机会: `{(output_year_dir / f'{year_window.year}-rejections.csv').name}`",
    ]
    if filter_metrics:
        lines.extend(
            [
                f"- Gene 过滤规则: `{filter_metrics.get('gene_filter_rule')}`",
                f"- Gene 拦截信号数: `{_format_num(int(filter_metrics.get('gene_filter_blocked_signal_count') or 0), 0)}`",
                f"- Gene 拦截占比: `{_format_pct(float(filter_metrics.get('gene_filter_blocked_signal_share') or 0.0))}`",
                f"- Gene 拦截明细: `{(output_year_dir / f'{year_window.year}-gene-filter-blocked-signals.csv').name}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 常见统计数据",
            "",
            f"- 净收益: `{_format_num(net_pnl, 2)}`",
            f"- 总收益率: `{_format_pct(total_return)}`",
            f"- 平仓笔数: `{_format_num(int(result.trade_count), 0)}`",
            f"- 胜率: `{_format_pct(float(result.win_rate))}`",
            f"- 平均盈利笔收益率: `{_format_pct(float(result.avg_win))}`",
            f"- 平均亏损笔收益率: `{_format_pct(float(result.avg_loss))}`",
            f"- 期望值 EV: `{_format_pct(float(result.expected_value))}`",
            f"- 利润因子 PF: `{_format_ratio(float(result.profit_factor))}`",
            f"- 最大回撤 MDD: `{_format_pct(float(result.max_drawdown))}`",
            f"- 暴露率: `{_format_pct(float(result.exposure_rate))}`",
            f"- 参与率: `{_format_pct(float(result.participation_rate))}`",
            f"- 信号机会数: `{_format_num(int(result.opportunity_count), 0)}`",
            f"- 实际成交买单数: `{_format_num(int(result.filled_count), 0)}`",
            f"- 现金不足跳过数: `{_format_num(int(result.skip_cash_count), 0)}`",
            f"- 仓位上限跳过数: `{_format_num(int(result.skip_maxpos_count), 0)}`",
            f"- 拒单率: `{_format_pct(float(result.reject_rate))}`",
            f"- 缺价率: `{_format_pct(float(result.missing_rate))}`",
            f"- 总手续费: `{_format_num(total_fees, 2)}`",
            f"- 平均持有天数: `{_format_num(avg_holding_days, 2)}`",
            "",
            "## 交易手感",
            "",
        ]
    )
    if net_pnl > 0:
        lines.append(f"- 账户全年是赚钱的，净赚 `{_format_num(net_pnl, 2)}`。")
    elif net_pnl < 0:
        lines.append(f"- 账户全年是亏钱的，净亏 `{_format_num(abs(net_pnl), 2)}`。")
    else:
        lines.append("- 账户全年基本打平。")
    if float(result.max_drawdown) > 0.20:
        lines.append("- 回撤偏大，拿着会不舒服。")
    elif float(result.max_drawdown) > 0.10:
        lines.append("- 回撤中等，能做但不算轻松。")
    else:
        lines.append("- 回撤不大，风险侧相对克制。")
    if filter_metrics:
        lines.append(
            f"- Gene 过滤实际拦掉了 `{_format_num(int(filter_metrics.get('gene_filter_blocked_signal_count') or 0), 0)}` 个信号，"
            "代表这条线确实在用个股寿命和结构风险做负向过滤。"
        )
    else:
        lines.append("- 这条线没有用 Gene 做 runtime 拦截，只是纯参考基线。")

    lines.extend(["", "## 最好和最差的一笔", ""])
    if not best_trade.empty:
        row = best_trade.iloc[0]
        lines.append(
            f"- 最好的一笔: `{row['code']}`，`{row['entry_date']} -> {row['exit_date']}`，"
            f"收益率 `{_format_pct(float(row['pnl_pct']))}`，盈利 `{_format_num(float(row['pnl']), 2)}`"
        )
    if not worst_trade.empty:
        row = worst_trade.iloc[0]
        lines.append(
            f"- 最差的一笔: `{row['code']}`，`{row['entry_date']} -> {row['exit_date']}`，"
            f"收益率 `{_format_pct(float(row['pnl_pct']))}`，盈利 `{_format_num(float(row['pnl']), 2)}`"
        )

    lines.extend(["", "## 退出原因分布", ""])
    if exit_breakdown:
        for key, value in exit_breakdown.items():
            lines.append(f"- `{key}`: `{value}` 笔")
    else:
        lines.append("- 无")

    lines.extend(["", "## 拒单 / 错过机会", ""])
    if reject_breakdown:
        for key, value in reject_breakdown.items():
            lines.append(f"- `{key}`: `{value}` 次")
    else:
        lines.append("- 无")

    lines.extend(["", "## 备注", ""])
    lines.append("- 逐笔台账里的 `entry_*` 字段代表开仓时真实看到的触发、排序、Gene、市场和行业上下文。")
    lines.append("- 卖出腿若是分批卖，会在台账里通过 `is_partial_exit` 和 `exit_reason` 标出来。")
    lines.append(f"- 报告生成时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    return "\n".join(lines) + "\n"


def _write_scenario_readme(path: Path, scenario: ScenarioSpec, metrics_rows: list[dict[str, object]]) -> None:
    lines = [
        f"# {scenario.title}",
        "",
        f"- 场景标识: `{scenario.slug}`",
        f"- 场景说明: {scenario.notes}",
        "",
        "## 年度总览",
        "",
        "| 年份 | 净收益 | 收益率 | 交易数 | 胜率 | EV | PF | MDD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics_rows:
        lines.append(
            f"| {row['year']} | {_format_num(row['net_pnl'], 2)} | {_format_pct(row['total_return'])} | "
            f"{int(row['trade_count'])} | {_format_pct(row['win_rate'])} | {_format_pct(row['expected_value'])} | "
            f"{_format_ratio(row['profit_factor'])} | {_format_pct(row['max_drawdown'])} |"
        )
    _write_text(path, "\n".join(lines) + "\n")


def _write_root_readme(
    path: Path,
    *,
    scenarios: list[ScenarioSpec],
    metrics_rows: list[dict[str, object]],
    working_db_path: Path,
    raw_db_path: Path,
    available_start: date,
    available_end: date,
) -> None:
    lines = [
        "# Closed-Loop Fullspan Backtest Pack",
        "",
        "## 数据与执行口径",
        "",
        f"- 执行工作库: `{working_db_path}`",
        f"- 原始库: `{raw_db_path}`",
        f"- 覆盖区间: `{available_start.isoformat()} ~ {available_end.isoformat()}`",
        "- 这批回测是重新从 raw DuckDB 回灌 L1，再重建 L2/L3 后跑出来的，不是沿用旧年报缓存。",
        "- Reference 场景是当前冻结主线参照物。",
        "- Experimental 场景是把 DTT / IRS / MSS size-only overlay / Gene negative filter / 25-75 partial exit / Williams sizing 拼成的实验组合线。",
        "",
        "## 场景",
        "",
    ]
    for scenario in scenarios:
        lines.append(f"- `{scenario.slug}`: {scenario.notes}")
    lines.extend(
        [
            "",
            "## 汇总表",
            "",
            "| 场景 | 年份 | 净收益 | 收益率 | 交易数 | 胜率 | EV | PF | MDD |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in metrics_rows:
        lines.append(
            f"| {row['scenario_slug']} | {row['year']} | {_format_num(row['net_pnl'], 2)} | "
            f"{_format_pct(row['total_return'])} | {int(row['trade_count'])} | {_format_pct(row['win_rate'])} | "
            f"{_format_pct(row['expected_value'])} | {_format_ratio(row['profit_factor'])} | "
            f"{_format_pct(row['max_drawdown'])} |"
        )
    _write_text(path, "\n".join(lines) + "\n")


def _run_scenario_year(
    *,
    db_path: Path,
    scenario: ScenarioSpec,
    cfg: Settings,
    year_window: YearWindow,
    initial_cash: float,
    year_dir: Path,
) -> dict[str, object]:
    signal_filter = _maybe_make_signal_filter(scenario)

    store = Store(db_path)
    try:
        descriptor = start_run(
            store,
            scope=f"closed_loop_fullspan_{scenario.slug}_{year_window.year}",
            modules=["backtest", "report"],
            config=cfg,
            runtime_env="backtest",
            artifact_root=str(year_dir),
            start=year_window.start,
            end=year_window.end,
        )
        clear_runtime_tables(store)
    finally:
        store.close()

    status = "FAILED"
    error_summary = None
    result = None
    try:
        result = run_backtest(
            db_path=db_path,
            config=cfg,
            start=year_window.start,
            end=year_window.end,
            initial_cash=initial_cash,
            run_id=descriptor.run_id,
            signal_filter=signal_filter,
        )
        status = "SUCCESS"
    except Exception as exc:
        error_summary = str(exc)
        raise
    finally:
        finish_store = Store(db_path)
        try:
            finish_run(finish_store, descriptor.run_id, status, error_summary=error_summary)
        finally:
            finish_store.close()

    post_store = Store(db_path)
    try:
        frames = _load_run_frames(post_store, descriptor.run_id, year_window.start, year_window.end)
    finally:
        post_store.close()

    signal_context = _build_signal_context_table(frames)
    trade_ledger = _build_trade_leg_ledger(frames, signal_context)
    roundtrip_ledger = _build_roundtrip_ledger(frames, trade_ledger)
    rejection_ledger = _build_rejection_ledger(frames, signal_context)
    filter_metrics = None if signal_filter is None else dict(signal_filter.build_metrics())

    _write_csv(year_dir / f"{year_window.year}-trade-legs.csv", trade_ledger)
    _write_csv(year_dir / f"{year_window.year}-roundtrip-trades.csv", roundtrip_ledger)
    _write_csv(year_dir / f"{year_window.year}-rejections.csv", rejection_ledger)
    if signal_filter is not None:
        _write_csv(
            year_dir / f"{year_window.year}-gene-filter-blocked-signals.csv",
            pd.DataFrame(signal_filter.blocked_rows),
        )
    summary_markdown = _build_summary_markdown(
        scenario=scenario,
        year_window=year_window,
        result=result,
        roundtrip_ledger=roundtrip_ledger,
        trade_ledger=trade_ledger,
        rejection_ledger=rejection_ledger,
        filter_metrics=filter_metrics,
        output_year_dir=year_dir,
        initial_cash=initial_cash,
    )
    _write_text(year_dir / f"{year_window.year}-summary.md", summary_markdown)

    net_pnl = float(roundtrip_ledger["pnl"].sum()) if not roundtrip_ledger.empty else 0.0
    total_return = net_pnl / initial_cash if initial_cash > 0 else 0.0
    payload = {
        "scenario_slug": scenario.slug,
        "scenario_title": scenario.title,
        "year": int(year_window.year),
        "run_id": descriptor.run_id,
        "net_pnl": net_pnl,
        "total_return": total_return,
        "trade_count": int(result.trade_count),
        "win_rate": float(result.win_rate),
        "expected_value": float(result.expected_value),
        "profit_factor": float(result.profit_factor),
        "max_drawdown": float(result.max_drawdown),
        "reject_rate": float(result.reject_rate),
        "missing_rate": float(result.missing_rate),
        "exposure_rate": float(result.exposure_rate),
        "participation_rate": float(result.participation_rate),
        "opportunity_count": float(result.opportunity_count),
        "filled_count": float(result.filled_count),
        "skip_cash_count": float(result.skip_cash_count),
        "skip_maxpos_count": float(result.skip_maxpos_count),
        "trade_legs_file": str(year_dir / f"{year_window.year}-trade-legs.csv"),
        "roundtrip_file": str(year_dir / f"{year_window.year}-roundtrip-trades.csv"),
        "summary_file": str(year_dir / f"{year_window.year}-summary.md"),
        "rejection_file": str(year_dir / f"{year_window.year}-rejections.csv"),
        "gene_filter_blocked_count": 0 if filter_metrics is None else int(filter_metrics.get("gene_filter_blocked_signal_count") or 0),
        "gene_filter_blocked_share": 0.0 if filter_metrics is None else float(filter_metrics.get("gene_filter_blocked_signal_share") or 0.0),
    }
    _write_json(_metrics_path(year_dir, year_window.year), payload)
    return payload


def _load_existing_metrics(output_root: Path, scenarios: list[ScenarioSpec]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    valid_slugs = {scenario.slug for scenario in scenarios}
    for metrics_path in sorted(output_root.glob("*/*/*-metrics.json")):
        try:
            payload = _read_json(metrics_path)
        except Exception:
            continue
        if str(payload.get("scenario_slug") or "") not in valid_slugs:
            continue
        rows.append(payload)
    rows.sort(key=lambda row: (str(row.get("scenario_slug") or ""), int(row.get("year") or 0)))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run closed-loop fullspan reports for 2020-2026")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--cash", type=float, default=None)
    parser.add_argument("--exec-db", default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    parser.add_argument("--raw-db", default=r"G:\EmotionQuant_data\duckdb\emotionquant.duckdb")
    parser.add_argument(
        "--working-db",
        default=r"G:\EmotionQuant-temp\backtest\closed_loop_fullspan_20200101_20260224.duckdb",
    )
    parser.add_argument(
        "--output-root",
        default=r"G:\EmotionQuant-report\backtest_reports\closed_loop_fullspan_2020_2026",
    )
    parser.add_argument("--reuse-working-db", action="store_true", default=False)
    parser.add_argument(
        "--scenario-slugs",
        default="",
        help="Comma-separated scenario slugs to run. Empty means all scenarios.",
    )
    parser.add_argument("--skip-existing", action="store_true", default=False)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exec_db = Path(args.exec_db).expanduser().resolve()
    raw_db = Path(args.raw_db).expanduser().resolve()
    working_db = Path(args.working_db).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    if not exec_db.exists():
        raise FileNotFoundError(f"Execution DB not found: {exec_db}")
    if not raw_db.exists():
        raise FileNotFoundError(f"Raw DB not found: {raw_db}")

    base_cfg = get_settings().model_copy(deep=True)
    initial_cash = float(args.cash if args.cash is not None else base_cfg.backtest_initial_cash)
    available_start = date(args.start_year, 1, 1)
    available_end = _detect_available_end(raw_db)
    year_windows = _build_year_windows(
        start_year=args.start_year,
        end_year=args.end_year,
        available_start=available_start,
        available_end=available_end,
    )
    if not year_windows:
        raise RuntimeError("No yearly windows resolved.")

    if args.reuse_working_db and working_db.exists():
        db_file = working_db
        print(f"[build] reuse existing working db: {db_file}")
    else:
        db_file = _build_long_window_execution_db(
            exec_source_db=exec_db,
            raw_source_db=raw_db,
            working_db_path=working_db,
            start=year_windows[0].start,
            end=year_windows[-1].end,
            initial_cash=initial_cash,
        )

    scenarios = _build_scenarios()
    if args.scenario_slugs:
        wanted_slugs = {slug.strip() for slug in str(args.scenario_slugs).split(",") if slug.strip()}
        scenarios = [scenario for scenario in scenarios if scenario.slug in wanted_slugs]
        if not scenarios:
            raise RuntimeError(f"No matching scenarios for --scenario-slugs={args.scenario_slugs}")

    metrics_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        scenario_dir = output_root / scenario.slug
        scenario_dir.mkdir(parents=True, exist_ok=True)
        scenario_metrics: list[dict[str, object]] = []
        for window in year_windows:
            year_dir = scenario_dir / str(window.year)
            metrics_path = _metrics_path(year_dir, window.year)
            if args.skip_existing and metrics_path.exists():
                payload = _read_json(metrics_path)
                metrics_rows.append(payload)
                scenario_metrics.append(payload)
                print(f"[skip] {scenario.slug} year={window.year} use existing metrics")
                continue
            cfg = _make_config(base_cfg, scenario, initial_cash)
            print(f"[run] {scenario.slug} year={window.year} window={window.start}..{window.end}")
            payload = _run_scenario_year(
                db_path=db_file,
                scenario=scenario,
                cfg=cfg,
                year_window=window,
                initial_cash=initial_cash,
                year_dir=year_dir,
            )
            metrics_rows.append(payload)
            scenario_metrics.append(payload)
            print(
                f"[done] {scenario.slug} year={window.year} "
                f"trades={payload['trade_count']} return={payload['total_return']:.4f}"
            )
        _write_scenario_readme(scenario_dir / "README.md", scenario, scenario_metrics)

    all_metrics = _load_existing_metrics(output_root, _build_scenarios())
    metrics_frame = pd.DataFrame(all_metrics).sort_values(["scenario_slug", "year"]).reset_index(drop=True)
    _write_csv(output_root / "metrics_summary.csv", metrics_frame)
    _write_root_readme(
        output_root / "README.md",
        scenarios=_build_scenarios(),
        metrics_rows=all_metrics,
        working_db_path=db_file,
        raw_db_path=raw_db,
        available_start=year_windows[0].start,
        available_end=year_windows[-1].end,
    )
    print(f"report_root={output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
