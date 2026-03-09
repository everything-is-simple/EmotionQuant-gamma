# A股市场规则参考

## 定位

`docs/reference/a-stock-rules/` 存放 A 股市场交易制度、涨跌停规则与申万行业分类参考。

这里回答的是“外部市场规则是什么”，不是“当前系统怎么执行”。

当前权威入口：

1. 当前主线设计：`blueprint/`
2. 历史冻结基线：`docs/design-v2/01-system/system-baseline.md`
3. 当前治理状态：`docs/spec/common/records/development-status.md`

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 交易规则 | `A股市场交易规则-tushare版.md` | 查询交易时间、撮合、停牌与 T+1 制度 |
| 涨跌停制度 | `A股涨跌停板制度-tushare版.md` | 查询主板/创业板/科创板/ST 的涨跌停差异 |
| 申万行业分类 | `A股申万行业指数-tushare版.md` | 查询 SW 行业层级与指数映射 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 判断规则变化是否需要同步设计或治理 |

## 使用规则

1. 本目录是外部参考，不直接定义仓库内执行语义或版本验收口径。
2. 若参考摘录与交易所、监管或数据源官方最新规则冲突，应以官方规则为准，并按需要回写 `blueprint / design-v2 / spec` 修正仓库口径。
3. 仓库内固定执行语义、A 股约束实现边界，优先查看 `blueprint/`、`docs/design-v2/01-system/system-baseline.md` 与当前代码。
4. 版本证据、回归结果与阶段记录，统一进入 `docs/spec/<version>/`，不堆回本目录。
5. 当前主开发线若对行业聚合、涨跌停校验、停牌处理有更细实现，以 `design-v2` 算法/模块设计为准，而不是以本目录文字直接替代实现。

## 相邻目录边界

- `blueprint/`：定义当前主线设计与模块边界。
- `docs/design-v2/`：定义模块如何落地这些规则。
- `docs/spec/`：保存版本证据、问题修复与阶段记录。
- `docs/reference/`：保存其他外部参考资料，不定义执行口径。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `blueprint/README.md`
- `docs/design-v2/02-modules/selector-design.md`
