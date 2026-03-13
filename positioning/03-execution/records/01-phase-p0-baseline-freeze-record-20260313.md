# Phase P0 Baseline Freeze Record

**日期**: `2026-03-13`  
**阶段**: `Positioning / P0`  
**对象**: `第三战场 control baseline formalization`  
**状态**: `Active`

---

## 1. 目标

本文用于把 `Positioning` 第三战场后续所有仓位实验所依赖的 baseline 正式写死。

这张 record 只回答四件事：

1. 后续仓位研究固定基于哪条交易骨架
2. 当前 control 组是什么
3. 当前哪些变量明确不许动
4. 下一张执行卡是什么

---

## 2. 正式冻结对象

`P0` 完成后的 formal freeze 固定为：

1. `pipeline baseline = legacy_bof_baseline`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `buy-side sizing denominator = current Broker risk budget + max position cap semantics`

这意味着：

`Positioning` 当前不再回答“买什么 / 何时买”，只回答在这条固定交易骨架上“买多少 / 卖多少”。

---

## 3. 当前 control 组

第三战场当前 control 组正式固定为两条：

1. `single-lot control`
2. `fixed-notional control`

它们的角色不是最终候选，而是：

1. 给后续 sizing family 提供最朴素对照组
2. 避免一上来就把复杂仓位公式和 baseline 绑定在一起
3. 帮助识别“收益变化到底来自 sizing 机制还是来自 baseline 漂移”

---

## 4. 首批 sizing hypothesis register

当前允许进入正式 replay 队列的首批 sizing family 固定为：

1. `fixed-risk`
2. `fixed-capital`
3. `fixed-ratio`
4. `fixed-unit`
5. `williams-fixed-risk`
6. `fixed-percentage`
7. `fixed-volatility`

当前它们都还不是 retained candidate。

当前它们只获得：

`进入第三战场正式对照矩阵的准入资格。`

---

## 5. 当前不允许动的变量

`P0` 之后，直到 `P1 / null control matrix` 完成前，当前明确不允许动：

1. `entry family`
2. `Selector / BOF` 触发逻辑
3. `MSS risk_regime`、`IRS score` 或其派生字段
4. `partial-exit / scale-out`
5. `Broker` 当前统一退出语义

其中最关键的一条是：

`MSS / IRS 不得再作为仓位大小的输入变量。`

---

## 6. 当前系统现实

`P0` 同时正式确认了第三战场的系统现实：

1. 当前代码里的买入数量仍由 `risk_per_trade_pct + max_position_pct` 驱动
2. 当前主线里这两个倍率仍可被 `MSS overlay` 缩放
3. 当前 `SELL` 仍默认全平，尚未形成正式 `partial-exit` 契约

所以第三战场的顺序必须固定为：

1. 先做 `position sizing lane`
2. 再做 `partial-exit lane`

不能倒过来。

---

## 7. 下一张执行卡

`P0` 完成后的 next main queue card 固定为：

`P1 / null control matrix`

它要回答的问题是：

`在同一条 frozen baseline 下，single-lot control 和 fixed-notional control 各自给出什么样的账户曲线、暴露形状和风险底噪。`

只有把 control 组先跑出来，后面的 `fixed-risk / fixed-ratio / fixed-volatility` 才有正式比较基准。

---

## 8. 正式结论

当前 `P0 baseline freeze` 的正式结论固定为：

1. 第三战场已正式从 `Normandy` 分离，成为独立仓位研究线
2. 第三战场当前只研究 `买多少 / 卖多少`，不重开 alpha provenance
3. 第三战场的 frozen baseline 已正式固定为 `legacy_bof_baseline / no IRS / no MSS / current full-exit semantics`
4. `single-lot control` 与 `fixed-notional control` 已被正式指定为 control 组
5. 首批 sizing hypothesis register 已冻结，但尚未产生 retained candidate
6. `partial-exit lane` 继续后置，必须等 sizing baseline 对照完成后再打开
7. 第三战场下一张正式执行卡固定为 `P1 / null control matrix`

---

## 9. 一句话结论

`P0` 已经把第三战场后面到底在比什么写死了；从现在开始，仓位实验不再允许混入 entry、MSS、IRS 和 partial-exit 漂移。`
