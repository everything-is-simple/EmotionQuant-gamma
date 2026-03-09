# EmotionQuant 低频量化系统基线（v0.01）

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `执行语义变更必须进入独立实验包或后续正式版本；仅允许历史说明、链接修复、归档指针与非语义性勘误。`  
**上游文档**: `无（v0.01 Frozen 系统级历史基线）`  
**数据运维记录**: `docs/spec/v0.01/records/data-rebuild-runbook-20260303.md`

> 当前定位声明：
> 本文是 `v0.01 Frozen` 的历史基线参考文档，只定义当时冻结下来的执行语义、模块边界与验收口径。
> 它不再承担当前主线设计正文，也不再承载实现偏差流水、Gate 过程记录或后续版本计划正文。
> 当前主线请看 `blueprint/`，当前治理与历史证据请看 `docs/spec/`。

## 1. 目标

构建一个低频、可回测、可执行、可复盘的 A 股结构交易系统，刻意避开高频与拥挤赛道。

系统只回答三件事：

1. 买谁：全市场缩池后的候选标的。
2. 何时买：T 日收盘触发即生成信号，T+1 开盘按开盘价买入。
3. 买多少/何时卖：`R` 风险仓位 + 失效优先退出。

## 2. v0.01 范围（强约束）

1. 形态触发器采用注册表机制，但 **仅启用 BOF（Spring/Upthrust）**。
2. `BPB / TST / PB / CPB` 全部在册，作为后续历史设想保留，不进入 `v0.01` 实盘口径。
3. 扫描流程固定为两阶段：
   1. 全市场粗筛（约 `5000 -> 200`）
   2. 候选池形态精扫（约 `200 -> 50~100 -> 最终信号`）
4. 执行语义固定：`signal_date=T`，`execute_date=T+1`，成交价 `T+1 open`。

## 3. 模块边界

1. `Data`：缓存、增量更新、清洗、落库。
2. `Selector`：基础过滤 + `MSS / IRS` 前置漏斗，输出候选池，不输出买卖动作。
3. `Strategy`：`BOF` 单形态触发检测，输出 `Signal`。
4. `Broker`：仓位、风控、撮合、退出。
5. `Backtest / Report`：回测与复盘统计。

### 3.0A 现行设计桥接映射（仅导航，不定义正文）

为避免把 `v0.01 Frozen` 历史基线误读成仓库现行设计，补充说明如下：

1. 仓库现行设计权威层已切换到：
   - `docs/design-migration-boundary.md`
   - `blueprint/README.md`
2. 现行设计的三层正文入口是：
   - `blueprint/01-full-design/`
   - `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
   - `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. 本文件正文只保留 `v0.01 Frozen` 历史执行语义，不直接定义仓库现行设计。

### 3.0B 历史治理与证据入口（仅导航）

`v0.01 Frozen` 的历史治理、证据与 release 归档统一位于：

1. `docs/spec/v0.01/README.md`
2. `docs/spec/v0.01/records/`
3. `docs/spec/v0.01/evidence/`
4. `docs/spec/common/records/development-status.md`

本文件不再继续堆叠实现偏差清单、长篇评审流水或一次性检查结果。

### 3.1 历史总览入口

如需回看 `v0.01 Frozen` 的结构补充，请查以下历史参考文档：

1. `docs/design-v2/01-system/architecture-master.md`
2. `docs/design-v2/02-modules/selector-design.md`
3. `docs/design-v2/02-modules/strategy-design.md`
4. `docs/design-v2/02-modules/broker-design.md`
5. `docs/design-v2/02-modules/data-layer-design.md`
6. `docs/design-v2/02-modules/backtest-report-design.md`

口径规则：

1. 本文件负责 `v0.01 Frozen` 的执行语义、模块边界、结果契约与版本范围。
2. 其余 `design-v2` 文档只承担历史结构补充与模块说明，不再承担独立算法 SoT 职责。
3. `docs/spec/v0.01/` 负责 `v0.01 Frozen` 的治理、evidence、records 与历史 runbook。
4. `docs/Strategy/` 与 `docs/reference/` 为理论/外部参考，不作为 `v0.01` 执行口径。
5. 仓库现行设计权威不在本文件内定义，而在 `blueprint/`。

### 3.2 结果契约（v0.01 字段冻结）

模块间只传递结果契约（pydantic 对象），字段口径如下：

1. `MarketScore`（`MSS -> Selector`）：`date, score, signal`
2. `IndustryScore`（`IRS -> Selector`）：`date, industry, score, rank`
3. `StockCandidate`（`Selector -> Strategy`）：`code, industry, score`
4. `Signal`（`Strategy -> Broker`）：`signal_id, code, signal_date, action, strength, pattern, reason_code`
5. `Order`（`Broker` 内部 `risk -> matcher`）：`order_id, signal_id, code, action, quantity, execute_date, pattern, is_paper, status, reject_reason`
6. `Trade`（`Broker -> Report`）：`trade_id, order_id, code, execute_date, action, price, quantity, fee, pattern, is_paper`

补充约束：

1. `Signal.action` 在 `v0.01` 仅允许 `BUY`；`SELL` 由 `Broker` 风控层内部生成。
2. `Signal.signal_id` 采用确定性幂等键：`f"{code}_{signal_date}_{pattern}"`。

## 4. v0.01 触发器口径（BOF）

做多 `Spring` 触发条件（全部满足）：

1. `Low < LowerBound * (1 - 1%)`
2. `Close >= LowerBound`
3. `Close` 位于当日振幅上部（收盘位置 `>= 0.6`）
4. `Volume >= SMA20(Volume) * 1.2`

执行语义（`v0.01 Frozen`）：

满足上述 4 条即在 **T 日收盘后** 生成 `BUY` 信号（`signal_date=T`），并在 **下一交易日开盘** 成交（`execute_date=T+1`，成交价 `T+1 open`）。

补充约束：

1. `LowerBound = min(adj_low[t-20, t-1])`，窗口不足 `20` 个交易日时不触发。
2. 价格字段统一使用 `adj = raw × adj_factor` 口径（`adj_open / adj_high / adj_low / adj_close`）。
3. `SMA20(Volume)` 使用过去 `20` 个有效交易日，停牌日不计入窗口。
4. `T+1` 指下一交易日，不是自然日。
5. 一字涨停、一字跌停、停牌日不作为可成交触发样本；可记录观察，但不得下单。

## 5. 风控口径（v0.01）

1. 单笔账户风险：`0.8%`
2. 次日不延续：退出
3. 收盘跌回结构内：退出
4. 同标的连续 3 次失败：冻结 120 天

执行与成本约束：

1. 单只仓位不得超过账户净值 `10%`。
2. 费用模型最小包含：佣金、印花税（卖出侧）、过户费；参数由 `config.py` 注入。
3. `is_halt=true`、买入开盘触及涨停、卖出开盘触及跌停时，订单应标记为 `REJECTED`。

## 6. 验收口径

1. 单形态回测（`BOF`）可独立运行。
2. 输出分环境统计（牛 / 震荡 / 熊）。
3. 报告必须包含中位数路径，不以最佳路径作为结论。

### 6.1 MSS/IRS 使用模式验证（v0.01 正式口径）

`MSS / IRS` 在 `v0.01` 视为待验证假设，但 `v0.01 Frozen` 的正式执行链路仍是 `Selector` 前置漏斗。回测与评审按以下顺序做消融对照：

1. `BOF baseline`：关闭 `ENABLE_MSS_GATE` 与 `ENABLE_IRS_FILTER`
2. `BOF + MSS gate`：仅开启 `MSS` 硬门控
3. `BOF + MSS gate + IRS filter`：再开启 `IRS` 硬过滤

每一步都必须输出同口径对照指标：胜率、盈亏比、期望值、最大回撤、分环境中位数路径。

历史结论（截至 `2026-03-06`）：

1. Top-down 模式下，`MSS hard gate` 明显压缩样本。
2. `IRS + MSS soft overlay` 后来成为 `v0.01-plus` 的替代主线方向。
3. 这些结论属于后续历史演进输入，不回写 `v0.01 Frozen` 的正式执行语义。

### 6.2 通过阈值与回退门（v0.01）

1. `BOF baseline` 最低通过门：
   1. `expected_value >= 0`
   2. `profit_factor >= 1.05`
   3. `max_drawdown <= 25%`
   4. `trade_count >= 60`
2. 新漏斗（如 `+MSS`、`+IRS`）相对前一配置的回退条件：
   1. `expected_value` 下降超过 `10%`
   2. `max_drawdown` 恶化超过 `20%`
   3. 任一市场环境的中位数路径由正转负，且连续两个评估窗未恢复
3. 验收报告必须同时给出：参数快照、样本区间、环境切分口径、回退判定结果。

### 6.3 Gene 模块使用规则（v0.01-v0.02）

1. `v0.01` 禁止启用 `ENABLE_GENE_FILTER`。
2. `gene` 仅允许做事后分析：基于 `BOF` 历史交易样本反推候选特征。
3. `v0.02` 之前，不允许将“5 牛 5 衰”定义作为硬过滤进入实盘流程。

## 7. 已冻结的历史演进说明

本节只保留历史对照价值，不定义当前主线路线图。

1. `v0.02` 的历史设想：加入 `BPB`，与 `BOF` 并行评估。
2. `v0.03` 的历史设想：加入 `TST / PB / CPB` 与组合模式评估。
3. 所有 `v0.02+` 表述都只代表 `v0.01` 当时留下的后续设想；仓库当前主开发线已经改为 `v0.01-plus`。

历史晋级门槛仍保留为参考：

1. `v0.01` 连续两个评估窗通过 §6.2，且无强制回退。
2. 新增形态必须先通过单形态回测，再进入组合评估。
3. 任何新增模块不得破坏 `T+1 Open` 执行语义与结果契约字段冻结规则。

## 8. 冲突处理规则

1. 若 `docs/design-v2/` 其他文档与本文件冲突，以本文件为准。
2. 若本文与 `blueprint/` 冲突，按“问题所处层级”裁决：
   1. 历史 `v0.01 Frozen` 口径，以本文为准。
   2. 当前主线设计与实现，以 `blueprint/` 为准。
   3. 当前治理状态、阶段判断、风险与推进，以 `docs/spec/common/records/development-status.md` 为准。

### 8.1 当前权威入口

1. `docs/design-migration-boundary.md`
2. `blueprint/README.md`
3. `blueprint/01-full-design/`
4. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
5. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
6. `docs/spec/common/records/development-status.md`

### 8.2 研究附录入口（非约束）

`docs/observatory/god_view_8_perspectives_report_v0.01.md` 作为系统观察框架与版本演进研究附录保留。

口径约束：

1. 该附录用于补充观察维度与路线思考，不作为 `v0.01` 的强制实现条款。
2. 涉及 `v0.02+` 的分桶、分层、生态管理、组合层建议，仅在对应版本评审通过后纳入执行口径。
3. 若附录与本文件冲突，仍以本文件（`Frozen`）为准。

## 9. 历史评审与偏差闭环索引

### 9.1 历史评审结论摘要

`v0.01 Frozen` 在封版前完成了多轮历史沙盘评审与偏差修复。现阶段只保留以下摘要：

1. 历史评审总计 16 轮，累计闭环偏差 `44` 项（`A1-S44`）。
2. 核心收敛方向包括：时序语义统一、确定性幂等键、`Broker` 信任分级修正、回测/撮合链路一致性、费用与涨跌停口径统一。
3. 这些偏差闭环属于历史实现治理证据，不再作为本文件正文长期维护对象。

### 9.2 历史证据归档位置

如果需要回看具体偏差项、评审标准、release 结论或重建 runbook，请直接查看：

1. `docs/spec/v0.01/records/release-v0.01-formal.md`
2. `docs/spec/v0.01/records/rebuild-v0.01-errata-20260304.md`
3. `docs/spec/v0.01/records/v0.01-post-baseline-retrospective-20260306.md`
4. `docs/observatory/sandbox-review-standard.md`
5. `docs/spec/v0.01/README.md`

### 9.3 当前维护边界

本文件后续只维护三类内容：

1. `v0.01 Frozen` 的历史执行语义与字段冻结口径。
2. 指向 `blueprint/` 与 `docs/spec/` 的边界说明。
3. 必要的历史归档入口。
