# Phase 8 / data contract residual audit
**状态**: `Active`  
**日期**: `2026-03-18`  
**类型**: `mainline audit package`

---

## 1. 目标

这张卡只回答一个问题：

`在 Phase 7 已经把数据底座切成 TDX local-first 之后，当前主线代码、测试、运行手册与下游战场里，还残留了多少旧数据合同假设。`

---

## 2. 为什么现在开这张卡

`Phase 7` 已经完成：

1. `vipdoc + hq_cache + mootdx` 成为主底座
2. `BaoStock` 降为 light incremental fallback
3. `TuShare` 降为 emergency fallback
4. `industry_member / l1_industry_member` 已成为活跃行业合同
5. `up_limit / down_limit` 已改为本地规则推导

当前最大的系统性隐患，已经从“数据层没打通”变成了：

`旧合同假设仍可能散落在 src/data -> selector -> broker -> backtest -> docs 的接缝处。`

---

## 3. 范围

本卡允许修改：

1. [`../../src/data`](../../src/data)
2. [`../../src/selector`](../../src/selector)
3. [`../../src/broker`](../../src/broker)
4. [`../../src/backtest`](../../src/backtest)
5. [`../../tests`](../../tests)
6. [`../../docs/reference`](../../docs/reference)
7. [`../../docs/spec/v0.01-plus`](../../docs/spec/v0.01-plus)

本卡明确不做：

1. 不重开新的数据源研究
2. 不再改写 `Phase 7` 的主底座方向
3. 不借机重开 `IRS / MSS` 主线
4. 不把任何 sidecar 研究结果偷升格成 runtime gate

---

## 4. 审计对象

本卡至少要清点以下残留假设：

1. 仍假设行业语义严格等同 `SW2021`
2. 仍假设 `l1_sw_industry_member` 是活跃合同
3. 仍假设涨跌停来自在线事实表
4. 仍假设 `raw_daily_basic` 是主链刚需
5. 仍假设在线源优先于本地源
6. 文档仍写旧口径但代码已切新口径

---

## 5. 交付物

本卡完成时应至少交付：

1. 一份正式残留审计 record
2. 一份残留假设清单
3. 一份必要修订清单
4. 更新后的主线入口与运行口径说明

---

## 6. 验收标准

1. 当前主线活跃合同与运行手册一致
2. 旧合同假设只允许留在迁移兼容层或历史 records
3. 不再出现“代码已切新合同，文档仍声称旧合同是活跃口径”的接缝
4. `preflight` 通过
