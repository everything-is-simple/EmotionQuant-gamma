# Strategy（理论基础）

## 定位

`docs/Strategy/` 存放 MSS / IRS / PAS 的理论来源、方法论梳理与研究映射。

这里回答的是“为什么这样设计”，不是“当前系统必须怎么执行”。`v0.01 Frozen` 历史执行口径见 `docs/design-v2/01-system/system-baseline.md`；新版设计权威层见 `blueprint/README.md`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 理论总览 | `theoretical-foundations.md` | 理论来源与系统映射总说明 |
| MSS 理论 | `MSS/` | 市场情绪系统来源 |
| IRS 理论 | `IRS/` | 行业轮动分类与行业口径来源 |
| PAS 理论 | `PAS/` | 价格行为方法论、形态来源与映射 |
| 核心映射 | `PAS/volman-ytc-mapping.md` | Volman 与 YTC 的结构映射 |

## 结构

```
Strategy/
├── README.md
├── theoretical-foundations.md
├── MSS/
│   ├── market-sentiment-system-2024-analysis.md
│   └── manual-sentiment-tracking-experience.md
├── IRS/
│   └── shenwan-industry-classification.md
└── PAS/
    ├── lance-beggs-ytc-analysis.md
    ├── xu-jiachong-naked-kline-analysis.md
    ├── volman-ytc-mapping.md
    └── tachibana-yoshimasa-analysis.md
```

## 使用规则

1. `Strategy/` 只提供理论依据、研究材料和映射说明，不直接充当执行 SoT。
2. 理论与实现冲突时，以 `blueprint/`、`steering/` 和当前版本 `spec/` 为准。
3. 新增研究材料时，优先补充映射关系与“采用 / 适配 / 不采用”边界，不必在 README 重复展开全文摘要。
4. 阶段性实现证据、回测结果、版本验收，不放在 `Strategy/`，统一归档到 `docs/spec/<version>/`。

## 当前完成度

| 领域 | 当前状态 | 备注 |
|---|---|---|
| MSS | 已有 2 份核心材料 | 足够支撑 `MSS-full` 理论溯源；当前在线实现为 `MSS-lite` |
| IRS | 已有申万行业分类材料 | 足够支撑 `IRS-lite` 行业口径来源；轮动/牛股基因仍在升级 |
| PAS | 已有 4 份核心材料 + 1 份关键映射 | 足够支撑 `PAS-full` 理论溯源；当前在线实现为 `PAS-trigger` |
| 深度补充 | 仍缺 2 份候选研究材料 | 不阻塞当前文档治理与 v0.01 重启判断 |

## 相邻目录边界

- `blueprint/`：定义当前新版系统怎么做。
- `docs/design-v2/`：保留历史基线与兼容桥接。
- `docs/observatory/`：定义如何审视和验证。
- `docs/spec/`：存放版本路线图、证据和历史记录。
- `docs/reference/`：存放外部规则和运维参考。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-migration-boundary.md`
- `blueprint/README.md`
- `docs/observatory/god_view_8_perspectives_report_v0.01.md`
- `docs/spec/common/records/development-status.md`
