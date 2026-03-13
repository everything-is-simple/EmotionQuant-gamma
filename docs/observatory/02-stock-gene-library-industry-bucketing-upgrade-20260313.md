# Stock Gene Library - 升级方案：行业分桶与相对强弱

**状态**: `Active Upgrade`  
**日期**: `2026-03-13`  
**对象**: `个股基因库的行业分桶升级方案`

---

## 1. 核心升级理念

### 1.1 从"绝对性格"到"相对强弱"

```
原方案：
├─ 这只股票的历史性格是什么？
├─ 平均涨 90 天，涨 50%
└─ 用这个性格来调整策略

升级方案：
├─ 这只股票的历史性格是什么？（保留）
├─ 在同行业的股票中，这只股票排第几？
├─ 在当前市场中，这只股票最受宠吗？
└─ 结合这三个维度，狠狠怼它
```

### 1.2 三个维度的组合

```
维度 1：历史个股股性（Historical Gene）
├─ 这只股票过去 5 年的性格
├─ 平均涨多久、涨多高、换手多少
└─ 用来判断"这只股票是不是好演员"

维度 2：近期个股股性（Recent Gene）
├─ 这只股票最近 3 个月的性格
├─ 最近涨多久、涨多高、换手多少
└─ 用来判断"这只股票最近是不是在状态"

维度 3：行业相对强弱（Industry Relative Strength）
├─ 在同行业的股票中，这只股票排第几
├─ 按行业分桶，看哪些个股最受宠
└─ 用来判断"这只股票在舞台上是不是主角"
```

---

## 2. 行业分桶的设计

### 2.1 为什么要分桶

```
问题：
├─ 我们有 5000 只 A 股
├─ BOF 可能同时触发 50 只
├─ 我们应该买哪 50 只？

答案：
├─ 不是"都买"
├─ 而是"按行业分桶，每个行业只买最强的"
└─ 这样就能集中火力，"狠狠怼它"
```

### 2.2 分桶的维度

```
按申万宏源一级行业分桶：
├─ 电子
├─ 计算机
├─ 电气设备
├─ 机械设备
├─ 汽车
├─ 房地产
├─ 银行
├─ 非银金融
├─ 医药生物
├─ 食品饮料
├─ ... 共 31 个行业

对每个行业：
├─ 计算所有股票的"近期股性评分"
├─ 排序，找出 Top 3-5
└─ 这些就是"最受宠的演员"
```

### 2.3 分桶的指标

```
对每只股票，计算：

历史股性评分（Historical Score）：
├─ 基于过去 5 年的数据
├─ 综合考虑：涨幅周期、涨幅幅度、新高密度、换手率
└─ 得分 0-100

近期股性评分（Recent Score）：
├─ 基于最近 3 个月的数据
├─ 综合考虑：涨幅周期、涨幅幅度、新高密度、换手率
└─ 得分 0-100

行业排名（Industry Rank）：
├─ 在同行业中的排名
├─ 例如：电子行业有 100 只股票，这只排第 5
└─ 排名 1-100

相对强弱评分（Relative Strength Score）：
├─ 综合历史评分、近期评分、行业排名
├─ 得分 0-100
└─ 用来判断"这只股票是不是最受宠的"
```

---

## 3. 相对强弱评分的计算

### 3.1 评分公式

```
相对强弱评分 = 
  0.3 * 历史股性评分 +
  0.5 * 近期股性评分 +
  0.2 * (100 - 行业排名百分比)

例如：
├─ 历史股性评分 = 75
├─ 近期股性评分 = 85
├─ 行业排名 = 5/100 = 5%
├─ 相对强弱评分 = 0.3*75 + 0.5*85 + 0.2*(100-5) = 22.5 + 42.5 + 19 = 84
```

### 3.2 评分的含义

```
相对强弱评分 >= 80：
├─ 这只股票是"最受宠的演员"
├─ 历史性格好，最近状态也好，在行业里排名靠前
└─ 优先级最高

相对强弱评分 60-80：
├─ 这只股票是"不错的演员"
├─ 历史性格不错，最近状态还可以
└─ 优先级中等

相对强弱评分 < 60：
├─ 这只股票是"一般的演员"
├─ 历史性格一般，或最近状态不好
└─ 优先级低，可能不买
```

---

## 4. 行业分桶的应用

### 4.1 选股流程

```
BOF 触发
  ↓
获得候选股票列表（可能 50 只）
  ↓
按申万宏源一级行业分桶
  ├─ 电子行业：10 只候选
  ├─ 计算机行业：8 只候选
  ├─ 医药生物行业：6 只候选
  └─ ... 其他行业
  ↓
对每个行业，计算相对强弱评分
  ├─ 电子行业：排名 1-10
  ├─ 计算机行业：排名 1-8
  ├─ 医药生物行业：排名 1-6
  └─ ... 其他行业
  ↓
选择相对强弱评分最高的股票
  ├─ 电子行业：Top 1-2
  ├─ 计算机行业：Top 1-2
  ├─ 医药生物行业：Top 1-2
  └─ ... 其他行业
  ↓
最终候选：15-20 只（而不是 50 只）
  ↓
结合 Positioning 的仓位大小，下单
```

### 4.2 为什么这样做

```
原来的做法：
├─ BOF 触发 50 只
├─ 全部买入
├─ 结果：分散了火力，每只仓位很小

新的做法：
├─ BOF 触发 50 只
├─ 按行业分桶，每个行业只买最强的
├─ 结果：集中了火力，每只仓位更大
└─ 这就是"狠狠怼它"
```

---

## 5. 数据架构升级

### 5.1 新增表结构

```sql
-- 历史股性评分表
CREATE TABLE l3_stock_historical_gene_score (
  stock_code VARCHAR,           -- 6 位股票代码
  industry_code VARCHAR,        -- 申万宏源行业代码
  industry_name VARCHAR,        -- 申万宏源行业名称
  historical_score FLOAT,       -- 历史股性评分（0-100）
  historical_score_components (
    avg_uptrend_duration_score FLOAT,
    avg_uptrend_return_score FLOAT,
    avg_new_high_density_score FLOAT,
    avg_turnover_score FLOAT
  ),
  sample_size INT,              -- 样本数
  last_updated DATE,            -- 最后更新日期
  
  PRIMARY KEY (stock_code)
);

-- 近期股性评分表
CREATE TABLE l3_stock_recent_gene_score (
  stock_code VARCHAR,           -- 6 位股票代码
  industry_code VARCHAR,        -- 申万宏源行业代码
  industry_name VARCHAR,        -- 申万宏源行业名称
  recent_score FLOAT,           -- 近期股性评分（0-100）
  recent_score_components (
    recent_uptrend_duration_score FLOAT,
    recent_uptrend_return_score FLOAT,
    recent_new_high_density_score FLOAT,
    recent_turnover_score FLOAT
  ),
  sample_size INT,              -- 样本数
  last_updated DATE,            -- 最后更新日期
  
  PRIMARY KEY (stock_code)
);

-- 行业排名表
CREATE TABLE l3_stock_industry_rank (
  stock_code VARCHAR,           -- 6 位股票代码
  industry_code VARCHAR,        -- 申万宏源行业代码
  industry_name VARCHAR,        -- 申万宏源行业名称
  industry_rank INT,            -- 在行业内的排名
  industry_total_count INT,     -- 行业内总股票数
  rank_percentile FLOAT,        -- 排名百分比（0-100）
  last_updated DATE,            -- 最后更新日期
  
  PRIMARY KEY (stock_code, industry_code)
);

-- 相对强弱评分表（最终结果）
CREATE TABLE l3_stock_relative_strength_score (
  stock_code VARCHAR,           -- 6 位股票代码
  industry_code VARCHAR,        -- 申万宏源行业代码
  industry_name VARCHAR,        -- 申万宏源行业名称
  relative_strength_score FLOAT,-- 相对强弱评分（0-100）
  historical_score FLOAT,       -- 历史股性评分
  recent_score FLOAT,           -- 近期股性评分
  industry_rank INT,            -- 行业排名
  rank_percentile FLOAT,        -- 排名百分比
  score_components (
    historical_weight FLOAT,    -- 0.3
    recent_weight FLOAT,        -- 0.5
    rank_weight FLOAT           -- 0.2
  ),
  last_updated DATE,            -- 最后更新日期
  
  PRIMARY KEY (stock_code)
);

-- 行业分桶快照表（每日）
CREATE TABLE l4_industry_bucket_snapshot (
  snapshot_date DATE,           -- 快照日期
  industry_code VARCHAR,        -- 申万宏源行业代码
  industry_name VARCHAR,        -- 申万宏源行业名称
  top_1_stock_code VARCHAR,     -- 排名第 1 的股票
  top_1_score FLOAT,            -- 排名第 1 的评分
  top_2_stock_code VARCHAR,     -- 排名第 2 的股票
  top_2_score FLOAT,            -- 排名第 2 的评分
  top_3_stock_code VARCHAR,     -- 排名第 3 的股票
  top_3_score FLOAT,            -- 排名第 3 的评分
  top_5_stock_codes VARCHAR,    -- 排名前 5 的股票列表
  total_stocks_in_industry INT, -- 行业内总股票数
  
  PRIMARY KEY (snapshot_date, industry_code)
);
```

---

## 6. 计算流程升级

### 6.1 历史股性评分计算

```
对每只股票：
  ↓
基于过去 5 年的数据：
├─ 计算平均涨幅周期
├─ 计算平均涨幅幅度
├─ 计算平均新高密度
├─ 计算平均换手率
  ↓
标准化这些指标（0-100）：
├─ 涨幅周期越长越好（最长 180 天 = 100 分）
├─ 涨幅幅度越大越好（最大 100% = 100 分）
├─ 新高密度越高越好（最高 0.5 根/天 = 100 分）
├─ 换手率越高越好（最高 10% = 100 分）
  ↓
加权平均：
├─ 历史股性评分 = 0.3*涨幅周期 + 0.3*涨幅幅度 + 0.2*新高密度 + 0.2*换手率
  ↓
存储到 l3_stock_historical_gene_score
```

### 6.2 近期股性评分计算

```
对每只股票：
  ↓
基于最近 3 个月的数据：
├─ 计算平均涨幅周期
├─ 计算平均涨幅幅度
├─ 计算平均新高密度
├─ 计算平均换手率
  ↓
标准化这些指标（0-100）：
├─ 同历史股性评分的标准化方式
  ↓
加权平均：
├─ 近期股性评分 = 0.3*涨幅周期 + 0.3*涨幅幅度 + 0.2*新高密度 + 0.2*换手率
  ↓
存储到 l3_stock_recent_gene_score
```

### 6.3 行业排名计算

```
对每个行业：
  ↓
获取该行业的所有股票
  ↓
按近期股性评分排序
  ↓
计算排名和排名百分比
  ↓
存储到 l3_stock_industry_rank
```

### 6.4 相对强弱评分计算

```
对每只股票：
  ↓
获取：
├─ 历史股性评分
├─ 近期股性评分
├─ 行业排名百分比
  ↓
计算相对强弱评分：
├─ 相对强弱评分 = 0.3*历史 + 0.5*近期 + 0.2*(100-排名百分比)
  ↓
存储到 l3_stock_relative_strength_score
```

### 6.5 行业分桶快照

```
每天收盘后：
  ↓
对每个行业：
├─ 按相对强弱评分排序
├─ 取 Top 5
├─ 记录 Top 1/2/3 的股票代码和评分
  ↓
存储到 l4_industry_bucket_snapshot
```

---

## 7. 与现有系统的集成

### 7.1 在 BOF 触发后的应用

```
BOF 触发
  ↓
获得候选股票列表
  ↓
查询 l3_stock_relative_strength_score
  ↓
按行业分桶，计算每只股票的相对强弱评分
  ↓
对每个行业，选择相对强弱评分最高的 1-2 只
  ↓
最终候选列表（集中火力）
  ↓
结合 Positioning 的仓位大小，下单
```

### 7.2 在 Positioning 中的应用

```
Positioning 现在要验证"买多少"

但"买多少"应该考虑：
├─ 这只股票的历史股性（波动率、最大回撤）
├─ 这只股票的近期股性（最近是否在状态）
├─ 这只股票的行业排名（是否是最受宠的）
└─ 综合这三个维度，调整仓位大小

例如：
├─ 相对强弱评分 >= 80：可以买满仓
├─ 相对强弱评分 60-80：买 70% 仓位
├─ 相对强弱评分 < 60：买 50% 仓位
```

---

## 8. 验证方案

### 8.1 验证的问题

```
问题 1：相对强弱评分是否有效？
├─ 相对强弱评分高的股票，是否真的涨得更好？
└─ 用 Normandy 的方式做 formal readout

问题 2：行业分桶是否有效？
├─ 按行业分桶选出的股票，是否真的比随机选择更好？
└─ 用 Normandy 的方式做 formal readout

问题 3：集中火力是否有效？
├─ 买 15-20 只集中火力的股票，是否比买 50 只分散火力更好？
└─ 用 Normandy 的方式做 formal readout
```

### 8.2 验证的方法

```
冻结：BOF entry + current sizing + current exit
变量：是否使用相对强弱评分和行业分桶
对照：
├─ Control：不使用相对强弱评分，随机选择
├─ Test 1：使用相对强弱评分，但不分桶
├─ Test 2：使用相对强弱评分，并分桶
└─ Test 3：使用相对强弱评分，分桶，并按评分调整仓位

看是否有稳定的改善
```

---

## 9. 一句话总结

**个股基因库升级方案：从"理解个股历史性格"升级到"按行业分桶，看哪些个股最受宠"。计算相对强弱评分，集中火力，狠狠怼最强的演员。**

---

## 10. 后续行动

### 立即（今天）

- 确认相对强弱评分的公式是否合理
- 确认行业分桶的维度是否正确

### 短期（本周）

- 实现相对强弱评分的计算
- 对所有 A 股计算相对强弱评分
- 生成行业分桶快照

### 中期（本月）

- 验证相对强弱评分的有效性
- 设计行业分桶的验证方案
- 准备做 Normandy 风格的 formal readout

### 长期（后续）

- 执行验证
- 如果验证通过，集成到主线
- 开始"狠狠怼它"
