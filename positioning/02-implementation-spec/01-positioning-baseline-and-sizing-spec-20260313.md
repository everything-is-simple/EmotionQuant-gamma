# Positioning Baseline And Sizing Spec

**日期**: `2026-03-13`  
**对象**: `第三战场当前唯一实现方案`  
**状态**: `Active`

---

## 1. 目标

本文只定义第三战场当前唯一实验方案：

`在固定 no IRS / no MSS baseline 下，先独立验证买多少，再独立验证卖多少。`

它不回答：

1. `买什么`
2. `何时买`
3. `新的 PAS / IRS / MSS` 是否成立

这些问题已经分别由主线与 `Normandy` 承担。

---

## 2. 当前唯一方案

第三战场当前唯一方案固定为两段：

1. `S1 / position sizing lane`
   - 固定 entry baseline 和当前 exit 语义
   - 只比较不同 sizing family
2. `S2 / partial-exit lane`
   - 只在 `Broker` 已支持部分减仓契约后打开
   - 研究 `卖多少 / 怎么分批卖`

当前必须明确写死：

`在 S1 未完成前，不允许把 sizing 和 partial-exit 混成一轮实验。`

---

## 3. 冻结 baseline

第三战场当前固定 baseline 为：

1. `legacy_bof_baseline`
2. `no IRS`
3. `no MSS`
4. `T+1 Open` 执行语义
5. 当前 `Broker` 的统一止损 / trailing-stop 全平退出语义

对应的硬边界是：

1. 不改 `entry family`
2. 不改 `Selector` / `BOF` 触发逻辑
3. 不让 `MSS risk_regime`、`IRS score` 或其派生字段进入 sizing 决策
4. 不在 `S1` 阶段引入 `partial-exit`

---

## 4. 当前仓位问题的系统现实

当前代码里的仓位仍然带有主线遗产：

1. `Broker` 当前按 `risk_per_trade_pct + max_position_pct` 计算买入数量
2. 这两个倍率在主线里仍可被 `MSS overlay` 缩放
3. `SELL` 当前仍默认全平，不支持正式 `scale-out`

所以第三战场的当前任务不是“再讨论理论”，而是：

1. 先把 sizing 从 `MSS overlay` 中隔离出来
2. 在同一 entry / exit baseline 下做可对照的 sizing replay
3. 等 `Broker` 部分减仓契约明确后，再研究 `卖多少`

---

## 5. 首批 hypothesis register

首批执行候选固定为：

1. `single-lot control`
   - 固定最小一手，作为最朴素对照组
2. `fixed-notional control`
   - 固定名义金额
3. `fixed-risk`
   - 固定每笔风险预算
4. `fixed-capital`
   - 固定资本单位
5. `fixed-ratio`
   - 随账户增长按阶梯加单位
6. `fixed-unit`
   - 固定单位数量
7. `williams-fixed-risk`
   - 以最大损失为锚的固定风险
8. `fixed-percentage`
   - 固定账户百分比风险
9. `fixed-volatility`
   - 按波动幅度决定单位

概念层只保留、但当前不作为首批执行卡的对象：

1. `martingale`
   - 只作为反例概念保留，不作为当前生存优先目标下的正式候选
2. `anti-martingale`
   - 作为方法论背景吸收进上述各类正向 sizing family

---

## 6. 证据口径

第三战场当前固定产出三类证据：

1. `matrix`
   - 各 sizing family 的统一窗口对照矩阵
2. `digest`
   - retained / no-go 裁决摘要
3. `record`
   - 每张卡的正式结论记录

当前评价指标必须至少包含：

1. `net_pnl`
2. `ev_per_trade`
3. `profit_factor`
4. `max_drawdown`
5. `trade_count`
6. `avg_position_size`
7. `exposure_utilization`
8. `ruin-sensitive path metrics`

---

## 7. 当前不允许做的事

第三战场当前明确不允许：

1. 借 `MSS / IRS` 给 sizing 加解释性特例
2. 一上来把 `买多少` 与 `卖多少` 混成同一轮
3. 先做局部参数微扫，再补 baseline freeze
4. 把书里的公式直接当真，不做长窗 formal replay
5. 直接把研究结果宣布为主线默认参数

---

## 8. 当前一句话方案

第三战场当前一句话方案固定为：

`以 legacy_bof_baseline 为固定 entry baseline，先在 no IRS / no MSS 条件下独立验证 sizing family，再在 Broker 契约允许后独立验证 partial-exit family。`
