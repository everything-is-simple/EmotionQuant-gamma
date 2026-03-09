# Phase 2 Card

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `P2 IRS 最小可交易排序层`  
**定位**: `当前主线第三张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
5. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

---

## 1. 目标

把当前 `IRS-lite` 补到：

`最小可交易排序层`

---

## 2. 范围

当前 phase 只做：

1. `RS`
2. `RV`
3. `RT`
4. `BD`
5. `GN`

当前 phase 明确不做：

1. 不做政策 / 主题 / 事件语义层
2. 不让 `IRS` 回到前置过滤
3. 不扩成完整自适应学习系统

---

## 3. 任务

### 3.1 Task P2-A Industry Daily Enrichment

**代码落点**

1. `src/data/cleaner.py`

**测试落点**

1. `tests/unit/data/` 下行业聚合单测

### 3.2 Task P2-B Industry Structure Daily

**代码落点**

1. `src/data/cleaner.py`
2. 新增行业结构聚合脚本

**测试落点**

1. `tests/unit/data/` 下结构聚合单测

### 3.3 Task P2-C IRS Scorer Rewrite

**代码落点**

1. `src/selector/irs.py`
2. `src/strategy/ranker.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. `tests/unit/selector/` 下 IRS scorer 单测

### 3.4 Task P2-D IRS Evidence

**脚本落点**

1. `scripts/backtest/run_v001_plus_irs_ablation.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

---

## 4. 出场条件

- [ ] 多周期强度已落地
- [ ] 相对量能已落地
- [ ] 轮动状态已落地
- [ ] 扩散度已落地
- [ ] 牛股基因轻量层已落地
- [ ] IRS 专项 evidence 已生成

---

## 5. 完成后必须回答的问题

1. 排序变化主要来自哪一层
2. `50.0` 发生在行业层、因子层还是 signal attach 层
3. 哪些票因行业排名映射变化被推上去或压下去
