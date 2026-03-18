# Blueprint

**状态**: `Active`  
**日期**: `2026-03-09`

---

## 1. 定位

`blueprint/` 是 `EmotionQuant-gamma` 根目录下的全新设计空间。

它的职责只有一个：

`承载新版、分层清晰、与旧 docs 体系明确隔离的设计书。`

这里不是旧 `docs/` 的补丁区，也不是一次性整理报告的堆放区。

---

## 2. 和旧体系的边界

旧体系仍然保留在：

1. `docs/`
2. `G:\EmotionQuant\EmotionQuant-beta\docs`
3. `G:\EmotionQuant\EmotionQuant-beta\Governance`
4. `G:\EmotionQuant\EmotionQuant-alpha\docs`
5. `G:\EmotionQuant\EmotionQuant-alpha\Governance`

这些内容现在只作为：

1. 历史基线
2. 设计资产来源
3. 对照与回退参考

不再作为 `blueprint/` 的正文存放位置。

---

## 3. 分层结构

`blueprint/` 目前固定为 3 层：

1. `01-full-design/`
   - 完整设计 SoT
   - 一旦冻结，不因实现压力随意改写
   - 阅读时应同时参考 `01-full-design/README.md` 的战场归属说明

2. `02-implementation-spec/`
   - 从完整设计中裁出的当前实现方案
   - 只定义本轮实现范围，不重写算法本体

3. `03-execution/`
   - roadmap / phase / task / checklists
   - 只服务执行，不承担设计正文

---

## 4. 当前入口

当前已经落下的入口文件有：

- `01-full-design/01-selector-contract-annex-20260308.md`
- `01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
- `01-full-design/03-irs-lite-contract-annex-20260308.md`
- `01-full-design/04-mss-lite-contract-annex-20260308.md`
- `01-full-design/05-broker-risk-contract-annex-20260308.md`
- `01-full-design/06-pas-minimal-tradable-design-20260309.md`
- `01-full-design/07-irs-minimal-tradable-design-20260309.md`
- `01-full-design/08-mss-minimal-tradable-design-20260309.md`
- `01-full-design/09-mainline-system-operating-baseline-20260309.md`
- `01-full-design/90-design-source-register-appendix-20260309.md`
- `01-full-design/91-cross-version-object-mapping-reference-20260308.md`
- `01-full-design/92-mainline-design-atom-closure-record-20260308.md`
- `02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
- `03-execution/00-current-dev-data-baseline-20260311.md`
- `03-execution/01-current-mainline-execution-breakdown-20260308.md`
- `03-execution/11-phase-6-unified-default-system-migration-package-card-20260317.md`
- `03-execution/12-phase-6a-promoted-subset-freeze-card-20260317.md`
- `03-execution/13-phase-6b-integrated-end-to-end-validation-card-20260317.md`
- `03-execution/14-phase-6c-unified-operating-runbook-refresh-card-20260317.md`
- `03-execution/15-phase-7-data-provider-refactor-card-20260317.md`
- `03-execution/16-phase-8-data-contract-residual-audit-card-20260318.md`
- `03-execution/17-phase-9-gene-mainline-integration-package-card-20260318.md`
- `03-execution/17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md`
- `03-execution/17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md`
- `03-execution/17.3-phase-9b-isolated-wave-role-validation-card-20260318.md`
- `03-execution/17.4-phase-9b-isolated-reversal-state-validation-card-20260318.md`
- `03-execution/17.5-phase-9b-isolated-context-trend-direction-before-validation-card-20260318.md`
- `03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md`
- `03-execution/17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md`
- `03-execution/18-phase-10-bof-risk-unit-lifecycle-package-card-20260318.md`

它们分别负责：

1. `01-05`：当前主线 core contract annex
2. `06-08`：当前主线 core algorithm body
3. `09`：当前主线 system operating baseline
4. `90-92`：来源、映射、闭环记录附录
5. `02-implementation-spec/`：当前唯一实现方案
6. `03-execution/00-current-dev-data-baseline-20260311.md`：当前本地环境 / 数据库 / TuShare 双通道 / 开工顺序固定前提
7. `03-execution/`：当前唯一执行拆解

## 4.1 设计来源声明

`01-full-design/` 中的算法文件来源：

| 文件 | 来源 | 当前角色 | 说明 |
|------|------|------|------|
| `01-selector-contract-annex-20260308.md` | gamma 新增 | core contract annex | 当前主线核心设计 |
| `02-pas-trigger-registry-contract-annex-20260308.md` | gamma 新增 | core contract annex | 当前主线核心设计 |
| `03-irs-lite-contract-annex-20260308.md` | gamma 新增 | core contract annex | 当前主线核心设计 |
| `04-mss-lite-contract-annex-20260308.md` | gamma 新增 | core contract annex | 当前主线核心设计 |
| `05-broker-risk-contract-annex-20260308.md` | gamma 新增 | core contract annex | 当前主线核心设计 |
| `06-pas-minimal-tradable-design-20260309.md` | gamma 新写 | core algorithm body | 基于 beta 四件套 + alpha v3.2.0 提炼 |
| `07-irs-minimal-tradable-design-20260309.md` | gamma 新写 | core algorithm body | 基于 beta 四件套 + alpha v3.3.0 提炼 |
| `08-mss-minimal-tradable-design-20260309.md` | gamma 新写 | core algorithm body | 基于 beta 四件套 + alpha v3.2.0 提炼 |
| `09-mainline-system-operating-baseline-20260309.md` | gamma 新写 | system operating baseline | 端到端运行路径、场景矩阵与系统级证据口径 |
| `90-design-source-register-appendix-20260309.md` | gamma 新增 | appendix | 来源登记，不参与当前主线排序 |
| `91-cross-version-object-mapping-reference-20260308.md` | gamma 新增 | appendix | 跨版本来源参考，不参与当前主线排序 |
| `92-mainline-design-atom-closure-record-20260308.md` | gamma 新增 | appendix | 闭环记录，不参与当前主线排序 |

**迁移原则**：

- `01-09` 组成当前主线核心设计包
- `01-05` 是 core contract annex，`06-08` 是 core algorithm body，`09` 是 system operating baseline
- `90-92` 全部是附录，不参与当前主线排序
- 所有文件默认冻结，只在"逻辑错误"或"外部约束变化"时修改
- alpha/beta 的完整算法文件保留在原仓库作为参考，不直接迁移到 gamma

**设计资产回收路径**：

1. `beta` 四件套（algorithm / data-models / information-flow / api）提供结构表达
2. `alpha` 算法文（v3.2.0 / v3.3.0）提供边界复核和验收口径
3. `gamma` 的 minimal tradable design 是提炼后的最小可交易版
4. 详细来源登记见 `90-design-source-register-appendix-20260309.md`

---

## 5. 使用规则

1. 先写 `01-full-design/`，再写 `02-implementation-spec/`，最后才写 `03-execution/`。
2. 不允许在 `03-execution/` 里重新发明设计。
3. 不允许再把 `development-status`、一次性 evidence、旧 `Frozen` 正文当作当前设计正文。
4. 若需要复用 `alpha / beta` 的成熟设计，只能提炼后写入 `blueprint/`，不能直接把旧文档当当前正文。

---

## 6. 当前目标

当前 `01-full-design/` 第一层 `contract annex` 已经补齐：

1. Selector
2. PAS Trigger / Registry
3. IRS-lite
4. MSS-lite
5. Broker / Risk

当前 `01-full-design/` 第二层正文推进状态如下：

1. `PAS` 最小可交易形态层正文已落地（`06-pas-minimal-tradable-design-20260309.md`）
2. `IRS` 最小可交易排序层正文已落地（`07-irs-minimal-tradable-design-20260309.md`）
3. `MSS` 最小可交易风控层正文已落地（`08-mss-minimal-tradable-design-20260309.md`）
4. 系统总纲已落地（`09-mainline-system-operating-baseline-20260309.md`）
5. 附录层已落地：来源登记、映射参考、闭环记录

当前 `02-implementation-spec/` 也已经落下第一份正文：

1. `01-current-mainline-implementation-spec-20260308.md`

当前 `03-execution/` 也已经落下第一份正文：

1. `00-current-dev-data-baseline-20260311.md`
2. `01-current-mainline-execution-breakdown-20260308.md`
3. `02-phase-0-contract-trace-card-20260309.md`
4. `03-phase-1-pas-card-20260309.md`
5. `03.5-phase-1.5-stabilization-card-20260310.md`
6. `04-phase-2-irs-card-20260309.md`
7. `05-phase-3-mss-card-20260309.md`
8. `06-phase-4-gate-card-20260309.md`
9. `06.1-phase-4.1-mss-broker-remediation-card-20260311.md`
10. `07-phase-5-research-line-migration-package-card-20260315.md`
11. `08-phase-5a-normandy-migration-boundary-absorption-card-20260315.md`
12. `09-phase-5b-positioning-migration-boundary-absorption-card-20260315.md`
13. `10-phase-5c-mainline-no-fake-governance-patch-card-20260315.md`
14. `11-phase-6-unified-default-system-migration-package-card-20260317.md`
15. `12-phase-6a-promoted-subset-freeze-card-20260317.md`
16. `13-phase-6b-integrated-end-to-end-validation-card-20260317.md`
17. `14-phase-6c-unified-operating-runbook-refresh-card-20260317.md`
18. `15-phase-7-data-provider-refactor-card-20260317.md`
19. `16-phase-8-data-contract-residual-audit-card-20260318.md`
20. `17-phase-9-gene-mainline-integration-package-card-20260318.md`
21. `17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md`
22. `17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md`
23. `17.3-phase-9b-isolated-wave-role-validation-card-20260318.md`
24. `17.4-phase-9b-isolated-reversal-state-validation-card-20260318.md`
25. `17.5-phase-9b-isolated-context-trend-direction-before-validation-card-20260318.md`
26. `17.6-phase-9c-formal-combination-freeze-card-20260318.md`
27. `17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md`
28. `18-phase-10-bof-risk-unit-lifecycle-package-card-20260318.md`

当前冻结后的使用顺序固定为：

1. 先看 `01-05`，确认跨模块 contract 边界
2. 再看 `06-08`，确认算法正文
3. 再看 `09`，确认端到端运行路径、系统级场景矩阵与证据口径
4. 再看 `02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
5. 再看 `03-execution/00-current-dev-data-baseline-20260311.md`，确认当前执行库、旧库候选、三目录纪律、TuShare 双通道和当前 phase 顺序
6. 再看当前 execution breakdown 与 phase card
7. 只有在做来源审计或历史回看时，才看 `90-92`
8. 实现只允许从 `01-09` 裁出，不允许跳过正文直接拿附录下定义
