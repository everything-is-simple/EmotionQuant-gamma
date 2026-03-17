# Ops Scripts

**状态**: `Active`  
**日期**: `2026-03-18`

---

## 1. 目录职责

`scripts/ops/` 放的是运维、预检、环境初始化、清理和少量专项辅助工具。

这层脚本的主要职责是：

1. 搭环境。
2. 跑预检。
3. 检查文档治理和路径纪律。
4. 清理临时目录。
5. 为少量专项任务提供脚手架或探针。

这层脚本不是：

1. 日常数据导入入口。
2. 默认回测 runner 入口。
3. 研究战场 evidence 的长期归档目录。

---

## 2. 常用主入口

| 脚本 | 作用 | 什么时候用 |
|---|---|---|
| `bootstrap_env.ps1` | 初始化 `.venv`、`.env`、数据/临时目录，安装依赖 | 新机器、新克隆仓库、环境损坏后重建 |
| `preflight.ps1` | 统一预检入口，按 profile 跑 docs/config/paths/lint/test | 提交前、推送前、阶段性收口前 |
| `clean_temp_files.ps1` | 清理 `TEMP_PATH` 下的临时产物和缓存 | 临时目录膨胀、需要腾空间、预检前后清理 |

---

## 3. 文档治理脚本

| 脚本 | 作用 |
|---|---|
| `check_docs.ps1` | 文档 gate 总入口 |
| `check_doc_authority.ps1` | 检查文档权威源和 SoT 纪律 |
| `check_doc_status.ps1` | 检查状态字段、文档状态一致性 |
| `check_doc_links.ps1` | 检查文档链接可达性 |
| `check_path_discipline.ps1` | 检查路径纪律 |
| `check_repo_config.ps1` | 检查仓库配置和运行前置条件 |

---

## 4. 专项辅助脚本

| 脚本 | 作用 | 备注 |
|---|---|---|
| `build_tachibana_replay_ledger.py` | 把 Tachibana 事件表整理成 replay ledger | 第二战场专项辅助 |
| `build_tachibana_tradebook_scaffold.py` | 从历史 workbook 搭 tradebook scaffold | 第二战场专项辅助 |
| `render_blueprint_diagrams.ps1` | 渲染 blueprint 图示 | 低频使用 |
| `file_ops_probe.py` | 文件能力探针 | 诊断用 |
| `pdf_probe.py` | PDF 处理探针 | 诊断用 |

---

## 5. 推荐使用顺序

### 5.1 新环境

1. `bootstrap_env.ps1`
2. `preflight.ps1 -Profile hook`

### 5.2 日常开发

1. 完成改动
2. `preflight.ps1 -Profile hook`
3. 需要时再跑 `preflight.ps1 -Profile full`

### 5.3 临时目录过大

1. `clean_temp_files.ps1 -DryRun`
2. 确认后再正式执行

---

## 6. 一句话结论

`scripts/ops/` 是“环境与治理运维层”，主入口是 `bootstrap_env.ps1`、`preflight.ps1`、`clean_temp_files.ps1`。
