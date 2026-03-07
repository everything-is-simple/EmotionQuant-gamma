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

### 2. `sandbox-review-standard.md` - 沙盘评审标准 ✅

**定位**：沙盘推演与偏差闭环的执行规范

**核心内容**：
- 七维评审框架（Schema契合/调用链完整性/幂等与确定性/状态机完整性/时序语义/边界冲突/报告口径）
- 证据模板（A-S 偏差清单，44项）
- 定稿门禁（防偏差控制点图）
- 连环失效检测

**使用场景**：
- 关键模块开发完成后的沙盘推演
- 版本发布前的全链路验证
- 偏差发现后的闭环修复

**约束说明**：
- 本文档为执行规范，必须遵守
- 涉及 Broker/Strategy/Data 的变更必须执行沙盘评审
- 偏差清单必须归档到 `docs/spec/v0.01/evidence/`

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
| `sandbox-review-standard.md` | `docs/workflow/6A-WORKFLOW.md` | 评审标准 vs 工作流程 |
| `sandbox-review-standard.md` | `docs/spec/v0.01/evidence/` | 评审标准 vs 证据归档 |

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

### 何时使用 `sandbox-review-standard.md`

**强制使用场景**：
- Broker 风控逻辑调整
- 执行语义或交易规则调整（T+1、涨跌停、费用模型）
- 模块契约字段变更
- 数据层 schema 变更

**可选使用场景**：
- 新增形态检测器（PAS）
- 新增因子（MSS/IRS）
- 报告模块优化

**不适用场景**：
- 文档更新
- 配置调整
- 日志优化

---

## 维护规则

### `god-view-8-perspectives-v0.01.md`

- **更新频率**：每个大版本（v0.01 → v0.02）更新一次
- **更新内容**：补充新的观察维度、更新版本演进建议
- **版本号**：跟随系统版本号（v0.01/v0.02/v0.03）

### `sandbox-review-standard.md`

- **更新频率**：发现新偏差类型时更新
- **更新内容**：补充偏差清单（A-S）、更新控制点图
- **版本号**：跟随系统版本（v0.01 正式版）

---

## 参考资料

- `docs/design-v2/system-baseline.md` - 系统设计基线
- `docs/workflow/6A-WORKFLOW.md` - 工作流程
- `docs/spec/v0.01/evidence/` - 证据归档
- `docs/spec/v0.01/roadmap/` - 版本路线图
