# Reference（参考资料）

## 定位

`docs/reference/` 存放外部规则摘录、运维参考与辅助说明材料。

这里回答的是“有哪些外部资料可供查阅”，不是“当前系统必须怎么执行”。系统执行口径仍以 `docs/design-v2/01-system/system-baseline.md` 为准，当前治理状态以 `docs/spec/common/records/development-status.md` 为准。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| A 股规则参考 | `a-stock-rules/README.md` | 查询交易制度、涨跌停与行业分类参考 |
| 运维参考 | `operations/README.md` | 查询临时文件、环境清理与提交前检查参考 |
| 执行 SoT | `docs/design-v2/01-system/system-baseline.md` | 遇到执行口径问题时回到权威入口 |

## 使用规则

1. `reference/` 只提供查阅材料，不直接充当设计 SoT、当前状态入口或版本归档入口。
2. 仓库内执行边界、模块契约与固定流程，以 `docs/design-v2/`、`docs/steering/`、`docs/workflow/` 为准。
3. 当前状态、治理结论与重启条件，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本路线图、证据、runbook、发布记录统一进入 `docs/spec/<version>/`，不回堆到 `reference/`。
5. 若参考摘录与交易所或数据源官方最新规则冲突，应以官方规则为准，并回写设计/治理文档修正仓库口径。
6. 当前主开发线若与历史参考描述冲突，以 `docs/spec/v0.01-plus/` 与对应算法 SoT 为准。

## 相邻目录边界

- `docs/design-v2/`：定义系统设计与执行语义。
- `docs/steering/`：定义不可变约束与治理快照。
- `docs/operations/`：存放仓库本地运维文档与敏感配置模板说明。
- `docs/spec/`：存放分版本路线图、证据与历史记录。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/reference/a-stock-rules/README.md`
- `docs/reference/operations/README.md`
