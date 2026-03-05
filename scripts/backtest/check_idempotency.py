from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.engine import run_backtest
from src.config import get_settings
from src.data.store import Store


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _to_jsonable(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


def _snapshot(store: Store, start: date, end: date) -> dict:
    orders = store.read_df(
        "SELECT order_id FROM l4_orders WHERE execute_date BETWEEN ? AND ? ORDER BY order_id",
        (start, end),
    )
    trades = store.read_df(
        "SELECT trade_id FROM l4_trades WHERE execute_date BETWEEN ? AND ? ORDER BY trade_id",
        (start, end),
    )
    report = store.read_df(
        """
        SELECT expected_value, profit_factor, max_drawdown, trades_count,
               reject_rate, missing_rate, exposure_rate, failure_reason_breakdown
        FROM l4_daily_report WHERE date = ? LIMIT 1
        """,
        (end,),
    )
    metrics = {}
    if not report.empty:
        row = report.iloc[0]
        metrics = {
            "expected_value": float(row["expected_value"] or 0.0),
            "profit_factor": float(row["profit_factor"] or 0.0),
            "max_drawdown": float(row["max_drawdown"] or 0.0),
            "trades_count": int(row["trades_count"] or 0),
            "reject_rate": float(row.get("reject_rate", 0.0) or 0.0),
            "missing_rate": float(row.get("missing_rate", 0.0) or 0.0),
            "exposure_rate": float(row.get("exposure_rate", 0.0) or 0.0),
            "failure_reason_breakdown": str(row.get("failure_reason_breakdown", "") or ""),
        }

    return {
        "order_ids": set(orders["order_id"].tolist()),
        "trade_ids": set(trades["trade_id"].tolist()),
        "metrics": metrics,
    }


def _clear_runtime_tables(store: Store) -> None:
    for t in ["l4_pattern_stats", "l4_daily_report", "l4_trades", "l4_orders", "l3_signals"]:
        store.conn.execute(f"DELETE FROM {t}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run backtest twice and verify idempotency")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--patterns", default="bof")
    p.add_argument("--cash", type=float, default=1_000_000)
    p.add_argument("--min-amount", type=float, default=None)
    p.add_argument("--output", default="docs/spec/v0.01/v0.01-idempotency-check-latest.json")
    return p


def main() -> int:
    args = build_parser().parse_args()
    start = _parse_date(args.start)
    end = _parse_date(args.end)

    cfg = get_settings().model_copy(deep=True)
    if args.min_amount is not None:
        cfg.min_amount = args.min_amount

    patterns = [p.strip().lower() for p in args.patterns.split(",") if p.strip()]

    store = Store(cfg.db_path)
    _clear_runtime_tables(store)
    store.close()

    first = run_backtest(
        db_path=cfg.db_path,
        config=cfg,
        start=start,
        end=end,
        patterns=patterns,
        initial_cash=args.cash,
    )
    s1 = Store(cfg.db_path)
    snap1 = _snapshot(s1, start, end)
    s1.close()

    sclr = Store(cfg.db_path)
    _clear_runtime_tables(sclr)
    sclr.close()

    second = run_backtest(
        db_path=cfg.db_path,
        config=cfg,
        start=start,
        end=end,
        patterns=patterns,
        initial_cash=args.cash,
    )
    s2 = Store(cfg.db_path)
    snap2 = _snapshot(s2, start, end)
    s2.close()

    key_equal = (snap1["order_ids"] == snap2["order_ids"]) and (snap1["trade_ids"] == snap2["trade_ids"])
    metrics_equal = snap1["metrics"] == snap2["metrics"]

    out = {
        "start": args.start,
        "end": args.end,
        "patterns": patterns,
        "cash": args.cash,
        "min_amount": args.min_amount,
        "first": _to_jsonable(asdict(first)),
        "second": _to_jsonable(asdict(second)),
        "order_id_set_equal": key_equal,
        "trade_id_set_equal": snap1["trade_ids"] == snap2["trade_ids"],
        "metrics_equal": metrics_equal,
        "first_metrics": snap1["metrics"],
        "second_metrics": snap2["metrics"],
        "order_count_1": len(snap1["order_ids"]),
        "order_count_2": len(snap2["order_ids"]),
        "trade_count_1": len(snap1["trade_ids"]),
        "trade_count_2": len(snap2["trade_ids"]),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_to_jsonable(out), ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(_to_jsonable(out), ensure_ascii=False, indent=2))
    return 0 if key_equal and metrics_equal else 2


if __name__ == "__main__":
    raise SystemExit(main())
