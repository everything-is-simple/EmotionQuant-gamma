# Positioning Backlog Methods Note

**日期**: `2026-03-13`  
**对象**: `第三战场后续队列补充说明`  
**状态**: `Active`

---

## 1. 目标

本文用于把《交易圣经 系统交易赢利要诀》目录里值得保留到第三战场后续队列的方法记下来，避免当前只盯着 `P2` 首批 sizing family 时，把后面真正有研究价值的方法遗忘掉。

本文不是当前 active card。

本文只负责：

1. 记录哪些方法已经进入 `P2`
2. 记录哪些方法值得后置进入 backlog
3. 说明为什么它们现在不抢占主队列

---

## 2. 已进入当前主队列的方法

书中第 8 章《资金管理》里，当前已经进入第三战场正式执行范围的方法有：

1. `fixed-risk`
2. `fixed-capital`
3. `fixed-ratio`
4. `fixed-unit`
5. `williams-fixed-risk`
6. `fixed-percentage`
7. `fixed-volatility`

这些方法已经冻结进：

`P2 / sizing family replay`

当前第三战场不会遗漏它们。

---

## 3. 明确保留到 backlog 的方法

### 3.1 Kelly

`Kelly` 必须保留到第三战场 backlog。

原因：

1. 它是资金管理方法族中的核心方法之一
2. 它本质上是在把已知 edge 转译成复利下注比例
3. 它对 `edge / odds` 的估计稳定性要求极高

当前不进入主队列的原因：

1. 第三战场当前还在跑最基础的 sizing family matrix
2. 现在直接上 `Kelly`，容易把估计误差放大成仓位灾难
3. 它更适合作为 retained sizing candidate 之后的增强组，而不是起手组

### 3.2 Fractional Kelly

`fractional Kelly` 必须和 `Kelly` 一起保留。

原因：

1. 真正可运营的 `Kelly` 通常不是满 Kelly，而是 `half Kelly / quarter Kelly / capped Kelly`
2. 它更贴近个人账户和不完全稳定 edge 的现实
3. 如果未来真的要开 `Kelly lane`，正式主对象更可能是 `fractional Kelly`，而不是 full Kelly

当前不进入主队列的原因：

1. 需要在 `P2 / P9` 之后，先知道是否存在 retained sizing baseline
2. 需要先知道我们对 `edge` 的估计是否足够稳定

### 3.3 Leverage Cap

`leverage cap` 必须保留为独立议题。

原因：

1. 仓位方法本身和账户级总杠杆上限不是一回事
2. 书中把“资金管理”和“交易杠杆”并列，提醒我们不能把两者混成同一层
3. 如果未来主线迁移，需要单独一层 `portfolio-level leverage cap`

当前不进入主队列的原因：

1. 当前第三战场还在回答单笔和单策略层的 `买多少`
2. 总杠杆上限属于更高层组合风险约束，不该抢在 `P2` 前定义

### 3.4 System-Defect Review

`system-defect review` 必须保留为第三战场的固定复核维度。

这里不是一种 sizing formula，而是一条裁决纪律：

`仓位方法不能被当成 alpha 替代品；它既可能放大优势，也可能放大系统缺陷。`

要点：

1. 一个在 `Normandy` 里已经被读成 `no-go` 的 PAS，不允许靠激进 sizing 直接翻案
2. sizing 改善必须区分“放大真实 edge”和“放大脆弱路径”
3. 后续 retained candidate 都应该补一条 `system-defect review`

---

## 4. 当前明确不进入主队列的方法

以下对象当前只保留概念层价值，不进入第三战场主队列：

1. `martingale`
2. `anti-martingale` 作为单独实验名词

原因：

1. `martingale` 当前只保留为反例
2. `anti-martingale` 的有价值部分已经被吸收到 `fixed-ratio / Kelly family` 的后续讨论里

---

## 5. 当前排序

第三战场当前的实际顺序固定为：

1. 先完成 `P2 / sizing family replay`
2. 再完成 `P9 / retained-or-no-go`
3. 若出现 retained sizing candidate，再决定是否打开：
   - `single-lot sanity replay`
   - `cross-exit sensitivity`
   - `Kelly / fractional Kelly follow-up`
   - `leverage cap`
   - `system-defect review`

---

## 6. 正式结论

当前 backlog methods 的正式口径固定为：

1. `Kelly` 值得做，但不是当前最短闭环的第一枪
2. `fractional Kelly` 比 full Kelly 更像未来真实可运营的研究对象
3. `leverage cap` 必须单独建模，不能和 sizing formula 混成一层
4. `system-defect review` 必须成为第三战场后续 retained candidate 的固定复核维度
5. 当前第三战场继续坚持：先把基础 sizing family 一张张跑成证据，再谈 Kelly 增强组

---

## 7. 一句话结论

`Kelly 很重要，但它现在属于 backlog；第三战场当前必须先把基础 sizing family 跑成证据，再谈 Kelly、杠杆上限和系统缺陷复核。`
