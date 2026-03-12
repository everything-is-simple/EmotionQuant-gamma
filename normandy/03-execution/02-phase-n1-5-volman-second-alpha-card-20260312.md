# Phase N1.5 Volman Second Alpha Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场寻找第二个自带 alpha 的执行卡`

---

## 1. 定位

`N1.5` 属于第二战场里的扩展 provenance 卡。

它不等于：

1. `N2 / Exit decomposition`
2. 当前主线新 phase
3. 旧 `N1` 的简单补跑

`N1.5` 只回答一个问题：

`在 BOF 已经坐稳 baseline 之后，Volman 语义里谁最像第二个自带 alpha 的人。`

---

## 2. 开工前提

开工前必须先继承：

1. `blueprint/README.md`
2. `normandy/README.md`
3. `normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`
4. `normandy/02-implementation-spec/02-volman-second-alpha-search-spec-20260312.md`
5. `normandy/03-execution/00-dev-data-baseline-inheritance-20260311.md`
6. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
7. `docs/Strategy/PAS/volman-pas-alpha-screening.md`
8. `docs/Strategy/PAS/volman-pas-v0-research-card-20260312.md`
9. `docs/Strategy/PAS/bof-firstborn-record-20260312.md`
10. `docs/Strategy/PAS/volman-rb-sb-fb-minimal-contract-note-20260312.md`

这意味着本卡默认继续遵守：

1. 三目录纪律
2. `RAW_DB_PATH / 本地旧库优先`
3. 双 TuShare key 主备分工
4. `T+1 Open` 执行语义
5. 不改写当前 `BOF` baseline

---

## 3. 目标

`N1.5` 当前只做四件事：

1. 把 `RB_FAKE / SB / FB` 定义成第一批 `Volman` 独立候选
2. 用统一长窗口比较它们与 `BOF_CONTROL` 的 raw entry edge
3. 明确谁最像第二个 standalone alpha object
4. 给后续是否进入更深一层 provenance 或 exit decomposition 提供入口

一句话说：

`BOF 不退位，但我们开始给 PAS 家族找第二个能自己扛 alpha 的人。`

---

## 4. 固定比较对象

`N1.5` 当前固定比较：

1. `BOF_CONTROL`
2. `RB_FAKE`
3. `SB`
4. `FB`

这里的硬约束是：

1. `BOF_CONTROL` 是固定对照，不参与“谁来接班”的情绪化表述
2. `SB` 必须保留在第一批候选里，不能因为复杂就删掉
3. `IRB / DD / BB / ARB` 不进入本卡首轮独立矩阵

---

## 5. 固定执行约束

本卡固定约束为：

1. 不重新打开 `MSS / Broker` 微调
2. 不把 `IRS` 拉回前置硬过滤
3. 不把 sidecar 层对象提前升格为独立 detector
4. 不允许用短窗样本直接宣布候选胜出
5. 一切 working db、实验缓存和中间产物一律落在 `G:\EmotionQuant-temp`

---

## 6. 任务拆解

### N1.5-A Candidate Contract

目标：

1. 写清 `RB_FAKE / SB / FB` 的最小结构定义
2. 写清各自与 `BOF_CONTROL` 的边界

### N1.5-B Matrix Build

目标：

1. 在统一长窗口上重放 `BOF_CONTROL / RB_FAKE / SB / FB`
2. 输出统一 `matrix summary`

### N1.5-C Overlap Digest

目标：

1. 输出各候选相对 `BOF_CONTROL` 的 overlap
2. 拆出哪些 trade 是重复 alpha，哪些 trade 是新增 alpha

### N1.5-D Gate Note

目标：

1. 写明谁可以进入下一层研究
2. 写明谁只保留为背景候选

---

## 7. 证据脚本

本卡若进入执行，当前默认需要落的脚本入口为：

1. `scripts/backtest/run_normandy_volman_alpha_matrix.py`
2. `scripts/backtest/run_normandy_volman_alpha_digest.py`

若脚本不存在，可在本卡执行时新增，但必须遵守：

1. 头部写明三目录纪律
2. 头部写明 `RAW_DB_PATH / 本地旧库优先`
3. 不把运行时产物写回仓库根目录

---

## 8. 出场条件

`N1.5` 只有在以下条件之一成立时才允许出场：

1. `RB_FAKE / SB / FB` 中至少一类被证明具备独立 raw alpha 价值
2. 三类候选全部被证据否定，且已明确写出 no-go record

---

## 9. 当前一句话任务

`以 BOF_CONTROL 为固定对照，把 RB_FAKE / SB / FB 作为第一批 Volman 独立候选跑起来，专门寻找第二个自带 alpha 的人。`
