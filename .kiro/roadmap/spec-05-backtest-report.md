# Spec 05: Backtest + Report

## 需求摘要
**Backtest**：用历史数据验证策略。backtrader 单引擎，调用 Broker 内核保证回测/实盘一致。
**Report**：期望值是否为正、左尾是否可控、右尾是否拿住。日志预警，不搞监控平台。
**联调**：全链路 data→selector→strategy→broker→report 每日自动跑通。

**设计文档**: `docs/design-v2/backtest-report-design.md`, `docs/design-v2/architecture-master.md` §4.5-4.6

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/backtest/__init__.py` | 包初始化 |
| `src/backtest/engine.py` | backtrader 封装（EmotionQuantStrategy + 数据喂入 + CLI） |
| `src/report/__init__.py` | 包初始化 |
| `src/report/reporter.py` | 统计指标计算 + 报告生成 + 预警检查 |
| `main.py` | CLI 入口（fetch/build/backtest/run） |

## 设计要点

### engine.py
- backtrader 只负责时间推进和数据管理，**不使用**其自带 broker/sizer
- EmotionQuantStrategy(bt.Strategy) 在 next() 中调用：
  1. execute_orders（执行昨日挂单）
  2. update_daily（止损/止盈检查）
  3. select_candidates → generate_signals（今日选股+信号）
  4. risk.check_signal（风控 → 生成 BUY 订单）
- 数据源：用上证综指(000001.SH)作为时钟驱动 next()，实际数据从 store 读取
- 支持 --patterns 参数覆盖 PAS_PATTERNS（单形态独立回测）

### reporter.py
**期望值指标**：win_rate, avg_win, avg_loss, profit_factor, expected_value
**左尾指标**：max_single_loss, max_drawdown, max_consecutive_loss, loss_p5
**右尾指标**：max_single_win, avg_holding_days_win, win_p95
**分布形态**：skewness, kurtosis
**稳定性**：rolling_ev_30d, sharpe, calmar

### 交易配对
BUY/SELL 按 (code, 时间顺序) 配对 → 计算每笔 pnl_pct、holding_days。回测结束仍持仓 → 按最后一天收盘价强制平仓。

### 预警规则（loguru.warning）
- rolling_ev_30d < 0 → 策略可能失效
- max_consecutive_loss ≥ 5 → 建议检查
- max_drawdown > 15% → 回撤超限
- profit_factor < 1.0 → 期望值为负
- skewness < -0.5 → 左尾过厚

### main.py CLI
```
python main.py fetch                              # 拉取增量数据
python main.py build --layers=l2,l3               # 生成 L2+L3
python main.py backtest --start=2023-01-01        # 默认回测
python main.py backtest --patterns=bof            # 单形态回测
# v0.02+ 才启用多形态组合
# python main.py backtest --patterns=bof,bpb --combination=ANY
python main.py run                                # 每日全链路
```

## 实现任务

### engine.py
- [ ] 实现 EmotionQuantStrategy(bt.Strategy)
- [ ] `__init__`: 创建 Store + Broker 实例
- [ ] `next()`: 4步流程（执行挂单 → 止损检查 → 选股 → 风控）
- [ ] `stop()`: 清仓 + 关闭 store
- [ ] `_get_market_data(date)`: 从 store 读 L2 当日数据
- [ ] 实现 `create_bt_data(store, start, end)`: 上证综指作为时钟 feed
- [ ] 实现 `run_backtest(db_path, config, start, end, patterns, combination, cash)`
- [ ] --patterns 参数覆盖 config.PAS_PATTERNS

### reporter.py — 统计计算
- [ ] `_pair_trades(trades_df)`: BUY/SELL 配对，返回 pnl_pct/holding_days
- [ ] `_compute_expectation(paired)`: win_rate, avg_win, avg_loss, profit_factor, EV
- [ ] `_compute_left_tail(paired, nav)`: max_single_loss, max_drawdown, max_consecutive_loss
- [ ] `_compute_right_tail(paired)`: max_single_win, avg_holding_days_win
- [ ] `_compute_distribution(paired)`: skewness, kurtosis
- [ ] `_compute_stability(paired, nav)`: rolling_ev_30d, sharpe, calmar
- [ ] `_build_nav_series(store, start, end, initial_cash)`: 逐日净值序列
- [ ] `_max_drawdown(nav)`: 净值峰谷回撤
- [ ] `_max_consecutive(is_loss)`: 最大连续亏损笔数

### reporter.py — 报告生成
- [ ] `generate_backtest_report(db_path, config, start, end)`: 全量统计 + 控制台输出 + 写 l4
- [ ] `generate_daily_report(store, trade_date)`: 每日一行写入 l4_daily_report
- [ ] `_compute_pattern_stats(paired, date)`: 逐形态统计，写 l4_pattern_stats
- [ ] 分环境统计（牛/震荡/熊）并输出分段胜率、期望值
- [ ] 输出中位数路径结论（不是最佳路径）
- [ ] 输出消融对照结果（BOF baseline / BOF+MSS / BOF+MSS+IRS）
- [ ] 控制台报告格式（期望值/左尾/右尾/分布/稳定性/逐形态）

### reporter.py — 预警
- [ ] `check_warnings(store, trade_date)`: 读 l4_daily_report，逐条检查
- [ ] WARNING_RULES 列表（5 条规则）
- [ ] 命中 → loguru.warning

### main.py
- [ ] argparse subcommands: fetch / build / backtest / run
- [ ] backtest 子命令：--start, --end, --patterns, --combination, --cash
- [ ] build 子命令：--layers, --start, --end, --force
- [ ] run 子命令：每日全链路（fetch → build → select → signal → broker → report）
- [ ] run_id 生成：`{trade_date}_{uuid[:8]}`
- [ ] 运行摘要写入 _meta_runs

### 纸上交易模式
- [ ] run 命令中 broker 使用纸上交易模式
- [ ] 纸上交易模式下全部交易 is_paper=true（不连券商）
- [ ] OBSERVE 股票 is_paper=true
- [ ] 结果写入 l4_trades（is_paper 字段区分）

### 单测
- [ ] _pair_trades：BUY/SELL 配对正确性（含部分成交、多次买卖）
- [ ] _compute_expectation：已知胜率和盈亏比验证 EV
- [ ] _max_drawdown：100→120→90→110 → DD=25%
- [ ] _max_consecutive：连亏序列计数
- [ ] check_warnings：mock l4_daily_report，验证预警触发
- [ ] 零交易 → 所有指标返回 0
- [ ] 全部盈利 → avg_loss=0, profit_factor=inf
- [ ] 回测结束仍持仓 → 按收盘价平仓

### 全链路联调
- [ ] 端到端：用 3 年真实数据跑完整回测
- [ ] 验证回测报告输出（期望值/回撤/夏普合理）
- [ ] 运行 `python main.py run` 每日流程跑通
- [ ] 验证 l4_trades / l4_daily_report / l4_pattern_stats 有数据

## 验收标准
1. `python main.py backtest --start=2023-01-01` 跑通，输出完整报告
2. `python main.py backtest --patterns=bof` 单形态回测可执行
3. 回测报告包含：胜率、盈亏比、期望值、最大回撤、夏普比率、逐形态统计
4. 零交易时所有指标返回 0，不报错
5. 预警规则命中时 loguru.warning 输出
6. `python main.py run` 每日全链路自动执行
7. l4_pattern_stats 记录每个形态的独立表现
