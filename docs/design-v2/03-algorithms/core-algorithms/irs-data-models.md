# IRS 数据模型设计

**版本**: `v0.01-plus IRS-lite + IRS-upgrade 设计骨架`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变当前主线契约边界的前提下，补充字段定义、质量标记与升级版预留字段。`  
**上游文档**: `irs-algorithm.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`

## 1. 定位

本文件回答三件事：

1. `IRS-lite` 当前到底落哪些表、哪些字段
2. 当前主线读取哪些字段、忽略哪些字段
3. 后续 `IRS-upgrade` 需要预留哪些扩展字段

## 2. 当前主线涉及的表

### 2.1 `l2_industry_daily`

当前职责：

1. 承载行业级日线聚合
2. 为 `IRS` 计算提供原始行业截面

当前最小字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | `DATE` | 交易日 |
| `industry` | `TEXT` | `SW2021` 一级行业 |
| `pct_chg` | `DOUBLE` | 行业日涨跌幅 |
| `amount` | `DOUBLE` | 行业成交额 |
| `market_total_amount` | `DOUBLE` | 全市场当日成交额 |
| `amount_delta_10d` | `DOUBLE` | 行业成交额相对 `10d` 变化 |

当前缺口：

1. 缺行业自身均量/均额基准
2. 缺行业内部强股密度
3. 缺行业扩散度
4. 缺行业牛股基因相关字段

### 2.2 `l3_irs_daily`

当前职责：

1. 存放行业级评分结果
2. 供 `Strategy / Ranker` 读取 `irs_score`

当前最小字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | `DATE` | 交易日 |
| `industry` | `TEXT` | 行业名 |
| `score` | `DOUBLE` | 当前主线使用的行业总分 |
| `rank` | `INTEGER` | 行业日排名 |
| `rs_score` | `DOUBLE` | 相对强度子分 |
| `cf_score` | `DOUBLE` | 资金流向子分 |

当前主线消费方式：

1. `Strategy / Ranker` 只读取：
   - `industry`
   - `score`
   - `rank`
2. 当前 `Broker / Risk` 不消费 `IRS`
3. 当前 `Selector` 不消费 `IRS`

## 3. 当前运行时对象

### 3.1 `IndustryScore`

建议对象口径：

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | `date` | 交易日 |
| `industry` | `str` | 行业名 |
| `score` | `float` | 行业总分 |
| `rank` | `int` | 日排名 |
| `rs_score` | `float` | 相对强度子分 |
| `cf_score` | `float` | 资金流向子分 |

说明：

1. 当前版本只要求这 6 个字段
2. 不强制把升级版字段立即进正式对象

## 4. 升级版预留字段

若进入 `IRS-upgrade`，建议在 `l2_industry_daily` / `l3_irs_daily` 逐步补齐以下字段。

### 4.1 行业轮动层

| 字段 | 层级 | 说明 |
|---|---|---|
| `rotation_status` | `L3` | `IN / HOLD / OUT` |
| `rotation_slope` | `L3` | 轮动斜率 |
| `rotation_detail` | `L3` | 启动/扩散/衰退等细分类 |
| `continuity_score` | `L3` | 行业持续性得分 |
| `diffusion_score` | `L3` | 行业扩散度得分 |

### 4.2 量能相对层

| 字段 | 层级 | 说明 |
|---|---|---|
| `amount_vs_industry_avg_20d` | `L2` | 当前成交额 / 行业 `20d` 均额 |
| `volume_vs_industry_avg_20d` | `L2` | 当前成交量 / 行业 `20d` 均量 |
| `activity_vs_market` | `L2` | 行业活跃度 / 全市场活跃度 |
| `crowding_score` | `L3` | 拥挤度修正 |

### 4.3 牛股基因层

| 字段 | 层级 | 说明 |
|---|---|---|
| `leader_score` | `L3` | 行业内龙头强度 |
| `gene_score` | `L3` | 行业牛股基因分 |
| `bof_hit_density` | `L2/L3` | 行业内 BOF 触发密度 |
| `strong_stock_ratio` | `L2/L3` | 行业内强势股占比 |

## 5. 质量与 fallback 字段

建议当前就明确以下字段口径，即便暂未全部落库：

| 字段 | 说明 |
|---|---|
| `quality_flag` | `normal / cold_start / stale / fallback` |
| `sample_days` | 有效历史样本天数 |
| `fallback_reason` | 缺失原因 |
| `data_fallback_used` | 是否使用中性兜底 |

## 6. 当前约束

1. 当前主线仍以 `score / rank` 作为最小消费面
2. 升级版字段必须先有证据和设计，不得直接把“想要的字段”一次性塞进正式契约
3. 若将来要正式扩 `IndustryScore`，必须先给 migration note
