# EmotionQuant 可复用资产登记（重启版模板）

**状态**: Active（正式治理）  
**最后更新**: 2026-03-04
**责任文件**: `docs/spec/common/records/reusable-assets.md`

---

## 1. 用途与规则

- 只登记“已验证可复用”的资产（模板/脚本/模块/流程），不登记草稿。
- 每次任务 A6 收口时复核：
  1. 若产出可跨任务复用，新增条目。
  2. 若资产失效，降级或移除。
- 资产必须有“复用边界”和“已验证场景”。

## 2. 分级标准

| 等级 | 定义 |
|---|---|
| S | 可直接复用，稳定，默认优先 |
| A | 可复用，但需少量适配 |
| B | 仅可参考，需要明显改造 |

---

## 3. 当前可复用资产（重启基线）

### 3.1 治理资产

| ID | 资产 | 路径 | 等级 | 复用边界 |
|---|---|---|---|---|
| GOV-001 | 6A 工作流 | `docs/workflow/6A-WORKFLOW.md` | S | 所有开发任务必须走 A1-A6 |
| GOV-002 | 技术债模板 | `docs/spec/common/records/debts.md` | S | 所有风险/欠账登记 |
| GOV-003 | 开发状态模板 | `docs/spec/common/records/development-status.md` | S | 周级/任务级进展记录 |
| GOV-004 | 复用资产模板 | `docs/spec/common/records/reusable-assets.md` | S | 资产沉淀与分级 |
| GOV-005 | 路线图+实现卡 | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-*.md` | S | 任务推进与勾选追踪 |

### 3.2 设计资产

| ID | 资产 | 路径 | 等级 | 复用边界 |
|---|---|---|---|---|
| DES-001 | 设计总纲（SoT） | `docs/design-v2/01-system/system-baseline.md` | S | 所有模块设计冲突裁决 |
| DES-002 | Data 设计 | `docs/design-v2/02-modules/data-layer-design.md` | A | Week1 实现参考 |
| DES-003 | Selector 设计 | `docs/design-v2/02-modules/selector-design.md` | A | Week2 实现参考 |
| DES-004 | Strategy 设计 | `docs/design-v2/02-modules/strategy-design.md` | A | Week2 实现参考 |
| DES-005 | Broker 设计 | `docs/design-v2/02-modules/broker-design.md` | A | Week3 实现参考 |
| DES-006 | Backtest/Report 设计 | `docs/design-v2/02-modules/backtest-report-design.md` | A | Week4 实现参考 |
| DES-007 | 沙盘评审标准 | `docs/observatory/sandbox-review-standard.md` | S | 所有模块定稿前七维评审 + 定稿门禁 |

---

## 4. 待沉淀资产（候选区）

| 候选ID | 候选资产 | 来源任务 | 预期等级 | 当前状态 |
|---|---|---|---|---|
| - | - | - | - | - |

---

## 5. 新增资产模板

```md
### ASSET-XXX
- 名称:
- 路径:
- 等级: S/A/B
- 来源任务:
- 已验证场景:
- 复用边界:
- 已知限制:
```

---

## 6. 版本记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-03-02 | v1.0 | 重启清零：建立正式模板并初始化基线资产 |
| 2026-03-03 | v1.1 | 新增 DES-007 沙盘评审标准资产 |
| 2026-03-04 | v1.2 | v0.01/spec-01 文档校对后复核：无新增可复用资产 |
| 2026-03-04 | v1.3 | v0.01/spec-02~05 文档校对后复核：无新增可复用资产 |
| 2026-03-04 | v1.4 | v0.01 实现前最后一轮总校对后复核：无新增可复用资产 |




