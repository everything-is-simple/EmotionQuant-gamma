# 第一版实现规格: 价格波段标尺

**状态**: `Active`  
**日期**: `2026-03-16`

---

## 1. 范围

第一版实现固定为 `price-only scaffold`：

1. 只消费 `l2_stock_adj_daily`
2. 只依赖复权 OHLC 与成交额字段
3. 只输出历史波段数据库，不产生实时交易信号
4. `G1` 研究层允许在窗口结束日追加一次 `factor_eval` 基线输出

---

## 2. DuckDB 合同

### 2.1 `l3_stock_gene`

补充说明：

1. 当前 schema 已正式补入 `trend_level`
2. 当前 schema 已正式补入 `current_context_trend_level / current_context_trend_direction`
3. 当前 schema 已正式补入 `current_wave_role_basis`
4. 这些字段当前属于“语义诚实化字段”，不是最终多层趋势完整实现

日级快照表，主键为 `(code, calc_date)`。

承载内容：

1. `bull_score / bear_score / gene_score`
2. 当前波段方向、角色、起点、终值、幅度、时长
3. 当前波段新高/新低数量、密度、最近一次极值
4. 自历史分位 / z-score
5. 同日同方向横截面 rank / percentile

### 2.2 `l3_gene_wave`

补充说明：

1. 当前 schema 已正式补入 `trend_level`
2. 当前 schema 已正式补入 `context_trend_level / context_trend_direction_before / context_trend_direction_after`
3. 当前 schema 已正式补入 `wave_role_basis`
4. 这些字段当前属于“语义诚实化字段”，不是最终多层趋势完整实现

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

### 2.4 `l3_gene_factor_eval`

`G1` 研究表，主键为 `(calc_date, factor_name, sample_scope, direction_scope, forward_horizon_trade_days, bin_label)`。

承载内容：

1. `magnitude / duration / extreme_density` 三个正式子因子
2. 固定 forward horizon 下的解释力分箱
3. `continuation_rate / reversal_rate`
4. `median_forward_return / median_forward_drawdown`
5. `monotonicity_score`

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
8. 在窗口结束日，基于 completed wave 回写一次 `l3_gene_factor_eval`

---

## 4. 当前转折实现

这里必须明确：

1. 当前 `1-2-3` 仍是三段波近似，不是最终三条件语义
2. 当前 `2B` 仍是固定短确认窗近似，不是层级相关时间窗
3. 当前 `MAINSTREAM / COUNTERTREND` 仍是相对于 `INTERMEDIATE_MAJOR_TREND_PROXY` 的近似
4. 当前实现可以运行，但不能假装等同于书义最终版

### 4.1 当前已落盘但仍属 proxy 的语义

当前代码和 schema 已经正式落盘，但仍属于“诚实 proxy”而不是最终语义的字段包括：

1. `trend_level`
   - 当前先固定写为 `INTERMEDIATE`
2. `context_trend_level`
   - 当前先固定写为 `INTERMEDIATE`
3. `context_trend_direction_before / after`
4. `current_context_trend_level / current_context_trend_direction`
5. `wave_role_basis / current_wave_role_basis`
   - 当前口径为 `INTERMEDIATE_MAJOR_TREND_PROXY`

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

### 5.1 `G1` 固定基线口径

`G1` 第一版固定为最小可复跑基线：

1. 因子只允许：
   - `magnitude`
   - `duration`
   - `extreme_density`
2. 样本口径固定为：
   - `SELF_HISTORY_PERCENTILE`
3. 分箱口径固定为：
   - `0-20 / 20-40 / 40-60 / 60-80 / 80-100`
4. forward horizon 第一版固定为：
   - `10` 个交易日
5. 方向统一折算为方向一致收益，避免 `UP / DOWN` 直接混淆

`G1` 的目标不是得到终局结论，而是先得到一把可复跑、可排序、可比较的子因子硬度基线。

---

## 6. 当前非目标

补充冻结：

1. 不假装当前 `1-2-3 / 2B / MAINSTREAM / COUNTERTREND` 语义已经最终完成

---

## 7. Closeout 后整改顺序

如果继续修第四战场，顺序固定为：

1. `GX3 / trend-level context refactor`
2. `GX4 / mainstream-countertrend semantics refactor`
3. `GX5 / 2B window semantics refactor`
4. `GX6 / 1-2-3 three-condition refactor`
5. `GX7 / post-refactor G4-G5-G6 revalidation`

也就是说，后续不是先开新统计卡，而是先把定义层和确认层修到站得住。

第一版明确不做：

1. 行业级 `gene`
2. 指数级 `gene`
3. PB / CPB 交易过滤
4. 与 `IRS / MSS` 的正式融合
5. 多 horizon 并行优化
6. 更复杂的标签联合解释
