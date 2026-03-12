# 辅助层保留清单

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `docs/reference/`, `docs/observatory/`, `docs/workflow/`, `docs/design-migration-boundary.md`, `docs/README.md`

---

## 1. 定位

本文只回答一个问题：

`旧设计世界退场后，docs/ 下这些辅助层对象哪些必须保留，哪些可以继续瘦身，哪些未来可以并入或退场。`

这里不定义当前系统设计 SoT。

这里也不做删除命令。

它只固定：

1. 当前必要性等级
2. 最小保留形态
3. 未来继续瘦身的顺序条件

---

## 2. 判定规则

当前分类固定按下面四条判断：

1. 仍承担正式流程 SoT、跨目录边界声明或仓库级总导航职责的对象，归入 `必须保留`
2. 仍有稳定价值，但已经不承担主线设计裁决职责的对象，归入 `可继续瘦身`
3. 只有在“上游入口已替代 + 当前引用链已切断 + 职责已被更窄对象吸收”三条件同时成立时，才允许进入 `未来可并入/退场`
4. 不允许因为“目录看起来旧”或“文件数量不多”就直接删除

---

## 3. 对象层分类

### 3.1 必须保留

| 对象 | 当前角色 | 必要原因 |
|---|---|---|
| `docs/workflow/` | 流程层 | `6A-WORKFLOW.md` 仍是当前唯一固定执行流程 SoT，`development-status.md` 与 `reusable-assets.md` 仍以它为正式流程入口。 |
| `docs/design-migration-boundary.md` | 边界声明层 | 仍承担“为什么现行设计迁入 blueprint、为什么 docs 已降级”的统一边界声明，`AGENTS / design-v2 / development-status / system-constitution` 仍直接引用。 |
| `docs/README.md` | docs 总导航层 | 根 `README.md` 仍把它作为文档总入口；只要 `docs/` 继续承载历史、治理和辅助层，它就必须存在。 |

### 3.2 可继续瘦身

| 对象 | 当前角色 | 最小保留形态 |
|---|---|---|
| `docs/reference/` | 参考层 | 只保留 `README.md`、`a-stock-rules/` 和 `operations/`；不回长外部方法论综述。 |
| `docs/observatory/` | 方法层 | 只保留 `sandbox-review-standard.md` 和少量历史观察附录；不再回收战役专属计划或临时路线。 |

### 3.3 未来可并入 / 退场

当前对象层这一栏固定为：

`空`

原因是：

1. `reference/` 仍被 `README / AGENTS / setup-guide` 持续引用
2. `observatory/` 仍有 `sandbox-review-standard.md` 作为正式方法论锚点
3. `workflow/` 当前仍有 `6A-WORKFLOW.md` 作为正式流程 SoT
4. `design-migration-boundary.md` 和 `docs/README.md` 仍是跨目录入口锚点

所以截至 `2026-03-12`：

`这五个对象都还不能整体退场。`

---

## 4. 文件层机会

下面这些不是“现在就删”，而是后续继续瘦身时优先观察的对象：

### 4.1 可继续瘦身

| 文件 | 当前定位 | 后续动作 |
|---|---|---|
| `docs/reference/operations/temp-files-guide.md` | 运维补充说明 | 若 `setup-guide.md` 后续已完整吸收，可考虑并回单一运维入口。 |
| `docs/reference/operations/data-source-and-migration.md.template` | 脱敏模板 | 若模板后续稳定迁入脚本或独立模板仓，可继续降级。 |
| `docs/observatory/god_view_8_perspectives_report_v0.01.md` | 历史观察附录 | 当前可保留，但只作为观察与路线思考附录，不得再抬升为现行策略设计依据。 |
| `docs/workflow/README.md` | 单目录导航页 | 目录仍存在时保留；若未来流程层只剩一个单文件直链入口，可再评估并入上级导航。 |

### 4.2 未来可并入 / 退场

| 文件 | 未来条件 | 目标方向 |
|---|---|---|
| `docs/observatory/god_view_8_perspectives_report_v0.01.md` | `blueprint/` 与 `v0.01` roadmap 不再直接引用时 | 可并入 `v0.01` 历史归档层 |
| `docs/reference/operations/data-source-and-migration.md.template` | 若模板改为脚本生成或仓库外维护时 | 可移出 `docs/reference/operations/` |
| `docs/workflow/README.md` | 若 `docs/README.md` 和根 `README.md` 均直链 `6A-WORKFLOW.md` 且流程层不再扩展时 | 可评估移除目录级 README |

---

## 5. 当前允许动作

对这组辅助层对象，当前只允许：

1. 维护入口、边界、目录说明
2. 删除重复导航和冗余综述
3. 继续收口到最小保留形态
4. 把战役专属计划和临时路线迁回各自战役层

当前明确不允许：

1. 在这些目录里补写当前主线设计正文
2. 把参考层、方法层、流程层重新抬成设计 SoT
3. 在未切断引用链前整体删除目录
4. 把单个“好用的方法论文件”误写成“当前 Gate 结论”

---

## 6. 一句话裁决

`reference / observatory / workflow / design-migration-boundary / docs-README 这五块目前都还有必要，但都属于辅助层，不属于当前系统设计层；后续只能继续瘦身，不能回升为主线正文。`
