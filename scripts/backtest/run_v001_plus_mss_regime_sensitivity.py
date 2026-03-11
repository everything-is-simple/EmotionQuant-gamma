from __future__ import annotations

# Phase 3 / MSS 专项证据脚本：
# 1. 运行时数据库与工作副本必须走 DATA_PATH / TEMP_PATH，不在仓库根目录落 DuckDB。
# 2. 仓库根目录只允许落代码、文档和脚本；因此最终 evidence 只写 docs/spec/，
#    中间 working db、artifact cache 全部走 TEMP_PATH。
# 3. 脚本目标不是重新定义主链，而是把“risk_regime 是否真的驱动了容量变化”做成可复查证据。

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import _pair_trades
from src.run_metadata import build_artifact_name, finish_run, start_run


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    return numeric


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _compute_pair_metrics(paired: pd.DataFrame) -> dict[str, float | int | None]:
    if paired.empty:
        return {
            "trade_count": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "expected_value": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
        }

    wins = paired[paired["pnl_pct"] > 0]
    losses = paired[paired["pnl_pct"] <= 0]
    total = float(len(paired))
    win_rate = float(len(wins) / total)
    avg_win = float(wins["pnl_pct"].mean()) if not wins.empty else 0.0
    avg_loss = float(abs(losses["pnl_pct"].mean())) if not losses.empty else 0.0
    profit_factor = None if avg_loss == 0.0 and avg_win > 0.0 else (avg_win / avg_loss if avg_loss > 0 else 0.0)
    expected_value = float(win_rate * avg_win - (1 - win_rate) * avg_loss)

    equity = paired.sort_values(["exit_date", "code", "pattern"]).copy()
    equity_curve = equity["pnl"].cumsum()
    running_peak = equity_curve.cummax()
    drawdown = ((running_peak - equity_curve) / running_peak.replace(0, pd.NA)).fillna(0.0)
    max_drawdown = float(drawdown.max()) if not drawdown.empty else 0.0

    return {
        "trade_count": int(total),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expected_value": expected_value,
        "profit_factor": _finite_or_none(profit_factor),
        "max_drawdown": max_drawdown,
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
                "avg_market_score": _finite_or_none(group["market_score"].mean()),
                "avg_effective_max_positions": _finite_or_none(group["effective_max_positions"].mean()),
                "avg_effective_risk_per_trade_pct": _finite_or_none(group["effective_risk_per_trade_pct"].mean()),
                "avg_effective_max_position_pct": _finite_or_none(group["effective_max_position_pct"].mean()),
                "overlay_reasons": sorted(
                    {str(value) for value in group["overlay_reason"].dropna().astype(str).tolist()}
                ),
            }
        )
    return rows


def _summarize_trace_by_reason(trace: pd.DataFrame, column: str) -> list[dict[str, object]]:
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


def _load_trace(store: Store, run_id: str) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT *
        FROM mss_risk_overlay_trace_exp
        WHERE run_id = ?
        ORDER BY signal_date ASC, signal_id ASC
        """,
        (run_id,),
    )


def _load_buy_entries(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT
            o.signal_id,
            t.code,
            t.pattern,
            t.execute_date AS entry_date,
            t.quantity,
            t.price,
            t.fee
        FROM l4_trades t
        INNER JOIN l4_orders o
            ON o.order_id = t.order_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date ASC, o.signal_id ASC
        """,
        (start, end),
    )


def _load_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT trade_id, order_id, code, execute_date, action, price, quantity, fee, pattern, is_paper
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )


def _build_paired_regime_frame(trace: pd.DataFrame, buy_entries: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    if trace.empty or buy_entries.empty or trades.empty:
        return pd.DataFrame(
            columns=[
                "code",
                "entry_date",
                "exit_date",
                "pattern",
                "quantity",
                "pnl",
                "pnl_pct",
                "signal_id",
                "risk_regime",
                "market_signal",
                "overlay_state",
                "overlay_reason",
            ]
        )

    trace_fields = trace[
        [
            "signal_id",
            "risk_regime",
            "market_signal",
            "overlay_state",
            "overlay_reason",
            "decision_status",
        ]
    ].drop_duplicates(subset=["signal_id"])
    # 这里只保留 ACCEPTED 的入场单：
    # regime sensitivity 关心的是“什么 regime 下实际入场并最终配对成交易”，
    # 拒绝原因另外从 trace summary 统计，不混到配对收益里。
    accepted_entries = buy_entries.merge(trace_fields, on="signal_id", how="left")
    accepted_entries = accepted_entries[accepted_entries["decision_status"] == "ACCEPTED"].copy()
    if accepted_entries.empty:
        return pd.DataFrame(
            columns=[
                "code",
                "entry_date",
                "exit_date",
                "pattern",
                "quantity",
                "pnl",
                "pnl_pct",
                "signal_id",
                "risk_regime",
                "market_signal",
                "overlay_state",
                "overlay_reason",
            ]
        )

    entry_lookup = (
        accepted_entries.sort_values(["entry_date", "signal_id"])
        .drop_duplicates(subset=["code", "entry_date", "pattern"], keep="first")
        [
            [
                "code",
                "entry_date",
                "pattern",
                "signal_id",
                "risk_regime",
                "market_signal",
                "overlay_state",
                "overlay_reason",
            ]
        ]
    )

    paired = _pair_trades(trades)
    if paired.empty:
        return paired
    return paired.merge(entry_lookup, on=["code", "entry_date", "pattern"], how="left")


def _summarize_pairs_by_regime(paired: pd.DataFrame) -> list[dict[str, object]]:
    if paired.empty:
        return []
    rows: list[dict[str, object]] = []
    for risk_regime, group in paired.groupby("risk_regime", dropna=False):
        label = "UNKNOWN" if risk_regime is None or pd.isna(risk_regime) else str(risk_regime)
        metrics = _compute_pair_metrics(group)
        rows.append(
            {
                "risk_regime": label,
                **metrics,
                "avg_pnl": _finite_or_none(group["pnl"].mean()),
                "avg_pnl_pct": _finite_or_none(group["pnl_pct"].mean()),
            }
        )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run v0.01-plus MSS regime sensitivity")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument(
        "--dtt-variant",
        default=None,
        help="DTT variant to keep fixed during MSS regime sensitivity; default uses current config.dtt_variant",
    )
    parser.add_argument("--patterns", default=None, help="Optional comma-separated patterns override")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--use-db-as-working-copy",
        action="store_true",
        help="Use --db-path as an already prepared working copy instead of copying it again",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__mss_regime_sensitivity.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    if args.dtt_variant:
        cfg.dtt_variant = args.dtt_variant.strip()

    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"mss-regime-sensitivity-{date.today():%Y%m%d}.duckdb"
    )
    patterns = (
        [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
        if args.patterns
        else cfg.pas_effective_patterns
    )

    db_file = db_path if args.use_db_as_working_copy else prepare_working_db(db_path, working_db_path)
    artifact_root = cfg.resolved_temp_path / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    # working db / artifact root 都放 TEMP_PATH：
    # repo 根目录只放可提交内容，避免把回测副本和中间缓存污染工作树。

    if not args.skip_rebuild_l3:
        build_store = Store(db_file)
        try:
            # 真实证据默认先重建 L3，确保 MSS/IRS 都和当前代码口径一致；
            # 只有在确认 working db 已准备好时，才允许 skip。
            build_layers(build_store, cfg, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    meta_store = Store(db_file)
    try:
        clear_runtime_tables(meta_store)
        run = start_run(
            store=meta_store,
            scope="mss_regime_sensitivity",
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
            initial_cash=args.cash,
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

    analysis_store = Store(db_file)
    try:
        trace = _load_trace(analysis_store, run.run_id)
        buy_entries = _load_buy_entries(analysis_store, start, end)
        trades = _load_trades(analysis_store, start, end)
        paired = _build_paired_regime_frame(trace, buy_entries, trades)
    finally:
        analysis_store.close()

    summary_run_id = run.run_id
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "mss_regime_sensitivity", "json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 最终证据允许回写仓库文档区；这是 blueprint 明确允许的“可检查产物”，
    # 不属于运行时缓存，也不应放进 DATA_PATH/TEMP_PATH。

    payload = {
        "summary_run_id": summary_run_id,
        "run_id": run.run_id,
        "db_path": str(Path(db_file).resolve()),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns,
        "overall_metrics": {
            "trade_days": result.trade_days,
            "trade_count": result.trade_count,
            "win_rate": result.win_rate,
            "avg_win": result.avg_win,
            "avg_loss": result.avg_loss,
            "expected_value": result.expected_value,
            "profit_factor": _finite_or_none(result.profit_factor),
            "max_drawdown": result.max_drawdown,
            "reject_rate": result.reject_rate,
            "missing_rate": result.missing_rate,
            "exposure_rate": result.exposure_rate,
            "opportunity_count": result.opportunity_count,
            "filled_count": result.filled_count,
            "skip_cash_count": result.skip_cash_count,
            "skip_maxpos_count": result.skip_maxpos_count,
            "participation_rate": result.participation_rate,
        },
        "trace_counts": {
            "overlay_trace_rows": int(len(trace)),
            "buy_entry_rows": int(len(buy_entries)),
            "paired_trade_rows": int(len(paired)),
        },
        "regime_trace_summary": _summarize_trace_by_regime(trace),
        "regime_trade_summary": _summarize_pairs_by_regime(paired),
        "overlay_reason_summary": _summarize_trace_by_reason(trace, "overlay_reason"),
        "decision_bucket_summary": _summarize_trace_by_reason(trace, "decision_bucket"),
        "sample_dates_with_regimes": [
            {
                "signal_date": _to_iso(row.signal_date),
                "signal_id": row.signal_id,
                "risk_regime": row.risk_regime,
                "overlay_reason": row.overlay_reason,
                "decision_status": row.decision_status,
            }
            for row in trace.head(20).itertuples(index=False)
        ],
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mss_regime_sensitivity={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
