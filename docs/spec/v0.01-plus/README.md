# v0.01-plus 阶段材料（治理归档入口）

**状态**: `Active`  
**最后更新**: `2026-03-08`

---

## 定位

`docs/spec/v0.01-plus/` 现在只承担 `v0.01-plus` 的治理归档职责：

1. roadmap
2. governance
3. evidence
4. records

它不再承担新版设计正文。

新版设计权威层已经迁移到 `blueprint/`。
旧设计世界退场后，本目录只接治理推进，不再兼做“过渡设计稿”容器。

---

## 当前主入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计权威层 |
| 当前实现方案 | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` | 当前唯一实现方案 |
| 当前执行拆解 | `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md` | 当前 phase / task / checklist |
| 当前治理状态 | `docs/spec/common/records/development-status.md` | 当前状态、风险与阶段推进 |
| 路线图主入口 | `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md` | 当前路线图归档 |
| 主线实现卡 | `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md` | 当前实现卡归档 |
| 主线切换 Gate | `docs/spec/v0.01-plus/governance/v0.01-plus-gate-checklist.md` | Gate 规则归档 |
| 契约补充 | `docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md` | 运行期契约归档 |
| 战役后续废案 | `docs/spec/v0.01-plus/90-archive/README.md` | 已退场修复路线与临时方案归档 |

---

## 使用规则

1. 讨论“新设计是什么”，不要在本目录展开，统一进入 `blueprint/`。
2. 本目录只维护 `v0.01-plus` 的治理、证据、记录和执行归档。
3. `v0.01 Frozen` 历史基线仍以 `docs/design-v2/01-system/system-baseline.md` 为准。
4. 若本目录材料与 `blueprint/` 冲突，以 `blueprint/` 为准；若与历史基线冲突，按问题类型区分：
   - 历史回看：以 `system-baseline.md` 为准
   - 当前主线：以 `blueprint/` 为准
5. 已经退场的 `v0.01-plus` 后续方案统一放在 `90-archive/`，不再回堆到共享目录。

---

## 相关文档

- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
