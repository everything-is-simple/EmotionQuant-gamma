# Phase N1.10 SB Refinement Or No-Go Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `SB refinement or no-go`

---

## 1. 定位

`N1.10` 是 `Normandy` 主队列对 `SB` 的正式裁决卡。

它不直接做 detector split。

它先把 `SB` 当前还有没有继续 refinement 的资格正式读完。

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/02-volman-second-alpha-search-spec-20260312.md`
3. `normandy/02-implementation-spec/08-sb-refinement-or-no-go-spec-20260312.md`
4. `normandy/03-execution/02-phase-n1-5-volman-second-alpha-card-20260312.md`
5. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
6. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`

---

## 3. 当前目标

`N1.10` 当前只做三件事：

1. 给 `SB` 生成 formal `sb_refinement_report`
2. 固定 `SB` full detector 的去留
3. 固定 `Normandy` 主队列下一张卡

---

## 4. 固定对象

本卡固定只围绕：

1. `SB`
2. `BOF_CONTROL`

硬约束：

1. `FB_BOUNDARY` 不回本卡
2. `RB_FAKE` 不提前重开
3. `BOF_CONTROL` 继续只做 baseline / 尺子

---

## 5. 任务拆解

### N1.10-A Pairing And Slice Audit

目标：

1. 固定 `buy-fill sequence -> exit sequence` 的 `SB` pairing 口径
2. 读 `signal_year_slices`
3. 读 `selected trace summary`

### N1.10-B Bucket And Watch-Branch Readout

目标：

1. 读 `strength / trend / retest / w_amplitude` 分桶
2. 读 `coarse branch candidates`
3. 判断是否存在值得保留的窄 watch branch

### N1.10-C Formal Decision

目标：

1. 固定 `SB` 当前是 `refinement continue` 还是 `no-go`
2. 固定 `Normandy` 主队列下一位优先级

---

## 6. 建议产物

本卡当前建议落的产物至少包括：

1. `src/backtest/normandy_sb_refinement.py`
2. `scripts/backtest/run_normandy_sb_refinement_report.py`
3. 一份正式 record

---

## 7. 出场条件

`N1.10` 只有在以下条件之一成立时才允许出场：

1. `SB` 已明确保留继续 refinement 的主队列资格
2. `SB` 已明确 current full detector `no-go`，并写明是否保留窄 watch branch

---

## 8. 当前一句话任务

`把 SB 当前 full detector 的去留读完，同时决定它是继续 refinement，还是正式 no-go 并让出 Normandy 主队列。`
