# docs/ 目录说明

**状态**: `Active`  
**日期**: `2026-03-16`  
**当前主线入口**: `../blueprint/README.md`

---

## 1. 定位

`docs/` 现在只承担三类职责：

1. 保存 `v0.01 Frozen` 的历史基线与历史归档
2. 保存跨版本治理、证据、records 与状态账本
3. 保存长期有效的理论来源、评审标准、运维参考与工作流

这里不再保留第二套“战役导航层”。
研究线入口统一收敛到根目录 `README.md`、仓库三线地图，以及各自的 `normandy/`、`positioning/`、`gene/` 目录。

如果你要看“现在系统怎么定义”，请直接进入：

1. `../README.md`
2. `spec/common/records/repo-line-map-20260312.md`
3. `spec/common/records/four-battlefields-integrated-system-map-20260316.md`
4. `spec/common/records/development-status.md`
5. `../blueprint/README.md`
6. `../blueprint/01-full-design/`
7. `../blueprint/02-implementation-spec/`
8. `../blueprint/03-execution/`

---

## 2. 当前保留结构

| 目录 / 文件 | 定位 |
|---|---|
| `design-migration-boundary.md` | `docs/` 与 `blueprint/` 的边界声明锚点 |
| `design-v2/` | `v0.01 Frozen` 历史基线 |
| `spec/` | 版本治理、证据、records 与状态账本 |
| `Strategy/` | 共享理论来源与方法映射 |
| `reference/` | 外部规则与运维参考 |
| `observatory/` | 评审标准与少量观察入口 |
| `workflow/` | 固定执行流程 |
| `navigation/` | 非破坏式文档重组入口，按四战场视角重新组织旧文档 |

口径固定如下：

1. `blueprint/` 是当前主线设计权威层
2. `docs/spec/` 是治理账本层
3. `docs/design-v2/` 是历史基线层
4. `docs/Strategy/`、`docs/reference/`、`docs/observatory/`、`docs/workflow/` 是长期辅助层

---

## 3. 读取顺序

### 3.1 当前主线

1. `../README.md`
2. `navigation/four-battlefields-document-shelf/README.md`
3. `spec/common/records/repo-line-map-20260312.md`
4. `spec/common/records/four-battlefields-integrated-system-map-20260316.md`
5. `spec/common/records/development-status.md`
6. `../blueprint/README.md`

### 3.2 历史与治理

1. `design-v2/README.md`
2. `design-v2/01-system/system-baseline.md`
3. `spec/README.md`
4. `spec/common/records/README.md`

### 3.3 长期辅助资料

1. `Strategy/README.md`
2. `reference/README.md`
3. `observatory/README.md`
4. `workflow/6A-WORKFLOW.md`

---

## 4. 维护规则

1. 新版设计正文只进 `blueprint/`
2. 战场专属草案、卡片、理论随记只进对应战场目录，不回堆到 `docs/`
3. `docs/` 里的临时导航层、重复入口和早期草案应持续清退
4. 历史材料如果仍要保留，应收进对应版本或战场自己的 `90-archive/`
5. 结构改动后，统一运行文档链接与权威入口检查

---

## 5. 相关入口

- `docs/navigation/four-battlefields-document-shelf/README.md`
- `docs/design-migration-boundary.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/common/records/four-battlefields-integrated-system-map-20260316.md`
- `docs/spec/common/records/repo-line-map-20260312.md`
- `docs/spec/common/records/supporting-layers-retention-checklist-20260312.md`
- `docs/design-v2/01-system/system-baseline.md`
- `../blueprint/README.md`
