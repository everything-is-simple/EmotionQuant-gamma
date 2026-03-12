# Strategy

## 定位

`docs/Strategy/` 是旧设计世界退场后保留下来的共享理论层，只保留跨战役共享的理论来源、方法论映射和经验补充。

这里回答“为什么这样设计、理论从哪来、哪些外部方法值得吸收”，不回答“当前系统现在按什么执行”。

从 `2026-03-12` 起，再加一条边界：

`只属于某一场战役的 research card / theory dossier / contract note / 身份记录，全部迁回对应战役，不再留在 Strategy 里伪装成共享理论来源。`

## 当前保留结构

| 目录/文件 | 角色 |
|---|---|
| `theoretical-foundations.md` | 策略理论总览与跨模块索引 |
| `MSS/` | 市场情绪理论来源与经验补充 |
| `IRS/` | 行业分类与行业口径来源 |
| `PAS/` | 价格行为、形态来源与映射 |

## 保留 / 降级 / 合并

### 保留

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `theoretical-foundations.md` | 保留 | 作为 Strategy 总索引，负责串联 MSS / IRS / PAS 的理论来源。 |
| `MSS/market-sentiment-system-2024-analysis.md` | 保留 | `MSS` 一级理论来源，信息密度高，和当前主线关联明确。 |
| `IRS/shenwan-industry-classification.md` | 保留 | `IRS` 行业口径基础资料，长期有效。 |
| `PAS/lance-beggs-ytc-analysis.md` | 保留 | `PAS` 核心来源之一，服务 `YTC` 形态回测。 |
| `PAS/volman-ytc-mapping.md` | 保留 | `YTC` 五形态映射主文档，当前 `PAS mini` 直接受益。 |
| `PAS/xu-jiachong-naked-kline-analysis.md` | 保留 | 面向 A 股语境的价格行为补充，当前 `BOF / 裸K` 方向仍有价值。 |

### 降级

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `MSS/manual-sentiment-tracking-experience.md` | 降级为经验补充 | 保留经验密度，但不再视作 `MSS` 一级设计来源。 |

### 迁出至战役层

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `normandy/01-full-design/90-research-assets/tachibana-yoshimasa-analysis.md` | 迁出至 `Normandy` 研究资产层 | `Tachibana` 当前只服务 `Normandy contrary alpha` 研究，不再留在 `Strategy/PAS` 中伪装成共享来源。 |

### 合并规则

1. `Strategy/` 后续原则上不再新增“泛综述”文件；新总结优先并入 `theoretical-foundations.md`。
2. 同一主题若已有“来源分析”或“映射主文档”，后续补充应并入原文，不再平行长出第二份概览稿。
3. 仅当材料满足“一级来源 / 高价值映射 / 长期有效口径”三类之一时，才允许保留为独立文件。
4. 偏经验、偏随笔、偏启发式的材料，默认降级为共享经验补充，不进入当前主线设计引用链。
5. 只属于 `Normandy` 的 research asset，统一迁到 `normandy/01-full-design/90-research-assets/`。

## 使用边界

1. `Strategy/` 不直接充当执行 SoT。
2. 当前可执行设计以 `blueprint/` 为准；`Strategy/` 只负责来源、映射和理论背景。
3. 共享理论材料优先保留“来源 + 映射 + 采用边界”，不再堆执行草案，也不再回长半设计稿。
4. 历史基线看 `docs/design-v2/01-system/system-baseline.md`。
5. 当前治理状态看 `docs/spec/common/records/development-status.md`。
6. 版本证据、评审结论与冻结记录统一看 `docs/spec/` 与 `docs/observatory/`。

## 相邻入口

1. `PAS/volman-ytc-mapping.md`
2. `../observatory/README.md`
3. `../spec/README.md`
4. `../../blueprint/README.md`
5. `../design-v2/01-system/system-baseline.md`
6. `../spec/common/records/development-status.md`
