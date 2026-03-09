# MSS Minimal Tradable Design

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `MSS 最小可交易风控层`  
**定位**: `当前主线 MSS 算法正文`  
**上游锚点**:

1. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`
5. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-algorithm.md`
6. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-data-models.md`
7. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-information-flow.md`
8. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-api.md`
9. `G:\EmotionQuant\EmotionQuant-alpha\docs\design\core-algorithms\mss\mss-algorithm.md`
10. `src/selector/mss.py`
11. `src/broker/risk.py`
12. `src/strategy/ranker.py`
13. `src/contracts.py`

---

## 1. 用途

本文不是第二份 `MSS-lite contract annex`。

本文回答的是：

`当前主线 MSS 到底要做到什么程度，才算从 “只有六因子分数 + 三态 overlay” 补到 “最小可交易风控层”。`

它冻结 6 件事：

1. 职责
2. 输入
3. 输出
4. 不负责什么
5. 决策规则 / 算法
6. 失败模式与验证证据

一句话说：

`06-contract-supplement` 负责把 MarketScore、overlay 和 fill 边界钉住；本文负责把当前主线 MSS 的状态层和风控映射面写实。`

---

## 2. 当前冻结结论

从本文生效起，当前主线 `MSS` 的最小可交易风控层固定定义为：

```text
market snapshot
-> six-factor raw components
-> normalized factor scores + aggregate score
-> phase / phase_trend / phase_days
-> position_advice / risk_regime
-> overlay
-> Broker capacity apply
```

这里的关键点只有 6 条：

1. `MSS` 仍然只做市场级风险调节，不回到 `Selector` 前置 gate。
2. 当前在线因子层继续沿用现有六因子和现有聚合权重，不重写 raw 公式。
3. `MarketScore.signal` 继续保留为 `BULLISH / NEUTRAL / BEARISH` 的兼容三态。
4. 当前主线必须补回 `phase / phase_trend / phase_days / position_advice / risk_regime`，但这些字段先落在 `l3_mss_daily / trace / overlay`，不反向污染 `final_score`。
5. `risk_regime` 才是 `Broker / Risk` 的长期稳定消费面，`mss_score` 继续只承担解释位。
6. 高分市场不等于放大风险，`CLIMAX` 必须允许落入 `RISK_OFF`。

---

## 3. 设计来源与当前代码现实

### 3.1 设计来源

当前对象统一按下面顺序回收：

1. `beta` 四件套提供六因子结构、市场快照、信息流和接口表达。
2. `alpha` 算法文提供状态层、仓位建议和验收口径回看。
3. `gamma` 的 `06-contract-supplement` 提供当前正式契约、overlay 和 fill 边界。
4. `gamma` 的 implementation / execution 文提供当前主线的实现目标。

### 3.2 当前代码现实

截至 `2026-03-09`，代码现实是：

1. `src/selector/mss.py` 已落地六因子 raw 计算、`MSS_BASELINE` 标准化、总分聚合和 `BULLISH / NEUTRAL / BEARISH` 三态。
2. `src/contracts.py` 中 `MarketScore` 仍只有 `date / score / signal` 三个正式字段。
3. `src/strategy/ranker.py` 当前只把 `mss_score` 写入 `l3_signal_rank_exp` 解释位，不把它并入 `final_score`。
4. `src/broker/risk.py` 当前按 `signal -> multiplier` 解析 `MssRiskOverlay`，并正确区分 `DISABLED / MISSING / NORMAL` 三种 overlay 状态。
5. 当前代码还没有正式落 `phase / phase_trend / phase_days / position_advice / risk_regime`。

### 3.3 当前冻结原则

因此本文的角色不是描述“现在代码已经做到什么”，而是冻结：

`P3 实现完成后，MSS 必须对齐到什么设计状态。`

---

## 4. 职责

当前主线 `MSS` 的职责固定为：

1. 计算市场级风险温度。
2. 识别当前市场所处阶段及其方向。
3. 把市场阶段稳定映射成 `position_advice` 和 `risk_regime`。
4. 让 `Broker / Risk` 读取统一 overlay 并据此缩放容量。
5. 为执行容量变化提供可追溯的市场层真相源。

当前主线 `MSS` 不直接回答：

1. 个股是否触发形态。
2. 行业应该排第几。
3. `final_score` 应该怎么合成。
4. 订单应该如何撮合和成交。

---

## 5. 输入

### 5.1 正式上游输入

| 输入对象 | 当前来源 | 用途 |
|---|---|---|
| `l2_market_snapshot` | 市场聚合快照表 | 六因子和状态层主输入 |
| `l3_mss_daily` 历史行 | 市场历史结果表 | `phase_trend / phase_days` 跨日状态输入 |
| 当前配置 | `config.py` | 阈值、倍率、baseline、variant 边界 |
| 交易日上下文 | `signal_date / next_trade_date` 等 | overlay 和执行时序连接 |

### 5.2 当前主线阶段模型

`MSS` 当前主线固定拆成 8 段：

| 阶段 | 名称 | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `M0` | `snapshot_load` | `l2_market_snapshot` | 当日市场快照 | 只读正式聚合表 |
| `M1` | `raw_factor_calc` | `M0` | 6 个 raw 因子 | 分母为 `0` 时按安全除法回落 |
| `M2` | `factor_normalize` | `M1 + MSS_BASELINE` | 6 个标准化因子分 | `std` 失效时该因子记 `50.0` |
| `M3` | `score_materialize` | `M2` | `MarketScore + l3_mss_daily.score` | 当前正式市场分 |
| `M4` | `phase_detect` | `M3 + score_hist` | `phase / phase_trend / phase_days` | 当前主线新增状态层 |
| `M5` | `regime_resolve` | `M4` | `position_advice / risk_regime` | 解释层到执行层的桥 |
| `M6` | `overlay_resolve` | `M5 + config + signal_date` | `MssRiskOverlay` | 当前 Broker 稳定入口 |
| `M7` | `broker_apply` | `M6 + BrokerRiskState + Signal` | 实际仓位上限 / 订单或拒绝 | 最终执行容量变化 |

### 5.3 最小市场快照字段

当前主线冻结的最小输入字段为：

| 字段 | 类型 | 必需性 | 用途 |
|---|---|---|---|
| `date` | `date` | `Required` | 交易日 |
| `total_stocks` | `int` | `Required` | 全市场样本数 |
| `rise_count` | `int` | `Required` | 上涨家数 |
| `fall_count` | `int` | `Required` | 下跌家数 |
| `strong_up_count` | `int` | `Required` | 强上涨家数 |
| `strong_down_count` | `int` | `Required` | 强下跌家数 |
| `limit_up_count` | `int` | `Required` | 涨停家数 |
| `limit_down_count` | `int` | `Required` | 跌停家数 |
| `touched_limit_up_count` | `int` | `Required` | 触板家数 |
| `new_100d_high_count` | `int` | `Required` | 100 日新高家数 |
| `new_100d_low_count` | `int` | `Required` | 100 日新低家数 |
| `continuous_limit_up_2d` | `int` | `Required` | 连续 2 板家数 |
| `continuous_limit_up_3d_plus` | `int` | `Required` | 连续 3 板及以上家数 |
| `continuous_new_high_2d_plus` | `int` | `Required` | 连续 2 日及以上新高家数 |
| `high_open_low_close_count` | `int` | `Required` | 高开低走极端行为家数 |
| `low_open_high_close_count` | `int` | `Required` | 低开高走极端行为家数 |
| `pct_chg_std` | `float` | `Required` | 市场涨跌幅标准差 |
| `amount_volatility` | `float` | `Required` | 市场成交额波动率 |

### 5.4 状态层历史输入

`phase_trend / phase_days` 允许读取下列最小历史字段：

1. `score_hist_3d`
2. `score_hist_8d`
3. `score_hist_20d`
4. `prev_phase`
5. `prev_phase_days`

这里的边界是：

1. 历史输入只允许来自 `MSS` 自己的历史结果，不允许从 `Selector / IRS / Broker` 倒灌。
2. 若历史窗口不足，则按 `cold start` 规则降级，不允许直接复用上一交易日完整结论。

### 5.5 当前配置冻结

当前代码已存在并冻结的配置键：

1. `MSS_VARIANT`
2. `MSS_GATE_MODE`
3. `MSS_BULLISH_THRESHOLD`
4. `MSS_BEARISH_THRESHOLD`
5. `MSS_SOFT_GATE_CANDIDATE_TOP_N`
6. `MSS_RISK_OVERLAY_VARIANT`
7. `MSS_BULLISH_MAX_POSITIONS_MULT`
8. `MSS_NEUTRAL_MAX_POSITIONS_MULT`
9. `MSS_BEARISH_MAX_POSITIONS_MULT`
10. `MSS_BULLISH_RISK_PER_TRADE_MULT`
11. `MSS_NEUTRAL_RISK_PER_TRADE_MULT`
12. `MSS_BEARISH_RISK_PER_TRADE_MULT`
13. `MSS_BULLISH_MAX_POSITION_MULT`
14. `MSS_NEUTRAL_MAX_POSITION_MULT`
15. `MSS_BEARISH_MAX_POSITION_MULT`

本轮允许新增但尚未落地的配置键：

1. `MSS_PHASE_THRESHOLD_MODE`
2. `MSS_PHASE_THRESHOLDS`
3. `MSS_TREND_SHORT_EMA`
4. `MSS_TREND_LONG_EMA`
5. `MSS_TREND_LOOKBACK_DAYS`
6. `MSS_REGIME_MULTIPLIERS`

### 5.6 不允许的输入回流

当前主线禁止：

1. 读取 `Selector` 候选结果改变市场状态。
2. 读取 `IRS` 或 `PAS` 内部特征改变市场状态。
3. 读取 Broker 当前持仓反向影响 `MarketScore`。
4. 用上一交易日 `phase / risk_regime` 顶替当日正式结果。

---

## 6. 输出

### 6.1 正式输出

当前主线 `MSS` 的正式输出仍固定为：

1. `MarketScore`
2. `l3_mss_daily`
3. `MssRiskOverlay`
4. `mss_risk_overlay_trace_exp`

### 6.2 解释层输出

当前主线必须补齐但不进入 `MarketScore` 的字段有：

1. `phase`
2. `phase_trend`
3. `phase_days`
4. `position_advice`
5. `risk_regime`
6. `trend_quality`

### 6.3 输出边界

当前主线固定采用下面三层边界：

| 层 | 当前对象 | 职责 |
|---|---|---|
| formal 层 | `MarketScore` | 市场层最小正式结果 |
| 市场层真相源 | `l3_mss_daily` | 记录市场总分、分项得分和状态层结果 |
| 执行真相源 | `MssRiskOverlay + mss_risk_overlay_trace_exp` | 解释为什么容量变化、为什么 fallback |

### 6.4 兼容期规则

当前存在 3 个必须显式冻结的兼容期语义：

1. `MarketScore.signal`
2. `l3_signal_rank_exp.mss_score`
3. `risk_regime`

从本文生效起，冻结如下：

1. `MarketScore.signal` 始终表示 `score` 推导出来的兼容三态。
2. `l3_signal_rank_exp.mss_score` 始终只表示 signal 侧附着市场分，服务解释和对照，不进入 `final_score`。
3. `risk_regime` 才是 `Broker / Risk` 的长期正式消费面。
4. 在兼容期内，若 `risk_regime` 还未正式落到 schema，允许在 `Broker / Risk` 内由 `phase + phase_trend + score` 解析，但不允许把它重新等同为 `signal`。

---

## 7. 不负责什么

当前主线 `MSS` 明确不负责：

1. 个股形态触发。
2. 行业横截面排序。
3. `final_score` 合成。
4. 前置候选漏斗裁剪。
5. 卖出状态机和撮合细节。
6. 政策 / 主题 / 新闻语义。

---

## 8. 决策规则 / 算法

### 8.1 在线算法范围

当前主线算法面固定为：

1. 六因子市场分
2. `phase`
3. `phase_trend`
4. `phase_days`
5. `position_advice`
6. `risk_regime`

当前明确不在线恢复：

1. `Selector` 前置 `MSS gate`
2. 把 `MSS` 写入 `final_score`
3. 完整自适应周期模型
4. 政策 / 事件 / 新闻解释层

### 8.2 六因子 raw 公式与聚合口径

当前六因子 raw 公式继续沿用 `src/selector/mss.py`，正式冻结为：

```text
market_coefficient_raw = rise_count / total_stocks

profit_effect_raw =
    0.4 * limit_up_ratio
  + 0.3 * new_high_ratio
  + 0.3 * strong_up_ratio

broken_rate = touched_limit_up_count / limit_up_count

loss_effect_raw =
    0.3 * broken_rate
  + 0.2 * limit_down_ratio
  + 0.3 * strong_down_ratio
  + 0.2 * new_low_ratio

cont_limit_up_ratio =
  (continuous_limit_up_2d + continuous_limit_up_3d_plus) / limit_up_count

cont_new_high_ratio =
  continuous_new_high_2d_plus / new_100d_high_count

continuity_raw =
    0.5 * cont_limit_up_ratio
  + 0.5 * cont_new_high_ratio

extreme_raw =
    panic_tail_ratio
  + squeeze_tail_ratio

amount_vol_ratio =
  amount_volatility / (amount_volatility + 1_000_000)

volatility_raw =
    0.5 * pct_chg_std
  + 0.5 * amount_vol_ratio
```

其中：

1. `safe_ratio(..., default=0.0)` 是当前正式安全除法口径。
2. `panic_tail_ratio = high_open_low_close_count / total_stocks`
3. `squeeze_tail_ratio = low_open_high_close_count / total_stocks`
4. `amount_volatility <= 0` 时，`amount_vol_ratio = 0.0`

当前标准化继续统一采用 `MSS_BASELINE + zscore_single()`：

```text
factor_score = clip((z + 3) / 6 * 100, 0, 100)
```

若 `std == 0`、`NaN` 或 baseline 缺失：

```text
factor_score = 50.0
```

当前总分公式冻结为：

```text
market_score =
    0.17 * market_coefficient
  + 0.34 * profit_effect
  + 0.34 * (100 - loss_effect)
  + 0.05 * continuity
  + 0.05 * extreme
  + 0.05 * (100 - volatility)
```

### 8.3 MarketScore.signal 兼容三态

当前兼容三态继续沿用现有阈值：

1. `score >= 65` -> `BULLISH`
2. `score <= 35` -> `BEARISH`
3. 其余 -> `NEUTRAL`

这里必须明确：

`signal` 只是兼容三态，不等于状态层结论，更不等于最终风险开关。`

### 8.4 phase_trend：阶段方向

`phase_trend` 回答的是：

`市场分现在是在上行、下行，还是横摆。`

当前主线优先采用 `8` 日趋势窗：

```text
ema_short = EMA(score_hist_8d, span=3)
ema_long  = EMA(score_hist_8d, span=8)
slope_5d  = (score_t - score_t-4) / 4
trend_band = max(0.8, 0.15 * std(score_hist_20d))
```

判定规则冻结为：

1. `UP`
   - `ema_short > ema_long`
   - 且 `slope_5d >= trend_band`
2. `DOWN`
   - `ema_short < ema_long`
   - 且 `slope_5d <= -trend_band`
3. 其余为 `SIDEWAYS`

若有效历史不足 `8` 个交易日，则进入 `cold start` 降级：

1. 最近 `3` 个交易日市场分严格递增 -> `UP`
2. 最近 `3` 个交易日市场分严格递减 -> `DOWN`
3. 其余 -> `SIDEWAYS`

此时：

1. `trend_quality = COLD_START`
2. 历史足够时 `trend_quality = NORMAL`

### 8.5 phase：市场阶段

`phase` 回答的是：

`当前市场正处于启动、发酵、加速、分歧、高潮、扩散回落，还是衰退。`

当前最小可交易版本不使用自适应分位数，固定阈值冻结为：

1. `T30 = 30`
2. `T45 = 45`
3. `T60 = 60`
4. `T75 = 75`

状态集合固定为：

1. `EMERGENCE`
2. `FERMENTATION`
3. `ACCELERATION`
4. `DIVERGENCE`
5. `CLIMAX`
6. `DIFFUSION`
7. `RECESSION`
8. `UNKNOWN`

判定规则冻结为：

1. `score >= 75` -> `CLIMAX`
2. 当 `phase_trend = UP` 时：
   - `score < 30` -> `EMERGENCE`
   - `30 <= score < 45` -> `FERMENTATION`
   - `45 <= score < 60` -> `ACCELERATION`
   - `60 <= score < 75` -> `DIVERGENCE`
3. 当 `phase_trend = SIDEWAYS` 时：
   - `score >= 60` -> `DIVERGENCE`
   - 其余 -> `RECESSION`
4. 当 `phase_trend = DOWN` 时：
   - `score >= 60` -> `DIFFUSION`
   - 其余 -> `RECESSION`
5. 无法完成判定时 -> `UNKNOWN`

这里的设计意图很明确：

1. 低分上行市场允许识别成 `EMERGENCE / FERMENTATION`，因为它们代表的是“风险开始回暖”，不是“已经很强”。
2. 高分市场默认先落 `CLIMAX`，优先体现“高位风险”。
3. `DIVERGENCE` 和 `DIFFUSION` 都不是强看多状态，它们只是风险开始分化的两种不同形态。

### 8.6 phase_days：阶段持续天数

`phase_days` 固定按连续计数规则计算：

1. 若无前一交易日状态 -> `1`
2. 若 `prev_phase == current_phase` 且 `prev_phase_days` 有效 -> `prev_phase_days + 1`
3. 其余 -> `1`

这里不允许：

1. 直接用自然日计数
2. 因为缺一天历史就把前值强行延续

### 8.7 position_advice：解释层仓位建议

`position_advice` 是解释层，不直接替代正式风险倍率。

当前固定采用区间建议：

| phase | position_advice |
|---|---|
| `EMERGENCE` | `80%-100%` |
| `FERMENTATION` | `60%-80%` |
| `ACCELERATION` | `50%-70%` |
| `DIVERGENCE` | `40%-60%` |
| `CLIMAX` | `20%-40%` |
| `DIFFUSION` | `30%-50%` |
| `RECESSION` | `0%-20%` |
| `UNKNOWN` | `0%-20%` |

这里的边界是：

1. `position_advice` 用来解释“为什么容量应该收缩或放大到这个区间”。
2. 它不是当前 Broker 直接消费的正式倍率字段。

### 8.8 risk_regime：Broker 风险状态

`risk_regime` 回答的是：

`Broker 今天应该按风险开启、中性，还是关闭来执行。`

当前主线固定为三态：

1. `RISK_ON`
2. `RISK_NEUTRAL`
3. `RISK_OFF`

判定规则冻结为：

1. `RISK_ON`
   - `phase in {EMERGENCE, FERMENTATION, ACCELERATION}`
   - 且 `phase_trend = UP`
2. `RISK_NEUTRAL`
   - `phase in {DIVERGENCE, DIFFUSION}`
   - 或 `phase = ACCELERATION` 但 `phase_trend != UP`
3. `RISK_OFF`
   - `phase in {CLIMAX, RECESSION, UNKNOWN}`

这个映射必须保留一个关键现实：

`高分并不自动等于 RISK_ON；高位高潮市场必须允许直接落入 RISK_OFF。`

### 8.9 risk_regime -> overlay 映射

当前最小可交易版本先冻结一个稳定映射面：

| risk_regime | `max_positions_mult` | `risk_per_trade_mult` | `max_position_mult` |
|---|---|---|---|
| `RISK_ON` | `1.0` | `1.0` | `1.0` |
| `RISK_NEUTRAL` | `0.7` | `0.7` | `0.7` |
| `RISK_OFF` | `0.4` | `0.4` | `0.4` |

在兼容期内，当前配置继续映射到现有三组配置键：

1. `RISK_ON -> MSS_BULLISH_*`
2. `RISK_NEUTRAL -> MSS_NEUTRAL_*`
3. `RISK_OFF -> MSS_BEARISH_*`

当前 `MssRiskOverlay` 还保留：

1. `state = DISABLED / MISSING / NORMAL`
2. `signal = BULLISH / NEUTRAL / BEARISH`
3. `score = market_score`

但从本文生效起，长期演进方向固定为：

`signal` 负责兼容，`risk_regime` 负责正式风险倍率。`

### 8.10 MarketScore、sidecar 和 overlay 的关系

当前主线必须显式区分下面 3 个对象：

1. `MarketScore / l3_mss_daily`
2. `l3_signal_rank_exp.mss_score`
3. `MssRiskOverlay`

冻结规则如下：

1. `MarketScore` 记录市场层正式结果。
2. `l3_signal_rank_exp.mss_score` 继续只服务解释和对照，不进入 `final_score`。
3. `MssRiskOverlay` 才是真正控制执行容量的对象。
4. `risk_regime` 落地后，Broker 必须以 `risk_regime` 而不是 `mss_score` 驱动倍率。

---

## 9. 失败模式与降级规则

### 9.1 市场层 `SKIP`

下面这些情况属于市场层 `SKIP`：

1. `l2_market_snapshot` 当日无数据
2. 批量区间内没有任何市场快照

统一表现为：

`当日不写 l3_mss_daily`

### 9.2 因子层 `FILL`

下面这些情况属于因子层 `FILL`：

1. 分母为 `0` 或字段缺失
   - 统一走 `safe_ratio(..., default=0.0)`
2. 计数字段或波动字段为空
   - 按 `0 / 0.0` 进入 raw 计算
3. baseline 缺失、`std == 0` 或 `NaN`
   - 对应因子得分记 `50.0`
4. 聚合后分数超界
   - `clip` 到 `0-100`

### 9.3 状态层 `FILL`

下面这些情况属于状态层 `FILL`：

1. 历史不足 `8` 个交易日
   - `phase_trend` 进入 `cold start`
   - `trend_quality = COLD_START`
2. 前一交易日状态缺失
   - `phase_days = 1`
3. 状态层无法可靠判定
   - `phase = UNKNOWN`
   - `risk_regime = RISK_OFF`

### 9.4 Overlay 层 `FILL`

下面这些情况属于 overlay 层 `FILL`：

1. `mss_risk_overlay_enabled = False`
   - `state = DISABLED`
   - `signal = NEUTRAL`
   - `score = DTT_SCORE_FILL`
   - 执行参数回到基础配置，不乘三态倍率
2. 当日 `l3_mss_daily` 缺失
   - `state = MISSING`
   - `signal = NEUTRAL`
   - `score = DTT_SCORE_FILL`
   - `risk_regime = RISK_NEUTRAL`
3. `signal` 标签非法
   - 强制归一到 `NEUTRAL`
4. `risk_regime` 未正式落库
   - 允许由 `phase + phase_trend + score` 现场解析

### 9.5 Broker 硬失败

下面这些情况属于当前硬失败：

1. `NO_NEXT_TRADE_DAY`
2. `ALREADY_HOLDING`
3. `MAX_POSITIONS_REACHED`
4. `NO_EST_PRICE`
5. `INSUFFICIENT_CASH`
6. `SIZE_BELOW_MIN_LOT`

### 9.6 当前必须显式记录的原因

当前主线至少必须显式记录：

1. `SNAPSHOT_MISSING`
2. `FACTOR_FILL_NEUTRAL`
3. `TREND_COLD_START`
4. `OVERLAY_DISABLED`
5. `OVERLAY_MISSING`
6. `BROKER_CAPACITY_REJECT`

### 9.7 不允许的降级

下面这些做法全部禁止：

1. 用 `mss_score = 50.0` 掩盖当日市场层根本没算出来。
2. 用上一交易日 `phase / risk_regime` 顶替当日正式结果。
3. 因为 schema 还没迁移，就把 `risk_regime` 继续停留在口头上。
4. 因为排序要快推进，就把 `MSS` 拉回 `Selector` 前置 gate。
5. 把 `mss_score` 写回 `final_score`。

---

## 10. 验证证据

当前主线 `MSS` 最低必须产出下面 4 组证据：

1. 六因子基础分布
2. `phase / position_advice / risk_regime` 分布
3. `overlay = DISABLED / MISSING / NORMAL` 三条路径对照
4. 不同 `risk_regime` 下的 `EV / PF / MDD`

每组至少比较：

1. `trade_count`
2. `EV`
3. `PF`
4. `MDD`
5. `avg_position_count`
6. `avg_position_size`

当前还必须能解释：

1. 容量变化来自真实状态变化，还是 fallback 路径。
2. `MarketScore.signal` 和 `risk_regime` 为什么不是一回事。
3. 哪些天是高分但必须降到 `RISK_OFF` 的 `CLIMAX`。

---

## 11. 当前实现映射与对齐要求

### 11.1 当前已落地

当前代码已与本文一致的部分：

1. 六因子 raw 公式和标准化框架。
2. `MarketScore` formal 最小契约。
3. `l3_mss_daily.score / signal + 6 个标准化因子分`。
4. `l3_signal_rank_exp.mss_score` 只做解释位。
5. `MssRiskOverlay` 的 `DISABLED / MISSING / NORMAL` 三态和容量缩放逻辑。
6. Broker 侧不把 `MSS` 写回 `final_score`。

### 11.2 当前必须对齐

P3 实现时，必须按本文完成：

1. 扩 `l3_mss_daily`
   - `phase`
   - `phase_trend`
   - `phase_days`
   - `position_advice`
   - `risk_regime`
   - `trend_quality`
2. 扩 `mss_risk_overlay_trace_exp`
   - 补齐状态层字段和 fallback 原因
3. 升级 `src/selector/mss.py`
   - 在现有六因子之上补 `phase_detect / regime_resolve`
4. 升级 `src/broker/risk.py`
   - 从“按 `signal` 选倍率”过渡到“按 `risk_regime` 选倍率”
   - 保留 `signal` 兼容字段
5. 保持 `src/strategy/ranker.py`
   - 继续只写 `mss_score` sidecar
   - 不把 `MSS` 并入 `final_score`
6. 补齐单测和专项消融

### 11.3 当前不允许的实现回退

实现层不允许：

1. 因为代码里现在只有六因子分数，就把本文重新压回 `MSS-lite`。
2. 因为当前 `MarketScore` 只有三字段，就不落状态层。
3. 因为 `mss_score` 已经在 rank sidecar 里，就把它误当正式风险开关。
4. 因为想快推进执行，就把 `MSS` 写回 `final_score` 或拉回前置 gate。

---

## 12. 冻结结语

从本文生效起，当前主线 `MSS` 的完成标准不再是：

`能算出 l3_mss_daily.score 并缩一刀仓位`

而是：

`能把六因子市场分 + phase / trend / regime 作为一个清晰分层、可追溯、可消融、可直接驱动 Broker 容量的市场风控层跑起来。`

只要状态层、`risk_regime` 或执行归因仍缺任何一块，当前 `MSS` 就仍然只是 `MSS-lite`，不算达到本版本的最小可交易强度。
