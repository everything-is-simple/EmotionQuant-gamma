# 第一版实现规格: 价格波段标尺

**状态**: `Active`  
**日期**: `2026-03-16`

---

## 1. 范围

第一版实现固定为 `price-only scaffold`：

1. 只消费 `l2_stock_adj_daily`
2. 只依赖复权 OHLC 与成交额字段
3. 只输出历史波段数据库，不产生实时交易信号

---

## 2. DuckDB 合同

### 2.1 `l3_stock_gene`

日级快照表，主键为 `(code, calc_date)`。

承载内容：

1. `bull_score / bear_score / gene_score`
2. 当前波段方向、角色、起点、终值、幅度、时长
3. 当前波段新高/新低数量、密度、最近一次极值
4. 自历史分位 / z-score
5. 同日同方向横截面 rank / percentile

### 2.2 `l3_gene_wave`

已完成波段账本，主键为 `(code, wave_id)`。

承载内容：

1. 波段起止、方向、价格区间
2. 幅度、持续天数、极值数量与密度
3. `MAINSTREAM / COUNTERTREND`
4. `INITIAL_TREND_* / ONE_TWO_THREE_* / TWO_B_WATCH`
5. 同向历史 rank / percentile / z-score

### 2.3 `l3_gene_event`

波段内极值事件账本，主键为 `(code, wave_id, event_seq)`。

承载内容：

1. `NEW_HIGH / NEW_LOW`
2. 第几次刷新
3. 事件价格、前一极值价格
4. 事件间隔天数、事件后密度
5. 是否构成 `2B` 失败

---

## 3. 计算流程

第一版计算流程固定为：

1. 为目标窗口向前回看 `260` 个交易日
2. 用价格摆动点检测确认 pivot
3. 由相邻反向 pivot 组成 completed wave
4. 统计每个 wave 内的新高/新低事件
5. 计算该股票同方向历史分位与 z-score
6. 对同日同方向股票做横截面排序
7. 回写三张 `l3_gene_*` 表

---

## 4. 当前转折实现

第一版不追求终极定义，只追求可重复、可回放、可比较。

当前实现口径：

1. `pivot`
   - 采用 5-bar fractal 风格的确认摆点
2. `1-2-3`
   - 由 completed wave 刷新同向极值后给出结构转折标签
3. `2B`
   - 新高/新低后，在短确认窗口内回落/回升穿回旧极值

---

## 5. 当前评分口径

第一版只允许三类子因子进入正式快照：

1. `magnitude`
2. `duration`
3. `extreme_density`

每个子因子都输出：

1. `rank`
2. `percentile`
3. `zscore`

`gene_score` 由三项分位均值构成，用于给出第一版综合尺。

---

## 6. 当前非目标

第一版明确不做：

1. 行业级 `gene`
2. 指数级 `gene`
3. PB / CPB 交易过滤
4. 与 `IRS / MSS` 的正式融合
