# EmotionQuant 历史重构设计总览

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史架构总览参考文档**。

它只回答三件事：

1. 当时的系统为什么要从旧体系重构。
2. `v0.01` 历史版本的总体模块边界是什么。
3. `system-baseline.md` 之外，还有哪些架构层摘要值得回看。

本文档**不是当前主线设计正文**。仓库现行设计权威层已迁入 `blueprint/`；若本文内容与现行设计冲突，以 `docs/design-migration-boundary.md` 和 `blueprint/` 为准。

---

## 2. 当前使用边界

当前阅读本文的正确用途只有三类：

1. 回看 `v0.01 Frozen` 时的整体系统拆分思路。
2. 理解历史上为什么从膨胀架构收缩到 6 模块 + `L1-L4` 分层。
3. 给 `system-baseline.md` 提供架构背景补充。

当前**不应**把本文当作：

1. 仓库现行设计 SoT。
2. 当前实现方案。
3. 当前执行拆解。
4. 当前模块算法正文。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行语义，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行设计请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/README.md`
3. `blueprint/01-full-design/`
4. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
5. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`

---

## 4. 历史上保留下来的核心架构价值

### 4.1 六模块拆分

`v0.01` 历史版本最值得保留的架构结论，是把系统收缩为 6 个模块：

1. `Data`
2. `Selector`
3. `Strategy`
4. `Broker`
5. `Backtest`
6. `Report`

这个拆分的历史价值在于：

1. 把数据、触发、风险、回测和报告分层。
2. 避免旧体系里“集成层过厚、模块边界模糊”的问题。
3. 为后续 `blueprint` 的主线设计提供了可复用骨架。

### 4.2 `L1-L4` 分层解耦

历史版本保留下来的另一条高价值结论是：

1. `L1` 原始数据
2. `L2` 加工数据
3. `L3` 算法输出
4. `L4` 历史分析缓存

这条分层语义后来没有被废弃，只是被现行主线重新解释和收口。

### 4.3 结果契约优先

历史版本明确强调：

1. 模块间只传结果契约。
2. 不跨模块传内部中间特征。
3. `Backtest` 和纸上交易共用同一 `Broker` 内核。

这些原则在当前主线里仍然具有连续性。

---

## 5. `v0.01 Frozen` 历史架构摘要

以下内容保留为历史摘要，不替代 `system-baseline.md`：

### 5.1 历史主链路

`v0.01 Frozen` 的历史执行链路可概括为：

`Data -> Selector -> Strategy -> Broker -> Backtest/Report`

其中：

1. `Selector` 历史上承担基础过滤和 `MSS/IRS` 前置漏斗。
2. `Strategy` 历史上承担 `BOF` 单形态触发。
3. `Broker` 历史上承担 `T+1 Open` 撮合、仓位和退出。

### 5.2 历史最小实现目标

`v0.01` 当时的最小可运行目标主要是：

1. 先跑通 `BOF` 单形态闭环。
2. 把 `MSS/IRS` 当成待验证假设。
3. 用统一 `Broker` 保障回测和纸上交易语义一致。
4. 以四周增量方式完成首轮最小系统。

### 5.3 为什么历史版本后来需要降级

本文之所以现在只能作为历史参考，是因为：

1. 当年的大量“后续迭代计划”已经不再等于当前主线。
2. `v0.01-plus` 已经替代原先的 top-down 主线。
3. `blueprint` 已接管当前正式设计正文。

---

## 6. 当前仍值得回看的内容

如果今天还要从本文中拿信息，优先只看以下四类：

1. 为什么系统坚持 6 模块边界。
2. 为什么坚持 `L1-L4` 分层。
3. 为什么强调结果契约与模块解耦。
4. 为什么 `Backtest` 与纸上交易共用 `Broker` 内核。

这些内容仍有长期价值。

---

## 7. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级，不再作为当前可执行口径：

1. 旧版四周落地计划。
2. 针对 `v0.02 / v0.03` 的历史演进安排。
3. 文内任何仍像当前实现说明的伪代码或落地节奏。
4. 把 `architecture-master.md` 当成系统级 SoT 的使用方式。

这些内容保留追溯价值，但不再承担现行设计职责。

---

## 8. 相邻文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/02-modules/data-layer-design.md`
3. `docs/design-v2/02-modules/selector-design.md`
4. `docs/design-v2/02-modules/strategy-design.md`
5. `docs/design-v2/02-modules/broker-design.md`
6. `docs/design-v2/02-modules/backtest-report-design.md`
7. `blueprint/README.md`
