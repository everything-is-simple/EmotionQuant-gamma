# 权威入口一致性审计（2026-03-07）

## 1. 审计目标

统一检查 `README.md`、`AGENTS.md` 与 `docs/*/README.md` 对以下三类入口的表述是否一致：

1. 系统设计 SoT
2. 当前治理状态
3. 分版本归档入口

## 2. 统一口径

| 类型 | 统一路径 | 统一表述 |
|---|---|---|
| 设计 SoT | `docs/design-v2/01-system/system-baseline.md` | 当前唯一系统设计口径 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 当前治理状态、历史摘要与重启条件 |
| 版本归档 | `docs/spec/` / `docs/spec/<version>/` | 分版本路线图、证据、records 与归档入口 |

补充边界：

- `docs/steering/`：治理铁律与快速约束，不替代设计 SoT。
- `docs/Strategy/`：理论来源，不直接定义执行口径。
- `docs/observatory/`：观察框架与评审标准，不直接改写设计 SoT。
- `docs/reference/`：外部参考资料，不作为执行口径或版本主入口。
- `docs/operations/`：仓库本地运维说明，不作为当前状态或版本证据入口。

## 3. 审计范围

| 文件 | 结果 | 说明 |
|---|---|---|
| `README.md` | pass | 已明确 SoT、当前状态与版本入口 |
| `AGENTS.md` | fix -> pass | 补齐当前治理状态入口 |
| `docs/README.md` | pass | 已作为总导航明确冲突优先级 |
| `docs/design-v2/README.md` | pass | 已明确 baseline 为唯一设计 SoT |
| `docs/design-v2/03-algorithms/core-algorithms/README.md` | fix -> pass | 改为算法级 SoT 入口，并补齐当前状态与 `docs/spec/` |
| `docs/Strategy/README.md` | pass | 已明确理论目录不充当执行 SoT |
| `docs/observatory/README.md` | pass | 已明确评审标准与证据归档边界 |
| `docs/spec/README.md` | fix -> pass | 补齐 baseline 与当前状态说明 |
| `docs/spec/common/README.md` | fix -> pass | 补齐 baseline 与当前状态说明 |
| `docs/spec/common/records/README.md` | fix -> pass | 补齐 baseline 与 `docs/spec/` 入口 |
| `docs/spec/v0.01/README.md` ~ `docs/spec/v0.06/README.md` | fix -> pass | 补齐 baseline 与当前状态说明 |
| `docs/steering/README.md` | fix -> pass | 补齐 SoT、当前状态与版本入口边界 |
| `docs/reference/README.md` | fix -> pass | 从泛化分类说明改为正式入口与边界说明 |
| `docs/reference/a-stock-rules/README.md` | fix -> pass | 补齐 baseline、当前状态与 `docs/spec/` |
| `docs/operations/README.md` | fix -> pass | 从旧运维清单改为仓库运维入口说明 |
| `docs/reference/operations/README.md` | fix -> pass | 补齐 baseline、当前状态与仓库运维入口关系 |

## 4. 本次修复

1. 将 `docs/reference/README.md`、`docs/operations/README.md`、`docs/steering/README.md` 收口为统一入口结构。
2. 将 `docs/reference/a-stock-rules/README.md` 与 `docs/design-v2/03-algorithms/core-algorithms/README.md` 改为次级入口文档，不再沿用旧“清单堆叠”风格。
3. 将 `docs/spec/README.md`、`docs/spec/common/README.md`、`docs/spec/common/records/README.md` 与 `docs/spec/v0.01` ~ `v0.06` 的 README 全部补齐 baseline / development-status / docs/spec 三类入口。
4. 在 `AGENTS.md` 中补齐当前治理状态入口。
5. 新增 `scripts/ops/check_doc_authority.ps1`，将入口一致性检查脚本化。

## 5. 验证

- 权威入口审计：`powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_authority.ps1`
- 结果：`All authority-entry references are present.`
- 链接与路径回归：`powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1`
- 结果：`No documentation link/path issues found.`
