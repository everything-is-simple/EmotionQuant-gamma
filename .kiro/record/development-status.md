# EmotionQuant 开发状态（重启版模板）

**状态**: Active（正式治理）  
**最后更新**: 2026-03-02  
**当前阶段**: Rebuild Week 0（治理与设计冻结后启动）

---

## 1. 权威入口（SoT）

| 类型 | 路径 | 说明 |
|---|---|---|
| 设计总纲 | `docs/design-v2/rebuild-v0.01.md` | 当前唯一设计口径 |
| 路线图 | `.kiro/roadmap/roadmap.md` | 周级推进计划 |
| 模块实现卡 | `.kiro/roadmap/spec-*.md` | 模块拆解与验收 |
| 工作流 | `.kiro/steering/6A-WORKFLOW.md` | 固定执行流程 |
| 技术债 | `.kiro/record/debts.md` | 风险与欠账追踪 |
| 资产复用 | `.kiro/record/reusable-assets.md` | 可复用沉淀 |

---

## 2. 当前总体状态

| 项目 | 结论 | 备注 |
|---|---|---|
| 系统设计 | 已完成终审修订 | 可进入正式版冻结 |
| 系统治理 | 已建立重启模板 | 从本周开始按 6A 强制执行 |
| 代码实现 | 待启动 | 按 Week1 -> Week4 推进 |

---

## 3. 迭代看板（四周）

| 周次 | 目标 | 对应 spec | 状态 |
|---|---|---|---|
| Week 1 | Data 层可运行闭环 | `spec-01-data-layer.md` | TODO |
| Week 2 | Selector + Strategy（BOF） | `spec-02-selector.md`, `spec-03-strategy.md` | TODO |
| Week 3 | Broker + Backtest | `spec-04-broker.md` | TODO |
| Week 4 | Report + 联调 + 纸上交易 | `spec-05-backtest-report.md` | TODO |

---

## 4. 本周执行区（滚动维护）

### 4.1 本周目标

- [ ] 填写本周目标（1-3 条）

### 4.2 进行中任务

| 任务 | 负责人 | 开始日期 | 状态 | 阻塞 |
|---|---|---|---|---|
| - | - | - | - | - |

### 4.3 已完成任务

| 日期 | 任务 | 结果 | 证据 |
|---|---|---|---|
| 2026-03-02 | 治理重启：record 三件套 + 6A 正式版模板落地 | completed | `.kiro/record/*.md`, `.kiro/steering/6A-WORKFLOW.md` |
| 2026-03-02 | 治理补丁：6A v1.2 强化 + architecture Order 修正 + 设计文档 4 项修复 | completed | `6A-WORKFLOW.md` v1.2, `architecture.md`, 4 design-v2 docs |

---

## 5. 每次任务收口必填（A6）

每个任务完成时，必须在本节追加一行：

| 日期 | 任务/PR | run | test | artifact | review | 记录同步 |
|---|---|---|---|---|---|---|
| 2026-03-02 | 治理重启模板落地 | n/a | n/a | `.kiro/record/*.md`, `.kiro/steering/6A-WORKFLOW.md` | 本次治理评审结论 | debts/status/assets/roadmap 已同步，spec=N/A（治理任务） |
| 2026-03-02 | 治理补丁：6A v1.2 + architecture Order + 设计文档修复 | n/a | n/a | `6A-WORKFLOW.md` v1.2, `architecture.md`, design-v2 docs | 治理评审 | debts=无变化, status=已同步, assets=无变化, roadmap=N/A, spec=N/A（治理任务） |

---

## 6. 风险与决策

| 日期 | 类型 | 内容 | 处理策略 | 状态 |
|---|---|---|---|---|
| 2026-03-02 | 治理决策 | 工作流取舍：6A 作为唯一执行流程，RIPER-5 仅保留条件评审思想 | 已并入 `.kiro/steering/6A-WORKFLOW.md`，reference 索引同步修订 | closed |

---

## 7. 版本记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-03-02 | v1.0 | 重启清零：建立正式模板并切换到 `.kiro` 治理基线 |
