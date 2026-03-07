# EmotionQuant 文档导航

**版本**: v2.1  
**最后更新**: 2026-03-07  
**文档状态**: Active

---

## 📖 定位

`docs/README.md` 只承担**总导航**职责：

1. 说明各目录的角色边界。
2. 给出当前有效入口。
3. 告诉读者“遇到什么问题该去哪里看”。

各子目录的详细清单、局部规则、局部背景，统一下沉到各自的 `README.md`，避免在总导航重复抄写一遍。

---

## 🔑 当前有效入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 设计 SoT | `docs/design-v2/01-system/system-baseline.md` | 当前唯一系统设计口径 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 当前治理状态、历史分段、重启条件 |
| 工作流 | `docs/workflow/6A-WORKFLOW.md` | 固定执行流程 |
| 文档总导航 | `docs/README.md` | 全局入口 |

---

## 🗺️ 目录地图

| 目录 | 角色 | 主入口 | 何时查看 |
|---|---|---|---|
| `design-v2/` | 系统设计与算法 SoT | `docs/design-v2/README.md` | 做设计、查模块边界、确认执行口径 |
| `observatory/` | 观察框架与评审标准 | `docs/observatory/README.md` | 做版本复盘、沙盘评审、证据核对 |
| `Strategy/` | 理论来源与方法论溯源 | `docs/Strategy/README.md` | 追溯 MSS/IRS/PAS 的理论依据 |
| `steering/` | 治理铁律与不可变约束 | `docs/steering/README.md` | 判断方案是否越界 |
| `spec/` | 分版本归档与治理记录 | `docs/spec/README.md` | 查路线图、证据、历史记录、当前状态 |
| `workflow/` | 任务执行流程 | `docs/workflow/6A-WORKFLOW.md` | 按 6A 执行任务 |
| `reference/` | 外部参考资料 | `docs/reference/README.md` | 查外部规则、运维参考，不作执行口径 |

---

## 🎯 按任务导航

### 1. 想确认“现在系统到底按什么口径执行”

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/steering/product.md`
3. `docs/spec/common/records/development-status.md`

### 2. 想开始一个实现/修订任务

1. `docs/workflow/6A-WORKFLOW.md`
2. `docs/design-v2/README.md`
3. `docs/steering/README.md`
4. 对应版本目录：`docs/spec/<version>/`

### 3. 想做评审、复盘或证据核对

1. `docs/observatory/sandbox-review-standard.md`
2. `docs/observatory/god_view_8_perspectives_report_v0.01.md`
3. `docs/spec/<version>/evidence/`

### 4. 想追溯历史决策或当前治理状态

1. `docs/spec/common/records/development-status.md`
2. `docs/spec/common/records/debts.md`
3. `docs/spec/common/records/reusable-assets.md`
4. `docs/spec/common/records/doc-thinning-audit-20260307.md`

### 5. 想查理论来源而不是执行规则

1. `docs/Strategy/README.md`
2. `docs/Strategy/theoretical-foundations.md`
3. 对应子目录：`docs/Strategy/MSS/`、`docs/Strategy/IRS/`、`docs/Strategy/PAS/`

---

## ⚖️ 冲突优先级

若文档之间出现冲突，按以下优先级处理：

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/steering/`
3. `docs/design-v2/` 其他文档
4. `docs/observatory/` 的评审标准
5. `docs/spec/common/records/development-status.md` 的当前状态说明
6. `docs/spec/` 其他历史归档
7. `docs/Strategy/` 与 `docs/reference/`

---

## 🧭 维护边界

1. `docs/README.md` 只保留全局导航，不重复列出各子目录的详细文件说明。
2. 子目录内部的详细清单、术语说明、局部维护规则，写在各自 `README.md`。
3. 一次性整理报告、检查报告、桥接审计统一标注为“历史记录/追溯记录”，不进入主入口首屏导航。
4. 文档路径与链接变更后，使用 `scripts/ops/preflight.ps1 -Profile docs` 或 `scripts/ops/check_docs.ps1` 做回归检查。

---

## 🔗 相关入口

- 仓库总览：`README.md`
- Agent 规则：`AGENTS.md`
- 代码实现：`src/`
- 文档预检入口：`scripts/ops/preflight.ps1`
- 文档 gate：`scripts/ops/check_docs.ps1`
- 文档状态检查：`scripts/ops/check_doc_status.ps1`

---

**维护责任**：项目负责人  
**更新原则**：仅在目录角色、主入口或优先级发生变化时更新

