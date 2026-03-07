# IRS-lite 信息流设计（当前执行版）

**版本**: `v0.01-plus IRS-lite + IRS-upgrade 设计骨架`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变当前主线执行边界的前提下，补充 IRS 输入、输出和上下游依赖说明。`  
**上游文档**: `irs-algorithm.md`, `down-to-top-integration.md`

## 1. 当前主线信息流

```text
L1/L2 行业日线
-> IRS-lite 计算
-> l3_irs_daily
-> Strategy / Ranker
-> final_score
```

这是当前在线最小信息流，不是完整 `IRS-full` 的终态。

## 2. 上游依赖

### 2.1 直接依赖

| 层 | 表 | 用途 |
|---|---|---|
| `L1` | `l1_index_daily` | 基准指数涨跌幅 |
| `L1` | `l1_sw_industry_member` | 股票到申万一级行业映射 |
| `L2` | `l2_industry_daily` | 行业日线聚合输入 |

### 2.2 当前不依赖

当前 `IRS-lite` 还不依赖：

1. `PAS` 触发密度
2. 行业内牛股画像
3. 行业生命周期状态
4. 行业内龙头梯队结构

## 3. 下游消费

### 3.1 当前主线

| 模块 | 消费方式 |
|---|---|
| `Strategy / Ranker` | 读取行业 `score`，写入 `irs_score` |

### 3.2 当前不允许的消费

| 模块 | 不允许的方式 |
|---|---|
| `Selector` | 把 `IRS` 当 Top-N 行业过滤器 |
| `Broker / Risk` | 直接读取 `IRS` 决定仓位 |

## 4. 当前边界

### 4.1 允许

1. `IRS` 作为后置排序增强
2. `IRS` 缺失时 fallback 为 `50`
3. `IRS` 在 sidecar 中保留解释字段

### 4.2 不允许

1. `IRS` 回到候选池前置过滤
2. `IRS` 直接决定是否允许 `BOF` 触发
3. `IRS` 与 `MSS` 混成单一行业-市场复合分

## 5. 升级版信息流

若进入 `IRS-upgrade`，建议扩成：

```text
L1/L2 行业日线 + 行业内结构 + PAS/BOF 行业聚合
-> 行业轮动层
-> 相对量能层
-> 扩散度层
-> 牛股基因层
-> 轮动状态 / 配置建议
-> l3_irs_daily（扩展字段）
-> Strategy / Ranker
```

### 5.1 新增上游

建议新增的上游聚合：

1. 行业内 `BOF` 触发密度
2. 行业内强势股占比
3. 行业内龙头强度
4. 行业当前量能相对自身均值

### 5.2 下游不变

即便升级，当前主线的消费边界仍建议保持：

1. `Strategy / Ranker` 负责消费 `IRS`
2. `Broker / Risk` 继续只消费 `MSS`

这能保证系统职责不重新打架

### 5.3 解释层增强

升级后，`l3_irs_daily` 至少应能解释：

1. 这个行业当前处于 `IN / HOLD / OUT` 哪个轮动状态
2. 轮动是在加速、扩散还是衰退
3. 当前建议是 `OVERWEIGHT / STANDARD / UNDERWEIGHT / AVOID`
4. 这些建议由哪些因子共同推导而来
