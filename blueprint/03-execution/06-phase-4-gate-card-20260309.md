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

### 2.1 Gate 标准必须先冻结

`Phase 4` 开工前，下面 3 件事必须已经写死，不能等结果出来再反推标准：

1. `GO / NO-GO` 的定量判断规则
2. `rollback condition` 的触发条件与回退目标
3. `P4-B` 四类 attribution 脚本各自回答什么问题

### 2.2 当前冻结的 GO / NO-GO 标准

本卡默认比较对象固定为：

1. `legacy_bof_baseline`
2. 当前主线默认路径（完成 `P0-P3` 后的 `v0.01-plus` 主链）

#### 2.2.1 GO 最低门槛

同时满足下面条件，才允许写 `GO`：

1. `Matrix Replay` 与 `check_idempotency.py` 全部通过
2. attribution bundle 四类证据齐全，且能解释主要收益变化来源
3. 相对 `legacy_bof_baseline`：
   - `expected_value >= legacy`
   - `profit_factor >= 0.95 * legacy`
   - `max_drawdown <= 1.10 * legacy`
4. 若 `exposure_rate / participation_rate` 发生明显变化，必须能由：
   - `Selector / PAS / IRS / MSS / Broker`
   路径中的至少一层明确解释
5. 回退路径已实测可执行

#### 2.2.2 NO-GO 触发条件

命中下面任一条，直接写 `NO-GO`：

1. 幂等不稳定
2. 失败路径不可追溯
3. attribution bundle 缺失关键一环，导致收益变化无法解释
4. 相对 `legacy_bof_baseline`：
   - `expected_value < legacy`
   - 且 `profit_factor < 0.95 * legacy`
5. `max_drawdown > 1.10 * legacy`
6. 新主线主要收益改善只能靠临时调参或不可复现窗口成立

### 2.3 rollback condition 冻结

`rollback` 不是一句口头结论，而是固定动作：

1. 回退目标：
   - `legacy_bof_baseline`
2. 触发条件：
   - 任一 `NO-GO` 条件命中
   - 或主线证据无法解释收益变化
3. 回退后要求：
   - 默认运行路径不切到新主线参数组合
   - `legacy_bof_baseline` 继续保持可重跑
   - `v0.01-plus` 线保留为实验/整改路径，不删除证据

### 2.4 Attribution Bundle 的意义

`P4-B` 不是机械重跑旧脚本，而是要回答：

1. 带上 `Phase 3 / MSS` 后，系统级收益变化来自哪里
2. 旧 evidence 与新 evidence 的差异是否由 `MSS` 风控层解释
3. 哪些脚本是继续消费旧链路，哪些脚本是 `Phase 3` 新增能力

其中：

1. `run_v001_plus_trade_attribution.py`
2. `run_v001_plus_windowed_sensitivity.py`
3. `run_v001_plus_rank_decomposition.py`

这三者在 `Phase 4` 的意义是：

`带上 MSS 新层后做系统级重跑，不是重复旧 Phase 2 证据。`

而：

4. `run_v001_plus_mss_regime_sensitivity.py`

其脚本创建归属固定在 `Phase 3`，`Phase 4` 只消费它的结果。

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
- [ ] 已明确区分“旧脚本重跑的系统级意义”和“新增 MSS regime 脚本的创建归属”

### 3.3 Task P4-C Mainline Decision

**文档落点**

1. `docs/spec/common/records/development-status.md`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 明确 `GO / NO-GO`
- [ ] 明确回退条件
- [ ] 明确默认参数是否调整
- [ ] `GO / NO-GO` 判断严格按本卡预先冻结标准执行，不允许事后改口径

---

## 4. 系统级出场条件

- [ ] 正常路径有系统级闭环样本
- [ ] 降级路径有系统级闭环样本
- [ ] 失败路径可追溯
- [ ] 回退路径可执行
- [ ] `GO / NO-GO` 已写回状态文档
- [ ] `GO / NO-GO` 已按本卡冻结阈值完成对 `legacy_bof_baseline` 的正式比较
- [ ] `rollback condition` 已写明触发条件、回退目标与回退后动作

---

## 5. 完成后必须回答的问题

1. 新主线是否真的比 `legacy` 更可信
2. 收益变化是否可以被系统路径解释
3. 当前默认运行路径是否应该切换
4. 如果不能切，rollback condition 是什么
5. 带上 `Phase 3 / MSS` 后，哪些历史区间的结果改变最明显，这些变化能否被 regime sensitivity 解释
