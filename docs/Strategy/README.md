# Strategy

**版本**：`理论来源单入口`  
**状态**：`Active`  
**封版日期**：`不适用（Active）`  
**变更规则**：`允许补充来源索引、目录导航与采用边界；不直接定义当前执行口径。`

---

## 定位

`docs/Strategy/` 是旧设计世界退场后保留下来的共享理论层，只保留跨战役共享的理论来源、方法论映射和经验补充。

这里回答“为什么这样设计、理论从哪来、哪些外部方法值得吸收”，不回答“当前系统现在按什么执行”。

从 `2026-03-12` 起，再加一条边界：

`只属于某一场战役的 research card / theory dossier / contract note / 身份记录，全部迁回对应战役，不再留在 Strategy 里伪装成共享理论来源。`

## 当前主线口径

当前主线固定链路为：

`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`

与本目录相关的固定边界是：

1. `PAS` 负责个股形态层。
2. `IRS` 负责行业级后置排序增强。
3. `MSS` 负责市场级风险调节。
4. `Strategy/` 只提供来源、映射、背景和共享经验补充。

当前正式设计与执行口径，请查看 `blueprint/`。

## 当前保留结构

| 目录/文件 | 角色 |
|---|---|
| `README.md` | Strategy 总索引、边界说明与跨模块入口 |
| `MSS/README.md` | `MSS` 理论来源导航 |
| `IRS/README.md` | `IRS` 行业口径与分类资料导航 |
| `PAS/README.md` | `PAS` 价格行为来源与映射导航 |
| `MSS/` | 市场情绪理论来源与经验补充 |
| `IRS/` | 行业分类与行业口径来源 |
| `PAS/` | 价格行为、形态来源与映射 |

## 保留 / 降级 / 合并

### 保留

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `README.md` | 保留并升级 | 作为 Strategy 单入口，统一承接总索引、边界说明与跨模块来源概览。 |
| `MSS/market-sentiment-system-2024-analysis.md` | 保留 | `MSS` 一级理论来源，信息密度高，和当前主线关联明确。 |
| `IRS/shenwan-industry-classification.md` | 保留 | `IRS` 行业口径基础资料，长期有效。 |
| `PAS/lance-beggs-ytc-analysis.md` | 保留 | `PAS` 核心来源之一，服务 `YTC` 形态回测。 |
| `PAS/volman-ytc-mapping.md` | 保留 | `YTC` 五形态映射主文档，当前 `PAS mini` 直接受益。 |
| `PAS/xu-jiachong-naked-kline-analysis.md` | 保留 | 面向 A 股语境的价格行为补充，当前 `BOF / 裸K` 方向仍有价值。 |

### 降级

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `MSS/90-archive/manual-sentiment-tracking-experience.md` | 已归档 | 仅保留为历史经验补充，不再视作 `MSS` 一级设计来源。 |

### 迁出至战役层

| 文件 | 处理结论 | 说明 |
|---|---|---|
| `tachibana-yoshimasa-analysis.md` | 已迁出 `Strategy/` | 该材料不再属于共享理论来源，后续只在对应战役研究资产层维护。 |

### 合并规则

1. `Strategy/` 后续原则上不再新增“泛综述”文件；新总结优先并入 `README.md`。
2. 同一主题若已有“来源分析”或“映射主文档”，后续补充应并入原文，不再平行长出第二份概览稿。
3. 仅当材料满足“一级来源 / 高价值映射 / 长期有效口径”三类之一时，才允许保留为独立文件。
4. 偏经验、偏随笔、偏启发式的材料，默认降级为共享经验补充，不进入当前主线设计引用链。
5. 只属于 `Normandy` 的 research asset，统一迁到 `normandy/01-full-design/90-research-assets/`。

## 跨模块来源概览

### 1. MSS 理论来源

#### 1.1 当前保留的核心参考

1. `MSS/market-sentiment-system-2024-analysis.md`
2. `MSS/90-archive/manual-sentiment-tracking-experience.md`

#### 1.2 主要提供的价值

`MSS` 方向当前主要从这些资料中吸收：

1. 市场广度、情绪强度、持续性的三维观测框架
2. 赚钱效应与亏钱效应的对称视角
3. 极端情绪样本与人工复核的经验背景
4. A 股涨跌停制度、T+1 语义对情绪系统的影响

#### 1.3 不直接采用的内容

当前不直接继承：

1. 固定温度公式
2. 固定七阶段阈值
3. 固定仓位百分比表
4. 手工经验中的推测样例数值

### 2. IRS 理论来源

#### 2.1 当前保留的核心参考

1. `IRS/shenwan-industry-classification.md`

#### 2.2 主要提供的价值

`IRS` 方向当前主要从这些资料中吸收：

1. 正式行业口径应为 `SW2021 一级行业`
2. 个股与行业成员关系的维护边界
3. 行业指数和行业成员数据的更新与审计方式

#### 2.3 不直接采用的内容

当前不直接继承：

1. 行业生命周期的静态 `PE / PB` 权重映射
2. 牛熊阶段行业配置表
3. 任意“某阶段超配某行业”的经验结论

### 3. PAS 理论来源

#### 3.1 当前保留的核心参考

1. `PAS/lance-beggs-ytc-analysis.md`
2. `PAS/volman-ytc-mapping.md`
3. `PAS/xu-jiachong-naked-kline-analysis.md`

#### 3.2 主要提供的价值

`PAS` 方向当前主要从这些资料中吸收：

1. `YTC` 五形态框架：`BOF / BPB / PB / TST / CPB`
2. 结构优先于单根 K 线的价格行为思想
3. `Volman -> YTC` 的微观结构映射线索
4. `BOF / Pin Bar` 的 A 股补充语境
5. A 股语境下的价格行为语言收口经验

#### 3.3 不直接采用的内容

当前不直接继承：

1. 外汇盘中 `tick` 级触发细节
2. 原书中的固定成功率、盈亏比和精确交易管理
3. 战役专属 contrary alpha 推测
4. 历史阶段性实施计划与旧周计划

## 使用边界

1. `Strategy/` 不直接充当执行 SoT。
2. 当前可执行设计以 `blueprint/` 为准；`Strategy/` 只负责来源、映射和理论背景。
3. 共享理论材料优先保留“来源 + 映射 + 采用边界”，不再堆执行草案，也不再回长半设计稿。
4. 历史基线看 `docs/design-v2/01-system/system-baseline.md`。
5. 当前治理状态看 `docs/spec/common/records/development-status.md`。
6. 版本证据、评审结论与冻结记录统一看 `docs/spec/` 与 `docs/observatory/`。

## 阅读建议

阅读顺序建议固定为：

1. 先看 `docs/Strategy/README.md`，明确 Strategy 的来源边界与目录结构。
2. 再按模块阅读 `MSS / IRS / PAS` 各自的来源导航与一级材料。
3. 需要落地实现时，立即回到 `blueprint/`。
4. 需要证据、版本和治理状态时，回到 `docs/spec/`。

## 相邻入口

1. `PAS/README.md`
2. `MSS/README.md`
3. `IRS/README.md`
4. `../observatory/README.md`
5. `../spec/README.md`
6. `../../blueprint/README.md`
7. `../design-v2/01-system/system-baseline.md`
8. `../spec/common/records/development-status.md`
