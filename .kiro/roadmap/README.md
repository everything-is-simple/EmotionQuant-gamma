# .kiro 工作集规则

## 作用

`.kiro/roadmap/` 作为“当前执行工作区”，按版本子目录组织。  
它不是全量归档目录，全量归档仍在 `docs/spec/`。

## 目录结构（按版本）

- `v0.01/`（当前实现阶段，Active）
  - `v0.01-mvp-roadmap.md`
  - `v0.01-mvp-spec-01-data-layer.md`
  - `v0.01-mvp-spec-02-selector.md`
  - `v0.01-mvp-spec-03-strategy.md`
  - `v0.01-mvp-spec-04-broker.md`
  - `v0.01-mvp-spec-05-backtest-report.md`
  - `v0.01-boundary-deterministic-rules.md`
  - `v0.01-data-contract-table.md`
  - `v0.01-gate-checklist.md`
  - `v0.01-implementation-card-template.md`
- `v0.02/`（预留，Not Active）
- `v0.03/`（预留，Not Active）
- `v0.04/`（预留，Not Active）
- `v0.05/`（预留，Not Active）
- `v0.06/`（预留，Not Active）

## 同步规则

1. 全量归档在 `docs/spec/`。
2. 当前版本在 `.kiro/roadmap/` 维护工作副本。
3. 每个版本使用单独子目录：`.kiro/roadmap/<version>/`。
4. 版本切换时，先更新本文件中的“当前工作集”列表。

