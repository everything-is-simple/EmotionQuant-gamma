# Phase N1.6 FB Second-Layer Provenance Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场 FB 候选第二层 provenance`

---

## 1. 定位

`N1.6` 是 `N1.5` 的后续卡，不是新一轮 `Volman` 大混战。

它只回答一个问题：

`FB 这个“第二个自带 alpha 候选”当前到底站得有多稳。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/02-volman-second-alpha-search-spec-20260312.md`
3. `normandy/02-implementation-spec/03-fb-second-layer-provenance-spec-20260312.md`
4. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
5. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`
6. `normandy/03-execution/evidence/normandy_volman_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t015510__volman_alpha_digest.json`

---

## 3. 当前目标

`N1.6` 当前只做三件事：

1. 生成 `FB focused dossier`
2. 明确 `FB` 的稳定性风险与依赖
3. 给出下一步研究入口

---

## 4. 固定比较对象

`N1.6` 当前固定只比较：

1. `BOF_CONTROL`
2. `FB`

硬约束：

1. `RB_FAKE / SB` 不回到本卡主比较集
2. `BOF_CONTROL` 继续只做 baseline，不参与“谁退位”的表述

---

## 5. 固定执行约束

本卡固定约束为：

1. 不重跑 `N1.5` 全矩阵，除非上游 evidence 损坏
2. 不先做主线升格
3. 不在本卡里展开 `MSS / Broker` 微调
4. 不把 `FB` 的短优势直接翻译成“比 BOF 更强”

---

## 6. 任务拆解

### N1.6-A Dossier Build

目标：

1. 从现有 `matrix / digest` 抽出 `FB` focused report
2. 写明 `FB` vs `BOF_CONTROL` 的核心指标

### N1.6-B Risk Read

目标：

1. 写明 `FB` 当前的样本风险
2. 写明 `FB` 的环境桶依赖
3. 写明 `FB` 是否属于补充型 alpha

### N1.6-C Next-Step Note

目标：

1. 输出 `FB` 下一步推荐动作
2. 明确是先做：
   - provenance 深挖
   - detector refinement
   - 还是 exit decomposition

---

## 7. 证据脚本

本卡当前默认需要落的脚本入口为：

1. `scripts/backtest/run_normandy_fb_candidate_report.py`

---

## 8. 出场条件

`N1.6` 只有在以下条件之一成立时才允许出场：

1. `FB` 被明确判定为值得继续深挖的补充型 alpha
2. `FB` 被明确判定为当前仍是脆弱候选，需先收缩 detector

---

## 9. 当前一句话任务

`围绕 FB 生成 focused dossier，把“第二个自带 alpha 候选”从一句判断推进到一份可执行、可追问的研究对象。`
