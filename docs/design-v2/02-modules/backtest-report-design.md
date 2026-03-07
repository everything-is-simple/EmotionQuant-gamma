# Backtest & Report 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`（与 `system-baseline.md` 对齐）  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误与说明性修订；执行语义变更需进入 v0.02+。`  
**上游文档**: `docs/design-v2/01-system/architecture-master.md` §4.5 + §4.6  
**创建日期**: `2026-03-01`  
**对应模块**: `src/backtest/engine.py`，`src/report/reporter.py`

## 冻结区与冲突处理

1. 本文档属于冻结区；默认只允许勘误、链接修复与说明性澄清。若涉及执行语义、模块边界或口径调整，必须进入后续版本处理。
2. 若本文档与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准，并应同步回写本文档。
3. 当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本证据、回归结果与阶段记录，统一归档到 `docs/spec/<version>/`。
---

## 1. 设计目标

**Backtest**：用历史数据验证策略有效性。单引擎（backtrader，仅负责时间推进与数据喂入），调用自研 Broker 内核保证回测/实盘语义一致。

**Report**：用数据说话——期望值是否为正、左尾是否可控、右尾是否拿住。不搞监控平台，日志预警足够。

### v0.01 报告强制项

1. 分环境统计：牛市/震荡/熊市分段输出胜率与期望值。
2. 中位数路径优先：以多窗口统计中位数结果作为主结论，不以最佳路径作为主结论。
3. 成本压力：报告必须展示手续费+滑点后的净表现。
4. 消融对照必做：`BOF baseline` / `BOF + MSS` / `BOF + MSS + IRS`。
5. 诚信指标必出：`reject_rate`、`missing_rate`、`exposure_rate`、`failure_reason_breakdown`。
6. 机会参与指标必出：`opportunity_count`、`filled_count`、`skip_*`、`participation_rate`。
7. 幂等验收以 `l4_orders/l4_trades` 主键集合一致为准，不以汇总指标近似一致替代。

---

## 2. Backtest — backtrader 封装

### 2.1 架构关系

```text
backtrader 负责：
  - 时间推进（逐日推进交易日历）
  - 数据喂入（L2 历史数据 → bt.feeds）
  - 调度 next()（每个交易日触发一次）

EmotionQuant 负责（在 bt.Strategy.next() 中调用）：
  - selector.select_candidates() → 候选池
  - strategy.generate_signals() → 信号
  - broker.process_signals() → 订单
  - broker.execute_orders() → 成交
  - broker.update_daily() → 止损/止盈检查
```

backtrader 自带的 broker 和 sizer **不使用**，只用它的时间推进和数据管理。所有风控和撮合走我们自己的 Broker 内核。

### 2.2 EmotionQuantStrategy（bt.Strategy 子类）

```python
import backtrader as bt
from data.store import Store
from selector.selector import select_candidates
from strategy.strategy import generate_signals
from broker.broker import Broker

class EmotionQuantStrategy(bt.Strategy):
    """
    将 Selector + Strategy + Broker 封装为 backtrader Strategy 类。
    backtrader 只负责时间推进和数据管理。
    """

    def __init__(self):
        self.store = Store(self.p.db_path)
        self.config = self.p.config
        self.broker_engine = Broker(self.store, self.config, self.p.initial_cash)

    def next(self):
        today = self.datas[0].datetime.date(0)

        # 1. 执行昨日生成的待执行订单
        pending_orders = self.broker_engine.get_pending_orders(today)
        if pending_orders:
            market_data = self._get_market_data(today)
            trades = self.broker_engine.execute_orders(pending_orders, market_data, today)
            # 持久化订单状态（FILLED / REJECTED）—— 审计链 Signal→Order→Trade 完整
            self.store.bulk_upsert("l4_orders",
                pd.DataFrame([o.model_dump() for o in pending_orders]))
            for trade in trades:
                # l4_trades 存在重跑场景，必须 upsert（按 trade_id 幂等覆盖）
                self.store.bulk_upsert("l4_trades", pd.DataFrame([trade.model_dump()]))
                # 信任分级更新（仅 SELL 触发：BUY 时持仓未了结，无法判定盈亏）
                if trade.action == "SELL":
                    self.broker_engine.risk.update_trust(trade.code, trade)

        # 2. 更新持仓（止损/止盈检查）
        market_data = self._get_market_data(today)
        sell_orders = self.broker_engine.update_daily(today, market_data)
        # sell_orders 在下一交易日执行；先持久化为 PENDING
        if sell_orders:
            self.store.bulk_upsert("l4_orders",
                pd.DataFrame([o.model_dump() for o in sell_orders]))

        # 3. 今日选股 + 信号生成
        candidates = select_candidates(self.store, today)
        signals = generate_signals(self.store, candidates, today, self.config)

        # 4. 风控检查 → 生成 BUY 订单
        buy_orders = []
        for signal in signals:
            order = self.broker_engine.risk.check_signal(signal, self.broker_engine, today)
            if order:
                self.broker_engine.add_pending_order(order)
                buy_orders.append(order)
        # 持久化 BUY 订单（PENDING）
        if buy_orders:
            self.store.bulk_upsert("l4_orders",
                pd.DataFrame([o.model_dump() for o in buy_orders]))

    def _get_market_data(self, date):
        """
        从 store 读取指定日期的撮合所需数据。
        L2 提供复权价序列，L1 提供停牌/涨跌停与原始开盘价。
        """
        return self.store.read_df(
            "SELECT a.*, b.open AS raw_open, b.is_halt, b.up_limit, b.down_limit "
            "FROM l2_stock_adj_daily a "
            "LEFT JOIN l1_stock_daily b "
            "  ON a.code = SPLIT_PART(b.ts_code, '.', 1) "
            "  AND a.date = b.date "
            "WHERE a.date = ?", (date,)
        )

    def stop(self):
        """回测结束：强制平仓所有未平仓持仓 → 关闭 store。"""
        last_date = self.datas[0].datetime.date(0)
        self._force_close_all(last_date)
        self.store.close()

    def _force_close_all(self, last_date: date):
        """
        回测末日强制平仓。
        这是 T+1 规则的回测终止结算例外：以最后一个交易日收盘价（含卖出滑点）对所有 open positions 生成 SELL Trade，
        确保 _pair_trades 的 BUY/SELL 数量一致。
        该动作属于回测终止结算，不构成交易决策语义从 T+1 到 T 的修改。
        """
        open_positions = self.broker_engine.get_open_positions()
        if not open_positions:
            return
        market_data = self._get_market_data(last_date)
        for pos in open_positions:
            bar = market_data[market_data.code == pos.code]
            if bar.empty:
                logger.warning(f"force_close: {pos.code} 最后交易日无数据，跳过")
                continue
            close_price = bar.iloc[0]["adj_close"]
            if self.config.SLIPPAGE_BPS > 0:
                close_price *= (1 - self.config.SLIPPAGE_BPS / 10000)  # 卖出侧滑点
            fee = self.broker_engine.matcher._calculate_fee(
                close_price * pos.quantity, "SELL"
            )
            fc_order_id = f"FC_{pos.code}_{last_date}"
            # 强平订单也需持久化，保证审计链完整
            fc_order = Order(
                order_id=fc_order_id,
                signal_id=fc_order_id,
                code=pos.code,
                action="SELL",
                pattern=pos.pattern,
                quantity=pos.quantity,
                execute_date=last_date,
                status="FILLED"
            )
            self.store.bulk_upsert("l4_orders", pd.DataFrame([fc_order.model_dump()]))
            trade = Trade(
                trade_id=f"{fc_order_id}_T",   # 确定性：重跑覆盖而非追加
                order_id=fc_order_id,
                code=pos.code,
                execute_date=last_date,
                action="SELL",
                pattern=pos.pattern,
                price=close_price,
                quantity=pos.quantity,
                fee=fee,
                is_paper=pos.is_paper,
            )
            # l4_trades 存在重跑场景，必须 upsert（按 trade_id 幂等覆盖）
            self.store.bulk_upsert("l4_trades", pd.DataFrame([trade.model_dump()]))
        logger.info(f"force_close_all: {len(open_positions)} 笔持仓已强平")
```

### 2.3 数据喂入

```python
def create_bt_data(store: Store, start: date, end: date) -> bt.feeds.PandasData:
    """
    从 DuckDB 读取数据，转为 backtrader 数据源。
    只需要一个"时钟"数据源驱动 next()，实际数据从 store 读取。
    """
    # 用上证综指作为时钟（保证每个交易日都触发 next）
    index_df = store.read_df(
        "SELECT date as datetime, open, high, low, close, volume "
        "FROM l1_index_daily WHERE ts_code = '000001.SH' "
        "AND date BETWEEN ? AND ? ORDER BY date",
        (start, end)
    )
    index_df["datetime"] = pd.to_datetime(index_df["datetime"])
    index_df.set_index("datetime", inplace=True)

    return bt.feeds.PandasData(dataname=index_df)
```

### 2.4 回测引擎入口

```python
def run_backtest(db_path: str, config, start: date, end: date,
                 patterns: list[str] = None, combination: str = None,
                 initial_cash: float = 1_000_000):
    """
    回测主入口。

    参数：
      patterns: 指定形态列表（覆盖 config.PAS_PATTERNS）
      combination: 指定组合模式（覆盖 config.PAS_COMBINATION）
    """
    # 覆盖配置（支持单形态独立回测）
    if patterns:
        config.PAS_PATTERNS = patterns
    if combination:
        config.PAS_COMBINATION = combination

    cerebro = bt.Cerebro()

    # 添加数据源（时钟）
    store = Store(db_path)
    data = create_bt_data(store, start, end)
    cerebro.adddata(data)
    store.close()

    # 添加策略
    cerebro.addstrategy(EmotionQuantStrategy,
                        db_path=db_path, config=config,
                        initial_cash=initial_cash)

    # 不使用 backtrader 自带撮合/风控逻辑（资金状态由 Broker 内核维护）

    # 运行
    results = cerebro.run()

    # 生成报告
    generate_backtest_report(db_path, config, start, end)

    return results
```

### 2.5 CLI 接口

```text
# 默认回测（使用 config 中的形态配置）
python main.py backtest --start=2023-01-01 --end=2025-12-31

# 单形态独立回测
python main.py backtest --patterns=bof --start=2023-01-01

# 多形态组合回测（v0.02+）
python main.py backtest --patterns=bof,bpb --combination=ANY --start=2023-01-01

# 指定初始资金
python main.py backtest --start=2023-01-01 --cash=500000
```

CLI 解析在 `main.py` 中用 argparse 实现：

```python
# main.py
parser_bt = subparsers.add_parser("backtest")
parser_bt.add_argument("--start", required=True, type=str)
parser_bt.add_argument("--end", type=str, default=str(date.today()))
parser_bt.add_argument("--patterns", type=str, default=None,
                       help="逗号分隔的形态列表，如 bof（v0.01）或 bof,bpb（v0.02+）")
parser_bt.add_argument("--combination", type=str, default=None,
                       choices=["ANY", "ALL", "VOTE"])
parser_bt.add_argument("--cash", type=float, default=1_000_000)
```

---

## 3. Report — 统计与报告

### 3.1 reporter.py 函数签名

```python
def generate_backtest_report(db_path: str, config, start: date, end: date):
    """
    回测结束后生成完整报告。
    读 l4_trades + l4_orders，计算统计指标，写 l4_daily_report + l4_pattern_stats。
    """

def generate_daily_report(store: Store, trade_date: date):
    """
    每日运行后生成当日报告。
    写 l4_daily_report 一行。
    """

def check_warnings(store: Store, trade_date: date):
    """
    检查预警规则，命中则 loguru.warning。
    """
```

### 3.2 核心统计指标计算

#### 期望值指标

```python
def _compute_expectation(paired: pd.DataFrame) -> dict:
    """
    从已配对交易数据计算期望值指标。
    paired 为 _pair_trades() 的输出，需包含 pnl_pct 列。
    调用方应先执行 paired = _pair_trades(trades_df)，再将 paired 传入。
    """
    wins = paired[paired["pnl_pct"] > 0]
    losses = paired[paired["pnl_pct"] <= 0]

    total = len(paired)
    if total == 0:
        return {"win_rate": 0, "avg_win": 0, "avg_loss": 0,
                "profit_factor": 0, "expected_value": 0}

    win_rate = len(wins) / total
    avg_win = wins["pnl_pct"].mean() if len(wins) > 0 else 0
    avg_loss = abs(losses["pnl_pct"].mean()) if len(losses) > 0 else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float("inf")
    expected_value = win_rate * avg_win - (1 - win_rate) * avg_loss

    return {
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "expected_value": expected_value,
    }
```

#### 交易配对

```python
def _pair_trades(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    将 BUY/SELL 交易配对，计算每笔完整交易的盈亏。
    返回 DataFrame：code, entry_date, exit_date, entry_price, exit_price,
                    pnl, pnl_pct, holding_days, pattern, fee_total

    前置条件：回测结束前必须已调用 force_close_all()，保证无未平仓持仓。
    配对规则：按数量配对（支持分批成交/分批平仓），不是按笔数 zip。
    """
    pairs = []
    # 按 code 分组，BUY/SELL 按时间顺序 FIFO 数量配对
    for code, group in trades_df.groupby("code"):
        group = group.sort_values(["execute_date", "trade_id"])
        buy_queue = []  # [{qty, price, fee, execute_date, pattern}]

        for t in group.itertuples():
            if t.action == "BUY":
                buy_queue.append({
                    "qty": t.quantity,
                    "original_qty": t.quantity,  # 原始数量（费用分摊分母，不随部分匹配递减）
                    "price": t.price,
                    "fee": t.fee,
                    "execute_date": t.execute_date,
                    "pattern": t.pattern,
                })
                continue

            # SELL：按 FIFO 与买单队列逐笔配对
            sell_qty = t.quantity
            while sell_qty > 0 and buy_queue:
                buy = buy_queue[0]
                matched_qty = min(buy["qty"], sell_qty)
                buy_fee_part = buy["fee"] * (matched_qty / buy["original_qty"])
                sell_fee_part = t.fee * (matched_qty / t.quantity)
                pnl = (t.price - buy["price"]) * matched_qty - buy_fee_part - sell_fee_part

                pairs.append({
                    "code": code,
                    "entry_date": buy["execute_date"],
                    "exit_date": t.execute_date,
                    "entry_price": buy["price"],
                    "exit_price": t.price,
                    "quantity": matched_qty,
                    "pnl": pnl,
                    "pnl_pct": pnl / (buy["price"] * matched_qty),  # 净收益率（含手续费）
                    "holding_days": (t.execute_date - buy["execute_date"]).days,
                    "pattern": buy["pattern"],   # Trade 已冗余携带 pattern 字段
                    "fee_total": buy_fee_part + sell_fee_part,
                })

                buy["qty"] -= matched_qty
                sell_qty -= matched_qty
                if buy["qty"] == 0:
                    buy_queue.pop(0)

            if sell_qty > 0:
                raise ValueError(f"{code}: SELL 数量超过 BUY 库存，出现负仓位")

        if buy_queue:
            raise ValueError(
                f"{code}: 存在未平仓数量 {sum(x['qty'] for x in buy_queue)}，"
                f"force_close_all 可能未执行"
            )

    return pd.DataFrame(pairs)
```

#### 左尾指标

```python
def _compute_left_tail(paired: pd.DataFrame, nav_series: pd.Series) -> dict:
    """
    左尾指标：损失有多坏。
    """
    losses = paired[paired["pnl_pct"] <= 0]
    return {
        "max_single_loss": losses["pnl_pct"].min() if len(losses) > 0 else 0,
        "max_drawdown": _max_drawdown(nav_series),
        "max_consecutive_loss": _max_consecutive(paired["pnl_pct"] <= 0),
        "loss_p5": losses["pnl_pct"].quantile(0.05) if len(losses) > 0 else 0,
    }

def _max_drawdown(nav: pd.Series) -> float:
    """净值序列的最大回撤。"""
    peak = nav.cummax()
    drawdown = (peak - nav) / peak
    return drawdown.max()

def _max_consecutive(is_loss: pd.Series) -> int:
    """最大连续亏损笔数。"""
    groups = (is_loss != is_loss.shift()).cumsum()
    return is_loss.groupby(groups).sum().max() if len(is_loss) > 0 else 0
```

#### 右尾指标

```python
def _compute_right_tail(paired: pd.DataFrame) -> dict:
    """
    右尾指标：收益有多好。
    """
    wins = paired[paired["pnl_pct"] > 0]
    return {
        "max_single_win": wins["pnl_pct"].max() if len(wins) > 0 else 0,
        "avg_holding_days_win": wins["holding_days"].mean() if len(wins) > 0 else 0,
        "win_p95": wins["pnl_pct"].quantile(0.95) if len(wins) > 0 else 0,
    }
```

#### 分布形态

```python
def _compute_distribution(paired: pd.DataFrame) -> dict:
    """
    收益分布形态。
    """
    from scipy import stats
    pnl = paired["pnl_pct"]
    return {
        "skewness": pnl.skew() if len(pnl) > 2 else 0,
        "kurtosis": pnl.kurtosis() if len(pnl) > 3 else 0,
    }
```

#### 稳定性指标

```python
def _compute_stability(paired: pd.DataFrame, nav: pd.Series,
                       trading_days: int = 250) -> dict:
    """
    稳定性指标：E(V) 是否持续为正。
    """
    # 滚动 30 日期望值
    rolling_ev = paired["pnl_pct"].rolling(30).apply(
        lambda x: x[x > 0].mean() * (x > 0).mean() - x[x <= 0].abs().mean() * (x <= 0).mean()
        if len(x) > 0 else 0
    )

    # 年化夏普
    daily_returns = nav.pct_change().dropna()
    sharpe = (daily_returns.mean() / daily_returns.std() * (trading_days ** 0.5)
              if daily_returns.std() > 0 else 0)

    # 卡玛比率
    annual_return = (nav.iloc[-1] / nav.iloc[0]) ** (trading_days / len(nav)) - 1
    max_dd = _max_drawdown(nav)
    calmar = annual_return / max_dd if max_dd > 0 else 0

    return {
        "rolling_ev_30d": rolling_ev.iloc[-1] if len(rolling_ev) > 0 else 0,
        "sharpe": sharpe,
        "calmar": calmar,
    }
```

### 3.3 净值序列构建

```python
def _build_nav_series(store: Store, start: date, end: date,
                      initial_cash: float) -> pd.Series:
    """
    从 l4_trades 构建每日净值序列。
    逐日模拟持仓市值 + 现金。
    """
    trades = store.read_df(
        "SELECT * FROM l4_trades WHERE is_paper = false "
        "AND execute_date BETWEEN ? AND ? ORDER BY execute_date",
        (start, end)
    )

    # 获取所有交易日
    trade_dates = store.read_df(
        "SELECT date FROM l1_trade_calendar "
        "WHERE date BETWEEN ? AND ? AND is_trade_day = true ORDER BY date",
        (start, end)
    )["date"].tolist()

    cash = initial_cash
    positions = {}  # code → (quantity, entry_price)
    nav_list = []

    for td in trade_dates:
        # 处理当日成交
        day_trades = trades[trades["execute_date"] == td]
        for _, t in day_trades.iterrows():
            if t["action"] == "BUY":
                positions[t["code"]] = (t["quantity"], t["price"])
                cash -= t["price"] * t["quantity"] + t["fee"]
            elif t["action"] == "SELL":
                if t["code"] in positions:
                    cash += t["price"] * t["quantity"] - t["fee"]
                    del positions[t["code"]]

        # 计算持仓市值
        portfolio_value = 0
        for code, (qty, _) in positions.items():
            price_row = store.read_df(
                "SELECT adj_close FROM l2_stock_adj_daily "
                "WHERE code = ? AND date = ?", (code, td)
            )
            if not price_row.empty:
                portfolio_value += price_row.iloc[0]["adj_close"] * qty

        nav_list.append({"date": td, "nav": cash + portfolio_value})

    return pd.DataFrame(nav_list).set_index("date")["nav"]
```

### 3.4 逐形态统计

```python
def _compute_pattern_stats(paired: pd.DataFrame, trade_date: date) -> pd.DataFrame:
    """
    按形态分组计算统计指标，写入 l4_pattern_stats。
    """
    rows = []
    for pattern, group in paired.groupby("pattern"):
        stats = _compute_expectation(group)
        rows.append({
            "date": trade_date,
            "pattern": pattern,
            "trade_count": len(group),
            **stats,
        })
    return pd.DataFrame(rows)
```

---

## 4. 预警规则

### 4.1 规则定义

```python
WARNING_RULES = [
    {
        "condition": lambda r: r.get("rolling_ev_30d", 0) < 0,
        "message": "⚠ 30日滚动期望值为负，策略可能失效",
        "level": "WARNING",
    },
    {
        "condition": lambda r: r.get("max_consecutive_loss", 0) >= 5,
        "message": "⚠ 连续亏损 5 笔，建议检查",
        "level": "WARNING",
    },
    {
        "condition": lambda r: r.get("max_drawdown", 0) > 0.15,
        "message": "⚠ 回撤超过 15%",
        "level": "WARNING",
    },
    {
        "condition": lambda r: r.get("profit_factor", float("inf")) < 1.0,
        "message": "⚠ 盈亏比 < 1，期望值为负",
        "level": "WARNING",
    },
    {
        "condition": lambda r: r.get("skewness", 0) < -0.5,
        "message": "⚠ 收益分布左偏，左尾过厚",
        "level": "WARNING",
    },
]
```

### 4.2 预警检查函数

```python
def check_warnings(store, trade_date):
    """
    读最新 l4_daily_report，逐条检查预警规则。
    命中则 loguru.warning。
    """
    report = store.read_df(
        "SELECT * FROM l4_daily_report WHERE date = ?", (trade_date,)
    )
    if report.empty:
        return

    row = report.iloc[0].to_dict()
    for rule in WARNING_RULES:
        if rule["condition"](row):
            logger.warning(f"[{trade_date}] {rule['message']}")
```

### 4.3 消融回退门（强制）

对 `BOF baseline -> BOF+MSS -> BOF+MSS+IRS` 的每次升级，report 层必须输出回退判定：

1. 相对前一配置 `expected_value` 下降超过 10% -> 回退
2. 相对前一配置 `max_drawdown` 恶化超过 20% -> 回退
3. 任一市场环境中位数路径由正转负且连续两个评估窗未恢复 -> 回退

---

## 5. 报告类型

### 5.1 回测报告

回测结束后生成，包含全量数据：

```text
generate_backtest_report() 输出：

1. 写 l4_daily_report（逐日统计）
2. 写 l4_pattern_stats（逐形态统计）
3. 控制台输出摘要：
   ─────────────────────────────────────
   回测区间: 2023-01-01 ~ 2025-12-31
   初始资金: ¥1,000,000
   最终净值: ¥1,234,567 (+23.5%)
   ─────────────────────────────────────
   期望值:
     胜率:       45.2%
     平均盈利:   +6.8%
     平均亏损:   -3.2%
     盈亏比:     2.13
     单笔期望:   +1.31%
   ─────────────────────────────────────
   左尾:
     单笔最大亏损: -8.5%
     最大回撤:     -12.3%
     最大连亏:     4 笔
   ─────────────────────────────────────
   右尾:
     单笔最大盈利: +22.1%
     盈利持仓均天:  8.3 天
   ─────────────────────────────────────
   分布:
     偏度: +0.45（右尾叠，好）
     峰度: 3.2
   ─────────────────────────────────────
   稳定性:
     夏普比率:  1.52
     卡玛比率:  1.91
   ─────────────────────────────────────
   逐形态:
     bof: 120笔, 胜率46%, 盈亏比2.1, EV+1.2%
     # v0.02+ 示例：bpb/pb/...
   ─────────────────────────────────────
```

### 5.2 每日选股报告

```text
generate_daily_report() 输出：

1. 写 l4_daily_report 一行
2. 控制台输出：
   ─────────────────────────────────────
   [2026-03-01] 每日选股报告
   ─────────────────────────────────────
   MSS: 72.3 (BULLISH)
   候选池: 68 只（Top-5 行业）
   信号: 3 只
     000001 BOF strength=0.78
     600519 BOF strength=0.65
     000858 BOF strength=0.61
   ─────────────────────────────────────
   当前持仓: 5 只
   今日浮盈: +2.3%
   累计净值: ¥1,045,678
   ─────────────────────────────────────
3. 检查预警规则
```

---

## 6. 数据写入

### 6.1 l4_daily_report 写入

```python
def _write_daily_report(store, trade_date, stats):
    """将统计结果写入 l4_daily_report。"""
    row = pd.DataFrame([{
        "date": trade_date,
        "candidates_count": stats.get("candidates_count", 0),
        "signals_count": stats.get("signals_count", 0),
        "trades_count": stats.get("trades_count", 0),
        "win_rate": stats.get("win_rate", 0),
        "avg_win": stats.get("avg_win", 0),
        "avg_loss": stats.get("avg_loss", 0),
        "profit_factor": stats.get("profit_factor", 0),
        "expected_value": stats.get("expected_value", 0),
        "max_drawdown": stats.get("max_drawdown", 0),
        "max_consecutive_loss": stats.get("max_consecutive_loss", 0),
        "skewness": stats.get("skewness", 0),
        "rolling_ev_30d": stats.get("rolling_ev_30d", 0),
        "sharpe_30d": stats.get("sharpe_30d", 0),
    }])
    store.bulk_upsert("l4_daily_report", row)
```

### 6.2 l4_pattern_stats 写入

```python
def _write_pattern_stats(store, pattern_stats_df):
    """将逐形态统计写入 l4_pattern_stats。"""
    if not pattern_stats_df.empty:
        store.bulk_upsert("l4_pattern_stats", pattern_stats_df)
```

---

## 7. 配置

```python
# config.py — Backtest & Report 配置

# 回测参数
BACKTEST_DEFAULT_START = "2023-01-01"
BACKTEST_DEFAULT_CASH = 1_000_000

# 报告参数
REPORT_ROLLING_WINDOW = 30        # 滚动统计窗口（交易日）
REPORT_ANNUALIZE_DAYS = 250       # 年化天数

# 预警阈值
WARN_EV_THRESHOLD = 0             # 期望值 < 此值触发预警
WARN_CONSECUTIVE_LOSS = 5         # 连亏 N 笔触发预警
WARN_MAX_DRAWDOWN = 0.15          # 回撤 > 此值触发预警
WARN_PROFIT_FACTOR = 1.0          # 盈亏比 < 此值触发预警
WARN_SKEWNESS = -0.5              # 偏度 < 此值触发预警
```

---

## 8. 单测要点

| 模块 | 测试方式 |
|------|---------|
| _pair_trades | 构造 BUY/SELL 交易序列，验证配对正确性（含部分成交、多次买卖） |
| _compute_expectation | 构造已知胜率和盈亏比的交易，验证 EV 计算 |
| _max_drawdown | 构造已知净值序列（如 100→120→90→110），验证 DD=25% |
| _max_consecutive | 构造连亏序列，验证计数 |
| _compute_pattern_stats | 多形态交易数据，验证分组统计 |
| check_warnings | mock l4_daily_report 数据，验证预警触发 |
| EmotionQuantStrategy | 用少量历史数据跑短期回测，验证全链路跑通 |

**关键边界用例**：
- 零交易 → 所有指标返回 0，不报错
- 全部盈利 → avg_loss=0, profit_factor=inf
- 全部亏损 → win_rate=0, expected_value 为负
- 只有 BUY 没有 SELL（回测结束时仍持仓）→ 按最后一天收盘价强制平仓
- 单笔交易 → skewness/kurtosis 返回 0（样本不足）



