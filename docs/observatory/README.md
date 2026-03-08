# Observatory（观察台）

## 定位

`docs/observatory/` 存放系统观察框架与评审标准。

这里回答的是“如何观察、如何验证、如何做发布前审视”，不是“模块内部如何实现”。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 历史研究附录 | `god_view_8_perspectives_report_v0.01.md` | 做历史复盘、路线思考、观察补充 |
| 当前评审标准 | `sandbox-review-standard.md` | 做沙盘评审、偏差闭环、定稿门禁 |
| 新版设计权威层 | `blueprint/README.md` | 查看新版设计、实现方案与执行拆解 |
| 当前治理归档 | `docs/spec/v0.01-plus/README.md` | 查看当前主线 Gate、记录与证据入口 |

## 使用规则

1. `god_view_8_perspectives_report_v0.01.md` 是研究附录，用于观察和规划，不直接改写当前执行口径。
2. `sandbox-review-standard.md` 是当前评审规范；涉及关键链路变更时，应按其要求产出证据。
3. 讨论 `v0.01 Frozen` 时，以 `docs/design-v2/01-system/system-baseline.md` 为准；讨论当前主线设计时，以 `blueprint/` 为准；讨论当前治理推进时，以 `docs/spec/v0.01-plus/` 为准。
4. 评审产物与证据统一落到 `docs/spec/<version>/evidence/` 或对应 records，不堆回 observatory 根目录。

## 按场景导航

### 1. 做版本规划或大范围复盘

1. `god_view_8_perspectives_report_v0.01.md`
2. `docs/spec/<version>/roadmap/`
3. `docs/spec/common/records/development-status.md`

### 2. 做模块评审或发布前验证

1. `sandbox-review-standard.md`
2. `blueprint/README.md`
3. `docs/spec/<version>/evidence/`

### 3. 做偏差闭环或门禁复核

1. `sandbox-review-standard.md`
2. 对应 evidence / records 文档
3. `docs/workflow/6A-WORKFLOW.md`

## 相邻目录边界

- `blueprint/`：定义新版设计与实现边界。
- `docs/design-v2/`：保留历史基线与兼容桥接。
- `docs/Strategy/`：提供理论来源与方法论背景。
- `docs/spec/`：保存具体版本证据与历史归档。
- `docs/workflow/`：规定任务执行流程。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/workflow/6A-WORKFLOW.md`
- `docs/spec/v0.01/evidence/`
- `docs/spec/common/records/development-status.md`
