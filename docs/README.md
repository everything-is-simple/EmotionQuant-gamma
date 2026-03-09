# docs/ 目录说明

**状态**: `历史设计存储层`  
**当前主线入口**: `../blueprint/README.md`

---

## 1. 定位

`docs/` 不再承载当前主线设计正文。

从 `2026-03-08` 起，这里只保留 2 类东西：

1. 历史基线与历史版本归档
2. 理论、评审、流程、参考资料等长期辅助资产

如果你想看“现在系统怎么定义”，请直接去：

1. `../blueprint/README.md`
2. `../blueprint/01-full-design/`
3. `../blueprint/02-implementation-spec/`
4. `../blueprint/03-execution/`

---

## 2. 当前保留结构

`docs/` 当前只建议长期保留下面 6 个入口：

| 目录 | 定位 | 是否为当前主线 |
|------|------|----------------|
| `../blueprint/` | 当前主线设计 | ✅ 是 |
| `design-v2/` | `v0.01 Frozen` 历史基线 | ❌ 否 |
| `spec/` | 历史治理记录 | ❌ 否 |
| `observatory/` | 观察框架与评审标准 | - |
| `reference/` | 外部规则与运维参考 | - |
| `Strategy/` | 理论来源与方法论映射 | - |
| `workflow/` | 固定执行流程 | - |

其中只有 `spec/` 还会持续增长；其余目录默认少增量、少分叉、少解释。

---

## 3. 使用顺序

### 3.1 看当前主线

1. `../blueprint/README.md`
2. `../blueprint/01-full-design/`
3. `../blueprint/02-implementation-spec/`
4. `../blueprint/03-execution/`

### 3.2 看历史与治理

1. `spec/common/records/development-status.md`
2. `spec/README.md`
3. `design-v2/01-system/system-baseline.md`

### 3.3 看长期辅助资产

1. `observatory/README.md`
2. `reference/README.md`
3. `Strategy/README.md`
4. `workflow/README.md`

---

## 4. 维护规则

1. 新版设计正文只进 `blueprint/`。
2. `docs/` 里不再新增“当前主线设计解释稿”。
3. `observatory / reference / Strategy / workflow` 只保留高价值入口，不做文件堆积。
4. `spec/` 只做版本治理、证据、records 归档。
5. 文档结构改动后，统一运行 `scripts/ops/check_docs.ps1`。

---

## 5. 相关入口

- 设计迁移边界：`docs/design-migration-boundary.md`
- 当前治理状态：`docs/spec/common/records/development-status.md`
- 历史基线：`docs/design-v2/01-system/system-baseline.md`
- 当前主线设计：`../blueprint/README.md`
