# design-v2 目录说明

**版本**: `历史基线入口`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `仅允许入口、链接与边界说明维护；不再新增新版设计正文。`

---

## 定位

`docs/design-v2/` 现在只承担两件事：

1. 保存 `v0.01 Frozen` 历史基线
2. 提供少数必要历史总览，供对照、回退与追溯使用

它不再承担新版主线设计权威层，也不再保留迁移期桥接稿。

---

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计权威层 |
| 设计迁移边界声明 | `docs/design-migration-boundary.md` | 说明为何 `design-v2/` 已降级 |
| v0.01 历史基线 | `01-system/system-baseline.md` | `v0.01 Frozen` 历史执行口径 |
| 架构历史总览 | `01-system/architecture-master.md` | 查旧架构与历史映射 |
| 历史模块设计 | `02-modules/` | 回看旧模块口径与冻结正文 |

---

## 使用规则

1. 讨论新版设计时，直接进入 `blueprint/`，不要回到 `design-v2/` 写正文。
2. 讨论 `v0.01 Frozen` 历史基线时，以 `01-system/system-baseline.md` 为准。
3. `design-v2/` 中带 `Frozen` 或历史口径的文档，只承担对照、回退、追溯职责。
4. 若旧文档与 `blueprint/` 冲突，以 `docs/design-migration-boundary.md` 和 `blueprint/` 为准。

---

## 相邻目录边界

- `blueprint/`：新版设计权威层。
- `docs/spec/`：治理、roadmap、evidence、records。
- `docs/observatory/`：观察框架与评审标准。
- `docs/Strategy/`：理论来源与方法论。

---

## 相关文档

- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
