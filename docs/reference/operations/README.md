# Reference / Operations

## 定位

`docs/reference/operations/` 只保留通用运维参考，不再保留临时模板和拆散的补充页。

这里回答：

1. 环境怎么配
2. 目录纪律怎么守
3. 临时文件怎么清理

## 当前保留文件

| 文件 | 角色 |
|---|---|
| `setup-guide.md` | 环境配置、目录纪律与临时文件清理总入口 |
| `current-mainline-operating-runbook-20260317.md` | 当前主线运行链路、风险开关、人工介入边界与 rollback 规则 |

## 使用边界

1. 这里只放通用运维参考，不放真实 Token、真实网关地址或本机敏感值
2. 当前主线设计看 `blueprint/`
3. 当前状态看 `docs/spec/common/records/development-status.md`
4. 历史冻结基线看 `docs/design-v2/01-system/system-baseline.md`

## 入口

1. `setup-guide.md`
2. `current-mainline-operating-runbook-20260317.md`
