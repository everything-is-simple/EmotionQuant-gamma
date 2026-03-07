# 运维参考（非主入口）

## 定位

`docs/reference/operations/` 存放通用运维参考材料，当前以临时文件与缓存管理说明为主。

这里回答的是“哪些临时目录和缓存应该怎么理解、怎么清理”，不是“本仓库当前推进状态”或“本地敏感配置怎么填写”。仓库本地运维主入口在 `docs/operations/README.md`；系统设计 SoT 以 `docs/design-v2/01-system/system-baseline.md` 为准；当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 临时文件参考 | `temp-files-guide.md` | 了解缓存、产物、IDE 配置与清理边界 |
| 仓库运维入口 | `docs/operations/README.md` | 回到本仓库的正式运维入口 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段与重启条件 |

## 使用规则

1. 这里是参考目录，不记录本机 Token、真实路径或一次性运维审计。
2. 本仓库环境配置与敏感模板，统一进入 `docs/operations/`。
3. 当前治理状态与是否恢复实现，统一查看 `docs/spec/common/records/development-status.md`。
4. 若清理策略与仓库脚本、`.gitignore` 或正式运维文档冲突，以正式运维入口和脚本为准。

## 相关文档

- `docs/operations/README.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `scripts/ops/check_doc_links.ps1`
