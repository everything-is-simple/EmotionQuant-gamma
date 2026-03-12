# Phase N1.11 BOF Pinbar Quality Provenance Card

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `BOF family broker-frozen quality provenance`

---

## 1. 定位

`N1.11` 不是新的跨 family 第二 alpha 搜索卡。

它只回答：

`在同一套 Broker 出场语义下，BOF family 内部的 key-level / pinbar quality split，是否能产出一个比 BOF_CONTROL 更值得保留的 retained branch。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/01-full-design/90-research-assets/bof-pinbar-keylevel-doctrine-note-20260312.md`
3. `normandy/02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md`
4. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
5. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

---

## 3. 当前目标

`N1.11` 当前只做三件事：

1. 跑一轮 `BOF_CONTROL / BOF_KEYLEVEL_STRICT / BOF_PINBAR_EXPRESSION / BOF_KEYLEVEL_PINBAR` 长窗 matrix
2. 在同一套 Broker exit semantics 下读取 retained branch 候选
3. 输出 `N1.11` formal gate note

---

## 4. 固定比较对象

`N1.11` 当前固定只比较：

1. `BOF_CONTROL`
2. `BOF_KEYLEVEL_STRICT`
3. `BOF_PINBAR_EXPRESSION`
4. `BOF_KEYLEVEL_PINBAR`

硬约束：

1. 不把 `FB / SB / Tachibana` 拉回本卡
2. 不把 `Pinbar` 写成独立新 family

---

## 5. 固定执行约束

本卡固定约束为：

1. `MSS / IRS` 不进入本卡
2. 继续复用当前统一 `Broker` 的 `stop_loss + trailing_stop + T+1 Open` 语义
3. 不在本卡改 exit 规则
4. 不在本卡引入 `金字塔加仓 / 分批止盈`

---

## 6. 任务拆解

### N1.11-A Matrix Build

目标：

1. 在统一长窗口上重放四支 `BOF` quality branches
2. 输出统一 `matrix summary`

### N1.11-B Branch Digest

目标：

1. 输出 `trade_count / EV / PF / MDD / participation`
2. 输出 `overlap / incremental / selected_trace` 摘要
3. 判断 retained branch 是否存在

### N1.11-C Gate Note

目标：

1. 固定 retained branch 或 family no-go
2. 决定是否进入 `N1.12`

---

## 7. 建议脚本入口

本卡当前建议落的脚本入口为：

1. `scripts/backtest/run_normandy_bof_quality_matrix.py`
2. `scripts/backtest/run_normandy_bof_quality_digest.py`

---

## 8. 出场条件

`N1.11` 只有在以下条件之一成立时才允许出场：

1. 已固定一支 retained branch 进入 `N1.12`
2. 已固定当前 `BOF` quality family 没有比 `BOF_CONTROL` 更值得继续推进的分支

---

## 9. 当前一句话任务

`别再横向扩张 family；先在同一套 Broker 下把 BOF / key-level / pinbar 的 quality branches 真刀真枪地比一次。`
