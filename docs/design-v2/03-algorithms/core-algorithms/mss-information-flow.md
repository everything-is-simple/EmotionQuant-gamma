# MSS-lite 信息流（当前执行版）

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变当前主线 DTT 语义的前提下，对 MSS 的输入链路、落库链路与执行消费链路做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/selector/mss.py`, `src/broker/risk.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容附录。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的信息流整理结果，不再构成仓库现行设计权威。现行 `MSS-lite` 正文以 `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 当前主线信息流总览

```text
L2 market snapshot
-> MSS score engine
-> l3_mss_daily
-> Broker Risk overlay
-> actual executable capacity
```

当前主线必须按这个方向流动。

任何把 `MSS` 重新接回 `Selector` 或 `Ranker` 的设计，都不是当前主线。

---

## 2. Spec-04 目标信息流

在恢复 `MSS-full` 的周期层后，当前主线目标信息流应扩成：

```text
L2 market snapshot
-> MSS score engine
-> temperature / signal
-> phase / phase_trend / phase_days
-> position_advice
-> risk_regime
-> Broker Risk overlay
-> actual executable capacity
```

其中：

1. `temperature / signal` 是兼容输出。
2. `phase / phase_trend / phase_days / position_advice` 是解释层与证据层核心。
3. `risk_regime` 是执行层消费核心。

---

## 3. 分阶段信息流

### 2.1 Step 1：读取市场快照

输入：

- `l2_market_snapshot`

输出：

- 单日市场横截面快照行

说明：

- 当前 `MSS` 只读市场级聚合，不读行业表，不读个股表，不读 PAS 检测结果。

### 2.2 Step 2：计算原始因子

`src/selector/mss.py` 先从快照行计算 6 个原始因子：

- `market_coefficient_raw`
- `profit_effect_raw`
- `loss_effect_raw`
- `continuity_raw`
- `extreme_raw`
- `volatility_raw`

### 2.3 Step 3：标准化与聚合

随后执行：

1. `zscore_single()` 标准化
2. 六因子加权聚合
3. 生成：
   - `score`
   - `signal`

### 2.4 Step 4：周期层与仓位建议层

`Spec-04` 恢复后，应在 `score / signal` 基础上继续派生：

1. `phase`
2. `phase_trend`
3. `phase_days`
4. `position_advice`
5. `risk_regime`

推荐语义：

- `phase`：七阶段周期标签
- `phase_trend`：上升 / 下降 / 横盘
- `phase_days`：当前周期已持续天数
- `position_advice`：原始仓位建议区间
- `risk_regime`：供执行层消费的状态压缩结果

### 2.5 Step 5：写入 L3

输出表：

- `l3_mss_daily`

写入字段：

- `date`
- `score`
- `signal`
- 六个标准化后组件字段
- `phase`（Spec-04）
- `phase_trend`（Spec-04）
- `phase_days`（Spec-04）
- `position_advice`（Spec-04）
- `risk_regime`（Spec-04）

### 2.6 Step 6：RiskManager 消费

`src/broker/risk.py` 在评估信号时：

1. 按 `signal.signal_date` 查询 `l3_mss_daily`
2. 派生 `MssRiskOverlay`
3. 动态覆盖：
   - `max_positions`
   - `risk_per_trade_pct`
   - `max_position_pct`
4. 输出最终 `RiskDecision`

恢复周期层后，执行层链路应解释为：

`temperature -> phase -> position_advice -> risk_regime -> 风险倍率`

---

## 4. 与其他算法的边界

### 3.1 与 Selector

当前主线中：

- `Selector` 不读取 `l3_mss_daily`
- `MSS` 不再缩小 `candidate_top_n`
- `MSS` 不再产生 gate / soft gate

### 3.2 与 IRS

当前主线中：

- `IRS` 与 `MSS` 并行存在，但不互相作为输入
- `IRS` 解决“同日谁更强”
- `MSS` 解决“今天能开多大风险预算”

### 3.3 与 PAS / BOF

当前主线中：

- `BOF` 先触发
- `MSS` 不得决定是否运行 `BOF`
- `MSS` 只影响触发后可执行数量与仓位

---

## 5. 运行时时序

```text
交易日 T 收盘后:
1. L2 market snapshot 已准备完毕
2. 计算 MSS -> 写 l3_mss_daily(T)
3. 运行 Selector / BOF / IRS 排序，生成 signal_date=T 的信号
4. Broker/Risk 在评估这些信号时读取 l3_mss_daily(T)
5. 在 T+1 执行时，风险预算已经由 T 日 MSS 固定
```

这个时序保证：

- `MSS` 与 `signal_date` 对齐
- 不向未来取值
- 执行层可以复盘当日为什么缩仓或放大

---

## 6. 当前信息流的设计意义

当前这套信息流的核心意义是：

1. 把 `MSS` 从“删样本工具”改成“控执行风险工具”
2. 把 `MSS` 与 `IRS` 的职责彻底拆开
3. 让 `排序增益` 和 `风险覆盖` 可以被单独解释与单独审计
4. 把原始 `MSS-full` 中的周期 / 趋势 / 仓位建议重新接回执行层解释，而不是只剩一个温度分

---

## 7. 权威结论

当前主线里，`MSS` 的正确信息流只有一条：

`l2_market_snapshot -> MSS -> 温度 -> 周期 -> 仓位建议 -> 风险倍率 -> 订单容量`

如果信息流不是这条，就说明文档或代码又回到了旧漏斗思维。

---

## 8. 相关文档

- `mss-algorithm.md`
- `mss-data-models.md`
- `mss-api.md`
- `down-to-top-integration.md`
- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`
