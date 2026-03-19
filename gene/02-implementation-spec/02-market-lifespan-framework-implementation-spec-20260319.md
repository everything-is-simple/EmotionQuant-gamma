# Market Lifespan Framework Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-19`  
**角色**: `书义寿命框架到 Gene 实现的映射说明`

---

## 1. 这份实现说明回答什么

这份实现说明只回答一个问题：

`书里的趋势定义、趋势改变和寿命框架，落到 Gene 代码里时，应该分别变成哪些对象、字段、表和执行卡。`

---

## 2. Canonical Object Mapping

### 2.1 趋势层级

书义对象与 Gene 对象固定映射为：

1. 长期趋势
   - `LONG`
   - 角色：给中级趋势提供 bull / bear 背景
2. 中级趋势
   - `INTERMEDIATE`
   - 角色：canonical Gene wave domain
3. 短期趋势
   - `SHORT`
   - 角色：给 1-2-3 / 2B 与局部 swing 提供确认支点

### 2.2 中级主要走势与次级折返

Gene canonical wave role 固定映射为：

1. `MAINSTREAM`
   - 当前中级走势方向与长期背景一致
2. `COUNTERTREND`
   - 当前中级走势方向与长期背景相反

后续任何 lifespan 统计若未特别声明，都默认优先消费：

`INTERMEDIATE + MAINSTREAM`

### 2.3 趋势改变对象

当前实现上必须分别保留：

1. `trendline break`
2. `1-2-3 step1 / step2 / step3`
3. `2B failure / confirm`

不允许把它们先压成一个黑盒 score，再试图反推定义。

---

## 3. Lifespan Surface Contract

### 3.1 样本范围

canonical lifespan history 当前应定义为：

1. 同一代码
2. 同一 `INTERMEDIATE` 层级
3. 同一长期背景方向
4. 同一 `MAINSTREAM` 角色
5. 已完成 completed wave

### 3.2 统计维度

canonical lifespan surface 至少需要：

1. `duration_trade_days`
2. `magnitude_pct`
3. `lifespan_joint_percentile`

### 3.3 分布读法

canonical banding 固定为：

1. `FIRST_QUARTER`
2. `SECOND_QUARTER`
3. `THIRD_QUARTER`
4. `FOURTH_QUARTER`
5. `UNSCALED`

### 3.4 阈值字段

canonical quartile thresholds 至少应落盘：

1. `q25`
2. `q50`
3. `q75`

legacy `p65 / p95` 只允许保留为历史兼容列，不再充当 forward canonical surface。

### 3.5 Average Lifespan / Odds Contract

除 quartile 与 joint percentile 外，canonical lifespan surface 还应正式暴露：

1. `magnitude_remaining_prob`
2. `duration_remaining_prob`
3. `lifespan_average_remaining_prob`
4. `lifespan_average_aged_prob`
5. `lifespan_remaining_vs_aged_odds`
6. `lifespan_aged_vs_remaining_odds`

这组字段的角色固定为：

1. 先给出中性寿命赔率
2. 再由 `wave_role + long context` 去解释是：
   - 主趋势继续的赔率
   - 还是修正段继续的赔率
3. 不允许在字段名层直接把它们写死成多头/空头交易建议

---

## 4. Table And Field Implications

### 4.1 `l3_stock_gene`

canonical snapshot 需要持续暴露：

1. 当前长期背景方向
2. 当前中级 wave role
3. 当前 lifespan quartile
4. 当前 joint lifespan percentile
5. 当前 prior mainstream retracement relation

### 4.2 `l3_gene_wave`

completed wave ledger 需要持续暴露：

1. `trend_level`
2. `context_trend_direction_before / after`
3. `wave_role`
4. `duration q25 / q50 / q75`
5. `magnitude q25 / q50 / q75`
6. `lifespan_joint_percentile / band`

### 4.3 `l3_gene_distribution_eval`

distribution eval 需要从“尾部阈值摘要”转向：

1. quartile summary
2. continuous distribution summary
3. payoff by quartile

---

## 5. Execution Implications

### 5.1 设计层

必须先改：

1. 术语冻结
2. 寿命框架定义
3. 运行面合同说明

### 5.2 统计层

必须重跑：

1. `G4`
2. `G5`
3. `G6`
4. `Phase 9 / duration`

### 5.3 运行层

在新 surface 跑完前，不允许直接宣布：

1. `FOURTH_QUARTER = hard negative filter`
2. `duration = runtime winner kept`

---

## 6. 一句话实现口径

Gene 的下一阶段实现，不是继续修一把“更聪明的 duration 刀”，而是把：

`中级主要走势 + 趋势改变确认 + 四分位连续寿命分布 + 平均寿命风险框架`

这四件事做成同一套可落盘、可回测、可审计的对象合同。
