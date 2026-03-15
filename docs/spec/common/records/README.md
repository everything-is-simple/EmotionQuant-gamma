# 跨版本治理记录

## 定位

`docs/spec/common/records/` 存放跨版本持续维护的治理记录与审计留痕。
这里回答的是“当前治理状态、技术债、资产复用和审计记录放在哪里”，不是“单个版本证据放在哪里”。

当前主线与历史基线的判定以 `development-status.md` 为准；
历史桥接审计与已退场治理材料统一收进 `90-archive/`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `development-status.md` | 查看当前治理阶段、历史摘要与重启条件 |
| 系统宪法 | `system-constitution-v1.md` | 查看当前跨线不可违背铁律 |
| 开发军规 | `development-discipline-v1.md` | 查看当前跨线通用的开发纪律与 baseline-first 执行规则 |
| `design-v2` 退场清单 | `design-v2-retirement-checklist-20260312.md` | 查看历史基线包的保留、降级与未来删除边界 |
| 辅助层保留清单 | `supporting-layers-retention-checklist-20260312.md` | 查看 reference / observatory / workflow / docs 导航层的保留与瘦身边界 |
| 技术债 | `debts.md` | 查看风险与欠债 |
| 资产复用 | `reusable-assets.md` | 查看可复用沉淀 |
| 历史治理归档 | `90-archive/README.md` | 查看桥接审计等已退场材料 |

## 使用规则

1. 本目录只记录跨版本治理信息，不记录单个版本专属证据
2. 单版本 runbook、勘误、发布记录仍放在 `docs/spec/<version>/records/`
3. 当前治理状态与是否恢复实现，以 `development-status.md` 为准
4. 若涉及 `v0.01 Frozen` 历史口径，以 `docs/design-v2/01-system/system-baseline.md` 为准；若涉及当前主线设计与实现，以 `blueprint/` 为准；若涉及当前治理推进，以 `docs/spec/v0.01-plus/` 为准

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/common/records/development-discipline-v1.md`
- `docs/spec/common/README.md`
