# design-v2 目录说明

**版本**: `v0.01-v0.06 目录入口`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `仅允许入口、链接与边界说明维护；当前主线设计以上游 SoT 为准，历史口径以 Frozen 基线为准。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 定位

`docs/design-v2/` 只存放系统级设计基线、模块级设计与算法级 SoT，不存放分阶段执行材料。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| v0.01 历史基线 | `01-system/system-baseline.md` | `v0.01 Frozen` 历史执行口径 |
| 当前主开发线 | `03-algorithms/core-algorithms/down-to-top-integration.md` | `v0.01-plus` 当前设计 SoT |
| 当前主线 Selector | `02-modules/selector-mainline-design.md` | 当前主线初选边界 |
| 当前主线 Broker / Risk | `02-modules/broker-risk-mainline-design.md` | 当前主线执行边界 |
| 架构总览 | `01-system/architecture-master.md` | 查历史架构与当前主线映射 |
| 模块设计 | `02-modules/` | 查职责、接口、边界 |
| 算法设计 | `03-algorithms/core-algorithms/README.md` | 查 MSS/IRS/PAS 当前算法口径 |

## 结构

```
design-v2/
├── README.md                   # 本文件
├── 01-system/                  # 系统级设计
│   ├── system-baseline.md      # 系统基线（单一事实源）
│   └── architecture-master.md  # 架构总览
├── 02-modules/                 # 模块级设计
│   ├── data-layer-design.md
│   ├── selector-design.md
│   ├── selector-mainline-design.md
│   ├── strategy-design.md
│   ├── broker-design.md
│   ├── broker-risk-mainline-design.md
│   └── backtest-report-design.md
└── 03-algorithms/              # 算法级 SoT
    └── core-algorithms/
        ├── README.md
        ├── mss-algorithm.md
        ├── irs-algorithm.md
        ├── pas-algorithm.md
        └── down-to-top-integration.md
```

## 使用规则

1. 讨论 `v0.01 Frozen` 历史口径时，以 `system-baseline.md` 为准。
2. 讨论 `v0.01-plus` 当前主开发线时，以 `down-to-top-integration.md` 与 `docs/spec/v0.01-plus/` 为准。
3. `02-modules/` 中凡标记为 `Frozen` 的文档只承担历史口径；当前主线边界应直接查看对应的 `*-mainline-design.md`。
4. `03-algorithms/` 负责回答 `MSS/IRS/PAS` 当前怎么算，不承载阶段证据归档。
5. 路线图、证据、runbook、发布记录统一放入 `docs/spec/<version>/`。

## 相邻目录边界

- `docs/spec/`：放版本推进、证据和历史记录，不放系统级 SoT。
- `docs/observatory/`：放观察框架与评审标准，不放设计实现细节。
- `docs/Strategy/`：放理论来源与方法论，不直接定义执行口径。
- `docs/steering/`：放治理铁律与不可变约束。

## 相关文档

- `docs/observatory/sandbox-review-standard.md`
- `docs/Strategy/theoretical-foundations.md`
- `docs/steering/product.md`
- `docs/spec/common/records/development-status.md`
