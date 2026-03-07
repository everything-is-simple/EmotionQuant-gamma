# Observatory（观察台）

## 定位

`docs/observatory/` 存放系统观察框架与评审标准。

这里回答的是“如何观察、如何验证、如何做发布前审视”，不是“模块内部如何实现”。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 宏观观察 | `god_view_8_perspectives_report_v0.01.md` | 做版本规划、系统复盘、全局审视 |
| 微观评审 | `sandbox-review-standard.md` | 做沙盘评审、偏差闭环、定稿门禁 |

## 使用规则

1. `god_view_8_perspectives_report_v0.01.md` 是研究附录，用于观察和规划，不直接改写当前执行口径。
2. `sandbox-review-standard.md` 是当前评审规范；涉及关键链路变更时，应按其要求产出证据。
3. 若与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准。
4. 评审产物与证据统一落到 `docs/spec/<version>/evidence/` 或对应 records，不堆回 observatory 根目录。

## 按场景导航

### 1. 做版本规划或大范围复盘

1. `god_view_8_perspectives_report_v0.01.md`
2. `docs/spec/<version>/roadmap/`
3. `docs/spec/common/records/development-status.md`

### 2. 做模块评审或发布前验证

1. `sandbox-review-standard.md`
2. `docs/design-v2/01-system/system-baseline.md`
3. `docs/spec/<version>/evidence/`

### 3. 做偏差闭环或门禁复核

1. `sandbox-review-standard.md`
2. 对应 evidence / records 文档
3. `docs/workflow/6A-WORKFLOW.md`

## 相邻目录边界

- `docs/design-v2/`：定义系统设计与执行边界。
- `docs/Strategy/`：提供理论来源与方法论背景。
- `docs/spec/`：保存具体版本证据与历史归档。
- `docs/workflow/`：规定任务执行流程。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/workflow/6A-WORKFLOW.md`
- `docs/spec/v0.01/evidence/`
- `docs/spec/common/records/development-status.md`
