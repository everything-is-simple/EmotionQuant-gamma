# 核心算法设计桥接目录

**版本**: `v0.01-v0.06 桥接目录`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `本目录仅保留 design-v2 阶段的兼容桥接与历史附录；现行算法修订必须进入 blueprint/，本目录只允许导航、勘误与桥接说明更新。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/README.md`

## 定位

`docs/design-v2/03-algorithms/core-algorithms/` 现只保留 `design-v2` 阶段整理出的算法桥接稿、兼容附录与历史说明。

这里不再回答“仓库现行算法怎么算”，而只负责三件事：

1. 给旧 `design-v2` 路径提供跳转与兼容入口
2. 保留 `v0.01 Frozen` 与 `design-v2` 收口阶段的历史附录
3. 为回看旧设计时提供最小上下文

仓库现行设计权威见 `blueprint/README.md`；跨模块执行基线仍以 `docs/design-v2/01-system/system-baseline.md` 的 `v0.01 Frozen` 历史口径为准；当前治理状态与推进阶段见 `docs/spec/common/records/development-status.md`；阶段证据与版本验收统一归档到 `docs/spec/`。

## 现行权威入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 系统基线 | `docs/design-v2/01-system/system-baseline.md` | 确认跨模块执行语义与总边界 |
| 设计迁移边界 | `docs/design-migration-boundary.md` | 确认 `blueprint/` 与 `docs/` 的分工 |
| 新版设计总入口 | `blueprint/README.md` | 查看现行三层文档结构 |
| Selector | `blueprint/01-full-design/03-selector-contract-supplement-20260308.md` | 查看现行 Selector 正文 |
| PAS-trigger / BOF | `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md` | 查看现行 PAS 正文 |
| IRS-lite | `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md` | 查看现行 IRS 正文 |
| MSS-lite | `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md` | 查看现行 MSS 正文 |
| Broker / Risk | `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md` | 查看现行执行边界 |
| 当前实现方案 | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` | 查看本轮唯一实现方案 |
| 当前执行拆解 | `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md` | 查看 phase / task / checklist |
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段与重启条件 |

## 结构

```text
core-algorithms/
├── README.md                    # 本文件
├── mss-algorithm.md             # MSS 当前算法口径
├── mss-data-models.md           # MSS 数据模型
├── mss-api.md                   # MSS 接口契约
├── mss-information-flow.md      # MSS 信息流
├── irs-algorithm.md             # IRS 当前算法口径
├── irs-data-models.md           # IRS 数据模型
├── irs-api.md                   # IRS 接口契约
├── irs-information-flow.md      # IRS 信息流
├── pas-algorithm.md             # PAS 当前算法口径
├── pas-data-models.md           # PAS 数据模型
├── pas-api.md                   # PAS 接口契约
├── pas-information-flow.md      # PAS 信息流
└── down-to-top-integration.md   # 集成模式与演进边界
```

## 使用规则

1. 本目录不是仓库现行算法 SoT；若需要现行设计正文，先回到 `docs/design-migration-boundary.md` 与 `blueprint/README.md`。
2. 理论来源与采用理由放在 `docs/Strategy/`，不在本目录重复展开研究材料。
3. 版本证据、回测结果、消融实验与验收结论，统一进入 `docs/spec/<version>/evidence/` 或对应 records。
4. 当前是否继续推进实现，不在本目录维护，统一查看 `docs/spec/common/records/development-status.md`。
5. 本目录中的 `algorithm / api / data-models / information-flow / integration` 文件，均视为历史桥接稿或兼容附录，不得重新升格为现行权威正文。
6. 若桥接稿与 `blueprint/` 现行正文冲突，以 `blueprint/` 为准；若涉及 `v0.01 Frozen` 历史执行语义，则仍以 `docs/design-v2/01-system/system-baseline.md` 为准。

## 当前版本范围

| 版本 | MSS | IRS | PAS | 集成模式 |
|---|---|---|---|---|
| v0.01 | 三态硬门控 | Top-N 硬过滤 | BOF 单形态闭环 | Top-Down |
| v0.01-plus | 市场级控仓位 | IRS-lite 排序增强 | BOF detector + DTT sidecar | Down-to-Top |
| v0.02 | 风险状态机增强 | 轮动层 + 基因层 | BOF + BPB | Down-to-Top |
| v0.03 | 动态风险覆盖 | 行业内结构增强 | TST / PB | Down-to-Top |
| v0.04 | 动态仓位带 | 生命周期增强 | CPB + 失败处理 | Down-to-Top |
| v0.05-v0.06 | 自适应阈值 | 自适应权重 | 形态强度 / 自适应参数 | Down-to-Top |

## 相邻目录边界

- `docs/design-v2/01-system/`：定义系统总语义与优先级。
- `docs/design-v2/02-modules/`：定义模块接口、职责与数据边界。
- `docs/Strategy/`：定义理论来源与方法论映射。
- `docs/spec/`：定义版本证据、路线图、records 与当前状态。
- `docs/observatory/`：定义评审标准与观察框架。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-v2/02-modules/selector-mainline-design.md`
- `docs/design-v2/02-modules/broker-risk-mainline-design.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `docs/Strategy/README.md`
- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`
