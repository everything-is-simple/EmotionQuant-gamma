# Broker / Risk Contract Annex

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `Broker / Risk`  
**上游锚点**:

1. `docs/design-v2/02-modules/broker-design.md`
2. `blueprint/01-full-design/92-mainline-design-atom-closure-record-20260308.md`
3. `src/contracts.py`
4. `src/broker/broker.py`
5. `src/broker/risk.py`
6. `src/broker/matcher.py`
7. `src/backtest/engine.py`

---

## 1. 用途

本文只补 `Broker / Risk` 当前主线缺失的契约原子。

它不重写 `Broker / Risk` 的主线职责，只冻结 6 件事：

1. `Broker / Risk` 当前正式消费和产出的契约
2. 内部状态对象和正式跨模块契约的边界
3. `signal_id / order_id / trade_id` 的稳定生成规则
4. `T 日收盘 -> T+1 Open` 的正式时序
5. A 股最小执行约束与拒绝语义
6. 执行归因与生命周期追溯口径

一句话说：

`当前 Broker / Risk 不再是旧 Trading 大全套，而是一个收窄后的执行内核；哪些字段是正式契约、哪些只是内部状态、订单为什么被拒、为什么成交、为什么过期，必须写死。`

---

## 2. 作用边界

本文只覆盖当前主线 `Broker / Risk`：

```text
ranked signals
-> process_signals
-> RiskDecision
-> pending orders
-> next-trade-day open matcher
-> Trade / portfolio update
-> exit scheduling / order expiry
```

本文不覆盖：

1. `Selector` 初选
2. `PAS-trigger / BOF` 触发
3. `IRS-lite` 行业排序
4. `MSS-lite` 市场打分本身
5. 旧 `Integration -> TradeSignal -> Trading` 全套桥接模型
6. GUI / Report 展示层

---

## 3. 设计来源

当前补充文的来源是“以 gamma 代码现实为准、定向吸收 beta 状态机原子”：

1. `beta trading-data-models.md`
2. `beta trading-information-flow.md`
3. `beta trading-api.md`
4. `gamma` 当前主线正文
5. `gamma` 当前 `src/broker/*`
6. `gamma` 当前 `src/backtest/engine.py`
7. `gamma` 当前 `tests/unit/broker/` 与 `tests/integration/backtest/`

其中：

1. `beta` 提供状态机、时序和执行约束的表达深度
2. `gamma` 提供当前主线正确边界：`Signal -> Order -> Trade`
3. 当前代码和测试提供已落地的幂等键、拒绝原因和 T+1 现实

---

## 4. Broker / Risk 阶段模型

### 4.1 阶段拆分

`Broker / Risk` 当前主线固定拆成 7 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `B0` | `signal_intake` | `list[Signal]` | 排序后的 signal 队列 | 无 signal 则无订单 |
| `B1` | `risk_assess` | `Signal + BrokerRiskState + MSS overlay` | `RiskDecision` | `NO_NEXT_TRADE_DAY / ALREADY_HOLDING / MAX_POSITIONS_REACHED / NO_EST_PRICE / INSUFFICIENT_CASH / SIZE_BELOW_MIN_LOT` |
| `B2` | `order_materialize` | `RiskDecision` | `Order(PENDING)` 或 `Order(REJECTED)` | 风控拒绝也落订单行 |
| `B3` | `open_match` | `Order + market bar` | `Trade` 或撮合拒绝 | `INVALID_ORDER_STATE / NO_MARKET_DATA / HALTED / LIMIT_UP / LIMIT_DOWN / INVALID_PRICE` |
| `B4` | `portfolio_apply` | `Trade` | `cash + portfolio` 新状态 | 买入前二次现金校验失败 -> `INSUFFICIENT_CASH_AT_EXECUTION` |
| `B5` | `exit_schedule` | `portfolio + signal_date close` | `SELL Order(PENDING)` | 无 next trade day / 无 close / 已有 pending sell 则不生成 |
| `B6` | `expiry_or_force_close` | `pending orders / backtest end day` | `EXPIRED Order` 或末日强平 `SELL Trade` | 超过 `MAX_PENDING_TRADE_DAYS` -> `ORDER_TIMEOUT` |

### 4.2 当前实现对应

当前代码主要对应：

1. `Broker.process_signals`
2. `RiskManager.assess_signal`
3. `Broker.execute_pending_orders`
4. `Matcher.execute`
5. `Broker.generate_exit_orders`
6. `Broker.expire_orders`
7. `backtest.engine._force_close_all`

当前必须固定的边界是：

1. `B1` 的结果对象是 `RiskDecision`
2. `B2-B6` 的正式持久化对象只有 `l4_orders / l4_trades`
3. `Position / BrokerRiskState / MssRiskOverlay / RiskDecision` 都还是 Broker 内部状态，不是跨模块正式契约

---

## 5. 正式执行契约

### 5.1 上游输入契约：Signal

`Broker / Risk` 当前唯一正式上游输入是 `Signal`。

其最小必需字段固定为：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `signal_id` | `str` | `Required` | 信号唯一键 |
| `code` | `str` | `Required` | 6 位纯代码 |
| `signal_date` | `date` | `Required` | 信号所属交易日 |
| `action` | `Literal["BUY"]` | `Required` | 当前上游正式信号只允许 `BUY` |
| `strength` | `float` | `Required` | 触发强度 |
| `pattern` | `str` | `Required` | 当前主线通常为 `bof` |
| `reason_code` | `str` | `Required` | 当前主线通常为 `PAS_BOF` |

当前 `Signal` 的兼容扩展字段：

1. `bof_strength`
2. `irs_score`
3. `mss_score`
4. `final_score`
5. `final_rank`
6. `variant`

这些扩展字段当前的作用是：

1. `final_score` 允许 `Broker` 决定同日竞争优先级
2. 其余字段主要用于解释和 sidecar

它们当前都不是下单所必需的正式字段。

### 5.2 正式输出契约：Order

`Order` 是 `Broker / Risk` 的正式跨模块输出契约之一。

当前稳定字段固定为：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `order_id` | `str` | `Required` | 订单唯一键 |
| `signal_id` | `str` | `Required` | 对应来源信号 |
| `code` | `str` | `Required` | 股票代码 |
| `action` | `Literal["BUY","SELL"]` | `Required` | 买卖方向 |
| `quantity` | `int` | `Required` | 下单股数 |
| `execute_date` | `date` | `Required` | 计划执行日 |
| `pattern` | `str` | `Required` | 来源形态 |
| `is_paper` | `bool` | `Optional` | 纸交标记 |
| `status` | `Literal["PENDING","FILLED","REJECTED","EXPIRED"]` | `Required` | 当前订单状态 |
| `reject_reason` | `str | None` | `Optional` | 拒绝或过期原因 |

### 5.3 正式输出契约：Trade

`Trade` 是 `Broker / Risk` 的正式跨模块输出契约之二。

当前稳定字段固定为：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `trade_id` | `str` | `Required` | 成交唯一键 |
| `order_id` | `str` | `Required` | 对应订单 |
| `code` | `str` | `Required` | 股票代码 |
| `execute_date` | `date` | `Required` | 成交日 |
| `action` | `Literal["BUY","SELL"]` | `Required` | 买卖方向 |
| `price` | `float` | `Required` | 实际成交价 |
| `quantity` | `int` | `Required` | 成交股数 |
| `fee` | `float` | `Required` | 总费用 |
| `pattern` | `str` | `Required` | 来源形态 |
| `is_paper` | `bool` | `Optional` | 纸交标记 |

### 5.4 当前持久化 reality

当前 `Store` 中的正式持久化表固定为：

| 表 | 角色 |
|---|---|
| `l4_orders` | 持久化 `Order` |
| `l4_trades` | 持久化 `Trade` |

其中：

1. 风控拒绝也必须落 `l4_orders`
2. 撮合拒绝通过更新既有订单行实现
3. `Trade` 当前一单最多一笔，不支持多笔部分成交

### 5.5 Broker 内部状态对象

下面这些对象当前只属于 Broker 内部：

| 对象 | 所在代码 | 作用 |
|---|---|---|
| `Position` | `src/broker/broker.py` | 当前持仓状态 |
| `BrokerRiskState` | `src/broker/risk.py` | 风控评估时的账户快照 |
| `RiskDecision` | `src/broker/risk.py` | 风控阶段输出 |
| `MssRiskOverlay` | `src/broker/risk.py` | 市场级容量覆盖结果 |

本轮必须冻结：

`它们不是跨模块正式契约。`

---

## 6. 幂等键与生命周期

### 6.1 当前稳定幂等键

当前幂等键规则固定为：

| 对象 | 规则 |
|---|---|
| `signal_id` | `build_signal_id(code, signal_date, pattern)` |
| `order_id` | 普通入场单：`build_order_id(signal_id)`，即当前等于 `signal_id` |
| `trade_id` | `build_trade_id(order_id)`，即当前为 `{order_id}_T` |

### 6.2 Broker 特例订单

当前 Broker 还会内部生成两类特例订单：

| 类型 | 规则 | 说明 |
|---|---|---|
| 退出单 | `EXIT_{code}_{signal_date}_{exit_reason.lower()}` | 来自 `STOP_LOSS / TRAILING_STOP` |
| 末日强平单 | `FC_{code}_{trade_date}` | 仅回测边界收口使用 |

### 6.3 当前冻结结论

当前必须冻结下面 3 条：

1. 普通入场链默认是一信号一订单一成交
2. 若未来引入部分成交或拆单，必须单独做 `trade_id` 迁移设计
3. `run_id` 当前不是 `Order / Trade` 正式字段，只能通过 `signal_id` 回溯到 sidecar

### 6.4 当前订单状态机

当前 `gamma` 的订单状态只允许：

1. `PENDING`
2. `FILLED`
3. `REJECTED`
4. `EXPIRED`

本轮明确不带回 `beta` 的：

1. `SUBMITTED`
2. `PARTIALLY_FILLED`
3. `CANCELLED`

原因很直接：

`当前代码和 schema 还没有这些状态的真实落点。`

---

## 7. 正式时序

### 7.1 当前主线时序

当前主线的正式时序固定为：

```text
T close:
  -> generate_exit_orders
  -> select_candidates
  -> generate_signals
  -> process_signals

T+1 open:
  execute_pending_orders
```

更精确地说，回测日循环中的顺序固定为：

1. 先执行今天到期的 pending orders
2. 再处理 pending order 过期
3. 再用今日收盘价检查退出触发并挂 `T+1 SELL`
4. 再基于今日收盘信号挂 `T+1 BUY`

### 7.2 T+1 语义

当前必须固定：

1. `signal_date = T`
2. `execute_date = next_trade_date(T)`
3. 成交价基于 `T+1` 的开盘 bar

### 7.3 非正常路径

当前两条例外路径也必须写死：

1. 订单过期：
   - 超过 `MAX_PENDING_TRADE_DAYS` 后，按交易日历推进，标记 `EXPIRED`
2. 回测末日强平：
   - 只用于末日收口，不代表正常生产语义

---

## 8. 风控、排序与 A 股约束

### 8.1 同日竞争优先级

当前 `Broker.process_signals` 的优先级固定为：

```text
sort key =
  final_score desc, if final_score exists
  else strength desc
```

然后逐条评估，并在同一批次内实时更新：

1. `state.cash`
2. `state.holdings`

这意味着：

1. 先被接受的信号会预占现金
2. 先被接受的信号会预占持仓名额
3. 后续信号可能因此被拒绝

### 8.2 当前风控评估面

当前 `RiskManager.assess_signal` 真正检查的是：

1. 是否存在下一交易日
2. 是否已有持仓
3. 是否触达 `max_positions`
4. 是否有可用估价
5. 是否达到最小 100 股整手
6. 是否能覆盖费用后的现金成本
7. `MSS-lite` 是否需要压缩容量

当前没有落地的旧语义，本轮明确不写成已实现：

1. 行业集中度上限
2. 总仓位比例状态机
3. 独立的卖出信号风控层

### 8.3 当前仓位计算

当前仓位大小固定按下面逻辑生成：

```text
nav = cash + portfolio_market_value
risk_budget = nav * overlay.risk_per_trade_pct
max_notional = nav * overlay.max_position_pct
est_stop_pct = max(STOP_LOSS_PCT, 0.01)

qty_by_risk = risk_budget / (est_price * est_stop_pct)
qty_by_cap = max_notional / est_price
quantity = floor(min(qty_by_risk, qty_by_cap) / 100) * 100
```

再经过：

1. 最小手数检查
2. 可支付费用检查
3. 执行时二次现金检查

### 8.4 当前撮合约束

`Matcher.execute` 当前固定遵守下面这些 A 股约束：

1. 只撮合 `status="PENDING"` 且 `execute_date=today` 的订单
2. 无 market bar 不成交
3. 停牌不成交
4. 买单开盘触及涨停不成交
5. 卖单开盘触及跌停不成交
6. 价格基于 `adj_open`，但涨跌停判断基于原始 `open / up_limit / down_limit`
7. 滑点按 `slippage_bps` 作用在 `adj_open`
8. 费用按：
   - 佣金 `max(amount * commission_rate, min_commission)`
   - 过户费 `amount * transfer_fee_rate`
   - 卖出印花税 `amount * stamp_duty_rate`

### 8.5 当前退出规则

当前最小退出机制固定为：

1. `STOP_LOSS`
2. `TRAILING_STOP`

它们的触发价分别来自：

1. `entry_price * (1 - STOP_LOSS_PCT)`
2. `max_price * (1 - TRAILING_STOP_PCT)`

且固定为：

`T 日收盘检查 -> T+1 开盘卖出`

---

## 9. Reject / Expire 语义

### 9.1 风控阶段拒绝原因

当前风控阶段拒绝原因固定为：

| `reject_reason` | 含义 |
|---|---|
| `NO_NEXT_TRADE_DAY` | 无下一交易日 |
| `ALREADY_HOLDING` | 当前已持仓 |
| `MAX_POSITIONS_REACHED` | 达到有效持仓数上限 |
| `NO_EST_PRICE` | 无法取得估价 |
| `INSUFFICIENT_CASH` | 预估成本下现金不足 |
| `SIZE_BELOW_MIN_LOT` | 达不到 100 股整手 |

### 9.2 撮合阶段拒绝原因

当前撮合阶段拒绝原因固定为：

| `reject_reason` | 含义 |
|---|---|
| `INVALID_ORDER_STATE` | 非当日待执行订单 |
| `NO_MARKET_DATA` | 无行情条 |
| `HALTED` | 停牌 |
| `LIMIT_UP` | 买单涨停不可成交 |
| `LIMIT_DOWN` | 卖单跌停不可成交 |
| `INVALID_PRICE` | 开盘价非法 |
| `INSUFFICIENT_CASH_AT_EXECUTION` | 执行时二次现金校验失败 |

### 9.3 过期原因

当前过期原因固定为：

| `reject_reason` | 含义 |
|---|---|
| `ORDER_TIMEOUT` | 超过 `MAX_PENDING_TRADE_DAYS` 未成交 |

### 9.4 当前冻结结论

本轮必须分开：

1. `Risk reject`
2. `Match reject`
3. `Execution-time cash reject`
4. `Expire`

否则后面所有参与率和拒绝分布都会失真。

---

## 10. Broker Trace 真相源

### 10.1 为什么必须单独有 trace

当前正式 `l4_orders / l4_trades` 只能告诉我们：

1. 订单最后是什么状态
2. 是否成交以及成交多少钱

但下面这些问题必须单独追：

1. 同日为什么这个 signal 排在前面
2. 这笔订单被拒是因为 `MSS` 缩仓、现金不足，还是涨停
3. 当天实际有效 `max_positions / risk_per_trade_pct / max_position_pct` 是多少
4. 这笔 SELL 是上游信号卖出，还是 Broker 自己生成的退出单

### 10.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`broker_order_lifecycle_trace_exp`

它不是正式跨模块契约，而是当前执行链真相源。

### 10.3 建议字段

| 字段 | 说明 |
|---|---|
| `run_id` | 当前运行标识，若可得则记录 |
| `signal_id` | 来源信号 |
| `order_id` | 订单键 |
| `trade_id` | 成交键，若成交 |
| `code` | 股票代码 |
| `signal_date` | 信号日 |
| `execute_date` | 计划执行日 |
| `action` | `BUY / SELL` |
| `pattern` | 来源形态 |
| `signal_priority_score` | 当前排序使用的分数：`final_score` 或 `strength` |
| `risk_state_cash_before` | 风控前现金 |
| `risk_state_holdings_before` | 风控前持仓数/集合摘要 |
| `mss_signal` | 当前 overlay 三态 |
| `mss_score` | 当前 overlay 分数 |
| `effective_max_positions` | 当前有效最大持仓 |
| `effective_risk_per_trade_pct` | 当前有效单笔风险预算 |
| `effective_max_position_pct` | 当前有效单票上限 |
| `target_quantity` | 风控初步目标股数 |
| `final_quantity` | 最终下单股数 |
| `order_status` | 最终订单状态 |
| `reject_reason` | 若拒绝或过期，记录原因 |
| `match_open_raw` | 撮合时原始开盘价 |
| `match_open_adj` | 撮合时复权开盘价 |
| `trade_price` | 若成交，记录价格 |
| `trade_fee` | 若成交，记录费用 |
| `origin` | `UPSTREAM_SIGNAL / EXIT_STOP_LOSS / EXIT_TRAILING_STOP / FORCE_CLOSE` |
| `created_at` | 写入时间 |

### 10.4 和正式表的边界

| 表/对象 | 职责 |
|---|---|
| `l4_orders` | 保存正式订单状态 |
| `l4_trades` | 保存正式成交结果 |
| `broker_order_lifecycle_trace_exp` | 解释订单为什么进入、为什么被拒、为什么成交或过期 |

这三者不能混写。

---

## 11. 和上下游的稳定连接

### 11.1 与 Strategy

当前主线下：

1. `Broker / Risk` 只消费正式 `Signal`
2. `SELL` 正式上游信号当前不存在
3. 退出卖单由 Broker 内部生成，不要求上游先产生卖出信号

### 11.2 与 MSS-lite

当前主线下：

1. `Broker / Risk` 是 `MSS-lite` 的唯一正式消费者
2. 它只消费 `MarketScore` 及其 overlay 结果
3. 它不回写 `MSS` 到 `final_score`

### 11.3 与 Backtest / Paper

当前主线铁律不变：

1. `Backtest` 和纸交应共用同一个 `Broker` 内核
2. 若后续包一层 paper pipeline，也只能包裹当前 `src/broker/*`
3. 不允许另写一套不同的订单状态、拒绝原因和 T+1 语义

---

## 12. 当前与后续

### 12.1 本文冻结的东西

本文已经冻结了：

1. `Signal / Order / Trade` 的正式边界
2. Broker 内部状态对象和正式契约的边界
3. 当前幂等键规则
4. `T 日收盘 -> T+1 Open` 的正式时序
5. 当前 A 股执行约束和拒绝原因
6. `broker_order_lifecycle_trace_exp`

### 12.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 增加 `broker_order_lifecycle_trace_exp` 或同等 artifact
2. 若要支持部分成交 / 拆单，必须先补 `trade_id` 迁移方案
3. 若要引入行业集中度或总仓位状态机，必须单独写升级 spec，不能口头算“已实现”
4. 让纸交入口包裹现有 Broker 内核，而不是分叉一套新执行语义

### 12.3 本文明确不做什么

本文不授权下面这些回退：

1. 把旧 `TradeSignal / Integration` 整套桥回来
2. 把 `MSS` 重新抬成信号生成前置 gate
3. 因为想快点推进实现，就继续把 `Order / Trade` 正式契约和内部状态对象混写
