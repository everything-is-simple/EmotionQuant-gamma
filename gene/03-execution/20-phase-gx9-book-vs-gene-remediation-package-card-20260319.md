# GX9 / 书义对齐整改包
**状态**: `Completed`  
**日期**: `2026-03-19`  
**类型**: `post-audit remediation package`  
**直接目标文件**: `gene / src/selector/gene.py / src/data/store.py / tests/unit/selector/test_gene.py`

---

## 1. 目标

这张卡只回答一件事：

`在《专业投机原理》对照审计已经把问题说清之后，第四战场下一轮整改应该怎么拆卡，才能既修正寿命/趋势/转折语义，又不把第一战场的 Phase 9 运行验证和 Gene 统计层混成一锅。`

---

## 2. 上游输入

1. [`records/20-phase-gx9-book-vs-gene-audit-record-20260319.md`](records/20-phase-gx9-book-vs-gene-audit-record-20260319.md)
2. [`../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md)
3. [`../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md)
4. [`../../blueprint/03-execution/17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](../../blueprint/03-execution/17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md)
5. [`../../blueprint/03-execution/17.9-phase-9f-frozen-combination-replay-card-20260319.md`](../../blueprint/03-execution/17.9-phase-9f-frozen-combination-replay-card-20260319.md)

---

## 3. 本卡的正式判断

本轮审计之后，真正需要开的不是一张“大而全重构卡”，而是三张更小的执行卡：

1. `GX10 / lifespan reference-basis expansion`
2. `GX11 / runtime surface semantic cleanup`
3. `GX12 / post-remediation revalidation and Phase 9 resync`

理由固定为：

1. `寿命轴` 的问题是“参考基础不够书义”
2. `context / reversal / age-band` 的问题是“运行面字段语义不够诚实、不够顺手”
3. 一旦前两件事真的落代码，`G4 / G5 / G6 / Phase 9` 都必须重新确认，不允许沿用旧证据口头硬接

---

## 4. 拆卡边界

### 4.1 `GX10` 负责什么

只负责修寿命轴的参考基础，包括：

1. 历史深度
2. 相对前一主要波段的折返宽度参照
3. 宽度 + 时间联合寿命读数

### 4.2 `GX11` 负责什么

只负责修运行面语义，包括：

1. `current_wave_age_band` 的别名定位
2. `current_context_*` 与 `context_*` 的口径诚实化
3. `reversal_state` 的压缩语义透明化
4. canonical snapshot 与 hierarchy snapshot 的使用边界

### 4.3 `GX12` 负责什么

只负责重验证与回灌，包括：

1. `G4 / G5 / G6`
2. `Phase 9B` 已证明三要素
3. `17.8 / 17.9` 的后续是否继续沿用旧 proxy surface

---

## 5. 与第一战场的关系

本卡明确写死：

1. `17.8 / 17.9` 不删除
2. 但若 `GX10 / GX11` 真正改写了 `duration / context / reversal` 的字段语义或计算基础，则 `17.8 / 17.9` 不得继续假装消费旧 surface 就够了
3. `GX12` 必须明确回答：
   - `Phase 9` 继续沿用旧 proxy evidence
   - 或 `Phase 9` 需要在整改后 surface 上重跑

---

## 6. 交付物

本卡完成时至少要留下：

1. 三张已开出的新卡
2. 每张卡的边界、顺序和依赖关系
3. 对 `Phase 9` 的影响边界说明

---

## 7. 完成结果

`GX9` 已完成本卡原定目标：

1. 审计记录已落盘：
   [`records/20-phase-gx9-book-vs-gene-audit-record-20260319.md`](records/20-phase-gx9-book-vs-gene-audit-record-20260319.md)
2. 三张下游整改卡已开出：
   - [`21-phase-gx10-lifespan-reference-basis-expansion-card-20260319.md`](./21-phase-gx10-lifespan-reference-basis-expansion-card-20260319.md)
   - [`22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md`](./22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md)
   - [`23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md`](./23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md)
3. `GX10 / GX11 / GX12` 与 `17.8 / 17.9` 的关系边界已经写明

因此本卡的 truthful 角色现已完成：

`先完成书义对齐审计，再把整改落成明确的小卡队列，而不是继续用口头方式推进。`

---

## 8. 下一步

按当前问题优先级，下一张执行卡固定为：

[`21-phase-gx10-lifespan-reference-basis-expansion-card-20260319.md`](./21-phase-gx10-lifespan-reference-basis-expansion-card-20260319.md)

一句话收口：

`GX9` 不是自己下场改代码，而是把“书义对齐整改”拆成寿命基础、运行面语义、强制重验证三张小卡。`
