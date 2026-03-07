# Steering（治理铁律）

**版本**: `v0.01-v0.06 目录入口`  
**状态**: `Frozen`（治理入口）  
**封版日期**: `2026-03-07`  
**变更规则**: `仅允许入口、链接与边界说明维护；治理快照与约束口径以上游 baseline 为准。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 定位

`docs/steering/` 存放系统治理铁律、A 股约束、架构快照与编码规范。

这里回答的是“哪些约束不能越界”，不是“完整系统设计细节写在哪里”。`v0.01 Frozen` 历史基线见 `docs/design-v2/01-system/system-baseline.md`；`v0.01-plus` 当前主开发线设计入口见 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`；当前治理状态与重启条件以 `docs/spec/common/records/development-status.md` 为准。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 产品铁律 | `product.md` | 判断方案是否违反核心约束 |
| A 股规则 | `a-stock-rules.md` | 判断执行语义、交易限制与市场规则 |
| 架构快照 | `architecture.md` | 快速查看模块、数据流与层次关系 |
| 编码规范 | `conventions.md` | 统一代码风格、分层与工程约束 |
| 文档状态 | `document-status.md` | 统一 `Frozen / Active / Draft` 语义 |

## 使用规则

1. `steering/` 是治理快照与快速约束层，不替代 `design-v2/` 的完整系统设计。
2. 若 `steering/` 与历史 `v0.01 Frozen` 基线冲突，以 `system-baseline.md` 为准；若与当前主开发线冲突，以 `docs/spec/v0.01-plus/` 与 `down-to-top-integration.md` 为准，并应同步修订对应治理文档。
3. 当前是否继续推进、当前处于何种治理阶段，不在 `steering/` 里维护，统一查看 `docs/spec/common/records/development-status.md`。
4. 版本路线图、证据与历史记录统一进入 `docs/spec/<version>/`，不回写到 `steering/`。

## 相邻目录边界

- `docs/design-v2/`：给出完整设计、模块边界与算法口径。
- `docs/spec/`：给出版本推进、验收证据与历史归档。
- `docs/reference/`：给出外部参考资料，不定义仓库内强约束。
- `docs/workflow/`：给出固定执行流程，不重复列治理条款。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/steering/document-status.md`
- `docs/spec/common/records/development-status.md`
- `docs/workflow/6A-WORKFLOW.md`
- `AGENTS.md`


