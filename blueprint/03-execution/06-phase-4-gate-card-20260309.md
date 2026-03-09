# Phase 4 Card

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `P4 全链回归与 Gate 收口`  
**定位**: `当前主线第五张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
4. `docs/spec/common/records/development-status.md`

---

## 1. 目标

把 `P0-P3` 的结果真正回到主线矩阵里，给出：

`系统级 GO / NO-GO`

---

## 2. 范围

当前 phase 只做：

1. 主线矩阵重跑
2. 幂等验证
3. trade attribution
4. windowed sensitivity
5. rank decomposition
6. regime sensitivity
7. `GO / NO-GO + rollback condition`

当前 phase 明确不做：

1. 不为了过 Gate 临时改默认参数
2. 不删除 `legacy` 回退路径
3. 不用局部证据冒充系统级闭环

---

## 3. 任务

### 3.1 Task P4-A Matrix Replay

**脚本落点**

1. `scripts/backtest/run_v001_plus_dtt_matrix.py`
2. `scripts/backtest/check_idempotency.py`

**检查项**

- [ ] 4 组矩阵可重跑
- [ ] `legacy` 可回退
- [ ] 幂等稳定

### 3.2 Task P4-B Attribution Bundle

**脚本落点**

1. `scripts/backtest/run_v001_plus_trade_attribution.py`
2. `scripts/backtest/run_v001_plus_windowed_sensitivity.py`
3. `scripts/backtest/run_v001_plus_rank_decomposition.py`
4. `scripts/backtest/run_v001_plus_mss_regime_sensitivity.py`

**检查项**

- [ ] trade attribution
- [ ] windowed sensitivity
- [ ] rank decomposition
- [ ] regime sensitivity

### 3.3 Task P4-C Mainline Decision

**文档落点**

1. `docs/spec/common/records/development-status.md`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 明确 `GO / NO-GO`
- [ ] 明确回退条件
- [ ] 明确默认参数是否调整

---

## 4. 系统级出场条件

- [ ] 正常路径有系统级闭环样本
- [ ] 降级路径有系统级闭环样本
- [ ] 失败路径可追溯
- [ ] 回退路径可执行
- [ ] `GO / NO-GO` 已写回状态文档

---

## 5. 完成后必须回答的问题

1. 新主线是否真的比 `legacy` 更可信
2. 收益变化是否可以被系统路径解释
3. 当前默认运行路径是否应该切换
4. 如果不能切，rollback condition 是什么
