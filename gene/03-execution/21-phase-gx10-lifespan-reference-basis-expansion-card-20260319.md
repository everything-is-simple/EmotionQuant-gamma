# GX10 / 寿命参考基础扩充卡
**状态**: `Completed`  
**日期**: `2026-03-19`  
**类型**: `targeted semantic implementation`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`能否把当前“简化版年龄尺”的 duration 语义，推进成更接近书义的寿命参考基础，而不直接把第四战场变成交易系统。`

---

## 2. 为什么必须开这张卡

当前审计已经确认三件事：

1. `duration_percentile` 是当前最值得继续深做的主轴
2. 当前实现仍主要是 `time-only ruler`
3. 当前 `GENE_LOOKBACK_TRADE_DAYS = 260`，历史深度对寿命轴明显偏浅

因此如果还要继续沿着寿命轴往下做，必须先补参考基础，而不是继续只围着 `p65 / p95` 打转。

---

## 3. 本卡允许修改

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. `gene` 相关 spec / record / evidence 入口

---

## 4. 本卡必须交付的最小语义

### 4.1 历史深度诚实化

必须显式回答：

1. 当前寿命参照是否仍固定 `260` 日
2. 若不是，新的历史深度如何确定
3. snapshot 中如何告诉下游“当前寿命样本有多深”

### 4.2 相对前一主要波段的折返宽度基础

必须把下面这个问题机械化：

`当前波段相对于前一主要波段，已经走了多少折返宽度`

这一层至少要有正式字段，不允许继续只停留在口头解释。

### 4.3 宽度 + 时间联合寿命读数

必须补一层正式输出，至少能回答：

1. 当前波段只看时间有多老
2. 当前波段只看宽度有多深
3. 把宽度和时间一起看时，它在自身历史里有多靠后

这里允许是：

1. `joint_percentile`
2. `joint_band`
3. `odds-style summary`

但不允许只把旧 `duration_percentile` 换个名字。

---

## 5. 本卡明确不做

1. 不直接决定新的 runtime gate
2. 不直接重写 `Phase 9B`
3. 不直接推进 mirror / conditioning
4. 不直接开组合 replay

---

## 6. 验收标准

1. 寿命轴不再只有 `time-only` 参照
2. 历史深度与样本规模对下游是可见的
3. 相对前一主要波段的折返宽度已有正式字段
4. 单测覆盖新语义
5. 文档明确写清“这仍是第四战场历史尺，不是直接交易决策”

---

## 7. 完成结果

本卡当前正式完成了三组最小交付：

1. 把寿命参考深度从单一 `260` 日结构窗口，拆成：
   `GENE_STRUCTURE_LOOKBACK_TRADE_DAYS = 260`
   `GENE_LIFESPAN_REFERENCE_TRADE_DAYS = 1260`
   并把 snapshot / wave ledger 的 `history_reference_trade_days` 与 `history_span_trade_days` 正式落盘
2. 补上相对前一主要波段的折返宽度字段：
   `prior_mainstream_wave_id`
   `prior_mainstream_magnitude_pct`
   `retracement_vs_prior_mainstream_pct`
3. 补上宽度 + 时间联合寿命读数：
   `lifespan_joint_percentile`
   `lifespan_joint_band`

这轮实现只把“寿命参考基础”补实，没有直接改写第一战场运行面，也没有把第四战场升级为 runtime hard gate。

验证口径当前写定为：

1. `py_compile` 已通过
2. `tests/unit/selector/test_gene.py` 新语义断言已补齐
3. 正式 `pytest` 在当前 Windows 会话里仍受 `basetemp` 权限问题干扰，因此本轮同时保留了等价手工 smoke 验证记录

配套 record：

[`records/21-phase-gx10-lifespan-reference-basis-expansion-record-20260319.md`](./records/21-phase-gx10-lifespan-reference-basis-expansion-record-20260319.md)

---

## 8. 下一步

本卡完成后，固定进入：

[`22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md`](./22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md)

一句话收口：

`GX10` 先把寿命尺的参考基础补对，再谈运行面怎么消费。`
