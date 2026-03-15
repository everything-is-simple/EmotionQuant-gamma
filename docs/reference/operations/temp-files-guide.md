# 临时文件与缓存目录说明

> 当前目录纪律优先级高于下文旧示例：
> - 仓库根目录不放运行时缓存、临时 DuckDB、测试临时目录
> - 临时文件统一放 `G:\EmotionQuant-temp`
> - 数据文件统一放 `G:\EmotionQuant_data`
> - 当前主线设计看 `blueprint/`，本文只解释缓存和清理策略，不定义设计口径

本文档说明 EmotionQuant 项目中各种临时文件和缓存目录的作用，以及为什么不彻底删除它们。

---

## 📂 目录分类

### 1. Python 运行时缓存（自动生成）

#### `__pycache__/`
- **作用**：Python 字节码缓存，加速模块导入
- **生成时机**：首次导入 Python 模块时自动生成
- **是否提交**：❌ 否（已在 `.gitignore` 中）
- **是否删除**：✅ 可以删除，下次运行会自动重新生成
- **位置**：`src/__pycache__/`, `tests/__pycache__/`, `scripts/data/__pycache__/`

**为什么不彻底删除**：
- 每次运行 Python 代码都会自动重新生成
- 删除后会导致首次运行变慢（需要重新编译）
- 不影响代码功能，只是性能优化

---

### 2. IDE 配置（个人偏好）

#### `.vscode/`（如本地存在）
- **作用**：VS Code 编辑器的工作区配置
- **内容**：
  - `settings.json`：编辑器设置（Python 解释器路径、格式化工具等）
  - `launch.json`：调试配置
  - `extensions.json`：推荐扩展
- **是否提交**：⚠️ 部分提交（团队共享配置可提交，个人配置不提交）
- **是否删除**：❌ 不建议删除（会丢失调试配置和编辑器设置）

**为什么不彻底删除**：
- 包含项目级的调试配置（如 `launch.json`）
- 包含团队共享的编辑器设置
- 删除后需要重新配置调试环境

**建议**：
- 提交团队共享的配置（如 Python 路径、格式化规则）
- 不提交个人偏好（如主题、字体大小）

---

### 3. 测试缓存（加速测试）

#### `.pytest_cache/`
- **作用**：pytest 测试框架的缓存
- **内容**：
  - 上次测试失败的用例（`--lf` 重跑失败用例）
  - 测试执行时间统计（`--durations` 显示慢用例）
- **是否提交**：❌ 否（已在 `.gitignore` 中）
- **是否删除**：✅ 可以删除，不影响测试功能

**为什么不彻底删除**：
- 加速测试（只重跑失败用例）
- 提供测试统计信息
- 删除后会丢失"上次失败用例"记录

---

### 4. Agent 追踪（开发辅助）

#### `.specstory/`（如本地工具生成）
- **作用**：部分 AI/IDE 工具的对话历史和上下文追踪
- **内容**：对话记录、代码变更历史、上下文快照
- **是否提交**：❌ 否（已在 `.gitignore` 中）
- **是否删除**：✅ 可以删除，但会丢失对话历史

**为什么不彻底删除**：
- 保留 AI 对话历史，便于回溯
- 提供上下文连续性（AI 记住之前的讨论）
- 删除后 AI 会"失忆"，需要重新解释项目背景

---

### 5. 临时文件（开发过程）

#### `G:\EmotionQuant-temp`
- **作用**：临时文件统一落点（工作副本、pytest、ruff/mypy cache、临时脚本）
- **内容**：
  - `G:\EmotionQuant-temp\codex-home\`：本地工具/MCP 配置（如启用）
  - `TEMP_PATH/backtest/`：工作副本 DuckDB
  - `TEMP_PATH/artifacts/`：脚本运行时中间结果
- **是否提交**：❌ 否（已在 `.gitignore` 中）
- **是否删除**：✅ 可以删除，但可能丢失本地工具配置或中间产物

**为什么不彻底删除**：
- 本地工具配置可能需要重新初始化
- 临时文件可能包含开发中的中间结果

---

### 6. 运行时产物（脚本输出）

#### `G:\EmotionQuant-temp\artifacts`
- **作用**：脚本运行产生的中间文件
- **内容**：
  - `bulk_download_progress.json`：批量下载进度记录
  - 其他脚本输出文件
- **是否提交**：❌ 否
- **是否删除**：✅ 可以删除，但会丢失进度记录

**为什么不彻底删除**：
- 保留进度记录，避免重复下载
- 提供断点续传能力
- 删除后需要重新下载所有数据

---

## 🧹 清理策略

### 何时清理

**必须清理**：
- 提交代码前（避免提交临时文件）
- 磁盘空间不足时
- 切换分支前（避免缓存冲突）

**不建议清理**：
- 正在开发时（会丢失缓存和配置）
- 正在运行测试时（会丢失测试缓存）
- 正在使用 AI Agent 时（会丢失对话历史）

### 如何清理

**方法 1：使用清理脚本（推荐）**
```powershell
# 预览将要删除的内容（不实际删除）
powershell -ExecutionPolicy Bypass -File scripts/ops/clean_temp_files.ps1 -DryRun

# 执行实际删除
powershell -ExecutionPolicy Bypass -File scripts/ops/clean_temp_files.ps1

# 如需连 TEMP_PATH/logs 一起清，再显式打开
powershell -ExecutionPolicy Bypass -File scripts/ops/clean_temp_files.ps1 -IncludeTempLogs
```

脚本当前默认会跳过 `.git`、`.venv`、`.vscode`、`docs/reference/`、`TEMP_PATH/codex-home/` 和 `TEMP_PATH/logs/`，避免误删主环境、编辑器配置、权威文档和本地工具配置。

**方法 2：手动删除**
```powershell
# 删除 Python 缓存
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 删除测试缓存
Remove-Item -Recurse -Force .pytest_cache

# 删除外部临时目录中的运行时产物
Remove-Item -Recurse -Force G:\EmotionQuant-temp\backtest, G:\EmotionQuant-temp\artifacts
```

**方法 3：Git 清理（最彻底）**
```bash
# 删除所有未跟踪的文件和目录（危险！会删除所有未提交的内容）
git clean -fdx

# 仅删除被 .gitignore 忽略的文件（安全）
git clean -fdX
```

---

## 📋 .gitignore 规则

当前 `.gitignore` 已正确配置，以下目录不会被提交：

```gitignore
# Python 缓存
__pycache__/
*.pyc
*.pyo

# IDE 配置
.vscode/
.idea/

# 测试缓存
.pytest_cache/
.coverage
pytest_tmp*/

# Agent 追踪
.specstory/
.claude/

# 临时文件
pytest-tmp/
pytest-cache-files-*/

# 运行时产物
*.log
logs/
cache/
```

---

## ❓ 常见问题

### Q1: 为什么 `.vscode/` 不建议直接删除？
**A**: 如果本地存在，它可能包含项目级调试配置和共享编辑器设置。删除后通常需要重新配置开发环境。

### Q2: 为什么 `__pycache__/` 总是重新生成？
**A**: Python 运行时自动生成，用于加速模块导入。这是 Python 的正常行为。

### Q3: 为什么 `.specstory/` 之类目录会占用空间？
**A**: 它们通常保存本地 AI/IDE 的对话历史和上下文快照。若当前工具链不依赖，可定期清理。

### Q4: 为什么 `artifacts/` 不提交？
**A**: 包含脚本运行的中间文件，每个人的运行结果不同，不应该提交到版本控制。

### Q5: 如何避免误删重要文件？
**A**: 使用 `clean_temp_files.ps1 -DryRun` 预览将要删除的内容，确认无误后再执行实际删除。

---

## 🎯 最佳实践

1. **定期清理**：每周清理一次临时文件，保持仓库整洁
2. **提交前检查**：使用 `git status` 确认没有临时文件被误提交
3. **保留配置**：如需保留本地 IDE / MCP 配置，清理前先确认对应目录的作用
4. **使用脚本**：优先使用 `clean_temp_files.ps1`，避免手动删除出错
5. **备份重要数据**：清理前确认 `artifacts/` 中没有重要的中间结果

---

## 📚 参考资料

- [Python __pycache__ 说明](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)
- [pytest 缓存机制](https://docs.pytest.org/en/stable/how-to/cache.html)
- [Git clean 命令](https://git-scm.com/docs/git-clean)
- [.gitignore 规则](https://git-scm.com/docs/gitignore)
