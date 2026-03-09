# Reference / Operations

## 定位

`docs/reference/operations/` 只保留通用运维参考。

这里回答：

1. 环境怎么配
2. 临时文件怎么理解和清理
3. 脱敏运维模板怎么放

这里不记录当前推进状态，也不定义系统设计口径。

## 当前保留文件

| 文件 | 角色 |
|---|---|
| `setup-guide.md` | 环境配置与目录纪律 |
| `temp-files-guide.md` | 临时文件与缓存清理说明 |
| `data-source-and-migration.md.template` | 脱敏运维模板 |

## 使用边界

1. 这里只放通用运维参考，不放真实 Token、真实网关地址或本机敏感值。
2. 当前主线设计看 `blueprint/`。
3. 当前状态看 `docs/spec/common/records/development-status.md`。
4. 历史冻结基线看 `docs/design-v2/01-system/system-baseline.md`。

## 入口

1. `setup-guide.md`
2. `temp-files-guide.md`
3. `data-source-and-migration.md.template`
