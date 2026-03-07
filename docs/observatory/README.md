# Observatory（观察台）

本目录存放 EmotionQuant 的系统观察框架和评审标准，用于全局视角的系统审视和质量把控。

---

## 文档清单

### 1. `god-view-8-perspectives-v0.01.md` - 八维观察框架

**定位**：系统观察框架与版本演进研究附录

**核心内容**：
- 八个观察维度（市场/行业/个股/形态/风控/数据/执行/生态）
- v0.01-v0.06 版本演进建议
- 分桶/分层/生态管理思路
- 组合层建议

**使用场景**：
- 版本规划时的全局视角参考
- 系统复盘时的多维度审视
- 未来路线图的思考框架

**约束说明**：
- 本文档为研究附录，不作为 v0.01 的强制实现条款
- 涉及 v0.02+ 的建议，仅在对应版本评审通过后纳入执行口径
- 若与 `system-baseline.md` 冲突，以 baseline 为准

---

### 2. `sandbox-review-standard.md` - 沙盘评审标准 ⚠️ 已迁移

**迁移说明**：
- 该文档已迁移至 `docs/design-v2/sandbox-review-standard.md`
- 原因：沙盘评审标准是系统级执行规范，应与 `system-baseline.md` 同级
- 请访问新位置查看最新版本

**原定位**：沙盘推演与偏差闭环的执行规范

**核心内容**：
- 七维评审框架（Schema契合/调用链完整性/幂等与确定性/状态机完整性/时序语义/边界冲突/报告口径）
- 证据模板（A-S 偏差清单，44项）
- 定稿门禁（防偏差控制点图）
- 连环失效检测

**新位置**：`docs/design-v2/sandbox-review-standard.md`

---

## 目录命名说明

**为什么叫 Observatory（观察台）？**

1. **观察（Observation）**：
   - `god-view` 提供八维观察框架
   - 从全局视角审视系统设计
   - 发现潜在问题和改进方向

2. **评审（Review）**：
   - `sandbox-review` 提供评审标准
   - 从执行层面验证设计正确性
   - 防止偏差和缺陷进入生产

3. **统一语义**：
   - Observatory 既是"观察站"也是"瞭望台"
   - 既能看到全局（god-view），也能看到细节（sandbox）
   - 既能前瞻（版本演进），也能回顾（偏差闭环）

**旧名称**：`docs/上帝的眼/`（已废弃）

---

## 与其他文档的关系

| 本目录 | 相关文档 | 关系 |
|--------|---------|------|
| `god-view-8-perspectives-v0.01.md` | `docs/design-v2/system-baseline.md` | 观察框架 vs 执行基线 |
| `god-view-8-perspectives-v0.01.md` | `docs/spec/v0.01/roadmap/` | 研究附录 vs 执行路线图 |
| ~~`sandbox-review-standard.md`~~ | `docs/design-v2/sandbox-review-standard.md` | 已迁移到 design-v2 |

---

## 使用指南

### 何时使用 `god-view-8-perspectives-v0.01.md`

**适用场景**：
- 版本规划会议（v0.02/v0.03 规划）
- 系统复盘会议（季度/半年度）
- 架构优化讨论（模块重构/性能优化）

**不适用场景**：
- 日常开发任务（应参考 `system-baseline.md`）
- 具体功能实现（应参考 `*-design.md`）
- Bug 修复（应参考 `debts.md`）

### 何时使用 `sandbox-review-standard.md` ⚠️ 已迁移

**文档已迁移至**：`docs/design-v2/sandbox-review-standard.md`

请访问新位置查看完整使用指南。

---

## 维护规则

### `god-view-8-perspectives-v0.01.md`

- **更新频率**：每个大版本（v0.01 → v0.02）更新一次
- **更新内容**：补充新的观察维度、更新版本演进建议
- **版本号**：跟随系统版本号（v0.01/v0.02/v0.03）

### ~~`sandbox-review-standard.md`~~ ⚠️ 已迁移

- **新位置**：`docs/design-v2/sandbox-review-standard.md`
- **更新频率**：发现新偏差类型时更新
- **更新内容**：补充偏差清单（A-S）、更新控制点图
- **版本号**：跟随系统版本（v0.01 正式版）

---

## 参考资料

- `docs/design-v2/system-baseline.md` - 系统设计基线
- `docs/workflow/6A-WORKFLOW.md` - 工作流程
- `docs/spec/v0.01/evidence/` - 证据归档
- `docs/spec/v0.01/roadmap/` - 版本路线图
