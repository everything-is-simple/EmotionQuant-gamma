# 运维操作指南

本目录存放系统运维、开发环境管理相关的操作指南。

## 📋 文档清单

### 1. 临时文件管理

- **temp-files-guide.md**
  - Python 缓存（`__pycache__/`）
  - IDE 配置（`.vscode/`）
  - 测试缓存（`.pytest_cache/`）
  - Agent 追踪（`.specstory/`）
  - 临时文件（`.tmp/`）
  - 运行时产物（`artifacts/`）
  - 清理策略与最佳实践

## 🎯 使用场景

1. **环境清理**：定期清理临时文件，释放磁盘空间
2. **问题排查**：了解各类缓存文件的作用，避免误删
3. **提交前检查**：确保不提交临时文件到版本控制

## 🔧 相关脚本

- 清理脚本：`scripts/ops/clean_temp_files.ps1`
- 环境检查：`scripts/setup/check_skills.ps1`

## 📚 相关文档

- 开发工作流：`docs/workflow/6A-WORKFLOW.md`
- Git 规则：`docs/steering/conventions.md`
