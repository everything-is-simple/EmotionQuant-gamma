# common 跨版本文档（归档）

本目录存放跨版本共用文档，避免在各版本目录中重复维护。

## 📂 目录结构

```
common/
├── records/                          # 跨版本治理记录
│   ├── development-status.md         # 阶段进展与 A6 收口记录
│   ├── debts.md                      # 技术债登记
│   ├── reusable-assets.md            # 可复用资产清单
│   └── README.md                     # 治理记录说明
├── bridge-review-20260304.md         # 跨版本桥接评审记录
└── v0.02-v0.06-freeze-min-checklist.md  # 跨版本冻结清单
```

## 📋 文档说明

### 1. `records/` - 跨版本治理记录

存放需要跨版本持续维护的治理信息：

- **development-status.md**：记录各阶段开发进展、A6 收口状态
- **debts.md**：登记技术债务、待优化项、已知问题
- **reusable-assets.md**：可复用的代码、配置、脚本清单

### 2. 跨版本评审与清单

- **bridge-review-20260304.md**：版本间桥接评审记录
- **v0.02-v0.06-freeze-min-checklist.md**：v0.02-v0.06 最小冻结清单

## 🔗 使用规则

1. **跨版本信息统一存放**：避免在各版本目录重复维护
2. **单版本专属信息分开存放**：runbook、勘误、发布记录仍放在 `docs/spec/<version>/records/`
3. **引用路径统一**：使用 `docs/spec/common/` 或 `docs/spec/common/records/`

## 📚 相关文档

- 版本归档入口：`docs/spec/README.md`
- 版本索引：`docs/spec/INDEX.md`
- 各版本材料：`docs/spec/v0.01/` ~ `docs/spec/v0.06/`

