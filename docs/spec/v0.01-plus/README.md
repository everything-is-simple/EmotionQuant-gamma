# v0.01-plus 阶段材料（当前主开发线）

## 定位

`docs/spec/v0.01-plus/` 存放 `v0.01-plus` 的当前主开发线材料。自本次治理决策起，`v0.01` 视为一次已冻结的历史尝试；`v0.01-plus` 作为其主线替代版本，承担后续 `down-to-top / DTT` 链路的实现、验证与收口。

当前执行与归档统一在 `docs/spec/v0.01-plus/`。`docs/design-v2/01-system/system-baseline.md` 继续作为 `v0.01 Frozen` 的历史基线；`docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` 作为 `v0.01-plus` 的当前设计入口；当前治理状态与实现是否恢复，以 `docs/spec/common/records/development-status.md` 为准。

## 当前主入口

- 路线图主入口：`docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`
- 主线实现卡：`docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
- 主线切换 Gate：`docs/spec/v0.01-plus/governance/v0.01-plus-gate-checklist.md`
- 契约补充：`docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`
- 运行命名规则：`docs/spec/v0.01-plus/governance/v0.01-plus-run-artifact-rules.md`

## 使用规则

1. 本目录存放 `v0.01-plus` 当前主开发线的路线图、Gate、契约与证据材料。
2. `v0.01 Frozen` 仍以 `docs/design-v2/01-system/system-baseline.md` 与 `docs/spec/v0.01/` 为准，但其角色降为历史基线、对照组与回退参考。
3. `legacy top-down` 仅保留用于 A/B 对照、回归验证与必要回退，不再作为当前主开发线的默认目标。
4. 当前阶段采用“兼容优先”的迁移策略：优先落地 `DTT` 主链，同时尽量维持下游 `Broker / Backtest / Report` 的兼容接口，排序明细可通过 sidecar 结果表承载。
5. `v0.01-plus` 不等同于 `v0.02`；`v0.02` 仍预留给后续 BPB/多形态扩展，不挪用当前命名。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
