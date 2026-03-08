# Workflow（执行流程）

## 定位

`docs/workflow/` 存放仓库级执行流程与任务收口规则。

这里回答的是“任务怎么推进、怎么验证、怎么同步”，不是“系统设计本身怎么定义”。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 固定流程 | `6A-WORKFLOW.md` | 当前唯一执行流程入口 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 判断当前主线、历史问题和进行中任务 |
| 版本归档 | `docs/spec/README.md` | 确认本次任务应挂到哪个版本目录 |

## 使用规则

1. 当前主开发线任务默认挂到 `docs/spec/v0.01-plus/`。
2. 历史回看、回归修复或对照验证，可挂回对应 `docs/spec/<version>/`。
3. 工作流不替代设计 SoT；涉及执行语义冲突时，先看 `development-status.md` 判定主线，再看 `blueprint/`。
4. A6 同步必须落到当前版本目录和 `docs/spec/common/records/`，不能只更新代码不留记录。

## 相关文档

- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/design-v2/01-system/system-baseline.md`
