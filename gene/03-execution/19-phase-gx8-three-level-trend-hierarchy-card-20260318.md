# GX8 / 三层趋势层级重构卡
**状态**: `Completed`
**日期**: `2026-03-18`
**类型**: `post-closeout targeted hypothesis`
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一件事：

`在 GX4 ~ GX7 已经把 mainstream/countertrend、2B、1-2-3 和 G4/G5/G6 的语义收口之后，能否把 trend_level 从单层 INTERMEDIATE proxy 推进到真正的 SHORT / INTERMEDIATE / LONG 三层并存语义。`

---

## 2. 本轮正式完成了什么

1. `l3_gene_wave` 不再只写 `INTERMEDIATE`
2. `SHORT / INTERMEDIATE / LONG` 三层 wave 已正式落库
3. `context_trend_level` 已能明确回答“当前 wave 相对于哪一层父趋势”
4. `wave_role_basis` 已分层写实：
   - `SHORT_PARENT_CONTEXT_DIRECTION`
   - `INTERMEDIATE_PARENT_CONTEXT_DIRECTION`
   - `LONG_SELF_DIRECTION_BOOTSTRAP`
5. `2B` 时间窗已随层级一起落盘：
   - `SHORT -> 1 bar`
   - `INTERMEDIATE -> 5 bar upper-bound`
   - `LONG -> 10 bar upper-bound`
6. `l3_stock_gene` 已新增三层 active snapshot 字段：
   - `current_short_*`
   - `current_intermediate_*`
   - `current_long_*`

---

## 3. 本轮刻意没有做什么

1. 不重开 `G4 / G5 / G6`
2. 不把 Gene 直接升格成 runtime hard gate
3. 不重写第二战场 trigger
4. 不直接改写第三战场 sizing / exit

---

## 4. 兼容口径

为避免偷偷改坏第一战场已完成的 isolated validation，本轮保留了一个显式兼容层：

1. `l3_stock_gene` 现有的 canonical 字段仍保持 `INTERMEDIATE proxy` 口径
2. 真正的三层 hierarchy 通过新增的 `current_short_* / current_intermediate_* / current_long_*` 字段暴露
3. 因此：
   - `GX8` 已完成
   - 但过去基于 proxy 口径收下来的 `Phase 9B` 结果不会被静默篡改

---

## 5. 交付物

1. 三层 wave ledger 实现
2. 三层 active snapshot hierarchy 字段
3. schema v15 迁移
4. `GX8` evidence
5. `GX8` record
6. 单测与预检通过记录

---

## 6. 验收结论

本卡验收标准现已满足：

1. `trend_level` 不再只是 `INTERMEDIATE`
2. `mainstream / countertrend` 已能回答相对于哪一层父趋势
3. `wave / snapshot / validation` 三层口径已明确分离并保持可审计一致
4. `pytest tests/unit/selector/test_gene.py -q` 已通过
5. `preflight` 已通过

---

## 7. 下一步

`GX8` 收口后，第四战场当前最自然的下一步不再是继续补 hierarchy，而是进入第一战场：

[`../../blueprint/03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md`](../../blueprint/03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md)

一句话收口：

`GX8 已经把“只有单层 INTERMEDIATE proxy”的定义债，推进成了“wave 真三层 + snapshot 三层暴露 + canonical 中层兼容视图”的正式实现。`
