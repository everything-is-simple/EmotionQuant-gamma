# Phase N1.13 Tachibana Refinement Or Backlog Retention Card

**状态**: `Active`  
**日期**: `2026-03-13`  
**对象**: `Tachibana refinement or backlog retention formal gate`

---

## 1. 定位

`N1.13` 不是把 `立花义正` 整体重新抬回 `Normandy` 主队列的大扩张卡。

它只回答：

`在 N1.8 已经证明 TACHI_CROWD_FAILURE 当前只是 observation-only、而 BOF family 也已在 N1.11/N1.12 读完的前提下，Tachibana 这条线下一步应进入更深一层 detector refinement，还是正式保留为 backlog retention。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
3. `normandy/01-full-design/90-research-assets/tachibana-crowd-failure-minimal-contract-note-20260312.md`
4. `normandy/03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md`
5. `normandy/03-execution/records/10-phase-n1-12-bof-pinbar-stability-or-no-go-record-20260313.md`
6. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

---

## 3. 当前目标

`N1.13` 当前只做三件事：

1. 重新读取 `TACHI_CROWD_FAILURE` 当前失败到底是：
   - detector 太宽 / 太浅
   - 还是对象本身在当前语义下只够 backlog
2. 若 refinement 仍有意义，固定下一条最小 refinement 假设
3. 若 refinement 不值得继续，正式把 `Tachibana` 收进 backlog retention

---

## 4. 固定研究对象

`N1.13` 当前固定只围绕：

1. `TACHI_CROWD_FAILURE`
2. `BOF_CONTROL`（仅作固定参考尺）

硬约束：

1. 不把 `FB / SB / RB_FAKE / BOF quality branches` 拉回本卡主比较集
2. 不把 `Tachibana` 说成 `PAS` 新形态
3. 不把 `立花执行纪律` 一次性并入新的首轮 detector

---

## 5. 固定执行约束

本卡固定约束为：

1. 不直接打开 `N2 / controlled exit decomposition`
2. 不在没有新 detector 假设的前提下重跑大型长窗 matrix
3. 不把“理论上还可以讲”误写成“主队列还该继续烧时间”
4. 若要保留 refinement，只允许保留一条更窄、更可复核的最小假设

---

## 6. 任务拆解

### N1.13-A Failure Readback

目标：

1. 重读 `N1.8` 的 overlap / incremental / environment / negative slices
2. 判断当前失败更像：
   - 高重叠非独立
   - detector 太粗
   - 或当前日线语义下不值得继续 formalize

### N1.13-B Refinement Gate

目标：

1. 若仍存在 refinement 价值，固定一条更窄的 detector refinement hypothesis
2. 写明：
   - 比当前 minimal contract 多了什么
   - 为什么这不是主观补丁
   - 下一轮若重跑，预期要验证什么

### N1.13-C Retention Decision

目标：

1. 输出正式决策：
   - `open_tachibana_refinement`
   - 或 `keep_tachibana_backlog_only`
2. 写明它在 `Normandy` 中的准确层级：
   - 主队列
   - 观察池
   - 后备研究队列

---

## 7. 建议脚本入口

本卡当前建议入口分两种：

1. 若只做治理决策与 refinement gate：
   - 直接消费现有 `N1.8 matrix + digest + record`
2. 若真的形成新的最小 refinement hypothesis：
   - 复用 `scripts/backtest/run_normandy_tachibana_alpha_matrix.py`
   - 复用 `scripts/backtest/run_normandy_tachibana_alpha_digest.py`

也就是说：

`N1.13` 默认先做决策卡，不默认要求立刻重跑长窗。

---

## 8. 出场条件

`N1.13` 只有在以下条件之一成立时才允许出场：

1. 已固定 `Tachibana` 下一条正式 refinement hypothesis
2. 已固定 `Tachibana` 当前只保留为 backlog retention，不再占主队列

---

## 9. 当前一句话任务

`别再让 Tachibana 停留在“以后再说”；现在就把它判清楚，到底值得继续 formalize，还是正式收进 backlog。`
