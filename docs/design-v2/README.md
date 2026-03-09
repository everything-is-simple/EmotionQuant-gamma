# design-v2 目录说明

**版本**: `历史参考入口`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `仅允许入口、链接、历史说明与边界声明维护；不再新增新版设计正文。`

---

## 定位

`docs/design-v2/` 现在只承担三件事：

1. 保存 `v0.01 Frozen` 历史基线
2. 提供少数必要历史总览，供对照、回退与追溯使用
3. 为 `docs/spec/` 中的历史治理记录提供只读背景入口

它不再承担新版主线设计权威层，也不再保留迁移期桥接稿。

换句话说：这里是**参考层**，不是当前设计层，也不是当前治理层。

---

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计权威层 |
| 当前治理入口 | `docs/spec/common/records/development-status.md` | 当前状态、风险与推进判断 |
| v0.01 历史治理归档 | `docs/spec/v0.01/README.md` | `v0.01 Frozen` 的 evidence / records / roadmap |
| 设计迁移边界声明 | `docs/design-migration-boundary.md` | 说明为何 `design-v2/` 已降级 |
| v0.01 历史基线 | `01-system/system-baseline.md` | `v0.01 Frozen` 历史执行口径 |
| 架构历史总览 | `01-system/architecture-master.md` | 查旧架构与历史映射 |
| 历史模块设计 | `02-modules/` | 回看旧模块口径与冻结正文 |

---

## 使用规则

1. 讨论新版设计时，直接进入 `blueprint/`，不要回到 `design-v2/` 写正文。
2. 讨论 `v0.01 Frozen` 历史基线时，以 `01-system/system-baseline.md` 为准。
3. `design-v2/` 中带 `Frozen` 或历史口径的文档，只承担对照、回退、追溯职责。
4. 历史实现证据、runbook、release、评审记录统一进入 `docs/spec/`，不要再回填到 `design-v2/` 正文。
5. 若旧文档与 `blueprint/` 冲突，以 `docs/design-migration-boundary.md` 和 `blueprint/` 为准。

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
- `docs/spec/common/records/development-status.md`
- `docs/spec/v0.01/README.md`
- `docs/design-v2/01-system/system-baseline.md`
