# Phase P1 Null Control Matrix Card

**日期**: `2026-03-13`  
**阶段**: `Positioning / P1`  
**对象**: `第三战场第二张执行卡`  
**状态**: `Active`

---

## 1. 目标

`P1` 只做一件事：

`在同一条 frozen baseline 下，把 single-lot control 和 fixed-notional control 跑成正式 null control matrix，并选出后续 sizing family 的 canonical control baseline。`

这一步的职责不是找最优仓位公式，而是先回答：

`后面的 fixed-risk / fixed-ratio / fixed-volatility 到底该拿哪条最朴素 control 去比。`

---

## 2. 本卡要回答的问题

`P1` 只回答下面 5 个问题：

1. `single-lot control` 和 `fixed-notional control` 在同一 frozen baseline 下各自给出什么账户曲线形状
2. 两条 control 的 `trade_count / fill_count / reject profile` 是否保持可比较的一致性
3. 两条 control 的 `avg_position_size / exposure_utilization / cash pressure` 有何差异
4. 两条 control 的 `net_pnl / ev_per_trade / profit_factor / max_drawdown` 分别落在什么层级
5. 哪一条 control 更适合被正式指定为后续 `P2~P8` 的 canonical control baseline

---

## 3. 冻结输入

本卡执行时，以下变量继续冻结，不允许漂移：

1. `pipeline baseline = legacy_bof_baseline`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `buy-side sizing denominator = current Broker risk budget + max position cap semantics`

本卡唯一允许变化的维度只有：

1. `single-lot control`
2. `fixed-notional control`

---

## 4. 目录纪律

本卡执行必须严格遵守三目录分离：

1. `G:\EmotionQuant-gamma`
   - 只保留执行卡、formal record、正式 evidence 和脚本代码
   - 不允许写入运行时 DuckDB、缓存目录、日志和一次性中间结果
2. `G:\EmotionQuant_data`
   - 只保留长期数据资产，例如主 DuckDB 和长期日志
3. `G:\EmotionQuant-temp`
   - 只保留 `P1` 的工作 DuckDB、回放缓存、临时对照产物和一次性检查结果

本卡后续脚本必须满足：

1. 工作数据库默认落 `G:\EmotionQuant-temp\backtest\` 或其子目录
2. 日志与临时 artifacts 默认落 `G:\EmotionQuant-temp\logs\`、`G:\EmotionQuant-temp\artifacts\`
3. 不允许把运行时脏产物写回仓库根目录
4. 只有正式 evidence / record 才允许回写到仓库

---

## 5. 本卡交付物

本卡正式交付物固定为：

1. 一份 `null control matrix`
2. 一份 `null control digest`
3. 一张 `P1 formal record`

其中矩阵至少要覆盖：

1. `net_pnl`
2. `ev_per_trade`
3. `profit_factor`
4. `max_drawdown`
5. `trade_count`
6. `avg_position_size`
7. `exposure_utilization`
8. `cash / slot pressure diagnostics`

---

## 6. 验收标准

本卡通过的条件固定为：

1. 两条 control 已在同一窗口和同一 baseline 下完成正式 replay
2. 已明确说明它们的收益差异来自哪里，而不是让差异停留在表面数值
3. 已正式指定后续 `P2~P8` 使用的 canonical control baseline
4. 已把 retained control 写进 formal record 和共享治理入口

---

## 7. 当前不允许做的事

在 `P1` 完成前，当前明确不允许：

1. 提前并行跑 `fixed-risk / fixed-ratio / fixed-volatility` 家族长窗矩阵
2. 先做 `fixed-notional` 参数微扫，再补 null control formal readout
3. 把 `partial-exit / scale-out` 混进 control 组对照
4. 让 `MSS / IRS` 重新进入仓位大小决定
5. 把 control 组中的任意一条直接宣布成正式主线默认仓位

---

## 8. 下一步出口

`P1` 完成后，下一步执行顺序固定为：

1. `P2~P8 sizing family replay`
2. `P9 retained-or-no-go`
3. `P10 partial-exit contract lane`

前提是：

`P1` 必须先把第三战场真正的 control baseline 正式定下来。

---

## 9. 一句话结论

`P1` 的职责不是找赢家，而是先把第三战场后续所有仓位对照要拿什么当尺子正式定下来。`
