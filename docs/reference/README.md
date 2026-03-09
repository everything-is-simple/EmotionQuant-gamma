# Reference

## 定位

`docs/reference/` 只保留长期可复用的参考资料。

这里回答“有哪些规则和运维参考可以查”，不回答“当前主线必须怎么做”。

## 当前保留结构

| 目录 | 角色 |
|---|---|
| `a-stock-rules/` | A 股交易规则、涨跌停、行业口径参考 |
| `operations/` | 环境配置、临时文件、脱敏运维模板 |

## 使用边界

1. `reference/` 不是设计 SoT。
2. 规则若与官方最新口径冲突，以官方规则为准。
3. 历史基线看 `docs/design-v2/01-system/system-baseline.md`。
4. 当前主线设计以 `blueprint/` 为准。
5. 当前治理状态以 `docs/spec/common/records/development-status.md` 为准。

## 相邻入口

1. `a-stock-rules/README.md`
2. `operations/README.md`
3. `../spec/README.md`
4. `../../blueprint/README.md`
5. `../design-v2/01-system/system-baseline.md`
6. `../spec/common/records/development-status.md`
