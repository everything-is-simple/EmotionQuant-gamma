# Selector 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`  
**历史相关文档**: `docs/design-v2/01-system/architecture-master.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史 Selector 模块参考文档**。

它保留的价值主要是：

1. 说明 `v0.01` 时期 `Selector` 的历史职责。
2. 记录当时为什么把 `MSS/IRS` 放在 Selector 前置漏斗中。
3. 给 `system-baseline.md` 提供模块级背景补充。

本文档不是仓库现行 `Selector` 设计正文。当前主线 `Selector` 权威设计已迁入 `blueprint/01-full-design/01-selector-contract-annex-20260308.md`。

---

## 2. 当前使用边界

当前阅读本文的正确用途是：

1. 回看 `v0.01 Frozen` 历史漏斗逻辑。
2. 理解历史版本中 `MSS/IRS` 的前置位置。
3. 对照当前主线为什么改成 `Selector` 只做基础过滤与规模控制。

当前不应把本文当作：

1. 当前主线 `Selector` 算法正文。
2. 当前 `MSS / IRS` 的正式设计来源。
3. 当前候选池排序或前置过滤的现行实现说明。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行口径，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行 `Selector` 设计请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
3. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
4. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`

---

## 4. `v0.01 Frozen` 中 Selector 的历史职责

历史上，`Selector` 回答的问题是：

`从全市场中先缩到可扫描候选池。`

其职责可概括为三层：

1. **基础过滤**：流动性、停牌、`ST`、次新股等。
2. **市场级漏斗**：`MSS gate`。
3. **行业级漏斗**：`IRS filter`。

历史版本里，`Selector` 输出的是候选池，而不是买卖动作。

---

## 5. 历史上保留的核心结论

### 5.1 两阶段扫描是历史高价值设计

`v0.01` 的一条重要历史结论是：

1. 全市场先做粗筛
2. 再对候选池做形态精扫

这个思路本身仍有价值，因为它解决的是计算规模与噪音控制问题，而不是某个特定版本的算法参数问题。

### 5.2 `MSS / IRS` 在历史版本中是前置漏斗

`v0.01 Frozen` 里：

1. `MSS` 历史上承担市场级前置 gate
2. `IRS` 历史上承担行业级前置 filter

这和当前主线已经不同，但作为历史对照仍然值得保留。

### 5.3 候选池分数只是 Selector 内部排序

历史版本里，`StockCandidate.score` 的角色是：

1. 仅服务候选池内部排序
2. 不直接替代 `PAS` 形态触发
3. 不直接成为最终交易分数

这条边界在今天仍值得保留。

---

## 6. 历史摘要：MSS / IRS / Gene 在 Selector 中的角色

### 6.1 MSS

历史版本中的 `MSS` 作用是：

1. 读市场快照
2. 计算市场温度
3. 输出 `BULLISH / NEUTRAL / BEARISH`
4. 在 `Selector` 阶段决定是否放行当日候选

### 6.2 IRS

历史版本中的 `IRS` 作用是：

1. 读行业日线聚合
2. 计算行业排序
3. 输出 `Top-N` 强势行业
4. 在 `Selector` 阶段缩小候选行业范围

### 6.3 Gene

历史版本中 `gene` 的定位更接近：

1. 第 2 迭代预留
2. 事后分析候选
3. 不是 `v0.01` 的实时主链路

这也是它今天不应被误读成历史正式口径的原因。

---

## 7. 历史验证顺序的保留价值

本文最值得保留的一条历史治理结论，是强制消融顺序：

1. `BOF baseline`
2. `BOF + MSS`
3. `BOF + MSS + IRS`

这条顺序的重要性在于：

1. 防止把 `MSS/IRS` 直接当成默认有效。
2. 强迫历史版本逐步验证漏斗增益。
3. 为后续主线切换留下了清晰的证据轨迹。

---

## 8. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级，不再作为当前执行语义：

1. 文内 `mss.py / irs.py / gene.py / selector.py` 的详细代码草案。
2. 历史版 `MSS` 六因子、`IRS` 两因子公式细节。
3. `gene` 第 2 迭代设计与未来计划。
4. 任何把本文当作当前 `Selector` SoT 的使用方式。

这些内容保留追溯价值，但已不再承担现行设计职责。

---

## 9. 与当前主线的关系

本文与当前主线的关系固定为：

1. 它说明历史版本里 `Selector` 曾承担 `MSS/IRS` 前置漏斗。
2. 它帮助解释为什么当前主线把 `Selector` 降回基础过滤与规模控制。
3. 它不定义当前主线的正式 `Selector` 契约和实现。

---

## 10. 相关文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/01-system/architecture-master.md`
3. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
4. `docs/spec/common/records/development-status.md`
