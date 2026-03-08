# MSS-lite Contract Supplement

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `MSS-lite`  
**上游锚点**:

1. `docs/design-v2/02-modules/broker-design.md`
2. `blueprint/01-full-design/02-mainline-design-atom-gap-checklist-20260308.md`
3. `src/contracts.py`
4. `src/selector/mss.py`
5. `src/broker/risk.py`
6. `src/strategy/ranker.py`
7. `src/config.py`

---

## 1. 用途

本文只补 `MSS-lite` 当前主线缺失的契约原子。

它不重写 `MSS-lite` 的主线职责，只冻结 6 件事：

1. `MSS-lite` 的最小市场快照
2. 市场层正式 `MarketScore` 契约
3. `l3_mss_daily / l3_signal_rank_exp.mss_score / MssRiskOverlay` 的边界
4. `signal -> risk overlay` 的固定映射面
5. `skip / fill / fail` 语义
6. `MSS` 执行归因的真相源

一句话说：

`当前 MSS-lite 只做市场级风险调节，但市场怎么打分、什么时候记 50、什么时候缩仓、哪些字段只是 sidecar、哪些字段才真正驱动 Broker，必须写死。`

---

## 2. 作用边界

本文只覆盖当前主线 `MSS-lite`：

```text
l2_market_snapshot
-> six-factor raw components
-> normalized factor scores + aggregate score
-> MarketScore / l3_mss_daily
-> rank sidecar mss_score
-> Broker risk overlay
-> position sizing / reject
```

本文不覆盖：

1. `Selector` 前置 `MSS gate`
2. 把 `MSS` 写回 `final_score`
3. `MSS-full` 的 `cycle / trend / phase_days / position_advice / risk_regime`
4. 用上一交易日 `MSS` 结果替代当日结果
5. Report / GUI 的展示层展开

---

## 3. 设计来源

当前补充文的来源是“保主线、裁原子”：

1. `beta mss-data-models.md`
2. `beta mss-information-flow.md`
3. `beta mss-api.md`
4. `gamma` 当前主线正文
5. `gamma` 当前 `src/selector/mss.py`
6. `gamma` 当前 `src/broker/risk.py`
7. `gamma` 当前 `src/strategy/ranker.py`

其中：

1. `beta` 提供完整 `MssMarketSnapshot / MssPanorama / overlay` 的表达深度
2. `gamma` 提供当前主线正确边界：只做 `Broker / Risk` 风险覆盖
3. 当前代码提供已落地的六因子、阈值、倍率和降级现实

---

## 4. MSS-lite 阶段模型

### 4.1 阶段拆分

`MSS-lite` 当前主线固定拆成 6 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `M0` | `market_snapshot_load` | `l2_market_snapshot` | `MSS-lite snapshot` | 当日无快照则无市场层输出 |
| `M1` | `raw_component_calc` | `M0` | 6 个 raw 因子 | 分母为 0 或观测缺失时按安全除法回落 |
| `M2` | `score_materialize` | `M1 + MSS_BASELINE` | `MarketScore + l3_mss_daily` | 单因子标准差失效时该因子记 `50.0` |
| `M3` | `rank_sidecar_attach` | `l3_mss_daily + DTT variant` | `l3_signal_rank_exp.mss_score` | 当前变体不带 `MSS` 或分数缺失时 `FILL=50.0` |
| `M4` | `overlay_resolve` | `l3_mss_daily + config + signal_date` | `MssRiskOverlay` | 覆盖关闭、当日缺行、信号标签非法时回落到 `NEUTRAL` 路径 |
| `M5` | `broker_apply` | `M4 + BrokerRiskState + Signal` | 实际仓位上限 / 订单或拒绝 | 无下一交易日、无估价、资金不足等按 Broker 拒绝原因返回 |

### 4.2 当前实现对应

当前代码主要对应：

1. `compute_mss / compute_mss_single`
2. `build_dtt_score_frame`
3. `RiskManager._load_mss_overlay`
4. `RiskManager.assess_signal`

其中必须特别钉住的是：

1. `M3` 只是解释层 sidecar，不是正式风险决策
2. `M4 / M5` 才是 `MSS-lite` 当前主线真正消费者

---

## 5. MSS-lite 最小输入快照

### 5.1 契约定位

当前主线不直接恢复 `beta` 的完整 `MssMarketSnapshot`。

当前只从中裁出一份 `MSS-lite snapshot`。

它的语义固定为：

`足够支持当前六因子评分和 Broker 风险覆盖的最小市场日快照。`

### 5.2 必需字段

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `date` | `date` | `Required` | 交易日 |
| `total_stocks` | `int` | `Required` | 当日市场总样本数 |
| `rise_count` | `int` | `Required` | 上涨家数 |
| `fall_count` | `int` | `Required` | 下跌家数 |
| `strong_up_count` | `int` | `Required` | 强上行家数 |
| `strong_down_count` | `int` | `Required` | 强下行家数 |
| `limit_up_count` | `int` | `Required` | 涨停家数 |
| `limit_down_count` | `int` | `Required` | 跌停家数 |
| `touched_limit_up_count` | `int` | `Required` | 触及涨停家数 |
| `new_100d_high_count` | `int` | `Required` | 100 日新高家数 |
| `new_100d_low_count` | `int` | `Required` | 100 日新低家数 |
| `continuous_limit_up_2d` | `int` | `Required` | 连续 2 日涨停家数 |
| `continuous_limit_up_3d_plus` | `int` | `Required` | 连续 3 日及以上涨停家数 |
| `continuous_new_high_2d_plus` | `int` | `Required` | 连续 2 日及以上新高家数 |
| `high_open_low_close_count` | `int` | `Required` | 高开低走极端行为家数 |
| `low_open_high_close_count` | `int` | `Required` | 低开高走极端行为家数 |
| `pct_chg_std` | `float` | `Required` | 全市场涨跌幅标准差 |
| `amount_volatility` | `float` | `Required` | 成交额波动率 |

### 5.3 当前与 beta 的裁剪关系

从 `beta MssMarketSnapshot` 中，本轮明确不带入：

1. `flat_count`
2. `yesterday_limit_up_today_avg_pct`
3. `cycle`
4. `trend`
5. `position_advice`
6. `neutrality`

原因很直接：

`这些字段属于 MSS-full 的解释层或观测层，不是当前 MSS-lite 的最小输入。`

---

## 6. 市场层正式契约

### 6.1 契约定位

`MarketScore` 是 `MSS-lite -> Broker / Risk` 的正式跨模块结果契约。

它的语义固定为：

`某个交易日的市场级风险温度结果。`

### 6.2 正式稳定字段

当前正式稳定字段先冻结为 `src/contracts.py` 中的最小形态：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `date` | `date` | `Required` | 市场结果所属交易日 |
| `score` | `float` | `Required` | 市场总分，范围 `0-100` |
| `signal` | `Literal["BULLISH","NEUTRAL","BEARISH"]` | `Required` | 三态市场标签 |

### 6.3 当前持久化表 reality

当前 `l3_mss_daily` 已经比最小契约多落了 6 列解释字段：

1. `market_coefficient`
2. `profit_effect`
3. `loss_effect`
4. `continuity`
5. `extreme`
6. `volatility`

因此当前正式层次要分开看：

| 层次 | 字段 |
|---|---|
| 跨模块结果契约 | `date / score / signal` |
| 当前持久化现实 | `date / score / signal + 6 个标准化因子分` |

### 6.4 契约不变量

1. 同一 `date` 只能有一行市场层结果。
2. `score` 必须裁剪在 `0-100`。
3. `signal` 只能由 `score + 阈值` 推导，不能人工另写。
4. `MarketScore` 是市场层结果，不等于 Broker 最终仓位参数。

---

## 7. 六因子与 baseline 语义

### 7.1 当前 6 个 raw 因子

当前 `gamma` 代码的 raw 公式必须视为本轮 SoT：

| 因子 | 当前 raw 公式 |
|---|---|
| `market_coefficient_raw` | `rise_count / total_stocks` |
| `profit_effect_raw` | `0.4 * limit_up_ratio + 0.3 * new_high_ratio + 0.3 * strong_up_ratio` |
| `loss_effect_raw` | `0.3 * broken_rate + 0.2 * limit_down_ratio + 0.3 * strong_down_ratio + 0.2 * new_low_ratio` |
| `continuity_raw` | `0.5 * cont_limit_up_ratio + 0.5 * cont_new_high_ratio` |
| `extreme_raw` | `panic_tail_ratio + squeeze_tail_ratio` |
| `volatility_raw` | `0.5 * pct_chg_std + 0.5 * amount_vol_ratio` |

其中：

1. `broken_rate = touched_limit_up_count / limit_up_count` 的安全变体，分母为 0 时回落 `0.0`
2. `cont_limit_up_ratio = (continuous_limit_up_2d + continuous_limit_up_3d_plus) / limit_up_count`
3. `cont_new_high_ratio = continuous_new_high_2d_plus / new_100d_high_count`
4. `amount_vol_ratio = amount_volatility / (amount_volatility + 1_000_000)`

### 7.2 当前标准化现实

当前代码不是用滚动样本实时估 `mean/std`，而是使用冻结锚点 `MSS_BASELINE`：

1. `market_coefficient_mean/std`
2. `profit_effect_mean/std`
3. `loss_effect_mean/std`
4. `continuity_mean/std`
5. `extreme_mean/std`
6. `volatility_mean/std`

然后统一调用 `zscore_single()`：

```text
score = clip((z + 3) / 6 * 100, 0, 100)
```

若 `std == 0` 或 `NaN`：

```text
factor_score = 50.0
```

### 7.3 当前聚合公式

当前总分公式固定为：

```text
market_score =
    0.17 * market_coefficient
  + 0.34 * profit_effect
  + 0.34 * (100 - loss_effect)
  + 0.05 * continuity
  + 0.05 * extreme
  + 0.05 * (100 - volatility)
```

### 7.4 当前冻结结论

本轮必须冻结下面这个现实：

1. `gamma` 当前代码里的六因子和权重才是当前 SoT
2. `beta` 的 `temperature / cycle / trend` 口径只作未来升级来源
3. 不允许为了实现方便，把当前 `MSS-lite` 再压成单一黑箱分数

---

## 8. 三层对象边界

### 8.1 必须分开的 3 个对象

当前主线里，下面 3 个对象必须分开理解：

| 对象 | 所在层 | 作用 |
|---|---|---|
| `MarketScore` / `l3_mss_daily` | 市场层 | 保存正式市场分数和三态结果 |
| `l3_signal_rank_exp.mss_score` | 排序 sidecar | 给当前 signal 记录一个市场附着分，供解释和对照使用 |
| `MssRiskOverlay` | Broker 内部 | 把市场三态映射成真实执行容量参数 |

### 8.2 当前冻结结论

从本补充文生效起，必须固定：

1. `l3_signal_rank_exp.mss_score` 不是 `final_score` 组成项
2. 当前 `final_score` 仍然只由 `bof_strength + irs_score` 决定
3. 真正控制执行容量的是 `MssRiskOverlay`
4. `l3_signal_rank_exp.mss_score` 只承担解释和对照职责

---

## 9. Overlay 映射矩阵

### 9.1 当前三态阈值

当前三态阈值固定为：

1. `score >= 65` -> `BULLISH`
2. `score <= 35` -> `BEARISH`
3. 其余 -> `NEUTRAL`

### 9.2 当前映射面

`MssRiskOverlay` 当前最小字段固定为：

| 字段 | 语义 |
|---|---|
| `signal` | 市场三态 |
| `score` | 市场层总分 |
| `max_positions` | 有效最大持仓数 |
| `risk_per_trade_pct` | 单笔风险预算 |
| `max_position_pct` | 单票上限 |

### 9.3 当前默认倍率矩阵

当前默认倍率矩阵固定为：

| `signal` | `max_positions_mult` | `risk_per_trade_mult` | `max_position_mult` |
|---|---|---|---|
| `BULLISH` | `1.0` | `1.0` | `1.0` |
| `NEUTRAL` | `0.7` | `0.7` | `0.7` |
| `BEARISH` | `0.4` | `0.4` | `0.4` |

这些默认值允许通过 `config.py` 受控调整，但映射面本身不允许改成别的对象或别的维度。

### 9.4 当前有效值计算

在当前 Broker 中，有效值固定按下面规则生成：

```text
effective_max_positions =
    0                               if base_max_positions <= 0
    max(1, int(base_max_positions * mult))  otherwise

effective_risk_per_trade_pct =
    base_risk_per_trade_pct * max(mult, 0)

effective_max_position_pct =
    base_max_position_pct * max(mult, 0)
```

这意味着：

1. 熊市当前只允许缩容，不默认把系统直接切到 `0` 仓
2. `max_positions` 的最小有效值是 `1`，前提是基础配置大于 `0`

### 9.5 当前启用条件

当前 `MSS` 风险覆盖只在下面条件同时满足时启用：

1. `use_dtt_pipeline = True`
2. `dtt_variant_normalized == mss_risk_overlay_variant`

当前默认在线变体固定为：

`v0_01_dtt_bof_plus_irs_mss_score`

---

## 10. Skip / Fill / Fail 语义

### 10.1 市场层 `SKIP`

下面这些情况属于市场层 `SKIP`：

| 场景 | 处理 |
|---|---|
| `l2_market_snapshot` 当日无行 | 不写 `l3_mss_daily` |
| 批量区间内没有任何市场快照 | `compute_mss()` 返回 `0` |

### 10.2 市场层 `FILL`

下面这些情况属于市场层 `FILL`：

| 场景 | 处理 |
|---|---|
| 分子或分母为空 / 分母为 `0` | `safe_ratio(..., default=0.0)` |
| 计数字段或波动字段为空 | 按 `0 / 0.0` 进入 raw 计算 |
| 未显式传入 baseline | 使用冻结的 `MSS_BASELINE` |
| 单因子 `std == 0` 或 `NaN` | 该因子得分记 `50.0` |
| 聚合后分数超界 | `clip` 到 `0-100` |

### 10.3 排序 sidecar `FILL`

下面这些情况属于 `l3_signal_rank_exp.mss_score` 的 `FILL`：

| 场景 | 处理 |
|---|---|
| 当前变体不带 `MSS overlay` | `mss_score = 50.0` |
| 当前变体带 `MSS overlay` 但当日 `l3_mss_daily` 缺失 | `mss_score = 50.0` |

### 10.4 Overlay 层 `FILL`

下面这些情况属于 `MssRiskOverlay` 的 `FILL`：

| 场景 | 处理 |
|---|---|
| `mss_risk_overlay_enabled = False` | `signal='NEUTRAL'`，`score=DTT_SCORE_FILL`，但执行参数回到基础配置，不乘三态倍率 |
| 当日 `l3_mss_daily` 缺失 | `signal='NEUTRAL'`，`score=DTT_SCORE_FILL`，再按 `NEUTRAL` 倍率映射 |
| `signal` 标签非法 | 强制归一到 `NEUTRAL` |
| `score` 为空 | `score=DTT_SCORE_FILL` |

### 10.5 当前 `FAIL`

下面这些情况属于当前硬失败：

| 场景 | 处理 |
|---|---|
| 市场快照缺 `date` | 计算失败，不允许默默补旧日期 |
| Broker 无下一交易日 | `NO_NEXT_TRADE_DAY` |
| Broker 无估价或估价非正 | `NO_EST_PRICE` |
| 资金不足 / 最小手数不足 | `INSUFFICIENT_CASH / SIZE_BELOW_MIN_LOT` |

### 10.6 当前冻结结论

本轮必须把这 4 类动作分开：

1. 市场层 `SKIP`
2. 市场层 `FILL`
3. 排序 sidecar `FILL`
4. Overlay / Broker `FILL or FAIL`

否则很容易把“今天没算出 MSS”误解成“今天直接不下单”。

---

## 11. MSS Trace 真相源

### 11.1 为什么必须单独有 trace

`l3_mss_daily` 只能告诉我们：

`今天市场打了多少分、落到哪个三态。`

但下面这些问题必须单独追：

1. 某天分数主要由哪几个因子推高或压低
2. 为什么 `ranker` 看到的是 `50`
3. 为什么 Broker 当天只给了 `0.7` 倍或 `0.4` 倍容量
4. 当日容量变化来自 `MSS` 缺失、覆盖关闭，还是市场真的转弱

### 11.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`mss_risk_overlay_trace_exp`

它不是正式跨模块契约，而是当前 `MSS-lite` 的执行归因真相源。

### 11.3 建议字段

| 字段 | 说明 |
|---|---|
| `date` | 市场结果所属交易日 |
| `variant` | 当前 DTT 变体 |
| `overlay_enabled` | 当前是否启用 `MSS overlay` |
| `market_coefficient_raw` | 原始大盘系数 |
| `profit_effect_raw` | 原始赚钱效应 |
| `loss_effect_raw` | 原始亏钱效应 |
| `continuity_raw` | 原始连续性 |
| `extreme_raw` | 原始极端因子 |
| `volatility_raw` | 原始波动因子 |
| `market_coefficient` | 标准化后大盘系数 |
| `profit_effect` | 标准化后赚钱效应 |
| `loss_effect` | 标准化后亏钱效应 |
| `continuity` | 标准化后连续性 |
| `extreme` | 标准化后极端因子 |
| `volatility` | 标准化后波动因子 |
| `market_score` | 最终市场分 |
| `market_signal` | 最终三态 |
| `ranker_mss_score` | 写进 `l3_signal_rank_exp` 的附着分 |
| `max_positions_mult` | 当前倍率 |
| `risk_per_trade_mult` | 当前倍率 |
| `max_position_mult` | 当前倍率 |
| `effective_max_positions` | 当前有效最大持仓 |
| `effective_risk_per_trade_pct` | 当前有效单笔风险预算 |
| `effective_max_position_pct` | 当前有效单票上限 |
| `coverage_flag` | `NORMAL / SCORE_FILL / SIGNAL_NORMALIZED / OVERLAY_DISABLED / SNAPSHOT_MISSING` |
| `created_at` | 写入时间 |

### 11.4 和正式表的边界

| 表/对象 | 职责 |
|---|---|
| `l3_mss_daily` | 保存正式市场层结果 |
| `l3_signal_rank_exp.mss_score` | 保存 signal 侧附着分，供解释和对照 |
| `mss_risk_overlay_trace_exp` | 保存真正驱动执行容量的因果链 |

这三者不能混写。

---

## 12. 和上下游的稳定连接

### 12.1 与 Selector

当前主线下：

1. `Selector` 不读取 `l3_mss_daily`
2. `src/selector/selector.py` 里的 `enable_mss_gate` 只属于 `legacy` 对照链
3. 不允许把 `MSS-lite` 再拉回当前主线前置漏斗

### 12.2 与 Strategy / Ranker

当前主线下：

1. `ranker` 允许把 `mss_score` 写进 `l3_signal_rank_exp`
2. `ranker` 不允许把 `mss_score` 并入 `final_score`
3. `MSS-lite` 在排序层只保留解释位，不保留决策位

### 12.3 与 Broker / Risk

当前主线下：

1. `Broker / Risk` 是 `MSS-lite` 的唯一正式消费者
2. 它只读取市场层结果，不读取 `MSS-full` 周期语义
3. 订单数量、持仓上限和单票上限的实际变化，都必须能回溯到 `MssRiskOverlay`

---

## 13. 当前与后续

### 13.1 本文冻结的东西

本文已经冻结了：

1. `MSS-lite snapshot` 最小输入
2. `MarketScore` 最小正式字段
3. `l3_mss_daily / mss_score / MssRiskOverlay` 的三层边界
4. 三态阈值和 overlay 映射面
5. `skip / fill / fail` 语义
6. `mss_risk_overlay_trace_exp`

### 13.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 增加 `mss_risk_overlay_trace_exp` 或同等 artifact
2. 把 `ranker` 侧 `mss_score` 和 Broker 侧 overlay 的命名隔离做实
3. 若要推进 `Spec-04 MSS-upgrade`，必须在当前补充文之上扩，不允许回头改义 `MSS-lite`
4. 若要调整三态倍率，必须进入证据矩阵，不允许口头改默认值

### 13.3 本文明确不做什么

本文不授权下面这些回退：

1. 把 `MSS` 拉回 `Selector` 前置 gate
2. 把 `MSS` 写回 `final_score`
3. 因为想更快推进实现，就继续把 `MarketScore / mss_score / overlay` 三层对象混写
