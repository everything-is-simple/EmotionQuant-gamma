# common 跨版本文档（归档）

## 定位

`docs/spec/common/` 存放跨版本共用的治理记录、冻结清单与历史审计材料。

这里回答的是“哪些材料需要跨版本持续维护”，不是“当前系统设计怎么定义”。系统设计 SoT 以 `docs/design-v2/01-system/system-baseline.md` 为准；当前治理状态与重启条件以 `docs/spec/common/records/development-status.md` 为准；版本归档入口统一在 `docs/spec/`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 治理记录 | `records/README.md` | 查看跨版本 records 的结构与边界 |
| 当前状态 | `records/development-status.md` | 查看当前治理阶段与历史摘要 |
| 冻结清单 | `v0.02-v0.06-freeze-min-checklist.md` | 查看后续版本冻结门槛 |
| 历史桥接 | `bridge-review-20260304.md` | 查看历史桥接审计，不作为当前执行入口 |

## 使用规则

1. 只存放跨版本共用材料，不重复存放单版本路线图、证据或发布记录。
2. 单版本专属 records 统一放在 `docs/spec/<version>/records/`。
3. 若与系统设计口径冲突，以 `docs/design-v2/01-system/system-baseline.md` 为准。
4. 当前状态、重启条件和治理节奏，以 `records/development-status.md` 为准。

## 相关文档- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
