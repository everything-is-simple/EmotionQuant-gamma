# Phase N1.9 FB Detector Refinement Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `FB cleaner vs boundary refinement`

---

## 1. 定位

`N1.9` 是 `N1.7` 裁决后的第一张执行卡。

它不再回答：

`FB 值不值得留。`

它只回答：

`FB 留下来之后，到底该保 cleaner 分支，还是 boundary 分支。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/04-fb-stability-and-purity-spec-20260312.md`
3. `normandy/02-implementation-spec/06-fb-detector-refinement-spec-20260312.md`
4. `normandy/03-execution/04-phase-n1-7-fb-stability-and-purity-card-20260312.md`
5. `normandy/03-execution/records/05-phase-n1-7-fb-stability-and-purity-record-20260312.md`
6. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_stability_report.json`
7. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_purity_audit.json`

---

## 3. 当前目标

`N1.9` 当前只做三件事：

1. 正式接通 `FB_CLEANER`
2. 正式接通 `FB_BOUNDARY`
3. 固定 retained branch 与下一步去向

---

## 4. 固定比较对象

本卡固定只比较：

1. `BOF_CONTROL`
2. `FB_CLEANER`
3. `FB_BOUNDARY`

硬约束：

1. `FB` parent family 不再以未拆分口径重跑主裁决
2. `SB / RB_FAKE / PB / TST / CPB` 不回到本卡主比较集
3. `BOF_CONTROL` 继续只做 baseline

---

## 5. 任务拆解

### N1.9-A Detector Split

目标：

1. `FB detector` 参数化
2. 保持默认 `FB` 行为不回退

### N1.9-B Refinement Matrix

目标：

1. 长窗 replay `FB_CLEANER`
2. 长窗 replay `FB_BOUNDARY`
3. 与 `BOF_CONTROL` 做固定对照

### N1.9-C Formal Decision

目标：

1. 固定哪支在 carrying edge
2. 固定是否允许直接打开 `N2`

---

## 6. 建议产物

本卡当前建议落的产物至少包括：

1. `scripts/backtest/run_normandy_fb_refinement_matrix.py`
2. `scripts/backtest/run_normandy_fb_refinement_digest.py`
3. 一份正式 record

---

## 7. 出场条件

`N1.9` 只有在以下条件之一成立时才允许出场：

1. `FB_BOUNDARY` 或 `FB_CLEANER` 已被固定为 retained branch
2. `FB family` 已被固定为 refinement 后 no-go

---

## 8. 当前一句话任务

`把“boundary-loaded 的 FB family”正式拆成 cleaner 与 boundary 两支，并把真正 carrying edge 的 retained branch 固定下来。`
