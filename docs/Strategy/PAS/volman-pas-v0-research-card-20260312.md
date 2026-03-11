# Volman PAS v0 最小研究卡

**文档版本**：`Draft v0.01`  
**文档状态**：`Active`  
**创建日期**：`2026-03-12`  
**变更规则**：`允许继续调整候选集、问题定义和实验边界；不直接进入当前主线默认路径。`

> **定位说明**：本文不是当前主线实施卡，而是一张研究卡。  
> 目标不是马上上线，而是先定义：`如果要从 Volman 单独开一条 PAS 研究线，v0 最小集合应该包含谁。`

---

## 1. v0 固定目标

`Volman PAS v0` 只回答一个问题：

`在不改写当前主线 BOF baseline 的前提下，Volman 语义里哪几类结构值得先被当成独立 alpha object 去做第一轮 provenance。`

这张卡不做：

1. 全七结构 detector 化
2. 主线切换
3. 直接给 `SB / FB / RB_FAKE` 判定“谁已经胜出”

---

## 2. v0 候选集

`Volman PAS v0` 首轮固定只保留三类独立候选：

1. `RB_FAKE`
2. `FB`
3. `SB`

原因很简单：

1. 这三类都有完整结构语义
2. 这三类都能单独定义触发与失效
3. 这三类都比 `IRB / DD / BB / ARB` 更像 standalone alpha object

---

## 3. 一条额外硬约束：别放过 SB

`SB` 在这张卡里不是“可选带上”，而是明确保留对象。

原因不是个人偏好，而是它在结构上确实有一个很强的研究价值：

1. 第一次失败制造怀疑
2. 第二次失败制造恐慌
3. forced exit 的力度理论上可能比一次性失败更重

因此 `SB` 要回答的核心问题不是：

`它像不像 CPB。`

而是：

`第二次失败后的清算链，是否能形成比 BOF 更强或不同型的 alpha。`

在没有证据之前，不能宣布 `SB` 比 `BOF` 更强；  
但在研究优先级上，也不能因为它复杂就把它从第一批候选里删掉。

---

## 4. 三个候选各自要回答什么

### 4.1 `RB_FAKE`

核心问题：

`Volman 版假突破失败，是否比当前 BOF detector 更接近原始 breakout-failure edge。`

它最适合作为：

1. reversal family 对照
2. `BOF` 的 Volman 语义细化版

### 4.2 `FB`

核心问题：

`首次回撤恢复，是否是独立于泛 PB/BPB 的 continuation alpha。`

它最适合作为：

1. trend continuation family 候选
2. `first pullback` 稀缺性验证对象

### 4.3 `SB`

核心问题：

`第二次失败后的再突破，是否会因为累积 trapped traders 与士气崩塌而带来更强 continuation edge。`

它最适合作为：

1. second-chance continuation family 候选
2. `double failure liquidation` 假说验证对象

---

## 5. v0 明确不独立化的对象

首轮先不单独立项：

1. `IRB`
2. `DD`
3. `BB`
4. `ARB`

原因分别是：

1. `IRB` 更像 timing refinement
2. `DD` 更像 micro trigger
3. `BB` 更像 pressure / quality enhancer
4. `ARB` 更像 composite structure layer

它们可以进入 sidecar，但不应抢第一批独立 detector 的位置。

---

## 6. v0 建议分层

### 6.1 独立 detector 层

1. `RB_FAKE`
2. `FB`
3. `SB`

### 6.2 sidecar 层

1. `IRB_handle`
2. `DD_hold`
3. `BB_pressure`

### 6.3 composite 层

1. `ARB_bias`

---

## 7. v0 建议研究顺序

如果按“最值得先问的问题”排序，我建议：

1. `RB_FAKE`
   - 先看它和当前 `BOF` 的重叠与增量差异
2. `SB`
   - 直接回答“第二次失败是否真比一次失败更有料”
3. `FB`
   - 作为顺势 continuation 对照

也就是说：

`SB` 不一定先于 `RB_FAKE` 落地，但一定要在第一轮最小集合里。

---

## 8. v0 的最小交付物

如果后面真要执行，我建议最小交付物只要这些：

1. 一份 `Volman PAS v0` implementation note
2. 一个只比较 `RB_FAKE / FB / SB` 的长窗 matrix
3. 一份 provenance digest
4. 一份和当前 `BOF` baseline 的归因对照

在这之前，不要先写：

1. 全量 taxonomy
2. 大而全 detector registry
3. 花哨的 quality 体系

---

## 9. 一句话结论

`Volman PAS v0` 的第一批对象不该只有 `RB_FAKE`，也不能把 `SB` 因为复杂就提前删掉；更稳的最小集合是 `RB_FAKE / FB / SB`，其中 `SB` 必须被保留为第一批核心候选。
