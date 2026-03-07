# 跨版本治理记录

## 定位

`docs/spec/common/records/` 存放跨版本持续维护的治理记录与审计留痕。

这里回答的是“当前治理状态、技术债、资产复用和审计记录放在哪里”，不是“单个版本证据放在哪里”。系统设计 SoT 以 `docs/design-v2/01-system/system-baseline.md` 为准；版本归档入口统一在 `docs/spec/`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `development-status.md` | 查看当前治理阶段、历史摘要与重启条件 |
| 技术债 | `debts.md` | 查看风险与欠账 |
| 资产复用 | `reusable-assets.md` | 查看可复用沉淀 |
| 入口审计 | `authority-entry-audit-20260307.md` | 查看入口一致性审计结果 |
| 文档瘦身审计 | `doc-thinning-audit-20260307.md` | 查看历史瘦身与归档审查记录 |

## 使用规则

1. 本目录只记录跨版本治理信息，不记录单个版本专属证据。
2. 单版本 runbook、勘误、发布记录仍放在 `docs/spec/<version>/records/`。
3. 当前治理状态与是否恢复实现，以 `development-status.md` 为准。
4. 若与系统设计口径冲突，以 `docs/design-v2/01-system/system-baseline.md` 为准。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `docs/spec/common/README.md`
