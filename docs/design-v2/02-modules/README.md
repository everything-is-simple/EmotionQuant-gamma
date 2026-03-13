# design-v2 / 02-modules 目录说明

**版本**: `v0.01 Frozen 模块参考入口`  
**状态**: `Frozen`  
**封版日期**: `2026-03-14`  
**变更规则**: `仅允许入口、链接、历史说明与边界声明维护；不再新增新版模块正文。`

---

## 定位

`docs/design-v2/02-modules/` 只承担两件事：

1. 保存 `v0.01 Frozen` 的模块级历史正文。
2. 给 `system-baseline.md` 提供按模块回看的补充入口。

这里不是当前主线模块设计层。当前模块 SoT 已迁入 `blueprint/01-full-design/`。

---

## 当前使用边界

当前阅读本目录的正确用途是：

1. 回看 `v0.01 Frozen` 时各模块的历史职责与冻结边界。
2. 对照当前主线为什么从旧模块口径迁移到 `blueprint/`。
3. 为历史回退、证据追溯和架构比较提供模块级背景。

当前不应把本目录当作：

1. 当前模块设计正文。
2. 当前实现方案。
3. 当前执行拆解。

---

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 历史系统基线 | `docs/design-v2/01-system/system-baseline.md` | `v0.01 Frozen` 系统级执行口径 |
| 历史架构总览 | `docs/design-v2/01-system/architecture-master.md` | 历史系统拆分与模块关系 |
| 当前设计总入口 | `blueprint/README.md` | 当前主线设计总入口 |
| 当前完整设计 SoT | `blueprint/01-full-design/` | 当前模块正式正文 |
| 当前实现方案 | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` | 当前唯一实现方案 |
| 当前治理状态 | `docs/spec/common/records/development-status.md` | 当前状态、风险与推进判断 |

---

## 历史模块映射

| 历史模块文档 | 历史职责 | 当前主线对应入口 |
|---|---|---|
| `data-layer-design.md` | `L1-L4` 分层、DuckDB 单库、Store 统一入口 | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` |
| `selector-design.md` | 基础过滤 + `MSS gate` + `IRS filter` 的历史漏斗 | `blueprint/01-full-design/01-selector-contract-annex-20260308.md` |
| `strategy-design.md` | `BOF` 单形态触发与 detector/registry 历史骨架 | `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md` |
| `broker-design.md` | `T+1 Open`、风险控制、撮合与信任状态 | `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md` |
| `backtest-report-design.md` | 回测时钟推进、报告、消融与归因 | `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md` |

---

## 使用规则

1. 讨论 `v0.01 Frozen` 历史模块边界时，可以直接读本目录。
2. 讨论当前模块设计时，直接进入 `blueprint/`，不要回到本目录补正文。
3. 若单篇模块文档与 `system-baseline.md` 冲突，以 `system-baseline.md` 为准。
4. 若本目录与 `blueprint/` 冲突，当前主线一律以 `blueprint/` 为准。

---

## 相关文档

1. `docs/design-v2/README.md`
2. `docs/design-v2/01-system/system-baseline.md`
3. `docs/design-v2/01-system/architecture-master.md`
4. `docs/design-migration-boundary.md`
5. `blueprint/README.md`
