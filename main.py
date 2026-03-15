from __future__ import annotations

import argparse
from datetime import date

from src.backtest.engine import run_backtest
from src.broker.broker import Broker
from src.config import get_settings
from src.data.builder import build_layers
from src.data.fetcher import bootstrap_l1_from_raw_duckdb, create_fetcher, fetch_incremental
from src.data.store import Store
from src.logging_utils import configure_logger, logger
from src.run_metadata import finish_run, start_run
from src.selector.selector import select_candidates
from src.strategy.strategy import generate_signals


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def cmd_fetch(args: argparse.Namespace) -> int:
    cfg = get_settings()
    store = Store(cfg.db_path)
    start = _parse_date(args.start) or cfg.history_start
    end = _parse_date(args.end) or date.today()
    artifact_root = str((cfg.resolved_temp_path / "fetch").resolve())
    run = start_run(
        store=store,
        scope="fetch",
        modules=["fetch"],
        config=cfg,
        runtime_env="cli",
        artifact_root=artifact_root,
        start=start,
        end=end,
    )
    try:
        raw_db_path = args.from_raw_db or cfg.raw_db_path.strip() or None

        if args.refresh_stock_info_only and not raw_db_path:
            raise ValueError("--refresh-stock-info-only requires --from-raw-db or RAW_DB_PATH.")

        if raw_db_path:
            result = bootstrap_l1_from_raw_duckdb(
                store=store,
                source_db=raw_db_path,
                start=start,
                end=end,
                refresh_stock_info_only=args.refresh_stock_info_only,
            )
            logger.info(
                "fetch raw bootstrap completed: "
                f"source={result.source_db}, trade_cal={result.trade_calendar_rows}, "
                f"stock_daily={result.stock_daily_rows}, index_daily={result.index_daily_rows}, "
                f"stock_info={result.stock_info_rows}, sw_industry_member={result.sw_industry_member_rows}, "
                f"stock_info_effective_range={result.stock_info_effective_from_min}.."
                f"{result.stock_info_effective_from_max}"
            )
            finish_run(store, run.run_id, "SUCCESS")
            return 0

        fetcher = create_fetcher(cfg)
        total = 0
        # 先拉交易日历，再拉其他表，确保 T+1 / next_trade_date 有基准。
        total += fetch_incremental(store, fetcher, "trade_cal", "l1_trade_calendar", start, end)
        total += fetch_incremental(store, fetcher, "stock_info", "l1_stock_info", start, end)
        total += fetch_incremental(store, fetcher, "sw_industry_member", "l1_sw_industry_member", start, end)
        total += fetch_incremental(store, fetcher, "index_daily", "l1_index_daily", start, end)
        total += fetch_incremental(store, fetcher, "stock_daily", "l1_stock_daily", start, end)
        logger.info(f"fetch completed, written rows={total}")
        finish_run(store, run.run_id, "SUCCESS")
        return 0
    except Exception as exc:
        logger.exception("fetch failed")
        finish_run(store, run.run_id, "FAILED", str(exc))
        return 1
    finally:
        store.close()


def cmd_build(args: argparse.Namespace) -> int:
    cfg = get_settings()
    store = Store(cfg.db_path)
    layers = [part.strip() for part in args.layers.split(",") if part.strip()]
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    artifact_root = str((cfg.resolved_temp_path / "build").resolve())
    run = start_run(
        store=store,
        scope="build",
        modules=["build"] + layers,
        config=cfg,
        runtime_env="cli",
        artifact_root=artifact_root,
        start=start,
        end=end,
    )
    try:
        written = build_layers(
            store=store,
            config=cfg,
            layers=layers,
            start=start,
            end=end,
            force=args.force,
        )
        logger.info(f"build completed, upsert rows={written}")
        finish_run(store, run.run_id, "SUCCESS")
        return 0
    except Exception as exc:
        logger.exception("build failed")
        finish_run(store, run.run_id, "FAILED", str(exc))
        return 1
    finally:
        store.close()


def cmd_run(args: argparse.Namespace) -> int:
    cfg = get_settings()
    store = Store(cfg.db_path)
    run = None
    try:
        trade_date = _parse_date(args.trade_date) or date.today()

        # 1) 先增量拉取交易日历，再确定 signal_date，避免“无日历无法推进 T+1”。
        fetcher = create_fetcher(cfg)
        cal_start = trade_date.replace(day=1)
        fetch_incremental(store, fetcher, "trade_cal", "l1_trade_calendar", cal_start, trade_date)
        signal_date = store.prev_trade_date(trade_date)
        if signal_date is None:
            raise RuntimeError("Cannot resolve signal_date from trade calendar.")
        artifact_root = str((cfg.resolved_temp_path / "daily").resolve())
        run = start_run(
            store=store,
            scope="daily",
            modules=["run", "fetch", "build", "selector", "strategy", "broker"],
            config=cfg,
            runtime_env="cli",
            artifact_root=artifact_root,
            signal_date=signal_date,
        )

        # 2) 增量拉取 L1，确保当日与前一交易日数据可用。
        fetch_incremental(store, fetcher, "stock_info", "l1_stock_info", signal_date, trade_date)
        fetch_incremental(store, fetcher, "sw_industry_member", "l1_sw_industry_member", signal_date, trade_date)
        fetch_incremental(store, fetcher, "index_daily", "l1_index_daily", signal_date, trade_date)
        fetch_incremental(store, fetcher, "stock_daily", "l1_stock_daily", signal_date, trade_date)

        # 3) 构建 L2/L3（MSS/IRS/Gene），信号仍由运行时 Strategy 产生。
        build_layers(store, cfg, layers=["l2", "l3"], start=signal_date, end=trade_date, force=False)

        # 4) 在 T 日收盘后（signal_date）选股并生成信号。
        candidates = select_candidates(store, signal_date, cfg)
        signals = generate_signals(store, candidates, signal_date, cfg, run_id=run.run_id)

        # 5) Broker 在 T+1（trade_date）执行撮合，并处理过期订单。
        broker = Broker(store, cfg)
        broker.process_signals(signals)
        trades = broker.execute_pending_orders(trade_date)
        expired = broker.expire_orders(trade_date)

        logger.info(
            f"run completed: trade_date={trade_date}, candidates={len(candidates)}, "
            f"signals={len(signals)}, trades={len(trades)}, expired={expired}"
        )
        finish_run(store, run.run_id, "SUCCESS")
        return 0
    except Exception as exc:
        logger.exception("run failed")
        if run is not None:
            finish_run(store, run.run_id, "FAILED", str(exc))
        return 1
    finally:
        store.close()


def cmd_backtest(args: argparse.Namespace) -> int:
    cfg = get_settings()
    store = Store(cfg.db_path)
    start = _parse_date(args.start) or cfg.history_start
    end = _parse_date(args.end) or date.today()
    artifact_root = str((cfg.resolved_temp_path / "backtest").resolve())
    run = start_run(
        store=store,
        scope="backtest",
        modules=["backtest", "selector", "strategy", "broker", "report"],
        config=cfg,
        runtime_env="cli",
        artifact_root=artifact_root,
        start=start,
        end=end,
    )
    try:
        patterns = [part.strip().lower() for part in (args.patterns or "").split(",") if part.strip()]
        result = run_backtest(
            db_path=cfg.db_path,
            config=cfg,
            start=start,
            end=end,
            patterns=patterns or None,
            initial_cash=args.cash,
            run_id=run.run_id,
        )
        logger.info(
            "backtest done: "
            f"days={result.trade_days}, trade_count={result.trade_count}, "
            f"EV={result.expected_value:.6f}, PF={result.profit_factor}, MDD={result.max_drawdown:.6f}"
        )
        finish_run(store, run.run_id, "SUCCESS")
        return 0
    except Exception as exc:
        logger.exception("backtest failed")
        finish_run(store, run.run_id, "FAILED", str(exc))
        return 1
    finally:
        store.close()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EmotionQuant CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Fetch L1 data")
    fetch.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    fetch.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    fetch.add_argument(
        "--from-raw-db",
        type=str,
        default=None,
        help="Bootstrap L1 tables from a local raw DuckDB instead of remote APIs",
    )
    fetch.add_argument(
        "--refresh-stock-info-only",
        action="store_true",
        help="When bootstrapping from raw DB, refresh only l1_stock_info snapshots",
    )
    fetch.set_defaults(func=cmd_fetch)

    build = sub.add_parser("build", help="Build L2/L3 data")
    build.add_argument("--layers", type=str, default="l2", help="Comma-separated layers: l2,l3,all")
    build.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    build.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    build.add_argument("--force", action="store_true", help="Force rebuild target layers")
    build.set_defaults(func=cmd_build)

    backtest = sub.add_parser("backtest", help="Run backtest")
    backtest.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    backtest.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    backtest.add_argument("--patterns", type=str, default="bof", help="Comma-separated patterns")
    backtest.add_argument("--cash", type=float, default=1_000_000, help="Initial cash")
    backtest.set_defaults(func=cmd_backtest)

    run = sub.add_parser("run", help="Run daily full pipeline (Week4)")
    run.add_argument("--trade-date", type=str, default=None, help="Execution date (YYYY-MM-DD)")
    run.set_defaults(func=cmd_run)

    return parser


def main() -> int:
    cfg = get_settings()
    configure_logger(cfg.resolved_log_path / "emotionquant.log", cfg.log_level)
    parser = create_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
