from __future__ import annotations

"""检查特定交易日的 raw/L1/L2 覆盖异常。

这不是日更脚本，而是诊断脚本。适合在怀疑某天漏数、错数时运行。
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.data.store import Store
from src.run_metadata import build_artifact_name, build_run_id, resolve_mode_variant


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _normalize_date(value: object) -> date | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date()  # pandas.Timestamp / datetime 统一转成 date
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit coverage anomalies for selected trade dates")
    parser.add_argument(
        "--dates",
        nargs="+",
        required=True,
        help="Trade dates to audit, e.g. 2026-02-10 2026-02-11 2026-02-13",
    )
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument("--raw-db-path", default=None, help="Raw source DuckDB path override")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__coverage_audit.json",
    )
    return parser


def _context_dates(store: Store, focus_dates: list[date]) -> list[date]:
    calendar = store.read_df(
        """
        SELECT date, prev_trade_day, next_trade_day
        FROM l1_trade_calendar
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (min(focus_dates), max(focus_dates)),
    )
    related: set[date] = set(focus_dates)
    for _, row in calendar.iterrows():
        trade_date = _normalize_date(row["date"])
        if trade_date in focus_dates:
            related.add(trade_date)
            prev_day = _normalize_date(row["prev_trade_day"])
            next_day = _normalize_date(row["next_trade_day"])
            if prev_day is not None:
                related.add(prev_day)
            if next_day is not None:
                related.add(next_day)
    return sorted(related)


def _query_execution_counts(store: Store, trade_date: date) -> dict[str, int]:
    return {
        "l1_stock_daily": int(
            store.read_scalar("SELECT COUNT(*) FROM l1_stock_daily WHERE date = ?", (trade_date,)) or 0
        ),
        "l2_stock_adj_daily": int(
            store.read_scalar("SELECT COUNT(*) FROM l2_stock_adj_daily WHERE date = ?", (trade_date,)) or 0
        ),
        "l2_industry_daily": int(
            store.read_scalar("SELECT COUNT(*) FROM l2_industry_daily WHERE date = ?", (trade_date,)) or 0
        ),
        "l3_mss_daily": int(
            store.read_scalar("SELECT COUNT(*) FROM l3_mss_daily WHERE date = ?", (trade_date,)) or 0
        ),
        "l3_irs_daily": int(
            store.read_scalar("SELECT COUNT(*) FROM l3_irs_daily WHERE date = ?", (trade_date,)) or 0
        ),
    }


def _query_raw_counts(raw_conn: duckdb.DuckDBPyConnection, trade_date: date) -> dict[str, int]:
    trade_key = trade_date.strftime("%Y%m%d")
    return {
        "raw_daily": int(
            raw_conn.execute("SELECT COUNT(*) FROM raw_daily WHERE trade_date = ?", [trade_key]).fetchone()[0]
        ),
        "raw_daily_basic": int(
            raw_conn.execute(
                "SELECT COUNT(*) FROM raw_daily_basic WHERE trade_date = ?",
                [trade_key],
            ).fetchone()[0]
        ),
    }


def _sample_codes(raw_conn: duckdb.DuckDBPyConnection, trade_date: date) -> list[str]:
    trade_key = trade_date.strftime("%Y%m%d")
    rows = raw_conn.execute(
        """
        SELECT ts_code
        FROM raw_daily
        WHERE trade_date = ?
        ORDER BY ts_code
        LIMIT 64
        """,
        [trade_key],
    ).fetchall()
    return [str(row[0]) for row in rows]


def _market_distribution(store: Store, trade_date: date) -> list[dict[str, object]]:
    rows = store.read_df(
        """
        SELECT
            COALESCE(info.market, 'NULL') AS market,
            COUNT(*) AS stock_count
        FROM l1_stock_daily sd
        LEFT JOIN l1_stock_info info
            ON info.ts_code = sd.ts_code
           AND info.effective_from = (
               SELECT MAX(effective_from)
               FROM l1_stock_info i2
               WHERE i2.ts_code = sd.ts_code
                 AND i2.effective_from <= sd.date
           )
        WHERE sd.date = ?
        GROUP BY 1
        ORDER BY 2 DESC, 1 ASC
        """,
        (trade_date,),
    )
    return rows.to_dict(orient="records")


def _diagnose(
    focus_dates: list[date],
    execution_counts: dict[date, dict[str, int]],
    raw_counts: dict[date, dict[str, int]],
) -> str:
    if all(
        execution_counts[trade_date]["l1_stock_daily"] == raw_counts[trade_date]["raw_daily"] > 1000
        for trade_date in focus_dates
    ):
        return (
            "raw 源库与执行库在焦点日期已经重新对齐。"
            " 当前不再存在 31 行截断；若后续回测结果仍异常，应优先检查 DTT 执行约束与参数灵敏度。"
        )
    for trade_date in focus_dates:
        exec_daily = execution_counts[trade_date]["l1_stock_daily"]
        raw_daily = raw_counts[trade_date]["raw_daily"]
        if raw_daily == exec_daily == 31:
            return (
                "异常根因在 raw 源库，不在 Selector。"
                " 这几天 raw_daily/raw_daily_basic 仅有 31 行，执行库只是如实镜像；"
                "L2 与 IRS 的覆盖坍缩是上游原始日线快照被截断后的连锁结果。"
            )
    return "未发现 raw/execution 的同步截断，需要继续排查 builder 或清洗链。"


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings()
    focus_dates = sorted({_parse_date(item) for item in args.dates})
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    raw_db_path = (
        Path(args.raw_db_path).expanduser().resolve()
        if args.raw_db_path
        else cfg.resolved_data_path / "duckdb" / "emotionquant.duckdb"
    )

    store = Store(db_path)
    context_dates = _context_dates(store, focus_dates)
    execution_counts = {trade_date: _query_execution_counts(store, trade_date) for trade_date in context_dates}
    market_counts = {trade_date: _market_distribution(store, trade_date) for trade_date in focus_dates}
    store.close()

    raw_conn = duckdb.connect(str(raw_db_path), read_only=True)
    raw_counts = {trade_date: _query_raw_counts(raw_conn, trade_date) for trade_date in context_dates}
    code_samples = {trade_date: _sample_codes(raw_conn, trade_date) for trade_date in focus_dates}
    raw_conn.close()

    mode, variant = resolve_mode_variant(cfg)
    run_id = build_run_id(
        scope="coverage_audit",
        mode=mode,
        variant=variant,
        start=min(focus_dates),
        end=max(focus_dates),
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT
        / "docs"
        / "spec"
        / "v0.01-plus"
        / "evidence"
        / build_artifact_name(run_id, "coverage_audit", "json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "run_id": run_id,
        "db_path": str(db_path),
        "raw_db_path": str(raw_db_path),
        "focus_dates": [item.isoformat() for item in focus_dates],
        "context_dates": [item.isoformat() for item in context_dates],
        "execution_counts": {item.isoformat(): execution_counts[item] for item in context_dates},
        "raw_counts": {item.isoformat(): raw_counts[item] for item in context_dates},
        "market_distribution": {item.isoformat(): market_counts[item] for item in focus_dates},
        "sample_ts_codes": {item.isoformat(): code_samples[item] for item in focus_dates},
        "diagnosis": _diagnose(focus_dates, execution_counts, raw_counts),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"coverage_audit={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
