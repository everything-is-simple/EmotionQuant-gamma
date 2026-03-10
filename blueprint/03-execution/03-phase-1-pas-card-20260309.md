# Phase 1 Card

**状态**: `Completed`  
**日期**: `2026-03-10`  
**对象**: `P1 PAS 最小可交易形态层`  
**定位**: `当前主线第二张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
4. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
5. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

---

## 1. 目标

把当前 `PAS-trigger` 补到：

`最小可交易五形态层`

截至 `2026-03-10`，本卡代码、测试、PAS 专项 evidence 与 records 已全部收口，允许进入后续 `Phase 2 / IRS`。

---

## 2. 范围

当前 phase 只做：

1. `BPB / PB / TST / CPB`
2. 五形态 registry 与单形态启停
3. `pattern_quality_score`
4. `stop / target / failure` 参考层
5. 单形态独立回测与 registry summary

当前 phase 明确不做：

1. 不恢复 `PAS-full` 机会等级体系
2. 不把质量层写回 formal `Signal`
3. 不让 Broker 强依赖参考止损 / 目标位
4. 不扩非 `YTC` 额外形态

---

## 3. 任务

### 3.1 Task P1-A Pattern Registry + BPB / PB

**代码落点**

1. `src/strategy/`
2. `src/strategy/registry.py`
3. `src/strategy/strategy.py`

**测试落点**

1. `tests/unit/strategy/` 下新增 `BPB / PB` detector 单测
2. registry 单测

### 3.2 Task P1-B TST / CPB

**代码落点**

1. `src/strategy/`
2. `src/strategy/registry.py`
3. `src/strategy/strategy.py`

**测试落点**

1. `tests/unit/strategy/` 下新增 `TST / CPB` detector 单测

### 3.3 Task P1-C Pattern Quality + Arbitration

**代码落点**

1. `src/strategy/`
2. `src/strategy/strategy.py`
3. `src/contracts.py` 或 sidecar 写入层

**测试落点**

1. `tests/unit/strategy/` 下 quality 单测
2. arbitration 单测

### 3.4 Task P1-D PAS Reference Layer

**代码落点**

1. `src/strategy/strategy.py`
2. `src/data/store.py`

**测试落点**

1. `tests/unit/strategy/` 下 reference layer 单测

### 3.5 Task P1-E PAS Evidence

**脚本落点**

1. `scripts/backtest/run_v001_plus_pas_ablation.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

---

## 4. 出场条件

- [x] `BPB / PB / TST / CPB` 已落地
- [x] 五形态 registry 已落地
- [x] `pattern_quality_score` 已落地
- [x] 参考层字段已落地
- [x] `PAS` 专项 evidence 已生成
- [x] 不破坏当前 `BOF` 基线

---

## 5. 完成后必须回答的问题

1. 哪些票是因为新增形态而出现
2. 哪些票是因为 `quality` 被筛下去或排上来
3. 哪个形态在什么环境桶下有效
4. 单形态和组合形态的执行摩擦是否不同

当前结论见：

1. `docs/spec/v0.01-plus/records/v0.01-plus-pas-ablation-20260310.md`
2. `docs/spec/v0.01-plus/evidence/pas_ablation_dtt_v0_01_dtt_bof_plus_irs_score_pas_registry_matrix_w20260105_20260224_t021051__pas_ablation.json`

收口摘要：

1. 新增形态里，`CPB / PB / TST` 都已显著改变选中集与成交集；`BPB` 在当前窗口没有形成成交样本。
2. `quality` 当前仍只停留在 `PAS trace / sidecar`，因此本轮 `rank_diff_days = 0`、`execution_diff_days = 0`，没有任何票因 `quality` 被筛下去或排上来。
3. 当前窗口里新增形态的有效样本几乎都落在 `NEUTRAL`，只足够支持“当前尚不能做环境桶启停”的保守结论。
4. 单形态与组合形态的执行摩擦差异明显：`CPB` 和 `YTC5_ANY` 的 `reject_rate / skip_maxpos_count` 明显高于 `BOF`，说明组合后拥挤摩擦已经成为正式问题。
