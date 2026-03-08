# Spec 文档入口（治理归档）

## 定位

`docs/spec/` 是分版本 roadmap、governance、evidence、records 的统一入口。

这里回答的是：

1. 当前状态怎么看
2. 版本材料放在哪里
3. 证据和 records 去哪里找

它不再定义新版设计本体。

---

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计权威层 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段、风险与看板 |
| 设计迁移边界声明 | `docs/design-migration-boundary.md` | 查看 `docs/` 与 `blueprint/` 的职责边界 |
| 跨版本治理 | `docs/spec/common/README.md` | 查看 common 层 records 与共用清单 |
| v0.01 | `docs/spec/v0.01/README.md` | 查看冻结版本材料与历史证据 |
| v0.01-plus | `docs/spec/v0.01-plus/README.md` | 查看当前主线治理、Gate、证据与 records |

---

## 存放规则

1. `docs/spec/<version>/` 存放单版本 roadmap、governance、evidence、records。
2. `docs/spec/common/` 存放跨版本治理记录与共用清单。
3. 新版设计正文不进入 `docs/spec/`，统一进入 `blueprint/`。
4. 历史基线问题以 `docs/design-v2/01-system/system-baseline.md` 为准。
5. 当前主线设计问题以 `blueprint/` 为准。

---

## 相关文档

- `blueprint/README.md`
- `docs/design-migration-boundary.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/README.md`
