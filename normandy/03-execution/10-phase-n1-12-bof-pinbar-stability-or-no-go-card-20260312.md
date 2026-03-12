# Phase N1.12 BOF Pinbar Stability Or No-Go Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `BOF family retained branch stability or no-go`

---

## 1. 定位

`N1.12` 只在 `N1.11` 已经产生 retained branch 的前提下打开。

它要回答的不是：

`这个 branch 看上去像不像更漂亮的 BOF。`

它当前只回答：

`这个 retained branch 是否足够稳定、足够纯，值得进入 N2 / controlled exit decomposition。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md`
2. `normandy/03-execution/09-phase-n1-11-bof-pinbar-quality-provenance-card-20260312.md`
3. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
4. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

---

## 3. 当前已知前提

截至 `2026-03-12`，下面这些边界已经写死：

1. `BOF` 是当前 baseline / control
2. 本轮只允许在 `BOF` family 内部做 quality refinement
3. `Broker` 出场语义继续冻结，不在本卡调整
4. `MSS / IRS` 不进入本卡

---

## 4. 当前要回答的问题

`N1.12` 当前固定只回答四个问题：

1. retained branch 的正向读数是否跨年站得住
2. retained branch 的主环境桶是否仍成立
3. retained branch 是否存在严重的 selected / executed 脱节
4. retained branch 对 `BOF_CONTROL` 的增量是否足够健康

---

## 5. 当前实验允许做什么

当前实验固定允许：

1. 读取 `broker_order_lifecycle_trace_exp`
2. 重建 `buy_fill -> exit` pairing
3. 输出 `year / environment / overlap / incremental / purity` 审核结果
4. 固定 `eligible_for_n2` 或 `branch_no_go`

当前实验固定不允许：

1. 重开 `FB / SB / Tachibana`
2. 顺手改 `Broker` 出场参数
3. 在本卡里把 `金字塔加仓 / 分批止盈` 混进来

---

## 6. 当前证据对象

`N1.12` 当前默认消费：

1. `N1.11` 的 `bof_quality_matrix`
2. `N1.11` 的 `bof_quality_digest`

本卡新增正式 evidence：

3. `bof_quality_stability_report`

---

## 7. 建议脚本入口

本卡当前建议落的脚本入口为：

1. `scripts/backtest/run_normandy_bof_quality_stability_report.py`

---

## 8. 出场条件

`N1.12` 只有在以下条件之一满足时才允许出场：

1. 已明确 retained branch `eligible_for_n2_exit_decomposition`
2. 已明确 retained branch 当前不稳，正式 `no-go`

---

## 9. 当前一句话任务

`如果 N1.11 真的挑出了一支更纯的 BOF branch，就在同一套 Broker 下把它读到稳定 or no-go 为止；别让它停留在“看起来不错”的阶段。`
