# Spec 文档入口（统一规则）

## 定位

`docs/spec/` 是分版本路线图、证据、records 与治理归档的统一入口。

这里回答的是“每个版本的材料放在哪里、当前状态怎么看”，不是“系统设计本身怎么定义”。`docs/design-v2/01-system/system-baseline.md` 继续作为 `v0.01 Frozen` 的历史基线；`docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` 作为 `v0.01-plus` 当前主开发线的设计入口；当前治理状态与重启条件以 `docs/spec/common/records/development-status.md` 为准。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段、历史摘要与重启条件 |
| 跨版本治理 | `docs/spec/common/README.md` | 查看 common 层的 records 与冻结清单 |
| v0.01 | `docs/spec/v0.01/README.md` | 查看冻结版本材料与历史证据 |
| v0.01-plus | `docs/spec/v0.01-plus/README.md` | 查看当前主开发线的 DTT 路线、Gate 与契约补充 |
| 后续版本 | `docs/spec/v0.02/README.md` ~ `docs/spec/v0.06/README.md` | 查看规划阶段路线图与实现卡 |

## 存放规则

1. `docs/spec/<version>/` 存放单版本路线图、治理、证据与 records。
2. `docs/spec/common/` 存放跨版本治理记录与共用清单。
3. 一次性桥接审计、瘦身审计等历史材料保留追溯价值，但不作为当前主入口。
4. 版本材料若涉及 `v0.01 Frozen` 历史口径，以 `docs/design-v2/01-system/system-baseline.md` 为准；若涉及 `v0.01-plus` 当前主开发线，以 `docs/spec/v0.01-plus/` 与 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` 为准。

## 当前版本映射

- v0.01
  - `v0.01/roadmap/v0.01-mvp-roadmap.md`
  - `v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`
  - `v0.01/roadmap/v0.01-mvp-spec-02-selector.md`
  - `v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`
  - `v0.01/roadmap/v0.01-mvp-spec-04-broker.md`
  - `v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md`
  - `v0.01/governance/v0.01-boundary-deterministic-rules.md`
  - `v0.01/governance/v0.01-data-contract-table.md`
  - `v0.01/governance/v0.01-gate-checklist.md`
  - `v0.01/evidence/`
  - `v0.01/records/`
- v0.01-plus
  - `v0.01-plus/README.md`
  - `v0.01-plus/roadmap/v0.01-plus-roadmap.md`
  - `v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
  - `v0.01-plus/governance/v0.01-plus-gate-checklist.md`
  - `v0.01-plus/governance/v0.01-plus-data-contract-table.md`
- v0.02
  - `v0.02/roadmap/v0.02-multi-pattern.md`
  - `v0.02/roadmap/v0.02-multi-pattern-spec-01-selector-strategy.md`
- v0.03
  - `v0.03/roadmap/v0.03-full-ytc.md`
  - `v0.03/roadmap/v0.03-full-ytc-spec-01-strategy-composition.md`
- v0.04
  - `v0.04/roadmap/v0.04-statistics-layer.md`
  - `v0.04/roadmap/v0.04-statistics-layer-spec-01-report-observability.md`
- v0.05
  - `v0.05/roadmap/v0.05-ecosystem.md`
  - `v0.05/roadmap/v0.05-ecosystem-spec-01-lifecycle-governance.md`
- v0.06
  - `v0.06/roadmap/v0.06-portfolio.md`
  - `v0.06/roadmap/v0.06-portfolio-spec-01-portfolio-layer.md`
- common
  - `common/records/development-status.md`
  - `common/records/debts.md`
  - `common/records/reusable-assets.md`
  - `common/records/authority-entry-audit-20260307.md`

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/README.md`
