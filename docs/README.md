# docs/ 目录说明

**状态**: `导航 / 历史 / 治理 / 辅助层`  
**当前主线入口**: `../blueprint/README.md`

---

## 1. 定位

`docs/` 已经对整个旧设计世界正式说再见。

从 `2026-03-08` 起，这里不再回答“当前系统正文是什么”，只保留 3 类东西：

1. 历史基线与历史版本归档
2. 当前主线所需的治理、证据与状态记录
3. 理论、评审、流程、参考资料等长期辅助资产

从 `2026-03-12` 起，再加一条新规则：

4. 先用 `campaigns/` 把三大战役和共用层分开，再进入具体目录

如果你想看“现在系统怎么定义”，请直接去：

1. `../blueprint/README.md`
2. `../blueprint/01-full-design/`
3. `../blueprint/02-implementation-spec/`
4. `../blueprint/03-execution/`

---

## 2. 当前保留结构

`docs/` 当前只建议长期保留下面这些入口：

| 目录 | 定位 | 是否为当前主线 |
|------|------|----------------|
| `campaigns/` | 三大战役 + 共用层统一导航 | - |
| `../blueprint/` | 当前主线设计 | ✅ 是 |
| `design-v2/` | `v0.01 Frozen` 历史基线 | ❌ 否 |
| `spec/` | 治理、证据、records 归档层 | ❌ 否 |
| `observatory/` | 观察框架与评审标准 | - |
| `reference/` | 外部规则与运维参考 | - |
| `Strategy/` | 理论来源与方法论映射 | - |
| `workflow/` | 固定执行流程 | - |

其中：

1. `campaigns/` 是先看战役、再进目录的总入口。
2. `blueprint/` 是当前设计世界。
3. `docs/` 是退场后的历史、治理与辅助世界。
4. `spec/` 会持续增长，但增长的是治理与证据，不是设计正文。

---

## 3. 使用顺序

### 3.1 看当前主线

1. `campaigns/README.md`
2. `campaigns/02-v0.01-plus/README.md`
3. `../blueprint/README.md`
4. `../blueprint/01-full-design/`
5. `../blueprint/02-implementation-spec/`
6. `../blueprint/03-execution/`

### 3.2 看历史与治理

1. `campaigns/README.md`
2. `campaigns/01-v0.01-frozen/README.md`
3. `spec/common/records/development-status.md`
4. `spec/README.md`
5. `design-v2/01-system/system-baseline.md`

### 3.3 看长期辅助资产

1. `campaigns/README.md`
2. `campaigns/00-shared/README.md`
3. `observatory/README.md`
4. `reference/README.md`
5. `Strategy/README.md`
6. `workflow/README.md`

---

## 4. 维护规则

1. 新版设计正文只进 `blueprint/`。
2. `docs/` 里不再新增“当前主线设计解释稿”“新版模块正文”或“半设计半记录”的混合文。
3. `observatory / reference / Strategy / workflow` 只保留高价值入口，不做文件堆积。
4. `spec/` 只做版本治理、证据、records 归档。
5. 文档结构改动后，统一运行 `scripts/ops/check_docs.ps1`。

---

## 5. 相关入口

- 设计迁移边界：`docs/design-migration-boundary.md`
- 三大战役总图：`docs/campaigns/README.md`
- 辅助层保留清单：`docs/spec/common/records/supporting-layers-retention-checklist-20260312.md`
- 当前治理状态：`docs/spec/common/records/development-status.md`
- 历史基线：`docs/design-v2/01-system/system-baseline.md`
- 当前主线设计：`../blueprint/README.md`
