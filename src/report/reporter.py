from __future__ import annotations

import json
from collections import deque
from datetime import date

import pandas as pd

from src.config import Settings
from src.data.store import Store
from src.logging_utils import logger


def _load_trades(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT
            trade_id,
            order_id,
            code,
            execute_date,
            action,
            price,
            quantity,
            fee,
            pattern,
            is_paper,
            position_id,
            exit_plan_id,
            exit_leg_id,
            exit_leg_seq,
            exit_reason_code,
            is_partial_exit,
            remaining_qty_after
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date, trade_id
        """,
        (start, end),
    )


def _pair_trades(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    FIFO 数量配对：支持分批买入/分批卖出。
    每笔 paired 结果均为净口径（已扣买卖两侧手续费分摊）。
    """
    if trades_df.empty:
        return pd.DataFrame(
            columns=[
                "code",
                "entry_date",
                "exit_date",
                "pattern",
                "quantity",
                "pnl",
                "pnl_pct",
                "position_id",
                "entry_leg_id",
                "exit_leg_id",
                "exit_leg_seq",
                "exit_reason",
                "is_partial_exit",
            ]
        )

    pairs: list[dict] = []
    normalized = trades_df.copy()
    for column, default in (
        ("position_id", None),
        ("exit_leg_id", None),
        ("exit_leg_seq", None),
        ("exit_reason_code", None),
        ("is_partial_exit", False),
    ):
        if column not in normalized.columns:
            normalized[column] = default
    normalized["position_key"] = normalized["position_id"].fillna(normalized["code"])
    for position_key, group in normalized.groupby("position_key"):
        ordered = group.sort_values(["execute_date", "trade_id"])
        buy_queue: deque[dict[str, object]] = deque()

        for row in ordered.itertuples(index=False):
            qty = int(row.quantity)
            if qty <= 0:
                continue

            if str(row.action).upper() == "BUY":
                buy_queue.append(
                    {
                        "remaining_qty": qty,
                        "original_qty": qty,
                        "price": float(row.price),
                        "fee": float(row.fee or 0.0),
                        "entry_date": row.execute_date,
                        "pattern": row.pattern,
                        "position_id": row.position_id,
                        "entry_trade_id": row.trade_id,
                    }
                )
                continue

            sell_qty_left = qty
            sell_price = float(row.price)
            sell_fee = float(row.fee or 0.0)
            while sell_qty_left > 0 and buy_queue:
                buy = buy_queue[0]
                matched_qty = min(sell_qty_left, int(buy["remaining_qty"]))
                buy_fee_alloc = buy["fee"] * (matched_qty / buy["original_qty"])
                sell_fee_alloc = sell_fee * (matched_qty / qty)

                pnl = (sell_price - buy["price"]) * matched_qty - buy_fee_alloc - sell_fee_alloc
                notional = buy["price"] * matched_qty
                pnl_pct = pnl / notional if notional > 0 else 0.0

                pairs.append(
                    {
                        "code": row.code,
                        "entry_date": buy["entry_date"],
                        "exit_date": row.execute_date,
                        "pattern": buy["pattern"],
                        "quantity": matched_qty,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "position_id": buy["position_id"] or row.position_id or position_key,
                        "entry_leg_id": buy["entry_trade_id"],
                        "entry_trade_id": buy["entry_trade_id"],
                        "exit_trade_id": row.trade_id,
                        "exit_leg_id": row.exit_leg_id,
                        "exit_leg_seq": row.exit_leg_seq,
                        "exit_reason": row.exit_reason_code,
                        "is_partial_exit": bool(row.is_partial_exit),
                    }
                )

                buy["remaining_qty"] -= matched_qty
                sell_qty_left -= matched_qty
                if buy["remaining_qty"] <= 0:
                    buy_queue.popleft()

    if not pairs:
        return pd.DataFrame(
            columns=[
                "code",
                "entry_date",
                "exit_date",
                "pattern",
                "quantity",
                "pnl",
                "pnl_pct",
                "position_id",
                "entry_leg_id",
                "exit_leg_id",
                "exit_leg_seq",
                "exit_reason",
                "is_partial_exit",
            ]
        )
    return pd.DataFrame(pairs)


def _compute_expectation(paired: pd.DataFrame) -> dict[str, float]:
    if paired.empty:
        return {
            "trade_count": 0.0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "expected_value": 0.0,
        }

    wins = paired[paired["pnl_pct"] > 0]
    losses = paired[paired["pnl_pct"] <= 0]
    total = float(len(paired))
    win_rate = float(len(wins) / total)
    avg_win = float(wins["pnl_pct"].mean()) if not wins.empty else 0.0
    avg_loss = float(abs(losses["pnl_pct"].mean())) if not losses.empty else 0.0
    if avg_loss == 0:
        profit_factor = float("inf")
    else:
        profit_factor = float(avg_win / avg_loss)
    expected_value = float(win_rate * avg_win - (1 - win_rate) * avg_loss)

    return {
        "trade_count": total,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "expected_value": expected_value,
    }


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_peak = equity.cummax()
    drawdown = (running_peak - equity) / running_peak.replace(0, pd.NA)
    drawdown = drawdown.fillna(0.0)
    return float(drawdown.max())


def _load_orders(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT order_id, signal_id, execute_date, action, status, reject_reason, is_paper
        FROM l4_orders
        WHERE execute_date BETWEEN ? AND ?
        ORDER BY execute_date, order_id
        """,
        (start, end),
    )


def _compute_failure_reason_breakdown(orders_df: pd.DataFrame) -> dict[str, int]:
    if orders_df.empty:
        return {}
    failed = orders_df[orders_df["status"].isin(["REJECTED", "EXPIRED"])].copy()
    if failed.empty:
        return {}
    failed["reason_key"] = failed["reject_reason"].fillna(failed["status"]).replace("", "UNKNOWN")
    grouped = failed.groupby("reason_key").size().sort_values(ascending=False)
    return {str(k): int(v) for k, v in grouped.items()}


def _compute_exposure_rate(store: Store, start: date, end: date) -> float:
    # 暴露率定义：窗口内“有真实持仓”的交易日占比。
    calendar = store.read_df(
        """
        SELECT date
        FROM l1_trade_calendar
        WHERE is_trade_day = TRUE AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start, end),
    )
    if calendar.empty:
        return 0.0

    trades = store.read_df(
        """
        SELECT execute_date, action, quantity
        FROM l4_trades
        WHERE execute_date BETWEEN ? AND ? AND is_paper = FALSE
        ORDER BY execute_date
        """,
        (start, end),
    )
    if trades.empty:
        return 0.0

    daily_delta = (
        trades.assign(delta=trades["quantity"] * trades["action"].map({"BUY": 1, "SELL": -1}).fillna(0))
        .groupby("execute_date", as_index=False)["delta"]
        .sum()
    )
    merged = calendar.merge(daily_delta, left_on="date", right_on="execute_date", how="left")
    merged["delta"] = merged["delta"].fillna(0)
    merged["position_qty"] = merged["delta"].cumsum()
    exposed_days = int((merged["position_qty"] > 0).sum())
    total_days = int(len(merged))
    return float(exposed_days / total_days) if total_days > 0 else 0.0


def _compute_opportunity_metrics(orders_df: pd.DataFrame, signals_count: int) -> dict[str, float]:
    if orders_df.empty:
        return {
            "opportunity_count": float(signals_count),
            "filled_count": 0.0,
            "skip_cash_count": 0.0,
            "skip_maxpos_count": 0.0,
            "participation_rate": 0.0,
        }

    buy_orders = orders_df[orders_df["action"] == "BUY"].copy()
    filled_count = int((buy_orders["status"] == "FILLED").sum()) if not buy_orders.empty else 0
    skip_cash_count = (
        int(
            (
                (buy_orders["status"] == "REJECTED")
                & (
                    buy_orders["reject_reason"].isin(
                        ["INSUFFICIENT_CASH", "INSUFFICIENT_CASH_AT_EXECUTION"]
                    )
                )
            ).sum()
        )
        if not buy_orders.empty
        else 0
    )
    skip_maxpos_count = (
        int(
            (
                (buy_orders["status"] == "REJECTED")
                & (buy_orders["reject_reason"] == "MAX_POSITIONS_REACHED")
            ).sum()
        )
        if not buy_orders.empty
        else 0
    )

    opportunity_count = int(signals_count)
    participation_rate = float(filled_count / opportunity_count) if opportunity_count > 0 else 0.0
    return {
        "opportunity_count": float(opportunity_count),
        "filled_count": float(filled_count),
        "skip_cash_count": float(skip_cash_count),
        "skip_maxpos_count": float(skip_maxpos_count),
        "participation_rate": float(participation_rate),
    }


def _attach_entry_environment(store: Store, paired: pd.DataFrame) -> pd.DataFrame:
    if paired.empty:
        out = paired.copy()
        out["signal_date"] = pd.NaT
        out["market_environment"] = "UNKNOWN"
        out["market_score"] = None
        return out

    tagged = paired.copy()
    tagged["entry_date"] = pd.to_datetime(tagged["entry_date"]).dt.normalize()
    start = tagged["entry_date"].min().date()
    end = tagged["entry_date"].max().date()

    calendar = store.read_df(
        """
        SELECT date, prev_trade_day
        FROM l1_trade_calendar
        WHERE date BETWEEN ? AND ?
        """,
        (start, end),
    )
    if calendar.empty:
        tagged["signal_date"] = pd.NaT
        tagged["market_environment"] = "UNKNOWN"
        tagged["market_score"] = None
        return tagged

    calendar["date"] = pd.to_datetime(calendar["date"]).dt.normalize()
    calendar["signal_date"] = pd.to_datetime(calendar["prev_trade_day"]).dt.normalize()
    tagged = tagged.merge(calendar[["date", "signal_date"]], left_on="entry_date", right_on="date", how="left")
    tagged = tagged.drop(columns=["date"])

    signal_dates = tagged["signal_date"].dropna()
    if signal_dates.empty:
        tagged["market_environment"] = "UNKNOWN"
        tagged["market_score"] = None
        return tagged

    mss = store.read_df(
        """
        SELECT date, signal, score
        FROM l3_mss_daily
        WHERE date BETWEEN ? AND ?
        """,
        (signal_dates.min().date(), signal_dates.max().date()),
    )
    if mss.empty:
        tagged["market_environment"] = "UNKNOWN"
        tagged["market_score"] = None
        return tagged

    mss["signal_date"] = pd.to_datetime(mss["date"]).dt.normalize()
    tagged = tagged.merge(mss[["signal_date", "signal", "score"]], on="signal_date", how="left")
    tagged["market_environment"] = tagged["signal"].fillna("UNKNOWN")
    tagged["market_score"] = pd.to_numeric(tagged["score"], errors="coerce")
    return tagged.drop(columns=["signal", "score"])


def _compute_environment_breakdown(store: Store, paired: pd.DataFrame) -> dict[str, dict[str, float]]:
    tagged = _attach_entry_environment(store, paired)
    if tagged.empty:
        return {}

    breakdown: dict[str, dict[str, float]] = {}
    for env in ("BULLISH", "NEUTRAL", "BEARISH", "UNKNOWN"):
        group = tagged[tagged["market_environment"] == env].copy()
        if group.empty:
            continue
        exp = _compute_expectation(group)
        breakdown[env] = {
            "trade_count": float(len(group)),
            "win_rate": float(exp["win_rate"]),
            "avg_win": float(exp["avg_win"]),
            "avg_loss": float(exp["avg_loss"]),
            "profit_factor": float(exp["profit_factor"]),
            "expected_value": float(exp["expected_value"]),
            "median_pnl_pct": float(group["pnl_pct"].median()),
        }
    return breakdown


def generate_backtest_report(
    store: Store,
    config: Settings,
    start: date,
    end: date,
    initial_cash: float,
) -> dict:
    """
    生成最小实验证据：EV / PF / MDD / trade_count。
    结果会回写 l4_daily_report，便于后续 Gate 对照。
    """
    trades = _load_trades(store, start, end)
    orders = _load_orders(store, start, end)
    paired = _pair_trades(trades)
    exp = _compute_expectation(paired)

    if paired.empty:
        max_dd = 0.0
    else:
        equity = initial_cash + paired["pnl"].cumsum()
        max_dd = _max_drawdown(equity)

    trade_count = int(exp["trade_count"])
    profit_factor = exp["profit_factor"]
    expected_value = exp["expected_value"]

    signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    trades_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l4_trades WHERE execute_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    orders_count = int(len(orders))
    rejected_count = int((orders["status"] == "REJECTED").sum()) if not orders.empty else 0
    missing_count = (
        int(((orders["status"] == "REJECTED") & (orders["reject_reason"] == "NO_MARKET_DATA")).sum())
        if not orders.empty
        else 0
    )
    reject_rate = float(rejected_count / orders_count) if orders_count > 0 else 0.0
    missing_rate = float(missing_count / orders_count) if orders_count > 0 else 0.0
    exposure_rate = _compute_exposure_rate(store, start, end)
    failure_breakdown = _compute_failure_reason_breakdown(orders)
    opportunity = _compute_opportunity_metrics(orders, signals_count)
    environment_breakdown = _compute_environment_breakdown(store, paired)

    row = pd.DataFrame(
        [
            {
                "date": end,
                "candidates_count": None,
                "signals_count": signals_count,
                "trades_count": trades_count,
                "win_rate": exp["win_rate"],
                "avg_win": exp["avg_win"],
                "avg_loss": exp["avg_loss"],
                "profit_factor": profit_factor,
                "expected_value": expected_value,
                "max_drawdown": max_dd,
                "max_consecutive_loss": None,
                "skewness": None,
                "rolling_ev_30d": None,
                "sharpe_30d": None,
                "reject_rate": reject_rate,
                "missing_rate": missing_rate,
                "exposure_rate": exposure_rate,
                "failure_reason_breakdown": json.dumps(failure_breakdown, ensure_ascii=False),
                "opportunity_count": int(opportunity["opportunity_count"]),
                "filled_count": int(opportunity["filled_count"]),
                "skip_cash_count": int(opportunity["skip_cash_count"]),
                "skip_maxpos_count": int(opportunity["skip_maxpos_count"]),
                "participation_rate": float(opportunity["participation_rate"]),
            }
        ]
    )
    store.bulk_upsert("l4_daily_report", row)

    logger.info(
            "backtest summary: "
            f"range={start}..{end}, trade_count={trade_count}, EV={expected_value:.6f}, "
            f"PF={profit_factor}, MDD={max_dd:.6f}, reject_rate={reject_rate:.6f}, "
            f"missing_rate={missing_rate:.6f}, exposure_rate={exposure_rate:.6f}, "
            f"participation_rate={opportunity['participation_rate']:.6f}"
    )

    return {
        "trade_count": float(trade_count),
        "win_rate": float(exp["win_rate"]),
        "avg_win": float(exp["avg_win"]),
        "avg_loss": float(exp["avg_loss"]),
        "expected_value": float(expected_value),
        "profit_factor": float(profit_factor),
        "max_drawdown": float(max_dd),
        "reject_rate": float(reject_rate),
        "missing_rate": float(missing_rate),
        "exposure_rate": float(exposure_rate),
        "opportunity_count": float(opportunity["opportunity_count"]),
        "filled_count": float(opportunity["filled_count"]),
        "skip_cash_count": float(opportunity["skip_cash_count"]),
        "skip_maxpos_count": float(opportunity["skip_maxpos_count"]),
        "participation_rate": float(opportunity["participation_rate"]),
        "environment_breakdown": environment_breakdown,
    }
