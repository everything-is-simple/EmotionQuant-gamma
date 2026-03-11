# Phase N1 PAS Alpha Provenance Card

**状态**: `Active`  
**日期**: `2026-03-11`  
**对象**: `第二战场第一张执行卡`

---

## 1. 定位

`N1` 不是当前主线 phase 的继续编号。

`N1` 只属于第二战场，目标是先回答一个问题：

`当前系统最像 raw alpha 来源的 PAS entry，到底是哪一类。`

---

## 2. 开工前提

开工前必须先继承：

1. `blueprint/README.md`
2. `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`
3. `normandy/README.md`
4. `normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`
5. `normandy/03-execution/00-dev-data-baseline-inheritance-20260311.md`

这意味着本卡默认继续遵守：

1. 三目录纪律。
2. 当前执行库 / 旧库候选区分。
3. `RAW_DB_PATH / 本地旧库优先`。
4. 双 TuShare key 主备分工。
5. `T+1 Open` 执行语义。

---

## 3. 目标

`N1` 当前只做三件事：

1. 用最简 Broker 跑长窗口 `PAS` 组合矩阵。
2. 比较不同 `PAS` 组合的 raw entry edge。
3. 确认第二战场下一步该优先追哪组 shape。

一句话说：

`先证明谁在创造 alpha，再讨论谁在吞掉 alpha。`

---

## 4. 固定比较对象

`N1` 当前固定比较：

1. `BOF`
2. `PB`
3. `CPB`
4. `BOF+PB`
5. `PB+CPB`
6. `YTC5_ANY`

若需要扩展，必须先完成本轮 evidence，再开下一张卡。

---

## 5. 固定执行约束

本卡固定约束为：

1. 不引入新的 `MSS` overlay。
2. 不继续冻结 `MSS / Broker` 候选。
3. `IRS` 不作为前置硬过滤进入本轮。
4. 默认使用最简 Broker或受控最小执行口径。
5. 一切 working db、实验缓存和中间产物一律落在 `G:\EmotionQuant-temp`。

---

## 6. 任务拆解

### N1-A Matrix Build

目标：

1. 在统一长窗口上重放 `BOF / PB / CPB / BOF+PB / PB+CPB / YTC5_ANY`。
2. 输出统一 `matrix summary`。

### N1-B Provenance Digest

目标：

1. 输出各 shape 的 `trade_count / EV / PF / MDD / participation`。
2. 确认最像 raw alpha 来源的 shape family。

### N1-C Gate Note

目标：

1. 写明哪些 shape 可以进入 `N2 / Exit decomposition`。
2. 写明哪些 shape 只保留为背景对照。

---

## 7. 证据脚本

`N1` 当前固定需要落的脚本入口为：

1. `scripts/backtest/run_normandy_pas_alpha_matrix.py`
2. `scripts/backtest/run_normandy_pas_alpha_digest.py`

若脚本未存在，可在本卡执行时新增，但必须遵守：

1. 脚本头部写明三目录纪律。
2. 脚本头部写明 `RAW_DB_PATH / 本地旧库优先`。
3. 脚本头部写明双 TuShare key 主备顺序。
4. 不把运行时产物写回仓库根目录。

---

## 8. 出场条件

`N1` 只有在以下条件同时满足时才允许出场：

1. 至少有一组 `PAS` 组合在统一长窗口里被证明比 `BOF` 更像 raw alpha 来源。
2. 已明确下一步进入 `N2 / Exit decomposition` 的候选 shape 集合。
3. 已写出正式 record，并把结论同步到第二战场入口。

---

## 9. 固定禁止项

本卡当前固定禁止：

1. 因为短窗结果好，就直接切换当前默认主线。
2. 把 `IRS` 拉回硬过滤，导致 provenance 样本先被压空。
3. 在 `N1` 中重新打开 `MSS / Broker` 微调。
4. 用仓库根目录存 working db、临时缓存或实验副本。

---

## 10. 当前一句话任务

`N1` 当前一句话任务固定为：

`以最简执行口径重跑 PAS 长窗口矩阵，先证明 BOF、PB、CPB 及其组合里谁更像真实 raw alpha 来源。`
