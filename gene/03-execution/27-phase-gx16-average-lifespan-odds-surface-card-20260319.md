# GX16 / 平均寿命赔率面接入卡
**状态**: `Completed`  
**日期**: `2026-03-19`  
**类型**: `targeted semantic implementation`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`能否把图 26-1 背后的平均寿命 / odds 框架，正式接入 Gene 的 wave / snapshot / distribution surface。`

---

## 2. 为什么必须开这张卡

只做四分位分布还不够。  
`345` 页开始的框架强调的是：

1. 当前走势还剩多少寿命
2. 当前走势已经老化到什么程度
3. 这两个概率之间的赔率关系

如果不把这层接入，Gene 仍然只是在做“分布读数”，还没进入书里的“平均寿命风险框架”。

---

## 3. 本卡必须交付

1. `magnitude_remaining_prob`
2. `duration_remaining_prob`
3. `lifespan_average_remaining_prob`
4. `lifespan_average_aged_prob`
5. `lifespan_remaining_vs_aged_odds`
6. `lifespan_aged_vs_remaining_odds`

并且这些字段必须同时进入：

1. `l3_gene_wave`
2. `l3_stock_gene`
3. `l3_gene_distribution_eval`

---

## 4. 完成结果

本卡当前已正式完成：

1. schema 已升级到 `v19`
2. 平均寿命赔率字段已进入 wave / snapshot / distribution_eval
3. 语义上采用中性合同：
   - `remaining`
   - `aged`
   - `odds`
   不直接写死成多/空交易判断
4. 定向单测已通过

配套 record：

[`records/27-phase-gx16-average-lifespan-odds-surface-record-20260319.md`](./records/27-phase-gx16-average-lifespan-odds-surface-record-20260319.md)

---

## 5. 一句话收口

`GX16` 把图 26-1 的平均寿命 / odds 框架正式接进了 Gene 的对象合同。`
