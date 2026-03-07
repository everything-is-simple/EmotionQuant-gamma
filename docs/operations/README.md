# Operations（仓库运维）

## 定位

`docs/operations/` 存放本仓库的运维文档、环境落地说明与敏感配置模板入口。

这里回答的是“这个仓库怎么落地、怎么维护、怎么排查”，不是“当前系统设计怎么执行”或“某个版本现在推进到哪里”。执行口径以 `docs/design-v2/01-system/system-baseline.md` 为准，当前状态以 `docs/spec/common/records/development-status.md` 为准。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 环境落地 | `setup-guide.md` | 配置仓库、本地目录与基础检查 |
| 数据源模板 | `data-source-and-migration.md.template` | 本地填写 Token、路径与迁移配置模板 |
| 数据源实配 | `data-source-and-migration.md` | 本地敏感配置与迁移记录，不提交 Git |
| 历史审计 | `root-files-check-report.md` | 追溯 2026-03-07 根入口检查，不作为当前主入口 |

## 使用规则

1. `operations/` 只存放仓库本地运维说明，不承载系统 SoT、治理状态或版本证据。
2. 涉及当前是否继续推进、是否满足重启条件，统一查看 `docs/spec/common/records/development-status.md`。
3. 涉及版本路线图、Gate、evidence、records，统一进入 `docs/spec/<version>/`。
4. `data-source-and-migration.md` 视为本地敏感文件；仓库内只保留 `.template`。
5. 一次性检查报告保留为追溯记录，不进入主入口首屏导航。
6. 仓库根目录 `G:\\EmotionQuant-gamma` 只放代码与文档；数据库统一在 `G:\\EmotionQuant_data`，临时文件统一在 `G:\\EmotionQuant-temp`。

## 相邻目录边界

- `docs/reference/operations/`：存放通用运维参考与临时文件说明，不包含仓库敏感配置。
- `docs/design-v2/`：定义系统设计与边界，不负责环境落地步骤。
- `docs/spec/`：存放版本材料与历史证据，不存放本地 Token/路径配置。
- `scripts/ops/`：存放可执行运维脚本；文档只解释目的和入口，不替代脚本。

## 相关文档

- `docs/spec/common/records/development-status.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/reference/operations/README.md`
- `scripts/ops/preflight.ps1`：统一开发预检入口（默认 `docs + config`，`-Profile full` 增加 `lint + test`；受限沙箱会话中，完整 `pytest` 可能需要提权执行）
- `scripts/ops/check_repo_config.ps1`：hooks / pyproject / 预检入口配置检查
- `scripts/ops/check_docs.ps1`：文档 gate（authority + status + links）
- `scripts/ops/check_doc_status.ps1`：文档状态语义检查
- `scripts/ops/check_doc_links.ps1`：链接与路径回归检查
- `scripts/ops/check_doc_authority.ps1`：权威入口一致性检查
- `.githooks/pre-commit`：提交前自动执行 `preflight.ps1 -Profile hook`




