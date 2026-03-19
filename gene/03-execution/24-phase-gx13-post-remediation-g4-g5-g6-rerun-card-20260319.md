# GX13 / 整改后 G4-G5-G6 联合重跑卡
**状态**: `Active`  
**日期**: `2026-03-19`  
**类型**: `forced statistical rerun`  
**直接目标文件**: [`../../scripts/report/run_gx13_post_remediation_revalidation.py`](../../scripts/report/run_gx13_post_remediation_revalidation.py)

---

## 1. 目标

这张卡只回答一个问题：

`在 GX10 / GX11 已经改动寿命基础和运行面透明层之后，G4 / G5 / G6 的统计 evidence 是否仍然站得住。`

---

## 2. 为什么必须开这张卡

`GX12` 已经正式裁定：

1. `G4 / G5 / G6` 方向结论可以先保留
2. 但它们的统计 evidence 不能继续沿用整改前 surface

所以这张卡不是可选优化，而是正式重跑卡。

---

## 3. 本卡必须重跑的对象

1. `compute_gene`
2. `compute_gene_validation`
3. `compute_gene_mirror`
4. `compute_gene_conditioning`

对应治理对象为：

1. `G4 / validation`
2. `G5 / mirror`
3. `G6 / conditioning`

---

## 4. 本卡允许修改

1. `gene` 相关 card / record / evidence
2. [`../../scripts/report/run_gx13_post_remediation_revalidation.py`](../../scripts/report/run_gx13_post_remediation_revalidation.py)

---

## 5. 验收标准

1. 已在正式执行库副本上完成 `G4 / G5 / G6` 联合重跑
2. 已留下可追溯 evidence
3. 已明确裁定：
   - `keep`
   - `keep_with_numeric_drift`
   - 或 `revoke`

---

## 6. 下游关系

本卡完成后，只解决第四战场统计层问题。  
它不会自动替代：

1. `17.8 / remediated duration rerun and sweep`
2. `17.9 / frozen combination replay`

---

## 7. 一句话状态

`GX13` 当前负责把 GX12 已经裁定必须重跑的 G4 / G5 / G6 真正跑出来，并把“方向保留”变成“有新 evidence 支撑的方向保留”。`
