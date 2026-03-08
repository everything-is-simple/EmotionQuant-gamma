# Broker / Risk 桥接稿（design-v2 -> blueprint）

**版本**: `v0.01-plus 桥接稿`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `本文仅保留 design-v2 阶段的兼容桥接说明；现行设计修订必须进入 blueprint/，本文只允许导航、勘误与桥接说明更新。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md`  
**对应模块**: `src/broker/risk.py`, `src/broker/matcher.py`, `src/backtest/engine.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容桥接稿。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的整理结果，不再构成仓库现行设计权威。现行 `Broker / Risk` 正文以 `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 职责

当前主线中的 `Broker / Risk` 负责：

1. 消费排序后的正式 `Signal`
2. 读取 `MSS-lite` 风险覆盖结果
3. 结合账户状态决定实际执行容量
4. 生成 `Order / Trade`

它回答的问题是：

`今天这些排序信号里，哪些能执行，能执行多少。`

---

## 2. 输入

`Broker / Risk` 当前主线读取：

1. 正式 `Signal`
2. `l3_signal_rank_exp` 或同等排序追溯结果
3. `l3_mss_daily`
4. 当前账户状态
   - 持仓
   - 现金
   - 风险暴露
5. 交易日上下文与行情数据

执行语义固定为：

`signal_date = T`，`execute_date = T+1`，成交价 = `T+1 Open`

---

## 3. 输出契约

`Broker / Risk` 输出：

1. `Order`
2. `Trade`
3. 执行层风险决策结果

最小可追溯链路必须满足：

1. `Signal -> Order -> Trade`
2. `run_id + signal_id` 能回到排序真相源
3. `MSS` 风险覆盖能解释仓位和截断变化

---

## 4. 不负责什么

当前主线中，`Broker / Risk` 不负责：

1. 生成候选池
2. 检测 `BOF`
3. 计算 `IRS` 行业分
4. 计算 `MSS` 市场分
5. 把 `MSS` 写回个股横截面总分

它消费上游结果，但不回写上游设计边界。

---

## 5. 决策规则 / 算法

当前主线固定链路为：

```text
ranked signals
-> attach MSS risk overlay
-> capacity decision
-> Order / Trade
```

核心规则：

1. 排序优先级来自 `BOF + IRS`，不是来自 `MSS`。
2. `MSS-lite` 只影响执行容量，不影响个股排序。
3. 风险覆盖当前至少调节：
   - `max_positions`
   - `risk_per_trade_pct`
   - `max_position_pct`
4. 最终下单集合由排序结果和风险预算共同决定。
5. 回测与纸上交易共用同一个 Broker 内核。

---

## 6. 失败模式与验证证据

主要失败模式：

1. `MSS` 被重新拉回前置 gate，破坏职责分离。
2. 排序解释链断裂，无法判断截断来自排序还是风控。
3. `Signal / Order / Trade` 幂等键不稳定，导致重跑不可比较。
4. 执行容量变化无法解释 `EV / MDD / PF` 的变化来源。

当前验证证据：

1. `docs/spec/v0.01-plus/evidence/execution_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t162521__execution_sensitivity.json`
2. `docs/spec/v0.01-plus/evidence/trade_attribution_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t165536__trade_attribution.json`
3. `docs/spec/v0.01-plus/evidence/windowed_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20251222_20260224_t_after_opt__windowed_sensitivity.json`
4. `docs/spec/v0.01-plus/records/v0.01-plus-trade-attribution-and-windowed-sensitivity-20260308.md`

当前证据的用途是：

1. 证明 `MSS` 已进入执行层
2. 判断是否满足默认路径切换条件

当前状态仍以 `development-status.md` 中的 `GO / NO-GO` 为准。
