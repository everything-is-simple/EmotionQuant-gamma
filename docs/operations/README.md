# 运维文档目录

本目录存放 EmotionQuant 系统的运维相关文档。

## 📋 文档清单

### 1. 环境配置

- **setup-guide.md** - 环境配置详细指南
  - 推荐目录结构（代码/数据/临时文件分离）
  - 详细的配置步骤和验证方法
  - 常见问题解答（Q&A）
  - 配置完成检查清单

### 2. 数据源管理

- **data-source-and-migration.md** - 数据源配置与数据库迁移记录
  - TuShare 双 Key 配置（官方账号 + 共享网关）
  - 数据库迁移指南（旧库 → 新库）
  - 数据完整性检查方法
  - Token 续费提醒和维护清单
  - ⚠️ 包含敏感信息，不提交到 Git

- **data-source-and-migration.md.template** - 数据源配置模板
  - 不包含敏感信息，可以提交到 Git
  - 其他开发者可以复制模板填写自己的配置

### 3. 检查报告

- **root-files-check-report.md** - 根目录入口文件检查报告
  - 18 个入口文件的检查结果
  - 配置完整性验证
  - 维护建议

## 🎯 使用场景

### 新人入职

1. 阅读 `setup-guide.md` 配置环境
2. 复制 `data-source-and-migration.md.template` 为 `data-source-and-migration.md`
3. 填写实际的 Token 信息和数据库路径

### 日常运维

1. 参考 `data-source-and-migration.md` 检查 Token 有效期
2. 按照维护清单定期检查数据完整性
3. 定期备份数据库文件

### 问题排查

1. 查看 `setup-guide.md` 的常见问题解答
2. 检查 `root-files-check-report.md` 确认配置文件状态

## 🔗 相关文档

- 系统设计：`docs/design-v2/`
- 参考资料：`docs/reference/operations/`
- 工作流程：`docs/workflow/`

## ⚠️ 安全提醒

- `data-source-and-migration.md` 包含敏感 Token 信息，已被 `.gitignore` 排除
- 不要将包含 Token 的文件提交到 Git
- 不要在公开场合分享 Token
