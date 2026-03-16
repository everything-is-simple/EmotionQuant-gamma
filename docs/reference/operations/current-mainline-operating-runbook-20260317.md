# Current Mainline Operating Runbook

**状态**: `Active`  
**日期**: `2026-03-17`  
**对象**: `当前主线运行链路、风险开关、人工介入边界与 rollback 规则`

---

## 1. 定位

本文不是算法正文，也不是研究卡。

它只回答：

1. 当前主线实际按什么链路运行
2. 哪些风险开关允许开启
3. 哪些对象只能作为 shadow / sidecar / report 使用
4. 人工介入允许到什么程度
5. 什么情况下必须 rollback 或停机

---

## 2. 当前允许的默认运行模式

当前唯一允许的默认运行模式固定为：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL`

当前仍同时写死：

1. `old IRS-lite / MSS-lite` 不回到默认运行层
2. `SINGLE_LOT_CONTROL` 只保留为 floor sanity baseline
3. `Gene` 当前只允许作为 `context sidecar / report / dashboard`
4. 任何 retained / watch 对象都不得口头升格为默认项

---

## 3. 当前默认运行链路

当前主线运行链路固定为：

```text
Selector 初选
-> BOF baseline entry
-> FIXED_NOTIONAL_CONTROL
-> FULL_EXIT_CONTROL
-> Broker 执行
-> Backtest / Report / Evidence
```

当前若并行生成第四战场信息，只允许以：

1. `stock self-history tags`
2. `market / industry mirror ranks`
3. `conditioning readout`

的 report-side / dashboard-side sidecar 身份出现，不得直接改写 entry、sizing、exit。

---

## 4. 开工前检查

每次正式运行前，最低检查固定为：

1. 运行 `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile hook`
2. 确认当前数据库为 `G:\EmotionQuant_data\emotionquant.duckdb`
3. 确认 `legacy_bof_baseline` 可重跑
4. 确认未私自打开研究线 retained / watch 开关
5. 确认本次 run 的目标是 baseline runtime，不是假装 Phase 6 promotion 已完成

---

## 5. 允许的风险开关

当前允许的正式运行开关固定为：

1. `entry family = BOF baseline only`
2. `sizing baseline = FIXED_NOTIONAL_CONTROL`
3. `exit baseline = FULL_EXIT_CONTROL`
4. `single-lot floor sanity` 可作为验证对照，不作为第二 operating lane
5. `Gene context sidecar` 可进入 report / attribution / dashboard

当前禁止的运行开关固定为：

1. 打开旧 `IRS-lite / MSS-lite` 作为默认 runtime layer
2. 把 `Gene` 条件层改成 hard filter
3. 把 `TRAIL_SCALE_OUT_25_75` 或其他 retained queue 改成默认 partial-exit
4. 把 `Normandy` watch / retained branch 改成默认 entry
5. 在没有 formal package 的前提下切换默认运行路径

---

## 6. 人工介入边界

当前人工允许做的事：

1. 因 `preflight`、数据契约或关键 trace 异常而暂停运行
2. 做 report-side 环境观察与复盘解释
3. 按 `Broker` 既有语义执行 `STOP_LOSS / FORCE_CLOSE`
4. 在 formal package 内记录问题并回退到 `legacy_bof_baseline`

当前人工禁止做的事：

1. 人工把 `Gene` 标签当成未编码的交易过滤器
2. 人工把 retained / watch 结论临时加到默认运行
3. 因少量样本亮点改写默认 sizing / exit
4. 不经 formal record 就宣布“统一默认系统已切换完成”

---

## 7. 报告与证据要求

每次正式运行后，最低要能回答：

1. 这次 run 是否仍在 `legacy_bof_baseline` 下运行
2. `FIXED_NOTIONAL_CONTROL / FULL_EXIT_CONTROL` 是否按预期执行
3. sidecar / report 是否清楚区分了 runtime layer 与 context layer
4. 任一失败路径是否都能通过 `run_id / signal_id` 回溯

---

## 8. Rollback 与停机规则

当前正式 rollback target 固定为：

`legacy_bof_baseline`

出现以下任一情况时，必须停止口头 promotion 并回到 baseline：

1. 端到端运行链被破坏
2. trace / report / sidecar 失真
3. 研究层对象被偷带进 runtime hard gate
4. 默认参数切换没有 formal package 和 formal gate

---

## 9. 与 Phase 6 的关系

本文当前服务于两件事：

1. 约束当前 baseline operating system
2. 为 `Phase 6 / unified default system migration package` 提供 runbook baseline

这意味着：

`在 Phase 6B integrated gate 跑完之前，本文优先保护当前 baseline，不为未过 gate 的统一默认系统候选背书。`
