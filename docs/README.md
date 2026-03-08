# EmotionQuant 文档导航

**版本**: `v2.2`  
**最后更新**: `2026-03-08`  
**文档状态**: `Active`

---

## 定位

`docs/README.md` 只承担总导航职责。

它回答的是：

1. 现在新版设计去哪里看
2. 历史基线去哪里看
3. 治理 / roadmap / evidence / status 去哪里看

它不再承担新版设计正文。

---

## 当前有效入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计空间总入口 |
| 设计迁移边界声明 | `docs/design-migration-boundary.md` | 说明 `blueprint/` 与 `docs/` 的职责边界 |
| v0.01 历史基线 | `docs/design-v2/01-system/system-baseline.md` | 冻结历史基线，用于对照、回退与回归验证 |
| 当前治理状态 | `docs/spec/common/records/development-status.md` | 当前阶段、风险、看板与重启条件 |
| 当前治理归档入口 | `docs/spec/README.md` | 版本治理、roadmap、evidence、records 总入口 |
| 工作流 | `docs/workflow/6A-WORKFLOW.md` | 固定执行流程 |

---

## 目录地图

| 目录 | 角色 | 主入口 | 何时查看 |
|---|---|---|---|
| `blueprint/` | 新版设计权威层 | `blueprint/README.md` | 看完整设计、实现方案、执行拆解 |
| `design-v2/` | 历史基线与兼容桥接 | `docs/design-v2/README.md` | 回看 `v0.01 Frozen` 或查旧桥接 |
| `spec/` | 治理 / roadmap / evidence / records | `docs/spec/README.md` | 看当前推进、证据、状态、版本材料 |
| `observatory/` | 观察框架与评审标准 | `docs/observatory/README.md` | 做评审、复盘、门禁核对 |
| `Strategy/` | 理论来源与方法论溯源 | `docs/Strategy/README.md` | 查理论依据，不看执行口径 |
| `steering/` | 治理铁律与不可变约束 | `docs/steering/README.md` | 判断方案是否越界 |
| `workflow/` | 任务执行流程 | `docs/workflow/README.md` | 按固定流程推进任务 |
| `reference/` | 外部参考资料 | `docs/reference/README.md` | 查规则、运维参考，不作执行口径 |
| `operations/` | 仓库运维文档 | `docs/operations/README.md` | 查环境落地、排障与本地运维 |

---

## 按任务导航

### 1. 想确认“新版设计到底按什么定义”

1. `blueprint/README.md`
2. `blueprint/01-full-design/`
3. `docs/design-migration-boundary.md`

### 2. 想确认“当前做到哪里、现在该执行什么”

1. `docs/spec/common/records/development-status.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/README.md`

### 3. 想回看旧系统或历史基线

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/design-v2/README.md`

### 4. 想做评审、复盘或证据核对

1. `docs/observatory/README.md`
2. `docs/spec/<version>/evidence/`
3. `docs/spec/common/records/development-status.md`

---

## 冲突优先级

若文档之间出现冲突，按以下优先级处理：

1. `docs/design-migration-boundary.md`
2. `blueprint/`
3. `docs/spec/common/records/development-status.md`
4. `docs/spec/`
5. `docs/design-v2/01-system/system-baseline.md`（仅历史基线问题）
6. `docs/steering/`
7. `docs/observatory/`、`docs/Strategy/`、`docs/reference/`

---

## 维护边界

1. 所有新设计，只能进入 `blueprint/`。
2. `docs/` 不再新增新版设计正文。
3. `docs/` 只维护：
   - 导航
   - 治理
   - records
   - evidence
   - 历史说明
   - 兼容跳转
4. 文档路径或入口变更后，统一运行 `scripts/ops/check_docs.ps1` 做回归检查。

---

## 相关入口

- 仓库总览：`README.md`
- Agent 规则：`AGENTS.md`
- 新版设计空间：`blueprint/README.md`
- 设计迁移边界声明：`docs/design-migration-boundary.md`
- 代码实现：`src/`
- 文档 gate：`scripts/ops/check_docs.ps1`
