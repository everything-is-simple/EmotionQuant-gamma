# Reference

## 定位

`docs/reference/` 只保留长期可复用的外部规则与运维参考。

这里回答：

1. 外部市场规则是什么
2. 环境和运维参考怎么查

这里不回答：

1. 当前主线怎么设计
2. 当前版本做到哪一步

## 当前结构

| 目录 | 角色 |
|---|---|
| `a-stock-rules/` | A 股交易制度、涨跌停、申万行业参考 |
| `operations/` | 环境配置、临时文件、脱敏运维模板 |

## 使用边界

1. `reference/` 不是设计 SoT。
2. 若参考内容与官方最新规则冲突，以官方规则为准。
3. 当前主线设计看 `blueprint/`。
4. 历史冻结基线看 `docs/design-v2/01-system/system-baseline.md`。
5. 当前状态看 `docs/spec/common/records/development-status.md`。

## 入口

1. `a-stock-rules/README.md`
2. `operations/README.md`
3. `../spec/common/records/development-status.md`
4. `../../blueprint/README.md`
