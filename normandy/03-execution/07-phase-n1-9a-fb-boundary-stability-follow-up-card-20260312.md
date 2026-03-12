# Phase N1.9A FB Boundary Stability Follow-up Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `FB_BOUNDARY focused stability follow-up`

---

## 1. 定位

`N1.9A` 是 `N1.9` 之后的 focused readout 卡。

它不再做 branch selection。

它只负责把 `FB_BOUNDARY` 当前能不能放行 `N2` 这件事正式写死。

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/06-fb-detector-refinement-spec-20260312.md`
3. `normandy/02-implementation-spec/07-fb-boundary-stability-follow-up-spec-20260312.md`
4. `normandy/03-execution/06-phase-n1-9-fb-detector-refinement-card-20260312.md`
5. `normandy/03-execution/records/06-phase-n1-9-fb-detector-refinement-record-20260312.md`
6. `normandy/03-execution/evidence/normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t083246__fb_refinement_matrix.json`
7. `normandy/03-execution/evidence/normandy_fb_refinement_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t094924__fb_refinement_digest.json`

---

## 3. 当前目标

`N1.9A` 当前只做两件事：

1. 给 `FB_BOUNDARY` 生成 focused stability report
2. 固定 `N2` 继续锁住还是放行

---

## 4. 固定对象

本卡固定只围绕：

1. `FB_BOUNDARY`
2. `BOF_CONTROL`

硬约束：

1. `FB_CLEANER` 不回本卡
2. `SB` 不提前进入本卡
3. `BOF_CONTROL` 继续只做 baseline / 尺子

---

## 5. 任务拆解

### N1.9A-A Focused Stability Slice

目标：

1. 读 `signal_year_slices`
2. 读 `quarter_activity`
3. 读 `negative trade examples`

### N1.9A-B Formal Decision

目标：

1. 固定 `FB_BOUNDARY` 是否 `N2 ready`
2. 固定 `Normandy` 主队列下一位优先级

---

## 6. 建议产物

本卡当前建议落的产物至少包括：

1. `scripts/backtest/run_normandy_fb_boundary_stability_report.py`
2. 一份正式 record

---

## 7. 出场条件

`N1.9A` 只有在以下条件之一成立时才允许出场：

1. `FB_BOUNDARY` 已明确可以进入 `N2`
2. `FB_BOUNDARY` 已明确仍不进入 `N2`，并把主队列优先级切走

---

## 8. 当前一句话任务

`把 retained branch FB_BOUNDARY 的 focused stability 问题读完，并决定 N2 继续锁住还是放行。`
