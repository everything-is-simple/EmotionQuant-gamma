# Stock Gene Library - 第四战场初步方案

**状态**: `Proposal`  
**日期**: `2026-03-13`  
**对象**: `第四战场：个股基因库的完整设计方案`

---

## 1. 定位

`stock-gene-library/` 是 `EmotionQuant-gamma` 的第四战场设计空间。

它的职责只有一个：

`隔离"个股历史性格特征"这条新研究主线，用于在 BOF 触发后调整策略。`

这里不是 `blueprint/` 的替代品，也不是对当前 `Normandy / Positioning` 的补充。

这里还必须再写死一条：

`Stock Gene Library 不是 v0.01 的子版本号，也不是新的主线版本线。`

它是研究战场，不是版本线。

---

## 2. 和当前三战场的边界

当前仓库已经有三条已知前提：

1. `Normandy`：买什么 + 何时买 + 是否卖坏（已完成）
2. `Positioning`：买多少 + 卖多少（进行中）
3. `Mainline`：BOF / no IRS / no MSS / current full-exit（可信运营线）

因此 `Stock Gene Library` 的边界固定为：

1. 不重开"买什么 / 何时买"的 alpha provenance 问题
2. 不继续在 `Normandy / Positioning` 里续跑旧卡
3. 不让"市场级"（MSS）或"行业级"（IRS）的因子进入
4. 只研究"个股级"的历史性格特征
5. 先在固定 baseline 下回答"这只股票的基因是什么"
6. 再在验证通过后，用基因来调整 BOF 触发后的策略
7. 若研究结论未来需要升格，必须先形成正式 record，再迁回 `blueprint/`

---

## 3. 核心理念

### 3.1 舞台 vs 演员

```
舞台（市场级）
├─ MSS：市场情绪温度
├─ IRS：行业热度
└─ 其他市场指标
    ↓
    舞台热不热闹，和演员表演精彩不精彩没有直接关系

演员（个股级）
├─ BOF：这只股票的形态 ✓（已验证）
├─ 个股基因：这只股票的历史性格 ？（待验证）
└─ 其他个股特征：？（待验证）
    ↓
    演员的表演质量才是真正重要的
```

### 3.2 个股基因的定义

`个股基因` = 这只股票的历史性格特征

它回答的问题是：

```
这只股票在历史上：
├─ 涨的时候，一般涨多久？
├─ 涨的时候，一般涨多高？
├─ 涨的时候，日线新高多少根？
├─ 涨的时候，换手率多少？
├─ 跌的时候，一般跌多久？
├─ 跌的时候，一般跌多深？
└─ 跌的时候，日线新低多少根？
```

### 3.3 个股基因的用途

```
BOF 触发
  ↓
查这只股票的基因
  ↓
根据基因预测：
├─ 这波涨幅可能涨多久？
├─ 这波涨幅可能涨多高？
├─ 这波涨幅期间会有多少根新高？
└─ 这波涨幅期间的换手率会是多少？

↓

根据预测来调整策略：
├─ 调整持仓周期目标
├─ 调整利润目标
├─ 调整 trailing-stop 宽度
└─ 调整仓位大小（在 Positioning 中）
```

---

## 4. 分层结构

`Stock Gene Library` 固定沿用 `blueprint/` 的三层结构：

1. `01-full-design/`
   - 第四战场完整设计 SoT
   - 只回答研究边界和系统性问题

2. `02-implementation-spec/`
   - 从完整设计中裁出的当前实验实现方案
   - 只定义本轮实验范围和对照口径

3. `03-execution/`
   - phase / task / checklists / evidence contract
   - 只服务执行，不承担算法正文

---

## 5. 当前目标

第四战场的当前目标固定为三件事：

1. 先定义"个股基因"的最小维度集合
2. 再计算所有 A 股（或关注股票池）的基因档案
3. 最后验证基因是否能改善 BOF 触发后的策略

一句话说：

`Stock Gene Library 不是为了"找新的 alpha"，而是为了"理解每只股票的历史性格"，从而在 BOF 触发后做出更聪明的决策。`

---

## 6. 个股基因的维度定义

### 6.1 涨幅基因（Uptrend Gene）

#### 时间维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_uptrend_duration_days` | 平均涨幅周期（天数） | 预测这波涨幅会持续多久 |
| `median_uptrend_duration_days` | 中位数涨幅周期 | 更稳健的周期预测 |
| `std_uptrend_duration_days` | 涨幅周期的标准差 | 判断周期是否稳定 |
| `max_uptrend_duration_days` | 历史最长涨幅周期 | 了解极端情况 |
| `min_uptrend_duration_days` | 历史最短涨幅周期 | 了解极端情况 |
| `p25_uptrend_duration_days` | 25 分位数 | 了解分布 |
| `p75_uptrend_duration_days` | 75 分位数 | 了解分布 |

#### 幅度维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_uptrend_return_pct` | 平均涨幅（百分比） | 预测这波涨幅会涨多高 |
| `median_uptrend_return_pct` | 中位数涨幅 | 更稳健的幅度预测 |
| `std_uptrend_return_pct` | 涨幅的标准差 | 判断幅度是否稳定 |
| `max_uptrend_return_pct` | 历史最大涨幅 | 了解极端情况 |
| `min_uptrend_return_pct` | 历史最小涨幅 | 了解极端情况 |
| `p25_uptrend_return_pct` | 25 分位数 | 了解分布 |
| `p75_uptrend_return_pct` | 75 分位数 | 了解分布 |

#### 形态维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_uptrend_new_high_count` | 平均每波段日线新高根数 | 预测这波涨幅的形态强度 |
| `median_uptrend_new_high_count` | 中位数新高根数 | 更稳健的形态预测 |
| `std_uptrend_new_high_count` | 新高根数的标准差 | 判断形态是否稳定 |
| `max_uptrend_new_high_count` | 历史最多新高根数 | 了解极端情况 |
| `min_uptrend_new_high_count` | 历史最少新高根数 | 了解极端情况 |
| `avg_uptrend_new_high_density` | 平均新高密度（新高根数/周期天数） | 判断新高是否密集 |

#### 换手维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_uptrend_turnover_at_new_high` | 新高时的平均换手率 | 预测这波涨幅的换手特征 |
| `max_uptrend_single_day_turnover` | 历史最大单日换手率 | 了解极端换手 |
| `avg_uptrend_max_daily_turnover` | 平均每波段的最大单日换手 | 判断换手是否激烈 |
| `uptrend_turnover_concentration` | 换手集中度（换手集中在几天） | 判断换手是否集中 |

#### 成交量维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_uptrend_daily_amount` | 涨幅期间的平均日成交额 | 了解成交活跃度 |
| `avg_uptrend_amount_growth` | 涨幅期间的成交额增长率 | 判断成交额是否在增加 |

### 6.2 跌幅基因（Downtrend Gene）

#### 时间维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_downtrend_duration_days` | 平均跌幅周期（天数） | 预测这波跌幅会持续多久 |
| `median_downtrend_duration_days` | 中位数跌幅周期 | 更稳健的周期预测 |
| `std_downtrend_duration_days` | 跌幅周期的标准差 | 判断周期是否稳定 |
| `max_downtrend_duration_days` | 历史最长跌幅周期 | 了解极端情况 |
| `min_downtrend_duration_days` | 历史最短跌幅周期 | 了解极端情况 |

#### 幅度维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_downtrend_return_pct` | 平均跌幅（百分比） | 预测这波跌幅会跌多深 |
| `median_downtrend_return_pct` | 中位数跌幅 | 更稳健的幅度预测 |
| `std_downtrend_return_pct` | 跌幅的标准差 | 判断幅度是否稳定 |
| `max_downtrend_return_pct` | 历史最大跌幅 | 了解极端情况 |
| `min_downtrend_return_pct` | 历史最小跌幅 | 了解极端情况 |

#### 形态维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_downtrend_new_low_count` | 平均每波段日线新低根数 | 预测这波跌幅的形态强度 |
| `median_downtrend_new_low_count` | 中位数新低根数 | 更稳健的形态预测 |
| `std_downtrend_new_low_count` | 新低根数的标准差 | 判断形态是否稳定 |
| `avg_downtrend_new_low_density` | 平均新低密度（新低根数/周期天数） | 判断新低是否密集 |

#### 换手维度

| 指标 | 定义 | 用途 |
|------|------|------|
| `avg_downtrend_turnover_at_new_low` | 新低时的平均换手率 | 预测这波跌幅的换手特征 |
| `max_downtrend_single_day_turnover` | 历史最大单日换手率 | 了解极端换手 |

### 6.3 稳定性指标（Stability Metrics）

| 指标 | 定义 | 用途 |
|------|------|------|
| `uptrend_gene_stability_score` | 涨幅基因稳定性评分（0-100） | 判断涨幅基因是否可信 |
| `downtrend_gene_stability_score` | 跌幅基因稳定性评分（0-100） | 判断跌幅基因是否可信 |
| `sample_size_uptrend` | 涨幅波段样本数 | 判断样本是否足够 |
| `sample_size_downtrend` | 跌幅波段样本数 | 判断样本是否足够 |
| `last_gene_update_date` | 基因最后更新日期 | 判断基因是否过时 |

---

## 7. 数据架构

### 7.1 存储策略

DuckDB 单库存储，通过 L1-L4 分层解耦。

| 层级 | 表名 | 内容 |
|------|------|------|
| L1 | `raw_daily_ohlcv` | 原始日线数据（来自 baostock / akshare） |
| L2 | `l2_daily_with_indicators` | 加工日线（新高/新低/换手率） |
| L3 | `l3_stock_gene_profile` | 个股基因档案（最终基因数据） |
| L4 | `l4_stock_gene_trace` | 基因追踪（基因计算过程和历史） |

### 7.2 L3 表结构：stock_gene_profile

```sql
CREATE TABLE l3_stock_gene_profile (
  stock_code VARCHAR,           -- 6 位股票代码
  gene_type VARCHAR,            -- 'uptrend' / 'downtrend'
  metric_name VARCHAR,          -- 指标名称（如 avg_uptrend_duration_days）
  metric_value FLOAT,           -- 指标值
  sample_size INT,              -- 样本数
  stability_score FLOAT,        -- 稳定性评分（0-100）
  last_updated DATE,            -- 最后更新日期
  created_at TIMESTAMP,         -- 创建时间
  
  PRIMARY KEY (stock_code, gene_type, metric_name)
);
```

### 7.3 L4 表结构：stock_gene_trace

```sql
CREATE TABLE l4_stock_gene_trace (
  stock_code VARCHAR,           -- 6 位股票代码
  trace_date DATE,              -- 追踪日期
  uptrend_segment_id INT,       -- 涨幅波段 ID
  downtrend_segment_id INT,     -- 跌幅波段 ID
  segment_type VARCHAR,         -- 'uptrend' / 'downtrend'
  segment_start_date DATE,      -- 波段开始日期
  segment_end_date DATE,        -- 波段结束日期
  segment_duration_days INT,    -- 波段持续天数
  segment_return_pct FLOAT,     -- 波段收益率
  new_high_count INT,           -- 新高根数
  new_low_count INT,            -- 新低根数
  max_daily_turnover FLOAT,     -- 最大单日换手率
  avg_daily_amount FLOAT,       -- 平均日成交额
  
  PRIMARY KEY (stock_code, trace_date, segment_id)
);
```

---

## 8. 计算流程

### 8.1 波段识别

```
日线数据
  ↓
识别涨幅波段：
├─ 从低点开始
├─ 到高点结束
├─ 中间不能有更低的低点
└─ 记录：开始日期、结束日期、涨幅、持续天数

识别跌幅波段：
├─ 从高点开始
├─ 到低点结束
├─ 中间不能有更高的高点
└─ 记录：开始日期、结束日期、跌幅、持续天数
```

### 8.2 波段特征计算

```
对每个波段：
  ↓
计算时间特征：
├─ 持续天数

计算幅度特征：
├─ 收益率（百分比）

计算形态特征：
├─ 日线新高根数（对涨幅波段）
├─ 日线新低根数（对跌幅波段）
├─ 新高/新低密度

计算换手特征：
├─ 新高/新低时的换手率
├─ 最大单日换手率
├─ 换手集中度

计算成交量特征：
├─ 平均日成交额
├─ 成交额增长率
```

### 8.3 基因统计

```
对所有波段特征：
  ↓
计算统计量：
├─ 平均值
├─ 中位数
├─ 标准差
├─ 最大值
├─ 最小值
├─ 25 分位数
├─ 75 分位数

计算稳定性评分：
├─ 如果标准差 / 平均值 < 0.3 → 稳定性高（80-100）
├─ 如果标准差 / 平均值 < 0.5 → 稳定性中（60-80）
├─ 如果标准差 / 平均值 >= 0.5 → 稳定性低（0-60）

存储到 l3_stock_gene_profile
```

---

## 9. 当前不允许做的事

第四战场当前明确不允许：

1. 借"个股基因"给 MSS/IRS 加解释性特例
2. 一上来就把"个股基因"和"BOF"混成同一轮
3. 先做局部参数微扫，再补基因定义
4. 把书里的公式直接当真，不做长窗 formal replay
5. 直接把研究结果宣布为主线默认参数

---

## 10. 当前一句话方案

第四战场当前一句话方案固定为：

`先定义个股基因的最小维度集合，再计算所有 A 股的基因档案，最后用 Normandy 的方式验证基因是否能改善 BOF 触发后的策略。`

---

## 11. 后续行动

### 立即（今天）

- 确认基因维度定义是否完整
- 确认数据架构是否合理

### 短期（本周）

- 实现波段识别算法
- 实现波段特征计算
- 对 100 只样本股票计算基因

### 中期（本月）

- 对所有 A 股计算基因
- 验证基因的稳定性
- 设计基因验证方案

### 长期（后续）

- 执行基因验证（Normandy 方式）
- 如果验证通过，集成到主线
- 如果验证不通过，分析原因并迭代

---

## 12. 一句话总结

`第四战场是"个股基因库"，用来理解每只股票的历史性格，从而在 BOF 触发后做出更聪明的决策。不是为了找新 alpha，而是为了更好地理解已有的 alpha。`
