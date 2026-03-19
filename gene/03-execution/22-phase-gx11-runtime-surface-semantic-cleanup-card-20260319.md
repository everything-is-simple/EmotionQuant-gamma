# GX11 / 运行面语义清理卡
**状态**: `Planned`  
**日期**: `2026-03-19`  
**类型**: `targeted contract cleanup`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在不偷改第四战场定义的前提下，能否把当前 Gene snapshot 里最容易误导人的运行面字段，整理成更诚实、更顺手、也更不容易被偷带的合同。`

---

## 2. 为什么必须开这张卡

本轮审计已经确认下面三类混淆：

1. `current_wave_age_band` 与 `current_wave_duration_band` 当前是同一个东西
2. `context_trend_direction_before` 的治理文案与 `current_context_trend_direction` 的 runtime 字段名并不完全同名
3. `reversal_state` 是压缩语义，方便但不够透明

这些问题不一定立刻做坏结果，但会让后续：

1. 组合 freeze
2. isolated validation
3. 运行时接线

都更容易带进语义漂移。

---

## 3. 本卡允许修改

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. Gene 相关 spec / record / runbook 文案

---

## 4. 本卡必须完成的清理项

### 4.1 `age_band` 定位收口

必须明确写死：

1. `current_wave_age_band` 是正式独立字段
2. 或它只是 `duration` 的展示别名

不允许继续维持“代码里重复、文档里像两回事”的状态。

### 4.2 `context` 口径诚实化

必须明确回答：

1. canonical snapshot 里的 `current_context_trend_level` 到底代表哪一层
2. hierarchy snapshot 与 canonical snapshot 的关系
3. 运行时应该读哪个字段，文档应如何叫它

### 4.3 `reversal_state` 透明化

必须让下游能直接看出：

1. 当前 reversal 是 `confirmed turn`
2. 还是 `2B watch`
3. 还是 `countertrend watch`

压缩字段可以保留，但不能再让它成为唯一可消费视图。

---

## 5. 本卡明确不做

1. 不重新定义 `1-2-3 / 2B`
2. 不直接修改 `Phase 9` 的裁决
3. 不新增新的组合字段
4. 不把 `mirror / conditioning / gene_score` 偷带进 runtime 入口

---

## 6. 验收标准

1. duplicate / alias / proxy 字段边界已写清
2. canonical snapshot 与 hierarchy snapshot 的消费边界已写清
3. `reversal_state` 透明度已提升
4. 单测已覆盖关键兼容层
5. 文档与代码口径一致

---

## 7. 下一步

本卡完成后，固定进入：

[`23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md`](./23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md)

一句话收口：

`GX11` 负责把 Gene 运行面从“能用但容易误读”清成“诚实且不容易偷带歧义”的合同。`

