from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.backtest.engine import run_backtest
from src.config import Settings, get_settings
from src.data.store import Store
from src.report.reporter import _load_orders, _load_trades, _pair_trades


@dataclass(frozen=True)
class YearWindow:
    year: int
    start: date | None
    end: date | None
    available: bool
    note: str


def _get_min_date(store: Store, table: str, date_col: str = "date") -> date | None:
    value = store.read_scalar(f"SELECT MIN({date_col}) FROM {table}")
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    return value


def _resolve_fixed_notional_amount(config: Settings, initial_cash: float) -> float:
    amount = float(config.fixed_notional_amount)
    if amount > 0:
        return amount
    return float(initial_cash * float(config.max_position_pct))


def build_current_mainline_config(config: Settings, initial_cash: float) -> Settings:
    cfg = config.model_copy(deep=True)
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


def infer_year_windows(
    *,
    requested_start_year: int,
    requested_end_year: int,
    available_start: date,
    available_end: date,
) -> list[YearWindow]:
    windows: list[YearWindow] = []
    for year in range(requested_start_year, requested_end_year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        start = max(year_start, available_start)
        end = min(year_end, available_end)
        available = start <= end
        if not available:
            note = (
                f"No current mainline data coverage for {year}. "
                f"Current executable DB covers {available_start.isoformat()} to {available_end.isoformat()}."
            )
            windows.append(YearWindow(year=year, start=None, end=None, available=False, note=note))
            continue

        if start == year_start and end == year_end:
            note = "Full calendar-year backtest window."
        elif start == year_start:
            note = f"Partial year: data currently ends at {end.isoformat()}."
        elif end == year_end:
            note = f"Partial year: data currently starts at {start.isoformat()}."
        else:
            note = f"Partial year: data covers {start.isoformat()} to {end.isoformat()}."
        windows.append(YearWindow(year=year, start=start, end=end, available=True, note=note))
    return windows


def _finite(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def _format_num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.{digits}f}"


def _safe_date_span_days(start: pd.Timestamp | date, end: pd.Timestamp | date) -> int:
    start_date = start.date() if isinstance(start, pd.Timestamp) else start
    end_date = end.date() if isinstance(end, pd.Timestamp) else end
    return int((end_date - start_date).days)


def build_plain_summary(metrics: dict[str, float], paired: pd.DataFrame, year_window: YearWindow, initial_cash: float) -> str:
    if paired.empty:
        return (
            f"{year_window.year} 年这套系统没有形成完整平仓交易，现阶段更像“有信号、有参与、但还没走完可统计样本”的年份。"
        )

    net_pnl = float(paired["pnl"].sum())
    total_return = net_pnl / initial_cash if initial_cash > 0 else 0.0
    trade_count = int(metrics["trade_count"])
    pf = float(metrics["profit_factor"])
    mdd = float(metrics["max_drawdown"])
    exposure = float(metrics["exposure_rate"])

    if total_return > 0.05:
        performance_text = "这一年整体是明显赚钱的。"
    elif total_return > 0:
        performance_text = "这一年整体是小幅赚钱的。"
    elif total_return > -0.03:
        performance_text = "这一年整体小亏，接近打平。"
    else:
        performance_text = "这一年整体亏损比较明确。"

    if trade_count >= 80:
        activity_text = "出手频率偏高。"
    elif trade_count >= 30:
        activity_text = "出手频率中等。"
    else:
        activity_text = "出手频率偏低。"

    if exposure >= 0.6:
        exposure_text = "大部分交易日都处在有仓位状态。"
    elif exposure >= 0.3:
        exposure_text = "有仓位时间中等。"
    else:
        exposure_text = "大多数时候都比较克制。"

    risk_text = (
        f"利润因子 {pf:.2f}，最大回撤 {_format_pct(mdd)}。"
        if math.isfinite(pf)
        else f"利润因子无法稳定定义，最大回撤 {_format_pct(mdd)}。"
    )
    return f"{performance_text}{activity_text}{exposure_text}{risk_text}"


def build_year_report(
    *,
    report_path: Path,
    year_window: YearWindow,
    metrics: dict[str, float],
    paired: pd.DataFrame | None,
    orders: pd.DataFrame | None,
    trades: pd.DataFrame | None,
    initial_cash: float,
    config: Settings,
    available_start: date,
    available_end: date,
) -> None:
    if not year_window.available:
        report_path.write_text(
            "\n".join(
                [
                    f"# {year_window.year} 年主线回测报告",
                    "",
                    "## 结论",
                    "",
                    "这一年当前没法正式回测。",
                    "",
                    "## 原因",
                    "",
                    year_window.note,
                    "",
                    "## 当前可执行数据库覆盖",
                    "",
                    f"- 起点: `{available_start.isoformat()}`",
                    f"- 终点: `{available_end.isoformat()}`",
                    "",
                    "## 怎么补",
                    "",
                    "如果要补这几年，需要先把旧库或原始数据回填成当前主线可执行库，再重跑年度回测。",
                    "",
                ]
            ),
            encoding="utf-8-sig",
        )
        return

    assert paired is not None
    assert orders is not None
    assert trades is not None

    net_pnl = float(paired["pnl"].sum()) if not paired.empty else 0.0
    total_return = net_pnl / initial_cash if initial_cash > 0 else 0.0
    gross_profit = float(paired.loc[paired["pnl"] > 0, "pnl"].sum()) if not paired.empty else 0.0
    gross_loss = float(paired.loc[paired["pnl"] <= 0, "pnl"].sum()) if not paired.empty else 0.0
    total_fees = float(pd.to_numeric(trades["fee"], errors="coerce").fillna(0.0).sum()) if not trades.empty else 0.0
    avg_holding_days = (
        float(
            paired.apply(
                lambda row: _safe_date_span_days(row["entry_date"], row["exit_date"]),
                axis=1,
            ).mean()
        )
        if not paired.empty
        else None
    )

    best_trade = paired.sort_values("pnl_pct", ascending=False).head(1)
    worst_trade = paired.sort_values("pnl_pct", ascending=True).head(1)
    exit_breakdown = (
        paired["exit_reason"].fillna("UNKNOWN").value_counts().sort_values(ascending=False).head(10).to_dict()
        if not paired.empty
        else {}
    )
    reject_breakdown = (
        orders[orders["status"].isin(["REJECTED", "EXPIRED"])]["reject_reason"]
        .fillna("UNKNOWN")
        .replace("", "UNKNOWN")
        .value_counts()
        .sort_values(ascending=False)
        .head(10)
        .to_dict()
        if not orders.empty
        else {}
    )
    summary = build_plain_summary(metrics, paired, year_window, initial_cash)

    lines: list[str] = [
        f"# {year_window.year} 年主线回测报告",
        "",
        "## 一句话结论",
        "",
        summary,
        "",
        "## 回测口径",
        "",
        f"- 窗口: `{year_window.start.isoformat()} ~ {year_window.end.isoformat()}`",
        f"- 说明: {year_window.note}",
        "- 系统口径: `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL`",
        "- 模式: `legacy pipeline / BOF only / no IRS runtime / no MSS runtime / no Gene hard gate`",
        f"- 初始资金: `{_format_num(initial_cash, 0)}`",
        f"- 固定单笔资金: `{_format_num(config.fixed_notional_amount, 0)}`",
        "",
        "## 常见统计数据",
        "",
        f"- 净收益: `{_format_num(net_pnl, 2)}`",
        f"- 总收益率: `{_format_pct(total_return)}`",
        f"- 平仓笔数: `{_format_num(metrics['trade_count'], 0)}`",
        f"- 胜率: `{_format_pct(metrics['win_rate'])}`",
        f"- 平均盈利笔收益率: `{_format_pct(metrics['avg_win'])}`",
        f"- 平均亏损笔收益率: `{_format_pct(metrics['avg_loss'])}`",
        f"- 期望值 EV: `{_format_pct(metrics['expected_value'])}`",
        f"- 利润因子 PF: `{_format_ratio(_finite(metrics['profit_factor']))}`",
        f"- 最大回撤 MDD: `{_format_pct(metrics['max_drawdown'])}`",
        f"- 暴露率: `{_format_pct(metrics['exposure_rate'])}`",
        f"- 参与率: `{_format_pct(metrics['participation_rate'])}`",
        f"- 信号机会数: `{_format_num(metrics['opportunity_count'], 0)}`",
        f"- 实际成交买单数: `{_format_num(metrics['filled_count'], 0)}`",
        f"- 现金不足跳过数: `{_format_num(metrics['skip_cash_count'], 0)}`",
        f"- 仓位上限跳过数: `{_format_num(metrics['skip_maxpos_count'], 0)}`",
        f"- 拒单率: `{_format_pct(metrics['reject_rate'])}`",
        f"- 缺价率: `{_format_pct(metrics['missing_rate'])}`",
        f"- 毛盈利: `{_format_num(gross_profit, 2)}`",
        f"- 毛亏损: `{_format_num(gross_loss, 2)}`",
        f"- 总手续费: `{_format_num(total_fees, 2)}`",
        f"- 平均持有天数: `{_format_num(avg_holding_days, 2)}`",
        "",
        "## 交易手感",
        "",
    ]

    if total_return > 0:
        lines.append(f"- 这一年账户是赚钱的，净赚 `{_format_num(net_pnl, 2)}`。")
    elif total_return < 0:
        lines.append(f"- 这一年账户是亏钱的，净亏 `{_format_num(abs(net_pnl), 2)}`。")
    else:
        lines.append("- 这一年账户基本打平。")

    if float(metrics["trade_count"]) == 0:
        lines.append("- 没有形成完整平仓样本，所以很多统计项只有形式值。")
    elif float(metrics["participation_rate"]) < 0.2:
        lines.append("- 有不少信号没有真正落成交易，系统比较克制。")
    else:
        lines.append("- 信号到成交的转化不算低，系统是真正在市场里出手的。")

    if float(metrics["max_drawdown"]) > 0.2:
        lines.append("- 回撤偏大，睡觉不太踏实。")
    elif float(metrics["max_drawdown"]) > 0.1:
        lines.append("- 回撤中等，能承受但不轻松。")
    else:
        lines.append("- 回撤不算夸张，风险侧还比较收敛。")

    lines.extend(["", "## 最好和最差的一笔", ""])

    if not best_trade.empty:
        row = best_trade.iloc[0]
        lines.extend(
            [
                f"- 最好的一笔: `{row['code']}`，`{str(row['entry_date'])[:10]} -> {str(row['exit_date'])[:10]}`，收益率 `{_format_pct(float(row['pnl_pct']))}`，盈亏 `{_format_num(float(row['pnl']), 2)}`",
            ]
        )
    if not worst_trade.empty:
        row = worst_trade.iloc[0]
        lines.extend(
            [
                f"- 最差的一笔: `{row['code']}`，`{str(row['entry_date'])[:10]} -> {str(row['exit_date'])[:10]}`，收益率 `{_format_pct(float(row['pnl_pct']))}`，盈亏 `{_format_num(float(row['pnl']), 2)}`",
            ]
        )

    lines.extend(["", "## 退出原因分布", ""])
    if exit_breakdown:
        for reason, count in exit_breakdown.items():
            lines.append(f"- `{reason}`: `{count}` 笔")
    else:
        lines.append("- 没有可统计的退出原因。")

    lines.extend(["", "## 拒单 / 失手机会", ""])
    if reject_breakdown:
        for reason, count in reject_breakdown.items():
            lines.append(f"- `{reason}`: `{count}` 次")
    else:
        lines.append("- 这一年基本没有明显的拒单堆积。")

    lines.extend(["", "## 市场环境拆分", ""])
    environment_breakdown = metrics.get("environment_breakdown", {})
    if environment_breakdown:
        for env, env_metrics in environment_breakdown.items():
            env_trade_count = _format_num(env_metrics.get("trade_count"), 0)
            env_win_rate = _format_pct(_finite(env_metrics.get("win_rate")))
            env_ev = _format_pct(_finite(env_metrics.get("expected_value")))
            env_pf = _format_ratio(_finite(env_metrics.get("profit_factor")))
            lines.append(
                f"- `{env}`: 交易 `{env_trade_count}` 笔，胜率 `{env_win_rate}`，EV `{env_ev}`，PF `{env_pf}`"
            )
    else:
        lines.append("- 这一年没有足够的环境拆分样本。")

    lines.extend(
        [
            "",
            "## 备注",
            "",
            "- 这份报告使用的是当前正式主线口径，不是研究线 retained/watch 口径。",
            f"- 报告生成时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8-sig")


def run_year(
    *,
    db_path: Path,
    config: Settings,
    start: date,
    end: date,
    initial_cash: float,
) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    store = Store(db_path)
    try:
        clear_runtime_tables(store)
    finally:
        store.close()

    result = run_backtest(
        db_path=db_path,
        config=config,
        start=start,
        end=end,
        patterns=["bof"],
        initial_cash=initial_cash,
        run_id=None,
    )
    store = Store(db_path)
    try:
        trades = _load_trades(store, start, end)
        orders = _load_orders(store, start, end)
        paired = _pair_trades(trades)
    finally:
        store.close()

    metrics: dict[str, float] = {
        "trade_count": float(result.trade_count),
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
        "environment_breakdown": result.environment_breakdown,
    }
    return metrics, paired, orders, trades


def build_index_report(
    *,
    output_path: Path,
    year_windows: list[YearWindow],
    generated_files: dict[int, Path],
    summaries: dict[int, dict[str, str]],
    available_start: date,
    available_end: date,
) -> None:
    lines = [
        "# 主线年度回测报告索引",
        "",
        "## 当前数据库覆盖",
        "",
        f"- 起点: `{available_start.isoformat()}`",
        f"- 终点: `{available_end.isoformat()}`",
        "",
        "## 年度总览",
        "",
        "| 年份 | 状态 | 核心结论 | 文件 |",
        "|---|---|---|---|",
    ]
    for year_window in year_windows:
        if not year_window.available:
            lines.append(
                f"| {year_window.year} | 无数据 | 当前可执行库不覆盖这年 | `{generated_files[year_window.year].name}` |"
            )
            continue
        summary = summaries[year_window.year]
        lines.append(
            f"| {year_window.year} | 已完成 | {summary['headline']} | `{generated_files[year_window.year].name}` |"
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run yearly current-mainline backtest reports")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--cash", type=float, default=None)
    parser.add_argument("--db-path", type=str, default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    parser.add_argument(
        "--output-root",
        type=str,
        default=r"G:\EmotionQuant-report\backtest_reports\mainline_yearly",
    )
    parser.add_argument(
        "--working-db-path",
        type=str,
        default=r"G:\EmotionQuant-temp\backtest\mainline_yearly_reports.duckdb",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_cfg = get_settings().model_copy(deep=True)
    initial_cash = float(args.cash if args.cash is not None else base_cfg.backtest_initial_cash)
    cfg = build_current_mainline_config(base_cfg, initial_cash)
    source_db = Path(args.db_path).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    working_db = Path(args.working_db_path).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    read_store = Store(source_db)
    try:
        available_start = _get_min_date(read_store, "l2_stock_adj_daily", date_col="date")
        available_end = read_store.get_max_date("l2_stock_adj_daily", date_col="date")
    finally:
        read_store.close()

    if available_start is None or available_end is None:
        raise RuntimeError("Current executable DB has no l2_stock_adj_daily coverage.")

    db_file = prepare_working_db(source_db, working_db)
    year_windows = infer_year_windows(
        requested_start_year=args.start_year,
        requested_end_year=args.end_year,
        available_start=available_start,
        available_end=available_end,
    )

    generated_files: dict[int, Path] = {}
    summaries: dict[int, dict[str, str]] = {}

    for year_window in year_windows:
        report_path = output_root / f"{year_window.year}-mainline-backtest-report.md"
        generated_files[year_window.year] = report_path
        if not year_window.available:
            build_year_report(
                report_path=report_path,
                year_window=year_window,
                metrics={},
                paired=None,
                orders=None,
                trades=None,
                initial_cash=initial_cash,
                config=cfg,
                available_start=available_start,
                available_end=available_end,
            )
            summaries[year_window.year] = {"headline": "无数据覆盖"}
            print(f"[{year_window.year}] unavailable")
            continue

        metrics, paired, orders, trades = run_year(
            db_path=db_file,
            config=cfg,
            start=year_window.start,
            end=year_window.end,
            initial_cash=initial_cash,
        )
        build_year_report(
            report_path=report_path,
            year_window=year_window,
            metrics=metrics,
            paired=paired,
            orders=orders,
            trades=trades,
            initial_cash=initial_cash,
            config=cfg,
            available_start=available_start,
            available_end=available_end,
        )
        net_pnl = float(paired["pnl"].sum()) if not paired.empty else 0.0
        total_return = net_pnl / initial_cash if initial_cash > 0 else 0.0
        if total_return > 0:
            headline = f"赚钱 {_format_pct(total_return)}"
        elif total_return < 0:
            headline = f"亏损 {_format_pct(total_return)}"
        else:
            headline = "基本打平"
        summaries[year_window.year] = {"headline": headline}
        print(
            f"[{year_window.year}] done start={year_window.start} end={year_window.end} "
            f"trades={int(metrics['trade_count'])} return={total_return:.4f}"
        )

    build_index_report(
        output_path=output_root / "README.md",
        year_windows=year_windows,
        generated_files=generated_files,
        summaries=summaries,
        available_start=available_start,
        available_end=available_end,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
