# Phase N1.8 Tachibana Contrary Alpha Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场 Tachibana contrary alpha 首轮实验`

---

## 1. 定位

`N1.8` 不是“立花义正全书复刻工程”。

它只回答：

`立花义正最核心的那条 crowd-extreme failure 逻辑，能不能在当前系统里形成真正的 alpha 产生点。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `docs/Strategy/PAS/tachibana-yoshimasa-analysis.md`
3. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`
4. `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
5. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`

---

## 3. 当前目标

`N1.8` 当前只做三件事：

1. 产出 `Tachibana minimal contract note`
2. 跑一轮 `BOF_CONTROL vs TACHI_CROWD_FAILURE` 的长窗 matrix
3. 给出 `Tachibana` 首轮裁决

---

## 4. 固定比较对象

`N1.8` 当前固定只比较：

1. `BOF_CONTROL`
2. `TACHI_CROWD_FAILURE`

硬约束：

1. 不把 `FB / SB / RB_FAKE` 拉回本卡主比较集
2. 不把 `Tachibana` 说成 `PAS` 新形态

---

## 5. 固定执行约束

本卡固定约束为：

1. 先 formalize 最小 detector，再跑长窗
2. 不在没有 detector 的情况下先报“回测结果”
3. 不把 `试单 / 加减仓 / 休息纪律` 一次性并入首轮 entry detector
4. 不在本卡里打开 `MSS / Broker` 微调

---

## 6. 任务拆解

### N1.8-A Minimal Contract

目标：

1. 从 `Tachibana` 理论骨架抽出最小可执行 detector
2. 写明理论边界、字段口径与失效点

### N1.8-B Matrix Build

目标：

1. 在统一长窗口上重放：
   - `BOF_CONTROL`
   - `TACHI_CROWD_FAILURE`
2. 输出统一 summary

### N1.8-C Readout

目标：

1. 写明 `Tachibana` 是否形成正向 alpha
2. 写明它与 `BOF` 的重叠与增量关系
3. 输出下一步建议

---

## 7. 建议脚本入口

本卡当前建议落的脚本入口为：

1. `scripts/backtest/run_normandy_tachibana_alpha_matrix.py`
2. `scripts/backtest/run_normandy_tachibana_alpha_digest.py`

---

## 8. 预计时间

当前预计耗时分两段：

1. `minimal contract + detector 骨架`
   - `1 ~ 2` 天
2. `正式 3 年长窗 matrix + digest`
   - 实际跑数 `2 ~ 3` 小时
   - 读数和 record `0.5 ~ 1` 天

---

## 9. 出场条件

`N1.8` 只有在以下条件之一成立时才允许出场：

1. `TACHI_CROWD_FAILURE` 已证明值得继续深挖
2. `TACHI_CROWD_FAILURE` 已证明当前不成立或只是在重复 `BOF`

---

## 10. 当前一句话任务

`别再把立花义正停留在理论观感层，而是把它收缩成一条最小可执行假设，和 BOF 真刀真枪地比一次。`
