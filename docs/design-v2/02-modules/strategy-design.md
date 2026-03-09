# Strategy 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`  
**理论来源**: `docs/Strategy/PAS/volman-ytc-mapping.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史 Strategy 模块参考文档**。

它保留的价值主要是：

1. 记录 `v0.01` 时期 `Strategy` 的历史职责与边界。
2. 说明为什么当时采用 `PatternDetector + registry` 的形态架构。
3. 补充 `BOF 单形态闭环` 在历史版本中的模块级语义。

本文档不是仓库现行 `Strategy` 正文。当前主线正式设计已迁入 `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`、`blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md` 与 `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`。

---

## 2. 当前使用边界

当前阅读本文的正确用途是：

1. 回看 `v0.01 Frozen` 的历史 `BOF` 触发链路。
2. 理解 `PatternDetector` 和 registry 为什么会出现在历史版本里。
3. 对照当前主线为何把 `PAS / IRS` 的正式正文迁到 `blueprint/`。

当前不应把本文当作：

1. 当前主线 `PAS` 的正式算法正文。
2. 当前 `IRS` 排序设计的正文。
3. 当前形态参数、组合方式和质量层定义的权威来源。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行口径，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行 `Strategy` 设计请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
3. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`

---

## 4. `v0.01 Frozen` 中 Strategy 的历史职责

历史上，`Strategy` 回答的问题是：

`候选池中的股票，今天是否触发买入信号。`

其职责可概括为：

1. 接收 `Selector` 输出的候选池。
2. 读取个股历史 `OHLCV`。
3. 运行 `PAS` 形态检测器。
4. 产出 formal `Signal`，交给 `Broker`。

历史版本中，`Strategy` 只做触发，不做市场级风险调节，也不直接处理订单执行。

---

## 5. 历史上保留的核心结论

### 5.1 `PatternDetector + registry` 是历史高价值骨架

`v0.01` 最值得保留的一条模块设计，不是某个具体阈值，而是：

1. 一个形态一个 detector
2. detector 统一签名
3. registry 负责启停与组合

这个骨架后来没有失效，只是被现行主线重新接管和扩写。

### 5.2 `v0.01` 的正式触发器只有 `BOF`

历史版本明确保留的执行事实是：

1. `BOF` 是唯一正式启用的形态
2. `BPB / PB / TST / CPB` 虽然在册，但不进入 `v0.01` 实盘口径

这点今天仍然必须被清楚区分，否则容易把历史预留内容误读成历史正式执行内容。

### 5.3 `Strategy` 不吞并 `MSS / IRS`

历史版本中，`Strategy` 的有效边界是：

1. 只看个股形态
2. 不把 `MSS/IRS` 分数直接作为形态输入
3. 不承担市场级或行业级决策

这条边界在当前主线里仍然有连续性。

---

## 6. 历史摘要：BOF 单形态闭环

`v0.01 Frozen` 的 `Strategy` 可概括为以下历史语义：

1. 候选池来自 `Selector`
2. `Strategy` 读取个股历史窗口
3. `BofDetector` 在 `T` 日收盘后判断是否触发
4. 若触发，则生成 `signal_date = T` 的 `BUY Signal`
5. 后续由 `Broker` 在 `T+1 Open` 执行

这里真正值得保留的是**时序语义与模块边界**，而不是文内所有历史代码草案。

---

## 7. 历史预留内容的正确地位

本文原先大量出现的 `BPB / PB / TST / CPB` 检测草案、辅助函数和组合模式设计，今天统一视为：

1. 历史预留设计
2. 历史探索痕迹
3. 后续主线设计的素材来源

它们**不再**构成：

1. `v0.01 Frozen` 的正式执行口径
2. 仓库现行 `PAS` 的正式正文
3. 当前实现计划或模块待办

---

## 8. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级：

1. 文内 `pas_bpb / pas_pb / pas_tst / pas_cpb` 的详细算法草案。
2. registry 中关于历史未来版本的实施安排。
3. 详细组合模式与投票逻辑草案。
4. 任何把本文当作当前 `PAS` 或 `IRS` 正式设计来源的用法。

这些内容保留追溯价值，但已不再承担现行设计职责。

---

## 9. 与当前主线的关系

本文与当前主线的关系固定为：

1. 它说明历史版本为什么从一开始就选择 detector/registry 架构。
2. 它帮助解释为什么 `BOF` 成为历史版本的唯一正式形态。
3. 它不定义当前主线的 registry、quality layer、reference layer 或 `IRS` 排序逻辑。

---

## 10. 相关文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/01-system/architecture-master.md`
3. `docs/Strategy/PAS/volman-ytc-mapping.md`
4. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
5. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
6. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
