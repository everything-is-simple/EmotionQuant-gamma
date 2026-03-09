# common 跨版本文档（归档）

## 定位

`docs/spec/common/` 存放跨版本共用的治理记录与少量需要长期保留的历史审计材料。

这里回答的是“哪些材料需要跨版本持续维护”，不是“当前系统设计怎么定义”。当前阶段与主线判定以 `docs/spec/common/records/development-status.md` 为准；版本归档入口统一在 `docs/spec/`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 治理记录 | `records/README.md` | 查看跨版本 records 的结构与边界 |
| 当前状态 | `records/development-status.md` | 查看当前治理阶段、历史摘要与主线切换判定 |
| 历史桥接 | `bridge-review-20260304.md` | 查看历史桥接审计，不作为当前执行入口 |

## 使用规则

1. 只存放跨版本共用材料，不重复存放单版本路线图、证据或发布记录。
2. 单版本专属 records 统一放在 `docs/spec/<version>/records/`。
3. 若涉及 `v0.01 Frozen` 历史口径，以 `docs/design-v2/01-system/system-baseline.md` 为准；若涉及当前主线设计与实现，以 `blueprint/` 为准；若涉及当前治理推进，以 `docs/spec/v0.01-plus/` 为准。
4. 当前状态、重启条件和治理节奏，以 `records/development-status.md` 为准。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`