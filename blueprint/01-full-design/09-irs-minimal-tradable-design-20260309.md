# IRS Minimal Tradable Design

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `IRS 最小可交易排序层`  
**定位**: `当前主线 IRS 算法正文`  
**上游锚点**:

1. `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`
5. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-algorithm.md`
6. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-data-models.md`
7. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-information-flow.md`
8. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-api.md`
9. `G:\EmotionQuant\EmotionQuant-alpha\docs\design\core-algorithms\irs\irs-algorithm.md`
10. `src/selector/irs.py`
11. `src/strategy/ranker.py`
12. `src/contracts.py`
13. `src/data/store.py`

---

## 1. 用途

本文不是第二份 `IRS-lite contract supplement`。

本文回答的是：

`当前主线 IRS 到底要做到什么程度，才算从 “两因子行业日评分器” 补到 “最小可交易排序层”。`

它冻结 6 件事：

1. 职责
2. 输入
3. 输出
4. 不负责什么
5. 决策规则 / 算法
6. 失败模式与验证证据

一句话说：

`05-contract-supplement` 负责把 IndustryScore、signal attach、skip / fill 边界钉住；本文负责把当前主线 IRS 的算法面写实。`

---

## 2. 当前冻结结论

从本文生效起，当前主线 `IRS` 的最小可交易排序层固定定义为：

```text
industry daily snapshot
-> RS / RV / RT / BD / GN
-> industry total score
-> daily unique rank
-> signal-level irs_score attach
-> rank trace
```

这里的关键点只有 5 条：

1. `IRS` 仍然只做后置行业增强，不回到 `Selector` 前置行业硬过滤。
2. 当前在线因子层固定为 `RS / RV / RT / BD / GN` 五层，不恢复 `IRS-full` 的完整生态。
3. `IndustryScore.score` 和 signal-level `irs_score` 继续明确保持为两个不同分数。
4. `l3_irs_daily` 是行业层主真相源，`irs_industry_trace_exp` 是 signal attach 真相源。
5. `50.0` 只能表示某一层的 fallback / fill，不能混成“IRS 整体今天算出来就是 50”。 

---

## 3. 设计来源与当前代码现实

### 3.1 设计来源

当前对象统一按下面顺序回收：

1. `beta` 四件套提供因子结构、数据模型、信息流和接口表达。
2. `alpha` 算法文提供成熟因子边界和验收口径回看。
3. `gamma` 的 `05-contract-supplement` 提供当前正式契约、signal attach 和 fill 边界。
4. `gamma` 的 implementation / execution 文提供当前主线的实现目标。

### 3.2 当前代码现实

截至 `2026-03-09`，代码现实是：

1. `src/selector/irs.py` 仍只实现 `RS + CF` 两层，并把结果写入 `l3_irs_daily.score / rs_score / cf_score`。
2. 行业层当前缺失 `RV / RT / BD / GN`，也没有正式 `rotation_status`。
3. 基准指数缺失时，当前代码按 `benchmark_pct = 0.0` 兜底。
4. `src/strategy/ranker.py` 当前把行业层 `rank` 线性映射成 signal-level `irs_score`，并没有原样透传 `IndustryScore.score`。
5. `irs_industry_trace_exp` 当前主要记录 signal attach 路径和 fill 原因，不承担完整因子原始值快照。

### 3.3 当前冻结原则

因此本文的角色不是描述“现在代码已经做到什么”，而是冻结：

`P2 实现完成后，IRS 必须对齐到什么设计状态。`

---

## 4. 职责

当前主线 `IRS` 的职责固定为：

1. 计算行业横截面的相对强弱和结构质量。
2. 产出行业层稳定、唯一、可追溯的当日排序。
3. 把行业层排序稳定附着到 signal 层。
4. 为后续排序变化提供可解释的五层来源。
5. 保持行业层 `SKIP`、因子层 `FILL`、signal 层 `FILL` 三类语义分离。

当前主线 `IRS` 不直接回答：

1. 某行业是否应该被前置剔除。
2. 市场是否允许放大或缩小仓位。
3. formal `Signal` 是否触发。
4. 订单应该如何撮合和执行。

---

## 5. 输入

### 5.1 正式上游输入

| 输入对象 | 当前来源 | 用途 |
|---|---|---|
| `l2_industry_daily` | 行业日线聚合表 | 行业层主输入 |
| `l2_industry_structure_daily` | 行业内结构辅助表 | `BD / GN` 结构输入 |
| `l1_index_daily` | 市场基准 | 相对强度参照 |
| `l1_sw_industry_member` | 行业映射 | `industry -> stock -> signal` 连接 |
| 当前配置 | `config.py` | 窗口、权重、阈值、fallback 规则 |

### 5.2 当前主线阶段模型

`IRS` 当前主线固定拆成 7 段：

| 阶段 | 名称 | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `I0` | `snapshot_load` | `l2_industry_daily` | 行业日快照 | 只读正式聚合表 |
| `I1` | `benchmark_attach` | `I0 + l1_index_daily` | 带基准的行业快照 | 基准缺失按规则兜底 |
| `I2` | `structure_attach` | `I1 + l2_industry_structure_daily` | 带结构观测的快照 | 只补结构，不改行业口径 |
| `I3` | `factor_score` | `I2 + history` | `RS / RV / RT / BD / GN` | 五层独立打分 |
| `I4` | `daily_rank` | 五层得分 | `IndustryScore + l3_irs_daily` | 生成唯一日内排序 |
| `I5` | `signal_attach` | `l3_irs_daily + candidate/signal` | signal-level `irs_score` | 只做后置附着 |
| `I6` | `truth_source_write` | `I4 + I5` | `l3_irs_daily + irs_industry_trace_exp` | 行业层和 attach 层分开写 |

### 5.3 最小输入字段

当前主线冻结的最小行业层输入字段为：

| 字段 | 类型 | 必需性 | 用途 |
|---|---|---|---|
| `industry` | `str` | `Required` | 当前正式行业名称 |
| `date` | `date` | `Required` | 交易日 |
| `pct_chg` | `float` | `Required` | 行业 1 日收益 |
| `amount` | `float` | `Required` | 行业成交额 |
| `stock_count` | `int` | `Required` | 行业样本数 |
| `rise_count` | `int` | `Required` | 上涨家数 |
| `fall_count` | `int` | `Required` | 下跌家数 |
| `amount_ma20` | `float` | `Required` | 行业 20 日成交额均值 |
| `return_5d` | `float` | `Required` | 行业 5 日收益 |
| `return_20d` | `float` | `Required` | 行业 20 日收益 |
| `benchmark_pct_chg` | `float` | `Required` | 基准 1 日收益 |
| `benchmark_return_5d` | `float` | `Required` | 基准 5 日收益 |
| `benchmark_return_20d` | `float` | `Required` | 基准 20 日收益 |

### 5.4 结构辅助字段

`BD / GN` 当前主线允许从 `l2_industry_structure_daily` 读取下列最小字段：

| 字段 | 类型 | 必需性 | 用途 |
|---|---|---|---|
| `strong_up_count` | `int` | `Required` | 强上涨家数 |
| `new_high_count` | `int` | `Required` | 行业内创新高家数 |
| `leader_count` | `int` | `Required` | 行业内强股数量 |
| `leader_strength` | `float` | `Required` | 龙头强度归一值，范围 `[0, 1]` |
| `strong_stock_ratio` | `float` | `Required` | 强股占比，范围 `[0, 1]` |
| `strong_stock_amount_share` | `float` | `Required` | 强股成交额占行业成交额比例 |
| `leader_follow_through` | `float` | `Required` | 强股次日延续率，范围 `[0, 1]` |
| `bof_hit_density_5d` | `float` | `Required` | 近 5 日 BOF 命中密度 |

### 5.5 允许的派生观测

在不新增跨模块输入契约的前提下，`IRS` 可以从行业快照内部派生：

1. `market_total_amount`
2. `flow_share`
3. `amount_vs_self_20d`
4. `amount_delta_10d`
5. `up_ratio`
6. `net_breadth`
7. `strong_up_ratio`
8. `new_high_ratio`
9. `rank_stability`
10. `top_rank_streak_5d`
11. `score_slope_5d`
12. `momentum_consistency`

### 5.6 当前配置冻结

当前代码已存在并冻结的配置键：

1. `IRS_TOP_N`
2. `IRS_MIN_INDUSTRIES_PER_DAY`
3. `DTT_SCORE_FILL`
4. `DTT_IRS_WEIGHT`

本轮允许新增但尚未落地的配置键：

1. `IRS_RS_WINDOWS`
2. `IRS_FACTOR_WEIGHTS`
3. `IRS_RT_LOOKBACK_DAYS`
4. `IRS_TOP_RANK_THRESHOLD`
5. `IRS_GN_LEADER_TOP_N`
6. `IRS_BD_STRONG_UP_PCT`

### 5.7 不允许的输入回流

当前主线禁止：

1. 读取 `MSS` 改变行业层评分。
2. 读取账户状态改变行业层评分。
3. 读取未触发 signal 的股票结果改变行业层排序。
4. 用 signal 层分数回写行业层总分。

---

## 6. 输出

### 6.1 正式输出

当前主线 `IRS` 的正式输出仍固定为：

1. `IndustryScore`
2. `l3_irs_daily`
3. signal-level `irs_score`
4. `irs_industry_trace_exp`

### 6.2 解释层输出

当前主线必须补齐但不进入 formal `IndustryScore` 的字段有：

1. `rs_score`
2. `rv_score`
3. `rt_score`
4. `bd_score`
5. `gn_score`
6. `rotation_status`
7. `rotation_slope`
8. `industry_count_today`
9. `attach_status`

### 6.3 输出边界

当前主线固定采用下面三层边界：

| 层 | 当前对象 | 职责 |
|---|---|---|
| formal 层 | `IndustryScore` | 行业层最小正式结果 |
| 行业层真相源 | `l3_irs_daily` | 记录行业总分、分项得分和日内排名 |
| signal attach 真相源 | `irs_industry_trace_exp + l3_signal_rank_exp` | 解释 signal-level `irs_score` 从哪里来、为什么 fill |

### 6.4 兼容期规则

当前存在两个必须显式冻结的兼容期语义：

1. `IndustryScore.score`
2. `Signal.irs_score`

从本文生效起，冻结如下：

1. `IndustryScore.score` 始终表示行业层总分。
2. signal-level `irs_score` 始终表示行业排名映射后的后置增强分。
3. 当前 `l3_irs_daily.cf_score` 只能被视为旧 `IRS-lite` 的历史字段，不得被重新解释成新版 `RV`。
4. 一旦 `RV` 上线，`l3_irs_daily` 必须显式增加 `rv_score`，不能继续让 `cf_score` 语义漂移。

---

## 7. 不负责什么

当前主线 `IRS` 明确不负责：

1. 行业前置过滤
2. 市场仓位覆盖
3. formal `Signal` 生成
4. `Broker` 风控与执行
5. 政策 / 主题 / 事件叙事
6. 自适应学习或在线调参体系

---

## 8. 决策规则 / 算法

### 8.1 在线因子范围与默认权重

当前主线算法面固定为：

1. `RS`
2. `RV`
3. `RT`
4. `BD`
5. `GN`

当前明确不在线恢复：

1. 政策 / 事件 / 主题语义层
2. 完整估值层
3. `allocation_advice / allocation_mode` 的当前主线强输出

当前总分权重冻结为：

```text
industry_total_score =
    0.30 * rs_score
  + 0.25 * rv_score
  + 0.15 * rt_score
  + 0.15 * bd_score
  + 0.15 * gn_score
```

### 8.2 统一归一化规则

当前五层因子统一采用下面规则：

1. 原始观测先按各自语义算出 `raw`
2. 需要跨日或跨行业标准化的量，统一使用 `zscore_single(raw, mean, std)`
3. `zscore_single` 的映射口径固定为 `[-3σ, +3σ] -> [0, 100]`
4. `std = 0`、`NaN` 或 baseline 缺失时，对应分量回退为 `50.0`

换句话说：

`IRS 当前主线继续沿用现有 baseline 思路，但把 baseline 的覆盖范围从 RS/CF 扩到 RS/RV/RT/BD/GN。`

### 8.3 RS：多周期相对强度层

`RS` 回答的是：

`这个行业相对市场到底强不强，而且是短强、中强，还是只是单日噪声。`

当前主线冻结为：

```text
rs_1d_raw  = industry_pct_chg - benchmark_pct_chg
rs_5d_raw  = industry_return_5d - benchmark_return_5d
rs_20d_raw = industry_return_20d - benchmark_return_20d
rank_stability_raw =
  1 - clip(std(rank_hist_5d) / max(industry_count_today / 3, 1), 0, 1)
```

其中：

1. `rank_hist_5d` 为行业近 5 个交易日的历史排名序列
2. 若 `rank_hist_5d` 不足 5 日，则 `rank_stability_raw` 记 `0.5`

`RS` 总分冻结为：

```text
rs_score =
    0.35 * zscore(rs_1d_raw)
  + 0.35 * zscore(rs_5d_raw)
  + 0.20 * zscore(rs_20d_raw)
  + 0.10 * (100 * rank_stability_raw)
```

### 8.4 RV：相对量能层

`RV` 回答的是：

`这个行业的活跃度是不是相对自己和相对全市场都在抬升，而且资金是不是集中到真正会跑的股票上。`

当前主线 `RV` 不再停留在旧 `CF = flow_share + amount_delta_10d`。

当前冻结的最小可交易定义是：

```text
market_total_amount   = sum(amount by date)
flow_share            = amount / max(market_total_amount, eps)
amount_vs_self_20d    = amount / max(amount_ma20, eps)
amount_delta_10d      = amount / max(amount_10d_ago, eps) - 1
strong_amount_share   = strong_stock_amount_share
```

`RV` 总分冻结为：

```text
rv_score =
    0.35 * zscore(amount_vs_self_20d)
  + 0.25 * zscore(flow_share)
  + 0.20 * zscore(amount_delta_10d)
  + 0.20 * (100 * clip(strong_amount_share, 0, 1))
```

这里的边界很明确：

1. `RV` 仍主要以成交额口径表达相对量能，这是为了对齐当前 `l2_industry_daily` 的真实输入现实。
2. 若后续补上行业成交量口径，可以作为 `RV` 的增强项，但本版不把它设为硬依赖。
3. 旧 `CF` 只保留为历史口径，不再作为当前主线的正式命名。

### 8.5 RT：轮动状态层

`RT` 回答的是：

`这个行业现在是刚启动、正在延续、开始衰竭，还是已经回落。`

当前主线固定使用：

```text
top_rank_streak_5d =
  count_consecutive(rank <= IRS_TOP_RANK_THRESHOLD, lookback=5)

score_slope_5d =
  (industry_total_score_t - industry_total_score_t-4) / 4

momentum_consistency =
  positive(score_diff over last 4 intervals) / 4
```

`rotation_status` 当前冻结为 5 个状态：

1. `START`
2. `CONTINUE`
3. `EXHAUST`
4. `FALLBACK`
5. `NEUTRAL`

判定规则冻结为：

1. `START`
   - `rank <= 3`
   - `top_rank_streak_5d in {1, 2}`
   - `score_slope_5d >= 2.0`
2. `CONTINUE`
   - `rank <= 3`
   - `top_rank_streak_5d >= 3`
   - `momentum_consistency >= 0.50`
3. `EXHAUST`
   - `rank <= 5`
   - `score_slope_5d < 0`
   - `momentum_consistency < 0.50`
4. `FALLBACK`
   - `rank > 5`
   - `score_slope_5d <= -2.0`
5. 其他情况为 `NEUTRAL`

`RT` 数值总分冻结为：

```text
rt_core =
  100 * clip(
      0.40 * (top_rank_streak_5d / 5)
    + 0.35 * clip((score_slope_5d + 4) / 8, 0, 1)
    + 0.25 * momentum_consistency,
    0,
    1
  )

status_bonus =
    5   if rotation_status in {"START", "CONTINUE"}
   -5   if rotation_status in {"EXHAUST", "FALLBACK"}
    0   otherwise

rt_score = clip(rt_core + status_bonus, 0, 100)
```

### 8.6 BD：行业扩散度层

`BD` 回答的是：

`这个行业的强，是不是已经从少数龙头扩散到板块内部。`

当前主线冻结的最小可交易定义是：

```text
up_ratio        = rise_count / max(stock_count, 1)
net_breadth     = (rise_count - fall_count) / max(stock_count, 1)
strong_up_ratio = strong_up_count / max(stock_count, 1)
new_high_ratio  = new_high_count / max(stock_count, 1)
bof_density     = clip(bof_hit_density_5d * 5, 0, 1)
```

`BD` 总分冻结为：

```text
bd_score =
  100 * clip(
      0.30 * up_ratio
    + 0.25 * ((net_breadth + 1) / 2)
    + 0.20 * strong_up_ratio
    + 0.15 * new_high_ratio
    + 0.10 * bof_density,
    0,
    1
  )
```

其中：

1. `strong_up_count` 的阈值由 `IRS_BD_STRONG_UP_PCT` 定义
2. `bof_hit_density_5d` 是行业内近 5 日 BOF 命中数量除以 `stock_count * 5`
3. `BD` 不读取 `PAS` 的内部特征，只允许读取已经聚合好的密度结果

### 8.7 GN：牛股基因轻量层

`GN` 回答的是：

`这个行业内部是不是已经长出了会持续跑出来的强股结构。`

当前主线 `GN` 只做轻量层，不恢复完整基因库。

当前冻结为：

```text
leader_count_ratio      = leader_count / max(stock_count, 1)
leader_strength_norm    = clip(leader_strength, 0, 1)
leader_follow_norm      = clip(leader_follow_through, 0, 1)
strong_stock_ratio_norm = clip(strong_stock_ratio, 0, 1)
```

`GN` 总分冻结为：

```text
gn_score =
  100 * clip(
      0.35 * leader_strength_norm
    + 0.25 * leader_count_ratio
    + 0.20 * leader_follow_norm
    + 0.20 * strong_stock_ratio_norm,
    0,
    1
  )
```

这里的关键裁剪是：

1. `GN` 只读取行业内部结构派生结果，不引入政策、主题、事件叙事。
2. `GN` 当前只做轻量排序增强，不回写成正式 `allocation_advice`。
3. `GN` 的强股判定必须来自当前主线已存在的结构结果，而不是额外引入另一套选股系统。

### 8.8 日内排序与唯一排名

当前主线行业层排序冻结为：

1. 先按 `industry_total_score` 降序
2. 若分数相同，按 `industry` 升序打平
3. `rank` 必须唯一且连续，范围 `1..N`

也就是说：

`当前主线不允许“并列第 1 名”这种输出。`

### 8.9 Signal attach 规则

当前主线 signal attach 继续保持 `05-contract-supplement` 已冻结的双层分数规则。

当日行业数为 `N` 时：

```text
signal_irs_score =
  100 * (1 - (rank - 1) / (N - 1))    if N > 1
  100                                 if N = 1
```

Signal attach 状态冻结为：

1. `NORMAL`
2. `DISABLED`
3. `FILL_UNKNOWN_INDUSTRY`
4. `FILL_NO_DAILY_SCORE`

对应规则冻结为：

1. 变体不使用 `IRS` 时，`signal_irs_score = DTT_SCORE_FILL`，状态为 `DISABLED`
2. `industry == 未知` 时，`signal_irs_score = DTT_SCORE_FILL`，状态为 `FILL_UNKNOWN_INDUSTRY`
3. 匹配不到当日行业层结果时，`signal_irs_score = DTT_SCORE_FILL`，状态为 `FILL_NO_DAILY_SCORE`
4. 只有匹配到 `l3_irs_daily` 的行业层排名时，才允许输出 `NORMAL`

### 8.10 行业层分数和 signal 层分数的关系

当前主线明确规定：

1. 行业层 `IndustryScore.score` 由五层因子直接决定。
2. signal-level `irs_score` 由行业排名线性映射决定。
3. signal 层不原样透传行业层总分。
4. 任何解释都必须明确自己说的是“行业层总分”还是“signal 层附着分”。

---

## 9. 失败模式与降级规则

### 9.1 行业层 `SKIP`

下面这些情况属于行业层 `SKIP`：

1. `l2_industry_daily` 当日无数据
2. 过滤掉 `未知` 后当日行业为空
3. 当日行业数 `< IRS_MIN_INDUSTRIES_PER_DAY`

这三种情况统一表现为：

`当日不写 l3_irs_daily`

### 9.2 因子层 `FILL`

下面这些情况属于因子层 `FILL`：

1. 基准收益缺失
   - `benchmark_pct_chg / benchmark_return_5d / benchmark_return_20d` 缺失时按 `0.0` 处理
2. baseline 缺失或 `std = 0`
   - 对应因子分量记 `50.0`
3. `amount_ma20` 或 `amount_10d_ago` 不足
   - 对应 `RV` 分量记 `50.0`
4. `rank_hist_5d` 或 `score_hist_5d` 不足
   - `RS.rank_stability` 或 `RT` 对应分量记 `50.0`
5. `l2_industry_structure_daily` 缺失
   - `BD / GN` 记 `50.0`

### 9.3 Signal 层 `FILL`

下面这些情况属于 signal 层 `FILL`：

1. `industry == 未知`
2. 当日匹配不到行业层结果
3. 当前变体不使用 `IRS`

统一处理为：

`signal_irs_score = DTT_SCORE_FILL`

### 9.4 当前必须显式区分的失败原因

当前主线至少必须显式记录：

1. `DAY_SKIP_NO_INDUSTRY_DATA`
2. `DAY_SKIP_BELOW_MIN_INDUSTRIES`
3. `BENCHMARK_FILL_ZERO`
4. `FACTOR_FILL_NEUTRAL`
5. `ATTACH_FILL_UNKNOWN_INDUSTRY`
6. `ATTACH_FILL_NO_DAILY_SCORE`

### 9.5 不允许的降级

下面这些做法全部禁止：

1. 用 signal 层 `50.0` 掩盖行业层整天根本没算出来。
2. 为了凑出更多排名，放宽行业数不足时的 `SKIP` 规则。
3. 因为当前 schema 只有 `cf_score`，就继续把 `rv_score` 留在口头上。
4. 因为排序要快推进，就把 `IRS` 拉回前置行业硬过滤。

---

## 10. 验证证据

当前主线 `IRS` 最低必须产出下面 3 组证据：

1. `IRS-lite`
2. `IRS-RSRV`
3. `IRS-RSRVRTBDGN`

每组至少比较：

1. `trade_count`
2. `EV`
3. `PF`
4. `MDD`
5. `rank_diff_days`
6. `execution_diff_days`

当前还必须能解释：

1. 排序变化主要来自 `RS / RV / RT / BD / GN` 哪一层
2. `50.0` 到底发生在行业层、因子层，还是 signal attach 层
3. 哪些票因为行业排名映射变化被推上去或压下去

---

## 11. 当前实现映射与对齐要求

### 11.1 当前已落地

当前代码已与本文一致的部分：

1. `IndustryScore` formal 最小契约
2. `l3_irs_daily` 的行业层日内唯一排名
3. 基准缺失时按 `0.0` 兜底
4. signal-level `irs_score` 由行业 `rank` 线性映射
5. `irs_industry_trace_exp` 已能记录 attach 正常与 fill 原因

### 11.2 当前必须对齐

P2 实现时，必须按本文完成：

1. 扩 `l2_industry_daily`
   - `amount_ma20`
   - `return_5d`
   - `return_20d`
2. 新增 `l2_industry_structure_daily`
   - `strong_up_count`
   - `new_high_count`
   - `leader_count`
   - `leader_strength`
   - `strong_stock_ratio`
   - `strong_stock_amount_share`
   - `leader_follow_through`
   - `bof_hit_density_5d`
3. 重写 `src/selector/irs.py`
   - 从 `RS + CF` 升级为 `RS + RV + RT + BD + GN`
4. 扩 `l3_irs_daily`
   - `rv_score`
   - `rt_score`
   - `bd_score`
   - `gn_score`
   - `rotation_status`
   - `rotation_slope`
5. 保持 `src/strategy/ranker.py` 的 attach 分层
   - 继续使用 rank 映射
   - 不改成原样透传行业层总分
6. 补齐单测和专项消融

### 11.3 当前不允许的实现回退

实现层不允许：

1. 因为代码里现在只有 `RS + CF`，就把本文重新压回“IRS-lite”。
2. 因为当前 `l3_irs_daily` 只有 `cf_score`，就继续让 `RV` 没有正式落点。
3. 因为排序层要快推进，就把 `IRS` 改写成行业 Top-N 前置过滤。
4. 因为 signal 层已经有 `irs_score`，就把行业层总分和 signal 层附着分混成一个数。

---

## 12. 冻结结语

从本文生效起，当前主线 `IRS` 的完成标准不再是：

`能算出 l3_irs_daily.score`

而是：

`能把 RS + RV + RT + BD + GN 作为一个清晰分层、可解释、可附着、可消融的行业排序层跑起来。`

只要这 5 层里还缺任何一层，或者行业层总分与 signal 层附着分仍然混写，当前 `IRS` 就仍然只是 `IRS-lite`，不算达到本版本的最小可交易强度。
