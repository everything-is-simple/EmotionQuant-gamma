# Spec 04: Broker

## 需求摘要
系统中唯一有"钱"的模块：接收信号 → 风控检查 → 下单 → 撮合成交。回测和纸上交易共用此内核。有状态（持仓、资金、信任分级）。

**设计文档**: `docs/design-v2/broker-design.md`, `docs/design-v2/architecture-master.md` §4.4

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/broker/__init__.py` | 包初始化 |
| `src/broker/risk.py` | RiskManager：开仓检查 + 四级止损 + 信任分级 |
| `src/broker/matcher.py` | Matcher：撮合引擎 + 手续费 |
| `src/broker/broker.py` | Broker：组合 Risk + Matcher，主入口 |

## 设计要点

### Broker 类
```python
class Broker:
    def __init__(self, store, config, initial_cash=1_000_000)
    def process_signals(self, signals, trade_date) -> list[Order]   # 风控 → 生成订单
    def execute_orders(self, orders, market_data) -> list[Trade]     # 撮合
    def update_daily(self, trade_date, market_data) -> list[Order]   # 止损/止盈检查
```
- Position dataclass: code, entry_date, entry_price, quantity, current_price, max_price, stop_loss, signal_type, is_paper

### 四级止损体系（优先级高→低）
1. **第零级：日内浮亏即走** — 买入次日收盘 < 买入价 → T+2 卖出
2. **第一级：个股止损** — 浮亏 ≥ -5% → 强制卖出
3. **移动止盈** — close < max_price × (1-8%) → 卖出（不设固定止盈，右尾不截断）
4. **第二级：组合回撤** — 净值从峰值回撤 ≥ 15% → 全部清仓 + 冷却 5 天
5. **第三级：连亏熔断** — 连续 5 笔亏损 → 暂停开仓 3 天

### 个股信任分级
- ACTIVE → 真单 | OBSERVE → 模拟单(is_paper=true) | BACKUP → 跳过
- 降级：3连亏 → OBSERVE；真买又亏 → BACKUP
- 升级：BACKUP 冷藏120个交易日 → OBSERVE；模拟盈利1次 → ACTIVE

### Matcher
- 成交价 = T+1 Open（adj_open）+ 滑点
- 停牌 → REJECTED(HALTED)
- 买入涨停 → REJECTED(LIMIT_UP)；卖出跌停 → REJECTED(LIMIT_DOWN)
- 手续费：佣金 max(万三,5元) + 印花税(千一,仅卖) + 过户费(万0.2,双边)

### SELL 信号产生
PAS 只产 BUY。SELL 由 risk.py 根据止损/止盈/信任规则直接创建 Order 给 matcher。

## 实现任务

### broker.py
- [ ] 实现 Broker 类（组合 RiskManager + Matcher）
- [ ] 实现 Position dataclass
- [ ] `process_signals`: 遍历信号 → risk.check_signal → 收集 Order
- [ ] `execute_orders`: 遍历 Order → matcher.execute → 更新 portfolio/cash
- [ ] `update_daily`: 每日收盘后调 risk.check_positions → 生成 SELL Order
- [ ] pending_orders 管理（add_pending_order / get_pending_orders）

### risk.py — 开仓检查
- [ ] 实现 RiskManager 类
- [ ] `check_signal`: 信任检查 → 熔断检查 → 持仓数量检查 → 仓位计算 → 生成 Order
- [ ] `_calculate_position_size`: 用信号日收盘价估算（禁止用 signal.strength 代替价格）
- [ ] `_next_trade_date` / `_trading_days_between`（查 l1_trade_calendar）

### risk.py — 四级止损
- [ ] `check_positions`: 遍历持仓，按优先级检查，返回 SELL Order 列表
- [ ] 新增：入场后次日不延续退出规则（v0.01 强制）
- [ ] `_check_intraday_loss`: 持仓 1 天且 close < entry_price
- [ ] `_check_stop_loss`: 浮亏 ≥ STOP_LOSS_PCT(-5%)
- [ ] `_check_trailing_stop`: 更新 max_price，回落 ≥ TRAILING_STOP_PCT(8%)
- [ ] `_check_portfolio_drawdown`: nav 回撤 ≥ 15% → 全清仓 + force_bearish_until
- [ ] `_is_loss_circuit_breaker_active`: 连续 N 笔亏损 → 冷却期

### risk.py — 信任分级
- [ ] `get_trust_tier(code)`: 读 l4_stock_trust
- [ ] `update_trust(code, trade_result)`: 降级/升级逻辑
- [ ] `_check_auto_promote`: BACKUP → OBSERVE（冷藏30天自动）
- [ ] 新股默认 ACTIVE

### matcher.py
- [ ] 实现 Matcher 类
- [ ] `execute(order, market_data)` → Trade | None
- [ ] 停牌/涨跌停检查
- [ ] 成交价 = adj_open + 滑点(slippage_bps)
- [ ] `_calculate_fee(amount, action)`: 佣金+印花税+过户费

### 数据持久化
- [ ] Order → l4_orders（生成/更新状态时写入）
- [ ] Trade → l4_trades（成交时写入）
- [ ] Trust → l4_stock_trust（降级/升级时更新）

### 单测
- [ ] check_signal：mock 满仓/熔断/信任降级，验证拒绝
- [ ] _check_stop_loss：构造浮亏场景
- [ ] _check_trailing_stop：先涨后跌场景
- [ ] _check_portfolio_drawdown：净值回撤清仓
- [ ] Matcher：停牌/涨停/跌停/正常成交
- [ ] _calculate_fee：买入/卖出费率验证（不足5元按5元）
- [ ] update_trust：3连亏→OBSERVE，真买又亏→BACKUP
- [ ] T+1：买入当天无法卖出

## 验收标准
1. 回测和纸上交易使用同一个 Broker 实例
2. 信号从 T 日到 T+1 成交，成交价为 T+1 开盘价
3. 停牌股订单 REJECTED，一字涨停买入 REJECTED
4. 止损 -5% 触发正确，移动止盈 -8% 从 max_price 触发
5. 3连亏降为 OBSERVE，模拟盈利1次升回 ACTIVE
6. 手续费：卖出含印花税，买入不含；不足5元按5元
7. T+1 买入后当天不能卖出（即使浮亏>5%）
