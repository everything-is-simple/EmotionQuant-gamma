# GX3 / trend-level context refactor

**状态**: `Completed`
**日期**: `2026-03-17`
**类型**: `post-closeout targeted hypothesis`
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡原本只回答一个问题：

`在不提前重写 2B / 1-2-3 语义的前提下，能否先把第四战场的 trend_level 与 context 语义正式落到 gene.py，并把当前单层 major_trend 口径降格为诚实的 intermediate proxy。`

---

## 2. 这张卡真实完成了什么

`GX3` 真正完成的不是三层 hierarchy 本体，而是第一阶段的“语义诚实化”：

1. `trend_level` 正式进入 `l3_gene_wave / l3_stock_gene`
2. `context_trend_level / context_trend_direction_*` 等字段正式进入 schema
3. `wave_role_basis / current_wave_role_basis` 被写成诚实的 proxy 口径
4. 当前实现不再把单层 `major_trend` 伪装成最终无层级定义

也就是说：

`GX3` 负责把“趋势有层级”这件事正式写进实现与落盘字段，但不声称自己已经完成三层趋势并存。`

---

## 3. 这张卡明确没有完成什么

`GX3` 第一阶段刻意没有完成：

1. `SHORT / INTERMEDIATE / LONG` 三层趋势并存
2. `mainstream / countertrend` 的真正上级参照层
3. `2B` 的层级化时间窗
4. `1-2-3` 的三条件 detector
5. `G4 / G5 / G6` 的后续重审收口

这些剩余项后来分别由：

1. `GX4`
2. `GX5`
3. `GX6`
4. `GX7`
5. `GX8`

接力完成。

---

## 4. 为什么现在可以收口

现在可以把 `GX3` 从 `Active` 收口，不是因为它当年自己把所有事都做完了，而是因为：

1. 它承诺的“第一阶段诚实化”已经完成
2. 当年保留的 hierarchy 定义债，已经由 [`19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](19-phase-gx8-three-level-trend-hierarchy-card-20260318.md) 真正补完
3. 当前再让 `GX3` 挂着 `Active`，只会制造治理口径不一致

因此这张卡现在的正确状态不是“继续实现”，而是：

`Completed via phase-1 delivery + formal handoff to GX8`

---

## 5. 文档口径

这张卡的正式口径现在固定为：

1. `GX3` 不重做代码
2. `GX3` 不冒充自己完成了三层 hierarchy
3. `GX3` 以第一阶段成果完成收口
4. 剩余 hierarchy 债由 `GX8` 接力并最终收口

---

## 6. 一句话结论

`GX3` 完成的是“先把 trend_level / context proxy 说诚实”，不是“把三层趋势全部做完”；现在它应以 formal handoff 方式收口，而不是继续假装自己仍在实现中。`

---

## 7. 文档入口

1. 配套 record：[`records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`](records/14-phase-gx3-trend-level-context-refactor-record-20260317.md)
2. 第一阶段 stage evidence：[`evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md`](evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md)
3. 接力 closeout：[`19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](19-phase-gx8-three-level-trend-hierarchy-card-20260318.md)
