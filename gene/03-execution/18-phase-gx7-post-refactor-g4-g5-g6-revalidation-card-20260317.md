# GX7 / post-refactor G4-G5-G6 revalidation
**状态**: `Planned`  
**日期**: `2026-03-17`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在 trend_level、mainstream/countertrend、2B、1-2-3 语义修正之后，G4 / G5 / G6 的统计读数和治理结论是否仍然成立，还是需要重写 validation / mirror / conditioning 的正式口径？`

---

## 2. 为什么现在开这张卡

[`../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md)
已经明确写死：

1. 定义层必须先于统计层
2. `mirror / conditioning / score / band` 不能反向篡改定义层
3. 如果前面的定义修正真的落到代码，就必须显式重审：
   - `snapshot / validation`
   - `mirror`
   - `conditioning`

所以这张卡不是新研究，而是“定义整改之后的强制复核卡”。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. `G4 / G5 / G6` 相关执行 record、evidence 与文档入口

本卡明确不做：

1. 不新增新的因子分位体系
2. 不新增新的 mirror 目标域
3. 不新增新的 conditioning pattern family
4. 不直接把任何研究读数升格成 runtime hard gate

---

## 4. 交付物

本卡完成时应至少交付：

1. `G4 / G5 / G6` 的重跑结果
2. 对旧结论“保留 / 修订 / 撤回”的正式说明
3. 更新后的 record 与 evidence
4. 对第四战场 closeout 口径的必要修订

---

## 5. 验收标准

1. `validation / mirror / conditioning` 不再继续消费已经过时的结构语义
2. `G4 / G5 / G6` 的正式结论能追溯到修正后的定义层
3. 文档入口、record、evidence 与代码口径一致
4. `preflight` 通过

---

## 6. 当前判断

这张卡是 `GX3 ~ GX6` 之后的收口卡，不是并行卡。

一句话：

`前面几张卡修定义，这张卡负责验定义修完之后，旧统计结论还能不能继续站住。`
