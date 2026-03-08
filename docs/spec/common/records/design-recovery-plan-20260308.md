# Gamma 当前主线设计恢复计划

**状态**: `Active`  
**日期**: `2026-03-08`  
**适用范围**: `G:\EmotionQuant-gamma\docs`  
**关联状态**: `docs/spec/common/records/development-status.md`

---

## 1. 问题定义

当前 `gamma` 文档的主要问题，不是简单的“过多”或“过少”，而是三类内容重新缠在一起：

1. 稳定设计层
2. 执行治理层
3. 历史/证据层

其直接后果是：

1. `Frozen` 文档通过“前置当前映射”承担了当前主线解释职责。
2. `development-status.md` 承担了部分设计解释职责。
3. 当前主线读者需要在同一份文档内反复切换历史口径与当前口径。

本计划只做设计抢救，不做全仓文档重构。

---

## 2. 目标

在冻结 `gamma` 现有目录总结构的前提下，恢复当前主线所需的最小稳定设计骨架。

恢复范围固定为 5 份当前主线文档：

1. `Selector`
2. `PAS-trigger / BOF`
3. `IRS-lite`
4. `MSS-lite`
5. `Broker / Risk`

每份恢复文档固定只回答 6 件事：

1. 职责
2. 输入
3. 输出契约
4. 不负责什么
5. 决策规则 / 算法
6. 失败模式与验证证据

---

## 3. 非目标

1. 不重写 `docs/` 总目录结构。
2. 不删除 `v0.01 Frozen` 历史文档。
3. 不把所有 `alpha / beta` 旧设计整体搬回 `gamma`。
4. 不让 `records` 或 `development-status` 继续承担当前主线设计 SoT。
5. 不在同一份正文里继续混写 `Frozen` 历史正文和 `v0.01-plus` 当前正文。

---

## 4. 设计分层规则

### 4.1 稳定设计层

位置：

- `docs/design-v2/02-modules/`
- `docs/design-v2/03-algorithms/core-algorithms/`

职责：

- 维护当前主线长期稳定的模块边界与算法边界
- 不承担阶段推进、任务看板、一次性评审结论

### 4.2 执行治理层

位置：

- `docs/spec/v0.01-plus/`
- `docs/spec/common/records/`

职责：

- 维护路线图、Gate、run 规则、当前状态、阶段记录
- 不承载当前主线设计正文

### 4.3 历史/证据层

位置：

- `docs/spec/<version>/evidence/`
- `docs/spec/<version>/records/`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-v2/02-modules/*-design.md` 中的 `Frozen` 历史正文

职责：

- 维护冻结基线、实验记录、回测证据、历史回退入口
- 不承担当前主线语义解释

---

## 5. 本次修复动作

1. 新增当前主线 5 份恢复文档。
2. 将 `Selector / Strategy / Broker` 的 `Frozen` 模块文档改为纯历史口径，并只保留当前主线导航链接。
3. 将 `design-v2` 与 `core-algorithms` 入口改为“稳定设计层”口径。
4. 将 `down-to-top-integration.md` 明确为当前主线集成骨架，而不是替代全部细案。
5. 将 `development-status.md` 明确为状态文档，不再作为设计解释入口。

---

## 6. 完成标准

满足以下条件即视为本轮恢复完成：

1. 当前主线的 5 个关键对象都有独立文档。
2. 每份当前主线文档都采用统一的 6 段结构。
3. `Frozen` 文档不再通过“当前主开发线映射”承担当前正文职责。
4. `design-v2/README.md` 与 `core-algorithms/README.md` 能直接把读者带到当前主线设计。
5. `development-status.md` 顶部明确声明“只记状态，不记设计正文”。
