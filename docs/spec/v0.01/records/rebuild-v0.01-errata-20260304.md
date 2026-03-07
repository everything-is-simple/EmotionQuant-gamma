# EmotionQuant v0.01 勘误补充（执行手册）

**版本**: v0.01 勘误补充  
**状态**: Active（仅补充执行约束，不改 Frozen 主干语义）  
**日期**: 2026-03-04  
**适用范围**: `docs/design-v2/01-system/system-baseline.md` 的实现细化

## 1. 目的

本补充用于收敛 v0.01 实施期的关键不确定性，确保实现具备以下属性：

1. 防未来函数（as-of 可得性）
2. 订单状态闭环（可终止）
3. 重跑可复现（run 元数据完整）
4. Schema 可演化（迁移有门）
5. 候选可解释（漏斗证据可回溯）

> 约束说明：若与 Frozen 主干冲突，以 `system-baseline.md` 为准；本文件仅增加实现细节，不改变执行语义。

## 2. 执行补充规则

### 2.1 As-Of 数据访问约束（新增）

1. Strategy / Selector 的表读取必须显式携带 `asof_date`。
2. 默认过滤规则：`trade_date <= asof_date`（或统一 `date <= asof_date`）。
3. 仅 `Store` 可放行读取；禁止业务模块直接拼接“无日期上限 SQL”。

### 2.2 订单生命周期补全（新增）

1. `l4_orders.status` 在 `PENDING/FILLED/REJECTED` 基础上补充 `EXPIRED`。
2. `PENDING` 订单必须具备过期条件（例如超过 N 个交易日自动过期）。
3. 报告层必须统计 `EXPIRED` 数量与占比。

### 2.3 `_meta_runs` 元数据扩展（新增）

每次 run 至少记录：

1. `config_hash`（参数快照哈希）
2. `data_snapshot`（数据版本/快照标识）
3. `git_commit`（代码版本）
4. `runtime_env`（运行环境标记）

### 2.4 Schema 版本门（新增）

1. DuckDB 增加 `_meta_schema_version`。
2. 启动时校验 `db_schema_version == code_schema_version`。
3. 版本不一致时必须阻断并提示“迁移或重建”，禁止静默继续运行。

### 2.5 候选可解释性落地（新增）

`StockCandidate` 结果契约不改字段冻结；解释性信息通过独立追踪表/报告字段落地，至少包含：

1. `asof_date`
2. `filters_passed`（经过的 gate 集合）
3. `reject_reason`（未入池原因，可多值）
4. `liquidity_tag`（流动性分层标签）

## 3. 实现落点建议

1. `src/data/store.py`: `read_table_asof` + schema_version gate
2. `l4_orders` DDL: `EXPIRED` 状态约束
3. `main.py` / runner: `_meta_runs` 扩展字段写入
4. `reporter`（Week4）: `EXPIRED` 与漏斗证据统计





