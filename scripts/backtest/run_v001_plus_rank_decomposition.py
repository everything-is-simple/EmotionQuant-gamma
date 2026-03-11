from __future__ import annotations

# Phase 4 / rank decomposition:
# 1. 默认 variant 必须对齐当前 pattern_* 命名，不能再沿用旧 bof_* 口径。
# 2. 正式执行库只从 DATA_PATH 读取，working copy/artefact cache 只放 TEMP_PATH。
# 3. 这个脚本只做 Gate 归因，不负责抓数；若窗口缺数据，先按 RAW_DB_PATH/旧库优先，
#    再按 TUSHARE_PRIMARY_* -> TUSHARE_FALLBACK_* 补齐后重跑。

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

from src.backtest.ablation import prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings, get_settings
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import build_artifact_name, build_run_id, finish_run, start_run

DTT_VARIANTS = [
    "v0_01_dtt_pattern_only",
    "v0_01_dtt_pattern_plus_irs_score",
    "v0_01_dtt_pattern_plus_irs_mss_score",
]

EPSILON = 1e-9


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run DTT variants and compare rank decomposition")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument(
        "--variants",
        default=",".join(DTT_VARIANTS),
        help="Comma-separated DTT variants to compare",
    )
    parser.add_argument("--dtt-top-n", type=int, default=None, help="Override DTT_TOP_N for this run")
    parser.add_argument("--max-positions", type=int, default=None, help="Override MAX_POSITIONS for this run")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__rank_decomposition.json",
    )
    return parser


def _clear_runtime_tables(store: Store, preserve_rank_exp: bool) -> None:
    tables = [
        "l4_pattern_stats",
        "l4_daily_report",
        "l4_trades",
        "l4_orders",
        "l4_stock_trust",
        "l3_signals",
    ]
    if not preserve_rank_exp:
        tables.append("l3_signal_rank_exp")
    for table in tables:
        store.conn.execute(f"DELETE FROM {table}")


def _build_variant_config(base: Settings, variant: str) -> Settings:
    cfg = base.model_copy(deep=True)
    cfg.pipeline_mode = "dtt"
    cfg.enable_dtt_mode = True
    cfg.dtt_variant = variant
    cfg.enable_mss_gate = False
    cfg.enable_irs_filter = False
    return cfg


def _parse_variants(text: str) -> list[str]:
    variants = [item.strip().lower() for item in text.split(",") if item.strip()]
    if not variants:
        raise ValueError("At least one DTT variant is required.")
    unknown = sorted(set(variants) - set(DTT_VARIANTS))
    if unknown:
        raise ValueError(f"Unsupported DTT variants: {', '.join(unknown)}")
    return variants


def _read_rank_frame(store: Store, run_id: str) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            run_id,
            signal_id,
            signal_date,
            code,
            industry,
            variant,
            bof_strength,
            irs_score,
            mss_score,
            final_score,
            final_rank,
            selected
        FROM l3_signal_rank_exp
        WHERE run_id = ?
        ORDER BY signal_date ASC, final_rank ASC, signal_id ASC
        """,
        (run_id,),
    )
    if frame.empty:
        return frame
    frame["signal_date"] = frame["signal_date"].apply(_to_iso)
    frame["selected"] = frame["selected"].astype(bool)
    return frame


def _read_buy_trade_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            o.signal_id,
            t.execute_date,
            t.code,
            t.pattern,
            t.quantity,
            t.price
        FROM l4_trades t
        INNER JOIN l4_orders o
            ON o.order_id = t.order_id
        WHERE t.action = 'BUY'
          AND t.execute_date BETWEEN ? AND ?
        ORDER BY t.execute_date ASC, t.code ASC, o.signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _read_rejected_buy_order_frame(store: Store, start: date, end: date) -> pd.DataFrame:
    frame = store.read_df(
        """
        SELECT
            signal_id,
            execute_date,
            code,
            reject_reason
        FROM l4_orders
        WHERE action = 'BUY'
          AND status = 'REJECTED'
          AND execute_date BETWEEN ? AND ?
        ORDER BY execute_date ASC, code ASC, signal_id ASC
        """,
        (start, end),
    )
    if frame.empty:
        return frame
    frame["execute_date"] = frame["execute_date"].apply(_to_iso)
    return frame


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _snapshot_metrics(store: Store, start: date, end: date, run_id: str) -> dict[str, float | int | None]:
    report = store.read_df(
        """
        SELECT expected_value, profit_factor, max_drawdown, trades_count,
               reject_rate, missing_rate, exposure_rate, opportunity_count,
               filled_count, skip_cash_count, skip_maxpos_count, participation_rate
        FROM l4_daily_report
        WHERE date = ?
        LIMIT 1
        """,
        (end,),
    )
    signal_count = int(
        store.read_scalar("SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?", (start, end)) or 0
    )
    ranked_signal_count = int(
        store.read_scalar("SELECT COUNT(*) FROM l3_signal_rank_exp WHERE run_id = ?", (run_id,))
        or 0
    )
    if report.empty:
        return {
            "signals_count": signal_count,
            "ranked_signals_count": ranked_signal_count,
        }
    row = report.iloc[0]
    return {
        "signals_count": signal_count,
        "ranked_signals_count": ranked_signal_count,
        "expected_value": _finite_or_none(row["expected_value"]),
        "profit_factor": _finite_or_none(row["profit_factor"]),
        "max_drawdown": _finite_or_none(row["max_drawdown"]),
        "trades_count": int(row["trades_count"] or 0),
        "reject_rate": _finite_or_none(row.get("reject_rate")),
        "missing_rate": _finite_or_none(row.get("missing_rate")),
        "exposure_rate": _finite_or_none(row.get("exposure_rate")),
        "opportunity_count": _finite_or_none(row.get("opportunity_count")),
        "filled_count": _finite_or_none(row.get("filled_count")),
        "skip_cash_count": _finite_or_none(row.get("skip_cash_count")),
        "skip_maxpos_count": _finite_or_none(row.get("skip_maxpos_count")),
        "participation_rate": _finite_or_none(row.get("participation_rate")),
    }


def _run_variant(
    db_file: Path,
    base_config: Settings,
    start: date,
    end: date,
    patterns: list[str],
    initial_cash: float | None,
    variant: str,
    artifact_root: Path,
) -> tuple[dict[str, object], pd.DataFrame]:
    cfg = _build_variant_config(base_config, variant)
    clear_store = Store(db_file)
    try:
        # 清执行态表，但保留前一个 run 的 rank sidecar，便于做跨 variant 对照。
        _clear_runtime_tables(clear_store, preserve_rank_exp=True)
    finally:
        clear_store.close()

    meta_store = Store(db_file)
    run = start_run(
        store=meta_store,
        scope="rank_decomp",
        modules=["backtest", "selector", "strategy", "broker", "report"],
        config=cfg,
        runtime_env="script",
        artifact_root=str(artifact_root),
        start=start,
        end=end,
    )
    meta_store.close()

    try:
        result = run_backtest(
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
        rank_frame = _read_rank_frame(snap_store, run.run_id)
        metrics = _snapshot_metrics(snap_store, start, end, run.run_id)
        buy_trade_frame = _read_buy_trade_frame(snap_store, start, end)
        rejected_buy_frame = _read_rejected_buy_order_frame(snap_store, start, end)
    finally:
        snap_store.close()

    return (
        {
            "variant": variant,
            "run_id": run.run_id,
            "trade_days": result.trade_days,
            "trade_count": result.trade_count,
            "win_rate": _finite_or_none(result.win_rate),
            "avg_win": _finite_or_none(result.avg_win),
            "avg_loss": _finite_or_none(result.avg_loss),
            "expected_value": _finite_or_none(result.expected_value),
            "profit_factor": _finite_or_none(result.profit_factor),
            "max_drawdown": _finite_or_none(result.max_drawdown),
            "metrics": metrics,
            "buy_trade_count": int(len(buy_trade_frame)),
            "buy_reject_count": int(len(rejected_buy_frame)),
            "buy_reject_maxpos_count": int(
                (rejected_buy_frame["reject_reason"] == "MAX_POSITIONS_REACHED").sum()
            )
            if not rejected_buy_frame.empty
            else 0,
        },
        rank_frame,
        buy_trade_frame,
        rejected_buy_frame,
    )


def _build_pair_samples(frame: pd.DataFrame, left_variant: str, right_variant: str) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for _, row in frame.head(5).iterrows():
        samples.append(
            {
                "signal_date": row["signal_date"],
                "code": row["code"],
                "signal_id": row["signal_id"],
                "left_rank": None if pd.isna(row[f"final_rank_{left_variant}"]) else int(row[f"final_rank_{left_variant}"]),
                "right_rank": None if pd.isna(row[f"final_rank_{right_variant}"]) else int(row[f"final_rank_{right_variant}"]),
                "left_score": None
                if pd.isna(row[f"final_score_{left_variant}"])
                else float(row[f"final_score_{left_variant}"]),
                "right_score": None
                if pd.isna(row[f"final_score_{right_variant}"])
                else float(row[f"final_score_{right_variant}"]),
                "left_selected": None
                if pd.isna(row[f"selected_{left_variant}"])
                else bool(row[f"selected_{left_variant}"]),
                "right_selected": None
                if pd.isna(row[f"selected_{right_variant}"])
                else bool(row[f"selected_{right_variant}"]),
            }
        )
    return samples


def _build_execution_samples(
    frame: pd.DataFrame,
    left_variant: str,
    right_variant: str,
    date_col: str,
    value_column: str | None = None,
) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for _, row in frame.head(5).iterrows():
        payload: dict[str, object] = {
            date_col: row[date_col],
            "code": row["code"],
            "signal_id": row["signal_id"],
        }
        if value_column is not None:
            left_value = row.get(f"{value_column}_{left_variant}")
            right_value = row.get(f"{value_column}_{right_variant}")
            payload[f"left_{value_column}"] = None if pd.isna(left_value) else float(left_value)
            payload[f"right_{value_column}"] = None if pd.isna(right_value) else float(right_value)
        payload["left_present"] = bool(row.get(f"present_{left_variant}", False))
        payload["right_present"] = bool(row.get(f"present_{right_variant}", False))
        if f"reject_reason_{left_variant}" in row.index:
            payload["left_reject_reason"] = row.get(f"reject_reason_{left_variant}")
        if f"reject_reason_{right_variant}" in row.index:
            payload["right_reject_reason"] = row.get(f"reject_reason_{right_variant}")
        samples.append(payload)
    return samples


def _compare_pair(left_variant: str, left_frame: pd.DataFrame, right_variant: str, right_frame: pd.DataFrame) -> dict[str, object]:
    compare_columns = ["signal_id", "signal_date", "code", "industry", "final_score", "final_rank", "selected"]
    left = left_frame[compare_columns].rename(
        columns={
            "signal_date": "signal_date",
            "code": "code",
            "industry": "industry",
            "final_score": f"final_score_{left_variant}",
            "final_rank": f"final_rank_{left_variant}",
            "selected": f"selected_{left_variant}",
        }
    )
    right = right_frame[compare_columns].rename(
        columns={
            "signal_date": "signal_date",
            "code": "code",
            "industry": "industry",
            "final_score": f"final_score_{right_variant}",
            "final_rank": f"final_rank_{right_variant}",
            "selected": f"selected_{right_variant}",
        }
    )
    merged = left.merge(
        right,
        on=["signal_id", "signal_date", "code", "industry"],
        how="outer",
        indicator=True,
    ).sort_values(["signal_date", "signal_id"], ascending=[True, True])

    shared_mask = merged["_merge"] == "both"
    left_only_mask = merged["_merge"] == "left_only"
    right_only_mask = merged["_merge"] == "right_only"
    rank_changed_mask = shared_mask & (
        merged[f"final_rank_{left_variant}"] != merged[f"final_rank_{right_variant}"]
    )
    score_changed_mask = shared_mask & (
        (
            merged[f"final_score_{left_variant}"] - merged[f"final_score_{right_variant}"]
        ).abs()
        > EPSILON
    )
    selected_changed_mask = shared_mask & (
        merged[f"selected_{left_variant}"] != merged[f"selected_{right_variant}"]
    )

    merged = merged.assign(
        rank_changed=rank_changed_mask,
        score_changed=score_changed_mask,
        selected_changed=selected_changed_mask,
    )

    per_signal_date: list[dict[str, object]] = []
    for signal_date, group in merged.groupby("signal_date", dropna=False):
        shared_count = int((group["_merge"] == "both").sum())
        date_payload: dict[str, object] = {
            "signal_date": str(signal_date),
            "shared_signal_count": shared_count,
            "left_only_count": int((group["_merge"] == "left_only").sum()),
            "right_only_count": int((group["_merge"] == "right_only").sum()),
            "rank_changed_count": int(group["rank_changed"].sum()),
            "score_changed_count": int(group["score_changed"].sum()),
            "selected_changed_count": int(group["selected_changed"].sum()),
            "is_multi_signal_date": shared_count >= 2,
        }
        changed_rows = group[
            (group["rank_changed"])
            | (group["score_changed"])
            | (group["selected_changed"])
            | (group["_merge"] != "both")
        ]
        if not changed_rows.empty:
            date_payload["sample_changes"] = _build_pair_samples(changed_rows, left_variant, right_variant)
        per_signal_date.append(date_payload)

    multi_signal_dates = [item for item in per_signal_date if bool(item["is_multi_signal_date"])]
    dates_with_rank_change = [item["signal_date"] for item in per_signal_date if int(item["rank_changed_count"]) > 0]
    dates_with_selected_change = [
        item["signal_date"] for item in per_signal_date if int(item["selected_changed_count"]) > 0
    ]
    dates_with_score_change = [item["signal_date"] for item in per_signal_date if int(item["score_changed_count"]) > 0]

    max_shared_signal_count = max((int(item["shared_signal_count"]) for item in per_signal_date), default=0)
    all_selected_stable = bool(
        shared_mask.sum() > 0
        and int(selected_changed_mask.sum()) == 0
        and merged.loc[shared_mask, f"selected_{left_variant}"].astype(bool).all()
        and merged.loc[shared_mask, f"selected_{right_variant}"].astype(bool).all()
    )

    if int(rank_changed_mask.sum()) == 0 and int(selected_changed_mask.sum()) == 0:
        if len(multi_signal_dates) == 0:
            conclusion = "所有 signal_date 都只有 1 条共享信号，排序层在该窗口内没有被真正触发。"
        elif int(score_changed_mask.sum()) > 0:
            conclusion = "分数发生变化，但最终名次与入选集合未变化。"
        else:
            conclusion = "分数、名次、入选集合都没有变化。"
    else:
        conclusion = "存在可观测的名次或入选集合变化，需要继续拆解收益来源。"

    return {
        "left_variant": left_variant,
        "right_variant": right_variant,
        "shared_signal_count": int(shared_mask.sum()),
        "left_only_count": int(left_only_mask.sum()),
        "right_only_count": int(right_only_mask.sum()),
        "rank_changed_count": int(rank_changed_mask.sum()),
        "score_changed_count": int(score_changed_mask.sum()),
        "selected_changed_count": int(selected_changed_mask.sum()),
        "signal_date_count": len(per_signal_date),
        "multi_signal_date_count": len(multi_signal_dates),
        "max_shared_signal_count_per_day": max_shared_signal_count,
        "all_shared_selected_stable": all_selected_stable,
        "dates_with_rank_change": dates_with_rank_change,
        "dates_with_score_change": dates_with_score_change,
        "dates_with_selected_change": dates_with_selected_change,
        "per_signal_date": per_signal_date,
        "conclusion": conclusion,
    }


def _compare_buy_trade_pair(
    left_variant: str,
    left_frame: pd.DataFrame,
    right_variant: str,
    right_frame: pd.DataFrame,
) -> dict[str, object]:
    left = left_frame.rename(
        columns={
            "quantity": f"quantity_{left_variant}",
            "price": f"price_{left_variant}",
        }
    )
    right = right_frame.rename(
        columns={
            "quantity": f"quantity_{right_variant}",
            "price": f"price_{right_variant}",
        }
    )
    merged = left.merge(
        right,
        on=["signal_id", "execute_date", "code", "pattern"],
        how="outer",
        indicator=True,
    ).sort_values(["execute_date", "signal_id"], ascending=[True, True])
    merged[f"present_{left_variant}"] = merged["_merge"].isin(["both", "left_only"])
    merged[f"present_{right_variant}"] = merged["_merge"].isin(["both", "right_only"])
    shared_mask = merged["_merge"] == "both"
    quantity_changed_mask = shared_mask & (
        merged[f"quantity_{left_variant}"] != merged[f"quantity_{right_variant}"]
    )
    price_changed_mask = shared_mask & (
        (merged[f"price_{left_variant}"] - merged[f"price_{right_variant}"]).abs() > EPSILON
    )
    merged = merged.assign(
        quantity_changed=quantity_changed_mask,
        price_changed=price_changed_mask,
    )
    per_execute_date: list[dict[str, object]] = []
    for execute_date, group in merged.groupby("execute_date", dropna=False):
        date_payload: dict[str, object] = {
            "execute_date": str(execute_date),
            "shared_buy_trade_count": int((group["_merge"] == "both").sum()),
            "left_only_count": int((group["_merge"] == "left_only").sum()),
            "right_only_count": int((group["_merge"] == "right_only").sum()),
            "quantity_changed_count": int(group["quantity_changed"].sum()),
            "price_changed_count": int(group["price_changed"].sum()),
        }
        changed_rows = group[
            (group["quantity_changed"]) | (group["price_changed"]) | (group["_merge"] != "both")
        ]
        if not changed_rows.empty:
            date_payload["sample_changes"] = _build_execution_samples(
                changed_rows,
                left_variant,
                right_variant,
                date_col="execute_date",
                value_column="quantity",
            )
        per_execute_date.append(date_payload)

    trade_set_change_count = int((merged["_merge"] != "both").sum())
    dates_with_trade_set_change = [
        item["execute_date"]
        for item in per_execute_date
        if int(item["left_only_count"]) > 0 or int(item["right_only_count"]) > 0
    ]
    dates_with_quantity_change = [
        item["execute_date"] for item in per_execute_date if int(item["quantity_changed_count"]) > 0
    ]
    if trade_set_change_count > 0 or int(quantity_changed_mask.sum()) > 0:
        conclusion = "BUY 成交集合或仓位数量发生变化，左右变体差异已进入执行约束。"
    elif int(price_changed_mask.sum()) > 0:
        conclusion = "BUY 成交集合未变，但左右变体的成交价格存在差异。"
    else:
        conclusion = "BUY 成交集合与仓位数量都未变化。"

    return {
        "left_variant": left_variant,
        "right_variant": right_variant,
        "shared_buy_trade_count": int(shared_mask.sum()),
        "left_only_count": int((merged["_merge"] == "left_only").sum()),
        "right_only_count": int((merged["_merge"] == "right_only").sum()),
        "trade_set_changed_count": trade_set_change_count,
        "quantity_changed_count": int(quantity_changed_mask.sum()),
        "price_changed_count": int(price_changed_mask.sum()),
        "execute_date_count": len(per_execute_date),
        "dates_with_trade_set_change": dates_with_trade_set_change,
        "dates_with_quantity_change": dates_with_quantity_change,
        "per_execute_date": per_execute_date,
        "conclusion": conclusion,
    }


def _compare_maxpos_reject_pair(
    left_variant: str,
    left_frame: pd.DataFrame,
    right_variant: str,
    right_frame: pd.DataFrame,
) -> dict[str, object]:
    left_maxpos = left_frame[left_frame["reject_reason"] == "MAX_POSITIONS_REACHED"].copy()
    right_maxpos = right_frame[right_frame["reject_reason"] == "MAX_POSITIONS_REACHED"].copy()
    left = left_maxpos.rename(columns={"reject_reason": f"reject_reason_{left_variant}"})
    right = right_maxpos.rename(columns={"reject_reason": f"reject_reason_{right_variant}"})
    merged = left.merge(
        right,
        on=["signal_id", "execute_date", "code"],
        how="outer",
        indicator=True,
    ).sort_values(["execute_date", "signal_id"], ascending=[True, True])
    merged[f"present_{left_variant}"] = merged["_merge"].isin(["both", "left_only"])
    merged[f"present_{right_variant}"] = merged["_merge"].isin(["both", "right_only"])

    per_execute_date: list[dict[str, object]] = []
    for execute_date, group in merged.groupby("execute_date", dropna=False):
        date_payload: dict[str, object] = {
            "execute_date": str(execute_date),
            "shared_reject_count": int((group["_merge"] == "both").sum()),
            "left_only_count": int((group["_merge"] == "left_only").sum()),
            "right_only_count": int((group["_merge"] == "right_only").sum()),
        }
        changed_rows = group[group["_merge"] != "both"]
        if not changed_rows.empty:
            date_payload["sample_changes"] = _build_execution_samples(
                changed_rows,
                left_variant,
                right_variant,
                date_col="execute_date",
            )
        per_execute_date.append(date_payload)

    reject_set_changed_count = int((merged["_merge"] != "both").sum())
    if reject_set_changed_count > 0:
        conclusion = "MAX_POSITIONS 拒单集合发生变化，左右变体差异已进入 Broker 风控边界。"
    else:
        conclusion = "MAX_POSITIONS 拒单集合未变化。"

    return {
        "left_variant": left_variant,
        "right_variant": right_variant,
        "shared_reject_count": int((merged["_merge"] == "both").sum()),
        "left_only_count": int((merged["_merge"] == "left_only").sum()),
        "right_only_count": int((merged["_merge"] == "right_only").sum()),
        "reject_set_changed_count": reject_set_changed_count,
        "execute_date_count": len(per_execute_date),
        "dates_with_reject_change": [
            item["execute_date"]
            for item in per_execute_date
            if int(item["left_only_count"]) > 0 or int(item["right_only_count"]) > 0
        ],
        "per_execute_date": per_execute_date,
        "conclusion": conclusion,
    }


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
    variants = _parse_variants(args.variants)
    if args.dtt_top_n is not None:
        cfg.dtt_top_n = int(args.dtt_top_n)
    if args.max_positions is not None:
        cfg.max_positions = int(args.max_positions)

    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"dtt-rank-decomp-{date.today():%Y%m%d}.duckdb"
    )
    db_file = prepare_working_db(source_db, working_db_path)
    artifact_root = (cfg.resolved_temp_path / "artifacts").resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)

    init_store = Store(db_file)
    try:
        # 先清一次，确保 working copy 里没有旧 run 遗留的 sidecar 噪音。
        _clear_runtime_tables(init_store, preserve_rank_exp=False)
    finally:
        init_store.close()

    if not args.skip_rebuild_l3:
        build_store = Store(db_file)
        try:
            build_layers(build_store, cfg, layers=["l3"], start=start, end=end, force=True)
        finally:
            build_store.close()

    run_summaries: list[dict[str, object]] = []
    rank_frames: dict[str, pd.DataFrame] = {}
    buy_trade_frames: dict[str, pd.DataFrame] = {}
    rejected_buy_frames: dict[str, pd.DataFrame] = {}
    for variant in variants:
        summary, rank_frame, buy_trade_frame, rejected_buy_frame = _run_variant(
            db_file=db_file,
            base_config=cfg,
            start=start,
            end=end,
            patterns=patterns or ["bof"],
            initial_cash=args.cash,
            variant=variant,
            artifact_root=artifact_root,
        )
        run_summaries.append(summary)
        rank_frames[variant] = rank_frame
        buy_trade_frames[variant] = buy_trade_frame
        rejected_buy_frames[variant] = rejected_buy_frame

    comparisons: dict[str, dict[str, object]] = {}
    for left_variant, right_variant in zip(variants, variants[1:], strict=False):
        key = f"{left_variant}_vs_{right_variant}"
        comparisons[key] = {
            "rank_impact": _compare_pair(
                left_variant,
                rank_frames[left_variant],
                right_variant,
                rank_frames[right_variant],
            ),
            "buy_trade_impact": _compare_buy_trade_pair(
                left_variant,
                buy_trade_frames[left_variant],
                right_variant,
                buy_trade_frames[right_variant],
            ),
            "maxpos_reject_impact": _compare_maxpos_reject_pair(
                left_variant,
                rejected_buy_frames[left_variant],
                right_variant,
                rejected_buy_frames[right_variant],
            ),
        }

    summary_run_id = build_run_id(
        scope="rank_decomposition",
        mode="dtt",
        variant=f"{variants[0]}_to_{variants[-1]}",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT
        / "docs"
        / "spec"
        / "v0.01-plus"
        / "evidence"
        / build_artifact_name(summary_run_id, "rank_decomposition", "json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "artifact_root": str(artifact_root),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns or ["bof"],
        "dtt_top_n": int(cfg.dtt_top_n),
        "max_positions": int(cfg.max_positions),
        "variants": variants,
        "runs": run_summaries,
        "comparisons": comparisons,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"rank_decomposition={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
