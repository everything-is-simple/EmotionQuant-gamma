# GX8 / three-level trend hierarchy refactor
**状态**: `Planned`  
**日期**: `2026-03-18`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在 GX4 ~ GX7 已经把 mainstream/countertrend、2B、1-2-3 和 G4/G5/G6 重审收口之后，能否把 trend_level 从当前的 INTERMEDIATE 单层 proxy，推进到真正的 short / intermediate / long 三层趋势并存语义。`

---

## 2. 为什么现在开这张卡

`GX4 ~ GX7` 已经证明：

1. 第四战场的统计层结论仍然站得住
2. `Gene` 的定义层已经明显比 `G8 closeout` 时更硬
3. 当前剩下的最大定义债，不再是 `2B / 1-2-3`

而是：

`trend_level 仍只是单层 INTERMEDIATE proxy`

这也是第四战场当前最后一块真正的硬骨头。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. 第四战场相关 card / record / README

本卡明确不做：

1. 不重开新的 mirror / conditioning 假设
2. 不直接改写第二战场 trigger
3. 不直接改写第三战场 sizing / exit
4. 不把 `Gene` 升格成 runtime hard gate

---

## 4. 交付物

本卡完成时应至少交付：

1. `trend_level` 三层语义的正式实现方案
2. `wave / context / parent trend` 的三层落盘说明
3. 对 `mainstream / countertrend` 的层级参照重审
4. 单测与 record

---

## 5. 验收标准

1. `trend_level` 不再只是 `INTERMEDIATE`
2. `mainstream / countertrend` 能明确回答“相对于哪一层父趋势”
3. `wave / snapshot / validation` 的语义保持一致
4. `preflight` 通过
