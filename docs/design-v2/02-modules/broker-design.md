# Broker 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史 Broker 模块参考文档**。

它保留的价值主要是：

1. 记录 `v0.01` 时期 `Broker` 的历史职责与边界。
2. 说明为什么回测与纸上交易共用同一 `Broker` 内核。
3. 补充 `T+1 Open`、仓位风控与信任分级在历史版本中的模块级语义。

本文档不是仓库现行 `Broker / Risk` 正文。当前主线正式设计已迁入 `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`。

---

## 2. 当前使用边界

当前阅读本文的正确用途是：

1. 回看 `v0.01 Frozen` 的历史执行语义如何在 `Broker` 层落地。
2. 理解历史版本中仓位、止损、撮合与信任状态机的大致边界。
3. 对照当前主线为什么把正式 `Broker / Risk` 正文迁入 `blueprint/`。

当前不应把本文当作：

1. 当前主线 `Broker / Risk` 的正式设计来源。
2. 当前代码实现的直接说明书。
3. 当前风控倍率、overlay 或执行状态机的权威定义。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行口径，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行 `Broker / Risk` 设计请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
3. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
4. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`

---

## 4. `v0.01 Frozen` 中 Broker 的历史职责

历史上，`Broker` 回答的问题是：

`收到 Signal 之后，是否允许开仓、何时成交、何时退出。`

其职责可概括为四层：

1. **开仓前检查**：仓位、重复持仓、冷却与信任状态。
2. **订单生成**：把 `Signal` 转成 `Order`。
3. **撮合成交**：按 `T+1 Open` 语义成交或拒绝。
4. **持仓管理**：止损、止盈、组合回撤与连续亏损熔断。

历史版本中，`Broker` 是唯一真正“有钱、有仓位”的模块。

---

## 5. 历史上保留的核心结论

### 5.1 回测与纸上交易共用同一内核

`v0.01` 最值得保留的一条历史设计，是：

1. 回测不用一套独立的交易语义
2. 纸上交易也不用另一套简化规则
3. 两者共用同一 `Broker` 内核

这个结论的长期价值在于：回测结果和后续模拟执行至少共享一套撮合与风险边界。

### 5.2 `T+1 Open` 是历史版本的核心执行语义

历史版本中，`Broker` 真正重要的不是实现细节，而是固定语义：

1. `signal_date = T`
2. `execute_date = T+1`
3. 成交价 = `T+1 Open`

这条语义是 `v0.01 Frozen` 的核心约束，今天仍然只能由 `system-baseline.md` 定义。

### 5.3 风控优先于交易管理花样

历史版本里，`Broker` 的关注重点不是复杂交易管理，而是：

1. 单笔风险
2. 失效优先退出
3. 连续亏损熔断
4. 组合回撤保护

这说明历史版本更关心“先别死”，而不是把执行层做成复杂 alpha 引擎。

---

## 6. 历史摘要：Risk / Matcher / Trust 的角色

### 6.1 Risk

历史版本中的 `RiskManager` 主要承担：

1. 开仓前检查
2. 仓位大小控制
3. 持仓期止损/止盈检查
4. 连亏与回撤熔断

### 6.2 Matcher

历史版本中的 `Matcher` 主要承担：

1. 根据 `execute_date` 推进订单
2. 读取市场数据完成撮合
3. 输出 `FILLED / REJECTED`
4. 记录费用与成交明细

### 6.3 Trust Tier

历史版本中的信任分级主要承担：

1. 把个股分成可交易、观察、冷却等状态
2. 对连续失败标的施加额外约束
3. 让纸上观察与正式交易共享同一条状态链

这套机制今天仍有参考价值，但不应继续被误读成现行正文。

---

## 7. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级：

1. 文内 `RiskManager / Matcher / Broker` 的详细代码草案。
2. 历史版本的具体阈值、天数和配置项清单。
3. 详细的 `Order / Trade` 生命周期实现细节。
4. 任何把本文当作当前 `Broker / Risk` SoT 的用法。

这些内容保留追溯价值，但已不再承担现行设计职责。

---

## 8. 与当前主线的关系

本文与当前主线的关系固定为：

1. 它说明历史版本里 `Broker` 如何承接 `T+1 Open` 语义。
2. 它帮助解释为什么当前主线仍坚持统一执行内核。
3. 它不定义当前主线的 overlay、capacity、risk regime 或正式状态机。

---

## 9. 相关文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/01-system/architecture-master.md`
3. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
4. `docs/spec/common/records/development-status.md`
