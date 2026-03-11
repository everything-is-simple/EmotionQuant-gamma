from __future__ import annotations

# Phase 4 / trade attribution:
# 1. 默认 variant 必须跟当前 pattern_* 主链一致，避免旧 bof_* 别名把 Gate 结论带偏。
# 2. 脚本只消费已经准备好的执行库；若窗口缺数据，补数顺序固定为本地旧库优先，
#    再按 TUSHARE_PRIMARY_* 和 TUSHARE_FALLBACK_* 执行兜底。
# 3. working db / artefact cache 只落 TEMP_PATH，最终 evidence 才允许写入 docs/spec/。

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import prepare_working_db
from src.backtest.replay_variants import REPLAY_VARIANTS, apply_replay_variant_runtime
from src.backtest.engine import run_backtest
from src.config import Settings, get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.report.reporter import _pair_trades
from src.run_metadata import build_artifact_name, build_run_id, finish_run, start_run

DEFAULT_VARIANTS = [
    "v0_01_dtt_pattern_only",
    "v0_01_dtt_pattern_plus_irs_score",
]
DEFAULT_EXECUTE_DATES = [
    "2026-01-20",
    "2026-01-30",
    "2026-02-04",
    "2026-02-05",
]
DEFAULT_SCENARIOS = [
    ("top1_pos1", 1, 1),
    ("top1_pos2", 1, 2),
    ("top2_pos1", 2, 1),
    ("top2_pos2", 2, 2),
    ("top50_pos10", 50, 10),
]
EPSILON = 1e-9


@dataclass(frozen=True)
class AttributionScenario:
    label: str
    dtt_top_n: int
    max_positions: int


@dataclass(frozen=True)
class ScenarioRunArtifacts:
    variant: str
    run_id: str
    buy_trades: pd.DataFrame
    maxpos_rejects: pd.DataFrame
    entry_pnl: pd.DataFrame


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_date_column(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    normalized = frame.copy()
    if column not in normalized.columns:
        normalized[column] = pd.Series(dtype="object")
        return normalized
    if normalized.empty:
        normalized[column] = normalized[column].astype("object")
        return normalized
    normalized[column] = normalized[column].apply(_to_iso).astype("object")
    return normalized


def _parse_variants(text: str) -> list[str]:
    variants = [item.strip().lower() for item in text.split(",") if item.strip()]
    if len(variants) != 2:
        raise ValueError("逐笔归因当前只支持 2 个 replay variant 对比。")
    unknown = sorted(set(variants) - REPLAY_VARIANTS)
    if unknown:
        raise ValueError(f"不支持的 replay variant: {', '.join(unknown)}")
    return variants


def _parse_scenarios(text: str | None) -> list[AttributionScenario]:
    if text is None or not text.strip():
        return [AttributionScenario(label=label, dtt_top_n=top_n, max_positions=max_pos) for label, top_n, max_pos in DEFAULT_SCENARIOS]

    scenarios: list[AttributionScenario] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            raise ValueError(f"非法场景定义: {item}，应为 label:dtt_top_n:max_positions")
        label, dtt_top_n, max_positions = parts
        scenarios.append(
            AttributionScenario(
                label=label,
                dtt_top_n=int(dtt_top_n),
                max_positions=int(max_positions),
            )
        )
    if not scenarios:
        raise ValueError("至少需要 1 个场景。")
    return scenarios


def _clear_runtime_tables(store: Store) -> None:
    # 逐笔归因只关心当前 run 的执行痕迹，先清运行态表，避免旧 run 串入结果。
    for table in (
        "l4_pattern_stats",
        "l4_daily_report",
        "l4_trades",
        "l4_orders",
        "l4_stock_trust",
        "l3_signals",
        "l3_signal_rank_exp",
    ):
        store.conn.execute(f"DELETE FROM {table}")


def _build_variant_config(base: Settings, variant: str, dtt_top_n: int, max_positions: int) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.dtt_top_n = int(dtt_top_n)
    cfg.max_positions = int(max_positions)
    # Phase 4 Gate replay 现在允许 legacy baseline 和 DTT 候选直接逐笔对照；
    # 这里统一走 replay alias 解释层，避免脚本自己再手搓 pipeline 分叉。
    return apply_replay_variant_runtime(cfg, variant)


def _read_buy_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            o.signal_id,
            t.execute_date,
            t.code,
            t.pattern,
            t.quantity,
            t.price,
            t.fee
        FROM l4_trades t
        INNER JOIN l4_orders o
            ON o.order_id = t.order_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date ASC, t.code ASC, o.signal_id ASC
        """,
        (start, end),
    )
    return _normalize_date_column(frame, "execute_date")


def _read_maxpos_rejects(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT signal_id, execute_date, code, reject_reason
        FROM l4_orders
        WHERE action = 'BUY'
          AND status = 'REJECTED'
          AND reject_reason = 'MAX_POSITIONS_REACHED'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, code ASC, signal_id ASC
        """,
        (start, end),
    )
    return _normalize_date_column(frame, "execute_date")


def _read_entry_pnl(store: Store, start: date, end: date) -> pd.DataFrame:
    trades = store.read_df(
        """
        SELECT trade_id, order_id, code, execute_date, action, price, quantity, fee, pattern, is_paper
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, trade_id ASC
        """,
        (start, end),
    )
    if trades.empty:
        return pd.DataFrame(
            columns=["execute_date", "code", "pattern", "entry_quantity", "entry_pnl", "entry_pnl_pct"]
        )

    # 这里复用报告层的配对逻辑，把 BUY/SELL 先配成 entry 视角，再做执行日归因。
    paired = _pair_trades(trades)
    if paired.empty:
        return pd.DataFrame(
            columns=["execute_date", "code", "pattern", "entry_quantity", "entry_pnl", "entry_pnl_pct"]
        )

    paired["entry_date"] = paired["entry_date"].apply(_to_iso)
    buy_trades = trades[trades["action"].str.upper() == "BUY"].copy()
    buy_trades["execute_date"] = buy_trades["execute_date"].apply(_to_iso)
    buy_trades["entry_notional"] = buy_trades["price"].astype(float) * buy_trades["quantity"].astype(float) + buy_trades["fee"].astype(float)
    buy_agg = (
        buy_trades.groupby(["execute_date", "code", "pattern"], as_index=False)
        .agg(entry_quantity=("quantity", "sum"), entry_notional=("entry_notional", "sum"))
    )
    pnl_agg = (
        paired.groupby(["entry_date", "code", "pattern"], as_index=False)
        .agg(entry_pnl=("pnl", "sum"), matched_quantity=("quantity", "sum"))
        .rename(columns={"entry_date": "execute_date"})
    )
    merged = buy_agg.merge(pnl_agg, on=["execute_date", "code", "pattern"], how="left")
    merged["entry_pnl"] = merged["entry_pnl"].fillna(0.0)
    merged["entry_pnl_pct"] = merged.apply(
        lambda row: 0.0 if float(row["entry_notional"] or 0.0) <= 0 else float(row["entry_pnl"]) / float(row["entry_notional"]),
        axis=1,
    )
    return _normalize_date_column(
        merged[["execute_date", "code", "pattern", "entry_quantity", "entry_pnl", "entry_pnl_pct"]],
        "execute_date",
    )


def _run_variant(
    db_file: Path,
    base_config: Settings,
    start: date,
    end: date,
    patterns: list[str],
    initial_cash: float | None,
    variant: str,
    dtt_top_n: int,
    max_positions: int,
    artifact_root: Path,
) -> ScenarioRunArtifacts:
    cfg = _build_variant_config(base_config, variant, dtt_top_n, max_positions)
    # 每个 variant 都用独立清库 + 重跑，保证左右对比只差配置，不差残留运行态。
    clear_store = Store(db_file)
    try:
        _clear_runtime_tables(clear_store)
    finally:
        clear_store.close()

    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="trade_attribution",
        modules=["backtest", "selector", "strategy", "broker", "report"],
        config=cfg,
        runtime_env="script",
        artifact_root=str(artifact_root),
        start=start,
        end=end,
    )
    meta_store.close()

    try:
        run_backtest(
            db_path=db_file,
            config=cfg,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=initial_cash,
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
        buy_trades = _read_buy_trades(snap_store, start, end)
        maxpos_rejects = _read_maxpos_rejects(snap_store, start, end)
        entry_pnl = _read_entry_pnl(snap_store, start, end)
    finally:
        snap_store.close()

    return ScenarioRunArtifacts(
        variant=variant,
        run_id=run.run_id,
        buy_trades=buy_trades,
        maxpos_rejects=maxpos_rejects,
        entry_pnl=entry_pnl,
    )


def _build_buy_attribution(buy_trades: pd.DataFrame, entry_pnl: pd.DataFrame) -> pd.DataFrame:
    if buy_trades.empty:
        return pd.DataFrame(
            columns=["signal_id", "execute_date", "code", "pattern", "quantity", "price", "fee", "entry_pnl", "entry_pnl_pct"]
        )
    merged = buy_trades.merge(
        entry_pnl,
        on=["execute_date", "code", "pattern"],
        how="left",
    )
    merged["entry_pnl"] = merged["entry_pnl"].fillna(0.0)
    merged["entry_pnl_pct"] = merged["entry_pnl_pct"].fillna(0.0)
    return merged


def _safe_float(value: object | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _summarize_trade_rows(frame: pd.DataFrame, left_variant: str, right_variant: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "left_quantity": None if pd.isna(row.get(f"quantity_{left_variant}")) else int(row[f"quantity_{left_variant}"]),
                "right_quantity": None if pd.isna(row.get(f"quantity_{right_variant}")) else int(row[f"quantity_{right_variant}"]),
                "left_entry_pnl": _safe_float(row.get(f"entry_pnl_{left_variant}")),
                "right_entry_pnl": _safe_float(row.get(f"entry_pnl_{right_variant}")),
                "left_entry_pnl_pct": _safe_float(row.get(f"entry_pnl_pct_{left_variant}")),
                "right_entry_pnl_pct": _safe_float(row.get(f"entry_pnl_pct_{right_variant}")),
            }
        )
    return rows


def _summarize_reject_rows(frame: pd.DataFrame, left_variant: str, right_variant: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "code": row["code"],
                "signal_id": row["signal_id"],
                "left_rejected": bool(row.get(f"rejected_{left_variant}", False)),
                "right_rejected": bool(row.get(f"rejected_{right_variant}", False)),
            }
        )
    return rows


def _build_date_payload(
    execute_date: str,
    left_variant: str,
    right_variant: str,
    left_attr: pd.DataFrame,
    right_attr: pd.DataFrame,
    left_rejects: pd.DataFrame,
    right_rejects: pd.DataFrame,
) -> dict[str, object]:
    left_attr = _normalize_date_column(left_attr, "execute_date")
    right_attr = _normalize_date_column(right_attr, "execute_date")
    left_rejects = _normalize_date_column(left_rejects, "execute_date")
    right_rejects = _normalize_date_column(right_rejects, "execute_date")
    left_buy = left_attr[left_attr["execute_date"] == execute_date].copy()
    right_buy = right_attr[right_attr["execute_date"] == execute_date].copy()
    left_buy = left_buy.rename(
        columns={
            "quantity": f"quantity_{left_variant}",
            "entry_pnl": f"entry_pnl_{left_variant}",
            "entry_pnl_pct": f"entry_pnl_pct_{left_variant}",
        }
    )
    right_buy = right_buy.rename(
        columns={
            "quantity": f"quantity_{right_variant}",
            "entry_pnl": f"entry_pnl_{right_variant}",
            "entry_pnl_pct": f"entry_pnl_pct_{right_variant}",
        }
    )
    merged_buy = left_buy.merge(
        right_buy,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="outer",
        indicator=True,
    )
    left_only = merged_buy[merged_buy["_merge"] == "left_only"].copy()
    right_only = merged_buy[merged_buy["_merge"] == "right_only"].copy()
    quantity_changed = merged_buy[
        (merged_buy["_merge"] == "both")
        & (merged_buy[f"quantity_{left_variant}"] != merged_buy[f"quantity_{right_variant}"])
    ].copy()

    left_reject_day = left_rejects[left_rejects["execute_date"] == execute_date].copy()
    right_reject_day = right_rejects[right_rejects["execute_date"] == execute_date].copy()
    left_reject_day[f"rejected_{left_variant}"] = True
    right_reject_day[f"rejected_{right_variant}"] = True
    merged_reject = left_reject_day.merge(
        right_reject_day,
        on=["signal_id", "execute_date", "code"],
        how="outer",
        indicator=True,
    )
    reject_changed = merged_reject[merged_reject["_merge"] != "both"].copy()

    left_changed_total = float(
        left_only[f"entry_pnl_{left_variant}"].fillna(0.0).sum() + quantity_changed[f"entry_pnl_{left_variant}"].fillna(0.0).sum()
    )
    right_changed_total = float(
        right_only[f"entry_pnl_{right_variant}"].fillna(0.0).sum() + quantity_changed[f"entry_pnl_{right_variant}"].fillna(0.0).sum()
    )
    if right_changed_total > left_changed_total + EPSILON:
        pnl_direction = f"{right_variant} 更好"
    elif right_changed_total + EPSILON < left_changed_total:
        pnl_direction = f"{right_variant} 更差"
    else:
        pnl_direction = "持平"

    return {
        "execute_date": execute_date,
        "trade_set_swaps": _summarize_trade_rows(pd.concat([left_only, right_only], ignore_index=True), left_variant, right_variant),
        "quantity_changes": _summarize_trade_rows(quantity_changed, left_variant, right_variant),
        "maxpos_reject_swaps": _summarize_reject_rows(reject_changed, left_variant, right_variant),
        "left_changed_entry_pnl_total": left_changed_total,
        "right_changed_entry_pnl_total": right_changed_total,
        "pnl_direction": pnl_direction,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run trade attribution for selected execute dates")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--execute-dates", nargs="+", default=DEFAULT_EXECUTE_DATES, help="Execute dates to attribute")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--variants", default=",".join(DEFAULT_VARIANTS), help="Comma-separated replay variants")
    parser.add_argument("--scenarios", default=None, help="Comma-separated label:dtt_top_n:max_positions items")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument("--skip-rebuild-l3", action="store_true", help="Reuse existing l3_mss_daily/l3_irs_daily in working DB")
    parser.add_argument("--output", default=None, help="Output JSON path")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    execute_dates = [_parse_date(item).isoformat() for item in args.execute_dates]
    patterns = [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
    variants = _parse_variants(args.variants)
    scenarios = _parse_scenarios(args.scenarios)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    output_root.mkdir(parents=True, exist_ok=True)
    working_root = (cfg.resolved_temp_path / "backtest").resolve()
    working_root.mkdir(parents=True, exist_ok=True)
    artifact_root = (cfg.resolved_temp_path / "artifacts").resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    # 这里显式把 working db 和 artifact cache 锁在 TEMP_PATH：
    # repo 根目录只留可提交证据，正式执行库仍留在 DATA_PATH。

    summary_run_id = build_run_id(
        scope="trade_attribution",
        mode="dtt",
        variant=f"{variants[0]}_vs_{variants[1]}",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "trade_attribution", "json")
    )

    results: list[dict[str, object]] = []
    for scenario in scenarios:
        working_db_path = working_root / f"trade_attr_{scenario.label}_top{scenario.dtt_top_n}_pos{scenario.max_positions}.duckdb"
        db_file = prepare_working_db(db_path, working_db_path)
        if not args.skip_rebuild_l3:
            build_store = Store(db_file)
            try:
                build_layers(build_store, cfg, layers=["l3"], start=start, end=end, force=True)
            finally:
                build_store.close()

        run_artifacts: dict[str, ScenarioRunArtifacts] = {}
        for variant in variants:
            run_artifacts[variant] = _run_variant(
                db_file=db_file,
                base_config=cfg,
                start=start,
                end=end,
                patterns=patterns or ["bof"],
                initial_cash=args.cash,
                variant=variant,
                dtt_top_n=scenario.dtt_top_n,
                max_positions=scenario.max_positions,
                artifact_root=artifact_root,
            )

        left_variant, right_variant = variants
        left_attr = _build_buy_attribution(run_artifacts[left_variant].buy_trades, run_artifacts[left_variant].entry_pnl)
        right_attr = _build_buy_attribution(run_artifacts[right_variant].buy_trades, run_artifacts[right_variant].entry_pnl)

        date_payloads = [
            _build_date_payload(
                execute_date=execute_date,
                left_variant=left_variant,
                right_variant=right_variant,
                left_attr=left_attr,
                right_attr=right_attr,
                left_rejects=run_artifacts[left_variant].maxpos_rejects,
                right_rejects=run_artifacts[right_variant].maxpos_rejects,
            )
            for execute_date in execute_dates
        ]
        results.append(
            {
                "label": scenario.label,
                "dtt_top_n": scenario.dtt_top_n,
                "max_positions": scenario.max_positions,
                "working_db_path": str(working_db_path),
                "variants": {
                    variant: {"run_id": artifacts.run_id} for variant, artifacts in run_artifacts.items()
                },
                "dates": date_payloads,
            }
        )

    payload = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(db_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "execute_dates": execute_dates,
        "patterns": patterns or ["bof"],
        "variants": variants,
        "scenarios": [asdict(item) for item in scenarios],
        "results": results,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"trade_attribution={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
