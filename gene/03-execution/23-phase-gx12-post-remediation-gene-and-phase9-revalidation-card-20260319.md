# GX12 / 整改后 Gene 与 Phase 9 重验证卡
**状态**: `Planned`  
**日期**: `2026-03-19`  
**类型**: `forced downstream revalidation`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`如果 GX10 / GX11 真的改动了寿命参考基础或运行面语义，G4 / G5 / G6 以及第一战场 Phase 9 的旧结论还能不能直接保留。`

---

## 2. 为什么必须开这张卡

当前不允许发生下面这种事：

1. 代码里的寿命和 context 语义已经变了
2. 但 `G4 / G5 / G6 / Phase 9B / 17.8 / 17.9` 继续假装旧 evidence 还原样有效

如果前面的整改真的落地，这张卡就是强制卡，不是可选卡。

---

## 3. 本卡必须覆盖的对象

1. `G4 / validation`
2. `G5 / mirror`
3. `G6 / conditioning`
4. `Phase 9B / duration_percentile`
5. `Phase 9B / context_trend_direction_before`
6. `Phase 9B / reversal_state`
7. `17.8 / duration sweep` 是否继续沿用旧 proxy surface
8. `17.9 / frozen combination replay` 是否需要等待新 surface

---

## 4. 本卡必须正式留下的结论

至少要写清：

1. 哪些旧结论可以 `keep`
2. 哪些旧结论必须 `rerun`
3. `Phase 9` 当前应读成：
   - `continue on legacy proxy surface`
   - 或 `pause and reopen on remediated surface`

---

## 5. 本卡明确不做

1. 不新增新的 Gene 因子
2. 不扩大 Phase 9 组合面
3. 不口头提前宣布 Gene package promotion

---

## 6. 验收标准

1. 所有受影响下游对象都已被明确裁定 `keep / rerun`
2. `17.8 / 17.9` 与整改后 Gene 的关系已写明
3. 不存在“代码已换面，但 evidence 继续沿用旧面”的治理漏洞

---

## 7. 一句话状态

`GX12` 是整改后的强制收口卡；前面真改了语义，后面就必须老老实实重审 Gene 统计层和 Phase 9 runtime 证据。`

