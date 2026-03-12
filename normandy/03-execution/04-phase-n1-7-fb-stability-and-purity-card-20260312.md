# Phase N1.7 FB Stability And Purity Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场 FB 稳定性与 purity 审核`

---

## 1. 定位

`N1.7` 是 `N1.6` 的后续卡。

它不再回答“FB 有没有资格留下”，而是回答：

`FB 留下来之后，够不够稳，够不够纯。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/03-fb-second-layer-provenance-spec-20260312.md`
3. `normandy/02-implementation-spec/04-fb-stability-and-purity-spec-20260312.md`
4. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
5. `normandy/03-execution/records/03-phase-n1-6-fb-dossier-record-20260312.md`
6. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`
7. `normandy/03-execution/evidence/normandy_volman_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t015510__volman_alpha_digest.json`
8. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_candidate_report.json`

---

## 3. 当前目标

`N1.7` 当前只做三件事：

1. 生成 `FB stability report`
2. 生成 `FB purity audit`
3. 给出 `FB` 的下一步裁决

---

## 4. 固定比较对象

`N1.7` 当前固定只比较：

1. `BOF_CONTROL`
2. `FB`

硬约束：

1. `SB / RB_FAKE / PB / TST / CPB` 不回到本卡主比较集
2. `BOF_CONTROL` 继续只做 baseline，不参与“谁退位”的表述

---

## 5. 固定执行约束

本卡固定约束为：

1. 不重跑 `N1.5` 全矩阵，除非上游 evidence 损坏
2. 不把 `FB` 当前成立直接翻译成主线升级
3. 不在本卡里展开 `MSS / Broker` 微调
4. 不把 `SB` 因为暂时落后就移出后续研究队列

---

## 6. 任务拆解

### N1.7-A Stability Slice

目标：

1. 按环境桶与时间段切片 `FB`
2. 写明 `FB` 正向 edge 的可复现性

### N1.7-B Purity Audit

目标：

1. 审核 `FB` 的 first-pullback 语义纯度
2. 写明当前 detector 的主要污染源

### N1.7-C Decision Note

目标：

1. 输出 `FB` 下一步推荐动作
2. 明确是先做：
   - `N2 exit decomposition`
   - `FB detector refinement`
   - 还是维持候选观察

---

## 7. 建议产物

本卡当前建议落的产物至少包括：

1. `scripts/backtest/run_normandy_fb_stability_report.py`
2. `scripts/backtest/run_normandy_fb_purity_audit.py`
3. 一份正式 record

---

## 8. 出场条件

`N1.7` 只有在以下条件之一成立时才允许出场：

1. `FB` 被明确判定为可以进入 `N2`
2. `FB` 被明确判定为先做 detector refinement 更合理

---

## 9. 当前一句话任务

`把 FB 从“第二个 alpha 候选”继续推进到“可继续深挖的稳定对象”或“必须先收缩 detector 的脆弱对象”。`
