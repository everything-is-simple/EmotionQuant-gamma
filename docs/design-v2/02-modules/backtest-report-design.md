# Backtest & Report 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史 Backtest / Report 参考文档**。

它保留的价值主要是：

1. 说明历史版本如何理解回测、报告与复盘职责。
2. 记录为什么历史版本坚持 `backtrader` 只做时钟推进，交易语义由自研 `Broker` 承担。
3. 补充历史版本对报告指标、消融对照和预警的关注重点。

本文档不是仓库现行回测或报告正文。当前主线相关实现与证据，以 `blueprint/` 和 `docs/spec/` 为准。

---

## 2. 当前使用边界

当前阅读本文的正确用途是：

1. 回看 `v0.01 Frozen` 的历史回测语义。
2. 理解历史版本中 `Backtest` 与 `Report` 的角色分工。
3. 对照当前主线为什么仍强调证据、消融和归因。

当前不应把本文当作：

1. 当前回测引擎的直接实现说明。
2. 当前报告字段、证据文件或脚本入口的权威定义。
3. 当前 `v0.01-plus` 评审口径的正式来源。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行口径，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行实现与推进请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/common/records/development-status.md`
5. `docs/spec/v0.01-plus/records/`

---

## 4. `v0.01 Frozen` 中 Backtest / Report 的历史职责

历史上，这两个模块回答的问题分别是：

### 4.1 Backtest

`历史数据下，这套交易语义是否成立。`

### 4.2 Report

`回测和每日运行后，结果是否具备正期望、可解释和可追溯性。`

历史版本中，它们共同服务的不是“展示平台”，而是：

1. 验证
2. 复盘
3. 回退判断

---

## 5. 历史上保留的核心结论

### 5.1 backtrader 只是时钟壳

`v0.01` 最值得保留的一条历史结论，是：

1. `backtrader` 只负责时间推进与喂数
2. 真正的交易语义仍由自研 `Broker` 承担

这个设计的价值在于：回测不再偷偷使用另一套 broker 规则。

### 5.2 报告关注的是“能否长期活下来”

历史版本中，报告最重视的不是炫技指标，而是：

1. 期望值是否为正
2. 左尾是否失控
3. 右尾有没有拿住
4. 表现是否稳定

这也是为什么历史版本强调分环境统计、中位数路径和回退门。

### 5.3 消融对照是历史高价值治理结论

历史版本保留下来的另一条重要结论是：

1. `BOF baseline`
2. `BOF + MSS`
3. `BOF + MSS + IRS`

必须做同口径对照。

这个结论后来直接影响了主线切换与 `v0.01-plus` 的证据组织方式。

---

## 6. 历史摘要：Backtest 与 Report 的模块边界

### 6.1 Backtest

历史版本中的 `Backtest` 主要承担：

1. 推进历史交易日时钟
2. 读取分层数据
3. 调用 `Selector / Strategy / Broker`
4. 将交易结果写入历史分析层

### 6.2 Report

历史版本中的 `Report` 主要承担：

1. 交易配对与收益统计
2. 左尾、右尾和稳定性指标计算
3. 逐形态或逐环境的拆解
4. 最小预警输出

### 6.3 两者共同的历史目标

二者共同服务的是：

1. 不让“看上去赚钱”的结果遮蔽真实回撤和样本问题
2. 让策略判断可以被证据追溯
3. 给版本升级或回退提供依据

---

## 7. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级：

1. 文内完整 `EmotionQuantStrategy` 代码草案。
2. 详细统计公式、DDL、CLI 与报告格式草案。
3. 历史预警规则的具体阈值表。
4. 任何把本文当作当前 evidence / report 规范正文的使用方式。

这些内容保留追溯价值，但已不再承担现行设计职责。

---

## 8. 与当前主线的关系

本文与当前主线的关系固定为：

1. 它说明历史版本为什么坚持统一交易内核与证据导向。
2. 它帮助解释当前主线仍然重视归因、消融和窗口化证据。
3. 它不定义当前 `v0.01-plus` 的具体报告文件、脚本或评审结论。

---

## 9. 相关文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/01-system/architecture-master.md`
3. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
4. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
5. `docs/spec/v0.01-plus/records/`
