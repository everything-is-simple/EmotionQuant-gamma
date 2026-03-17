# Data Layer 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与历史说明补充；执行语义变更必须进入后续版本或现行设计层。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

---

## 1. 文档定位

本文档是 `v0.01 Frozen` 的**历史 Data Layer 参考文档**。

它保留的价值主要是：

1. 记录 `L1-L4` 分层在历史版本中的语义。
2. 说明为什么历史版本坚持 DuckDB 单库存储与统一 `Store` 入口。
3. 给 `system-baseline.md` 提供数据层背景补充。

本文档不是仓库现行数据层正文。当前主线数据实现与推进，以 `blueprint/` 和 `docs/spec/` 为准。

---

## 2. 当前使用边界

当前阅读本文的正确用途是：

1. 回看 `v0.01 Frozen` 的历史分层语义。
2. 理解历史版本里 `fetch / clean / build / store` 的边界。
3. 对照当前主线哪些数据层语义被继承，哪些已经迁走。

当前不应把本文当作：

1. 当前仓库数据表结构的权威定义。
2. 当前 `L2/L3` 扩展字段的正式来源。
3. 当前数据脚本与运行命令的实现说明书。

---

## 3. 当前权威入口

### 3.1 历史冻结入口

`v0.01 Frozen` 的历史执行口径，以以下文件为准：

1. `docs/design-v2/01-system/system-baseline.md`

### 3.2 现行设计入口

仓库现行数据层设计与推进请直接查看：

1. `docs/design-migration-boundary.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/common/records/development-status.md`

### 3.3 当前数据提供方重构入口

`v0.01 Frozen` 之后，现行主线已经进入 `Phase 7 / data provider refactor`。
当前正式阅读入口补充为：

1. `blueprint/03-execution/15-phase-7-data-provider-refactor-card-20260317.md`

这一轮重构的现行口径是：

`vipdoc historical base + T0002/hq_cache static assets + BaoStock light incremental + TuShare emergency fallback`

其中 `mootdx` 的角色已经明确为：

1. 读取本地 `vipdoc` 日线
2. 读取本地 `block_*.dat` 板块成员
3. 作为股票列表/名称的轻量兜底接口

---

## 4. `v0.01 Frozen` 中 Data Layer 的历史职责

历史上，`Data Layer` 回答的问题是：

`如何把原始数据稳定变成可供 Selector / Strategy / Broker / Report 消费的分层数据。`

其职责可概括为四层：

1. **L1**：原始采集结果
2. **L2**：加工后的标准化日线与聚合快照
3. **L3**：算法输出
4. **L4**：历史分析缓存

历史版本里，这是一套“逻辑分层 + 单库存储”的设计，而不是多套独立数据系统。

---

## 5. 历史上保留的核心结论

### 5.1 DuckDB 单库 + 分层语义是高价值结论

`v0.01` 最值得保留的一条数据层结论，是：

1. 不搞多数据库并行体系
2. 不搞重型数据中台
3. 用 DuckDB 单库存储承接 `L1-L4`

这个结论的重要性，在于它把复杂度压回了可维护范围。

### 5.2 `L1-L4` 的依赖方向很重要

历史版本坚持的关键边界是：

1. `L2` 只读 `L1`
2. `L3` 只读 `L1/L2`
3. `L4` 只读 `L1/L2/L3`

这条依赖方向今天仍然是高价值约束，因为它直接决定模块耦合度和重跑边界。

### 5.3 `Store` 统一入口是历史高价值抽象

历史版本强调：

1. 所有读写都经 `store.py`
2. 避免在各模块里散落 SQL 和连接管理
3. 统一处理 upsert、批量写和幂等

这个抽象在今天依然有保留意义。

---

## 6. 历史摘要：Fetcher / Cleaner / Builder / Store

### 6.1 Fetcher

历史版本中的 `fetcher` 主要承担：

1. 拉取原始市场数据
2. 处理主备数据源与失败重试
3. 将原始结果写入 `L1`

### 6.2 Cleaner

历史版本中的 `cleaner` 主要承担：

1. 从 `L1` 生成标准化个股日线
2. 生成市场快照与行业聚合
3. 把结果写入 `L2`

### 6.3 Builder

历史版本中的 `builder` 主要承担：

1. 调度 `L2/L3/L4` 重建
2. 按层次推进生成流程
3. 控制增量或指定日期重算

### 6.4 Store

历史版本中的 `Store` 主要承担：

1. 统一数据库连接
2. 封装批量读写
3. 保证 upsert 和幂等语义

---

## 7. 当前已经过时或容易误导的旧内容

本次整理后，以下内容统一降级：

1. 文内完整 DDL 与全部历史字段细节。
2. `fetcher / cleaner / builder / store` 的详细实现草案。
3. 历史 CLI、重试、线程和磁盘空间细节。
4. 任何把本文当作当前表结构 SoT 的使用方式。

这些内容保留追溯价值，但已不再承担现行设计职责。

---

## 8. 与当前主线的关系

本文与当前主线的关系固定为：

1. 它说明历史版本为什么坚持 `L1-L4` 和 DuckDB 单库。
2. 它帮助解释当前主线数据层为何仍保留分层依赖语义。
3. 它不定义当前 `L2/L3` 扩展字段、sidecar 表或现行运行脚本。

---

## 9. 相关文档

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/01-system/architecture-master.md`
3. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
4. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
