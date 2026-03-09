# PAS Minimal Tradable Design

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `PAS 最小可交易形态层`  
**定位**: `当前主线 PAS 算法正文`  
**上游锚点**:

1. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
2. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`
5. `docs/Strategy/PAS/lance-beggs-ytc-analysis.md`
6. `docs/Strategy/PAS/volman-ytc-mapping.md`
7. `docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md`
8. `docs/observatory/god_view_8_perspectives_report_v0.01.md`
9. `docs/observatory/sandbox-review-standard.md`
10. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-algorithm.md`
11. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-data-models.md`
12. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-information-flow.md`
13. `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-api.md`
14. `G:\EmotionQuant\EmotionQuant-alpha\docs\design\core-algorithms\pas\pas-algorithm.md`
15. `docs/design-v2/02-modules/strategy-design.md`
16. `src/strategy/pas_bof.py`
17. `src/strategy/registry.py`
18. `src/strategy/strategy.py`

---

## 1. 用途

本文不是第二份 `PAS contract annex`。

本文回答的是：

`当前主线 PAS 到底要做到什么程度，才算从 “只有 BOF trigger” 补到 “最小可交易形态层”。`

它冻结 6 件事：

1. 职责
2. 输入
3. 输出
4. 不负责什么
5. 决策规则 / 算法
6. 失败模式与验证证据

一句话说：

`04-contract-supplement` 负责 formal `Signal`、trace 和字段边界；本文负责把当前主线 PAS 的五形态算法面、注册表边界和回测口径写实。`

---

## 2. 当前冻结结论

从本文生效起，当前主线 `PAS` 的最小可交易形态层固定定义为：

```text
StockCandidate
-> pattern registry (BOF / BPB / PB / TST / CPB)
-> detector arbitration
-> pattern quality
-> stop / target / failure 参考层
-> formal Signal + PAS truth source
```

这里的关键点只有 6 条：

1. `PAS mini` 不是 `BOF + BPB`，而是至少包含 `YTC` 五种核心形态：`BOF / BPB / PB / TST / CPB`。
2. 五形态必须都能单独启停、单独回测、单独统计，不允许只留“组合后总结果”。
3. `pattern_quality_score` 和 `stop / target / failure` 必须恢复，但先进入 sidecar / trace，不污染 formal `Signal`。
4. `PAS` 仍然只负责个股形态层，不回吞 `IRS / MSS / Broker` 的职责。
5. 后续新增 `PAS` 形态允许继续扩，但必须经过 registry 注册、专项回测和证据门禁，不能直接塞进当前主线。
6. `docs/observatory/` 提到的“信号质量因子”“注册表生态管理”“环境分桶”“执行摩擦”对 `PAS` 都是观察与证据要求，不是可选项。

---

## 3. 设计来源与当前代码现实

### 3.1 设计来源

当前对象统一按下面顺序回收：

1. `beta` 四件套提供算法结构、数据模型、信息流和接口表达。
2. `alpha` 算法文提供成熟边界和验收口径回看。
3. `YTC` 与 `Volman` 研究文提供五形态和微观结构映射来源。
4. `许佳冲` 研究文提供 `BOF / Pin Bar` 的 A 股细化来源。
5. `god_view_8_perspectives` 和 `sandbox-review-standard` 提供回测与评审目标。
6. `gamma` 的 `04-contract-supplement` 提供当前正式契约与 trace 边界。

### 3.2 当前代码现实

截至 `2026-03-09`，代码现实是：

1. `src/strategy/pas_bof.py` 已落地 `BOF`。
2. `src/strategy/registry.py` 仍只允许 `PAS_PATTERNS=bof`。
3. `src/strategy/strategy.py` 已有 `pas_trigger_trace_exp` 和 formal `Signal` 的双层结构。
4. `BPB / PB / TST / CPB / pattern_quality / reference layer / registry ablation` 还没有正式落到代码。

### 3.3 当前冻结原则

因此本文的角色不是描述“现在代码已经做到什么”，而是冻结：

`P1 实现完成后，PAS 必须对齐到什么设计状态。`

---

## 4. 职责

当前主线 `PAS` 的职责固定为：

1. 对 `Selector` 已入池候选做个股形态检测。
2. 运行 `YTC` 五形态注册表并生成 formal `BUY Signal`。
3. 产出可追溯的 detector 级真相源。
4. 为后续排序提供形态强度解释位。
5. 产出不进入 formal `Signal` 的质量层和交易管理参考层。
6. 保证每个形态都能单独回测、单独归因、单独淘汰。

当前主线 `PAS` 不直接回答：

1. 这只票最终排第几。
2. 市场是否允许放大仓位。
3. 这笔单应该如何撮合。
4. 卖出状态机该如何运行。

---

## 5. 输入

### 5.1 正式上游输入

| 输入对象 | 当前来源 | 用途 |
|---|---|---|
| `StockCandidate` | `Selector` | 候选入口 |
| 个股历史窗口 | `l2_stock_adj_daily` | 形态检测主输入 |
| 当前配置 | `config.py` | 窗口、阈值、组合模式、registry 开关 |

### 5.2 当前主线阶段模型

`PAS` 当前主线固定拆成 8 段：

| 阶段 | 名称 | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `P0` | `candidate_accept` | `StockCandidate` | 待检测候选 | 只接收正式候选 |
| `P1` | `history_load` | `code + asof_date + lookback_days` | 历史窗口 | 不做跨模块回填 |
| `P2` | `registry_eval` | 历史窗口 + `PAS_PATTERNS` | 五形态单 detector 结果 | 每个 detector 独立评估 |
| `P3` | `pattern_arbitration` | 单形态结果列表 | 当日选中的 `selected_pattern` | 默认 `ANY` |
| `P4` | `quality_score` | 已选形态 + 结构观测 | `pattern_quality_score` | 解释层 |
| `P5` | `reference_layer` | 已选形态 + 质量层 | `stop / target / failure` | 参考层 |
| `P6` | `formalize` | 选中形态 | formal `Signal` + truth source | formal 最小字段不变 |
| `P7` | `ablation_attach` | `Signal + registry run label` | 单形态 / 多形态回测标签 | 为 report 和 evidence 服务 |

### 5.3 最小历史窗口输入

当前主线冻结的最小输入字段为：

| 字段 | 类型 | 必需性 | 用途 |
|---|---|---|---|
| `code` | `str` | `Required` | 股票代码 |
| `date` | `date` | `Required` | 交易日 |
| `adj_open` | `float` | `Required` | 开盘价 |
| `adj_high` | `float` | `Required` | 最高价 |
| `adj_low` | `float` | `Required` | 最低价 |
| `adj_close` | `float` | `Required` | 收盘价 |
| `volume` | `float` | `Required` | 成交量 |
| `volume_ma20` | `float` | `Required` | 20 日平均成交量 |

### 5.4 允许的派生观测

在不新增跨模块输入契约的前提下，`PAS` 可以从历史窗口内部派生：

1. `lower_bound`
2. `range_high / range_low`
3. `close_pos`
4. `body_ratio`
5. `volume_ratio`
6. `breakout_ref`
7. `pullback_low`
8. `pullback_depth`
9. `history_days`
10. `support_level`
11. `resistance_level`
12. `test_distance`
13. `trend_peak`
14. `trend_floor`
15. `retest_count`
16. `compression_width`
17. `neckline_ref`
18. `handle_width`
19. `structure_span_days`

### 5.5 当前配置冻结

当前代码已存在并冻结的配置键：

1. `PAS_PATTERNS`
2. `PAS_COMBINATION`
3. `PAS_LOOKBACK_DAYS`
4. `PAS_MIN_HISTORY_DAYS`
5. `PAS_EVAL_BATCH_SIZE`
6. `PAS_BOF_BREAK_PCT`
7. `PAS_BOF_VOLUME_MULT`

本轮允许新增但尚未落地的配置键：

1. `PAS_PATTERN_PRIORITY`
2. `PAS_SINGLE_PATTERN_MODE`
3. `PAS_REGISTRY_ENABLED`
4. `PAS_QUALITY_ENABLED`
5. `PAS_REFERENCE_ENABLED`
6. `PAS_BPB_LOOKBACK`
7. `PAS_BPB_BREAKOUT_WINDOW`
8. `PAS_BPB_PULLBACK_MIN`
9. `PAS_BPB_PULLBACK_MAX`
10. `PAS_BPB_VOLUME_MULT`
11. `PAS_PB_LOOKBACK`
12. `PAS_PB_PULLBACK_MIN`
13. `PAS_PB_PULLBACK_MAX`
14. `PAS_PB_VOLUME_MULT`
15. `PAS_TST_LOOKBACK`
16. `PAS_TST_DISTANCE_MAX`
17. `PAS_TST_VOLUME_MULT`
18. `PAS_CPB_LOOKBACK`
19. `PAS_CPB_RETEST_MIN`
20. `PAS_CPB_NECKLINE_BREAK_PCT`
21. `PAS_CPB_VOLUME_MULT`

### 5.6 不允许的输入回流

当前主线禁止：

1. 读取 `IRS` 分数决定形态是否触发。
2. 读取 `MSS` 分数决定形态是否触发。
3. 读取账户状态改变 detector 判定。
4. 用上一交易日 signal 顶替当日形态结果。

---

## 6. 输出

### 6.1 正式输出

当前主线 `PAS` 的正式跨模块输出仍固定为：

1. formal `Signal`
2. `pas_trigger_trace_exp`

### 6.2 解释层输出

当前主线必须补齐但不进入 formal `Signal` 的字段有：

1. `selected_pattern`
2. `pattern_quality_score`
3. `quality_breakdown_json`
4. `entry_ref`
5. `stop_ref`
6. `target_ref`
7. `risk_reward_ref`
8. `failure_handling_tag`
9. `pattern_group`
10. `registry_run_label`

### 6.3 输出边界

当前主线固定采用下面三层边界：

| 层 | 当前对象 | 职责 |
|---|---|---|
| formal 层 | `Signal` / `l3_signals` | 最小买入信号 |
| detector 真相源 | `pas_trigger_trace_exp` | 解释为什么触发、为什么未触发、当前选中了哪个 pattern |
| 排序与证据层 | `l3_signal_rank_exp + evidence artifacts` | 解释入选与排序，并支持单形态独立回测 |

### 6.4 强度字段兼容期规则

当前存在一个兼容期语义残留：

`bof_strength`

从本文生效起，冻结如下：

1. formal `Signal.strength` 始终表示 `selected_pattern` 的通用形态强度。
2. 在兼容期内，若下游仍保留 `bof_strength` 命名，它只能被视为 `pas_trigger_strength` 的历史别名。
3. 一旦 `PB / TST / CPB` 上线，任何只写 `bof_strength` 而不写 `selected_pattern` 的 sidecar 都视为语义无效。

---

## 7. 不负责什么

当前主线 `PAS` 明确不负责：

1. 行业层排序
2. 市场层控仓位
3. `final_score` 合成
4. 卖出和止损执行
5. 主题 / 事件 / 政策语义
6. 多指标学习系统

---

## 8. 决策规则 / 算法

### 8.1 在线形态范围与默认组合

当前主线算法面固定为：

1. `BOF`
2. `BPB`
3. `PB`
4. `TST`
5. `CPB`

这 5 个对象共同构成当前 `PAS mini` 的最低在线范围。

当前明确不在线恢复：

1. `PAS-full` 机会等级体系
2. 非 `YTC` 的额外 `PAS` 形态
3. 主题 / 事件 / 政策形态语义

默认组合规则冻结为：

1. 默认 `PAS_COMBINATION=ANY`
2. `ALL / VOTE` 仅保留为实验模式
3. `PAS_SINGLE_PATTERN_MODE` 必须允许五形态逐个独立跑
4. 同一股票同一交易日多形态同时触发时：
   - 先比 `strength`
   - 若并列，按 `PAS_PATTERN_PRIORITY`
   - 初始推荐优先级：`bpb > pb > tst > cpb > bof`

### 8.2 BOF 正式判定

当前 `BOF` 沿用代码现实，正式条件固定为：

1. `today_low < lower_bound * (1 - break_pct)`
2. `today_close >= lower_bound`
3. `close_pos >= 0.6`
4. `today_volume >= volume_ma20 * volume_mult`

其中：

```text
lower_bound = min(adj_low[t-20, t-1])
close_pos   = (today_close - today_low) / (today_high - today_low)
body_ratio  = abs(today_close - today_open) / (today_high - today_low)
volume_ratio = today_volume / volume_ma20
```

`BOF` 强度公式冻结为：

```text
strength =
  clip(
      0.4 * close_pos
    + 0.3 * min(volume_ratio / 2, 1)
    + 0.3 * body_ratio,
    0,
    1
  )
```

### 8.3 BPB 正式判定

当前主线 `BPB` 不直接沿用旧 `MA20` 依赖版本。

当前冻结的 `BPB` 最小可交易日线定义是：

`先出现有效突破，再出现可接受深度的回踩，最后在支撑上方重新确认。`

#### 8.3.1 观测窗口

固定使用两个窗口：

1. `setup_window = t-25 ~ t-6`
2. `pullback_window = t-5 ~ t-1`

派生观测：

```text
breakout_ref  = max(setup_window.adj_high)
base_low      = min(setup_window.adj_low)
breakout_peak = max(pullback_window.adj_high)
pullback_low  = min(pullback_window.adj_low)
volume_ratio  = today_volume / volume_ma20
```

#### 8.3.2 触发条件

`BPB` 必须同时满足：

1. `breakout_leg_exists`
   - `pullback_window` 中至少存在一根 bar 满足：
   - `adj_close > breakout_ref`
   - 且 `volume / volume_ma20 >= 1.2`
2. `support_hold`
   - `pullback_low >= breakout_ref * (1 - 0.03)`
3. `pullback_depth_valid`
   - `pullback_depth = (breakout_peak - pullback_low) / max(breakout_peak - breakout_ref, eps)`
   - `0.25 <= pullback_depth <= 0.80`
4. `confirmation`
   - `today_close > max(pullback_window.adj_high)`
   - `today_close >= breakout_ref`
   - `today_volume >= volume_ma20 * PAS_BPB_VOLUME_MULT`
5. `not_overextended`
   - `today_close <= breakout_peak * 1.03`

#### 8.3.3 强度公式

`BPB` 强度冻结为：

```text
confirm_strength = clip((today_close - breakout_ref) / max(0.10 * breakout_ref, eps), 0, 1)
volume_strength  = clip(volume_ratio / 2.0, 0, 1)
depth_quality    = 1.0 if 0.40 <= pullback_depth <= 0.60
                   else 0.7 if 0.25 <= pullback_depth <= 0.80
                   else 0.0
body_ratio       = abs(today_close - today_open) / max(today_high - today_low, eps)

strength =
  clip(
      0.40 * confirm_strength
    + 0.25 * volume_strength
    + 0.20 * depth_quality
    + 0.15 * body_ratio,
    0,
    1
  )
```

#### 8.3.4 历史灵感与当前裁剪

旧 `Volman / YTC` 中的：

1. `first pullback`
2. `cup handle`
3. `market condition score`

当前允许作为解释层加分项，但不作为 `BPB` 的正式硬条件。

### 8.4 PB 正式判定

当前主线 `PB` 的最小可交易日线定义是：

`趋势已经建立，价格进行一次可控深度的简单回调，然后在结构支撑上方恢复。`

#### 8.4.1 观测窗口

固定使用：

1. `trend_window_a = t-40 ~ t-21`
2. `trend_window_b = t-20 ~ t-6`
3. `pullback_window = t-5 ~ t-1`

派生观测：

```text
trend_peak   = max(trend_window_b.adj_high)
trend_floor  = min(trend_window_a.adj_low)
mid_floor    = min(trend_window_b.adj_low)
pullback_low = min(pullback_window.adj_low)
rebound_ref  = max(pullback_window.adj_high)
volume_ratio = today_volume / volume_ma20
```

#### 8.4.2 触发条件

`PB` 必须同时满足：

1. `trend_established`
   - `max(trend_window_b.adj_high) > max(trend_window_a.adj_high)`
   - 且 `min(trend_window_b.adj_low) > min(trend_window_a.adj_low)`
2. `pullback_depth_valid`
   - `pullback_depth = (trend_peak - pullback_low) / max(trend_peak - trend_floor, eps)`
   - `0.20 <= pullback_depth <= 0.50`
3. `support_hold`
   - `pullback_low >= mid_floor * 0.98`
4. `rebound_confirm`
   - `today_close > rebound_ref`
   - `today_close <= trend_peak * 1.03`
5. `volume_confirm`
   - `today_volume >= volume_ma20 * PAS_PB_VOLUME_MULT`

#### 8.4.3 强度公式

`PB` 强度冻结为：

```text
rebound_strength = clip((today_close - rebound_ref) / max(0.08 * rebound_ref, eps), 0, 1)
depth_quality    = 1.0 if 0.25 <= pullback_depth <= 0.40
                   else 0.7 if 0.20 <= pullback_depth <= 0.50
                   else 0.0
trend_quality    = clip((mid_floor - trend_floor) / max(0.10 * trend_floor, eps), 0, 1)
volume_strength  = clip(volume_ratio / 2.0, 0, 1)

strength =
  clip(
      0.35 * rebound_strength
    + 0.25 * depth_quality
    + 0.20 * trend_quality
    + 0.20 * volume_strength,
    0,
    1
  )
```

### 8.5 TST 正式判定

当前主线 `TST` 的最小可交易日线定义是：

`价格回到已知支撑位附近完成测试，并在支撑上方出现有效反弹确认。`

#### 8.5.1 观测窗口

固定使用：

1. `structure_window = t-60 ~ t-6`
2. `test_window = t-5 ~ t-1`

派生观测：

```text
support_level  = min(structure_window.adj_low)
test_low       = min(test_window.adj_low)
test_high_ref  = max(test_window.adj_high)
test_distance  = abs(test_low - support_level) / max(support_level, eps)
lower_shadow_ratio =
  (min(today_open, today_close) - today_low) / max(today_high - today_low, eps)
volume_ratio   = today_volume / volume_ma20
```

#### 8.5.2 触发条件

`TST` 必须同时满足：

1. `near_support`
   - `test_distance <= PAS_TST_DISTANCE_MAX`
2. `support_hold`
   - `today_close >= support_level`
3. `bounce_confirm`
   - `today_close > test_high_ref`
   - 或 `today_close > today_open` 且 `today_close > support_level * 1.01`
4. `rejection_candle`
   - `lower_shadow_ratio >= 0.35`
5. `volume_confirm`
   - `today_volume >= volume_ma20 * PAS_TST_VOLUME_MULT`

#### 8.5.3 强度公式

`TST` 强度冻结为：

```text
support_closeness = 1 - clip(test_distance / max(PAS_TST_DISTANCE_MAX, eps), 0, 1)
bounce_strength   = clip((today_close - support_level) / max(0.05 * support_level, eps), 0, 1)
rejection_strength = clip(lower_shadow_ratio, 0, 1)
volume_strength   = clip(volume_ratio / 1.5, 0, 1)

strength =
  clip(
      0.35 * support_closeness
    + 0.30 * bounce_strength
    + 0.20 * rejection_strength
    + 0.15 * volume_strength,
    0,
    1
  )
```

### 8.6 CPB 正式判定

当前主线 `CPB` 的最小可交易日线定义是：

`回调结构不是一次完成，而是在关键支撑带附近经过两次及以上测试后，形成 W 型或复杂底部，再向上突破颈线。`

#### 8.6.1 观测窗口

固定使用：

1. `base_window = t-20 ~ t-1`
2. `setup_window = t-40 ~ t-21`

派生观测：

```text
support_band_low  = min(base_window.adj_low)
support_band_high = quantile(base_window.adj_low, 0.35)
neckline_ref      = max(base_window.adj_high)
retest_count      = count(adj_low within support band)
compression_width = (max(base_window.adj_high) - min(base_window.adj_low)) / max(min(base_window.adj_low), eps)
volume_ratio      = today_volume / volume_ma20
```

#### 8.6.2 触发条件

`CPB` 必须同时满足：

1. `retest_enough`
   - `retest_count >= PAS_CPB_RETEST_MIN`
2. `support_band_valid`
   - `support_band_high / max(support_band_low, eps) <= 1.03`
3. `compression_valid`
   - `compression_width <= 0.12`
4. `neckline_break`
   - `today_close > neckline_ref * (1 + PAS_CPB_NECKLINE_BREAK_PCT)`
5. `volume_confirm`
   - `today_volume >= volume_ma20 * PAS_CPB_VOLUME_MULT`

#### 8.6.3 强度公式

`CPB` 强度冻结为：

```text
neckline_strength = clip((today_close - neckline_ref) / max(0.10 * neckline_ref, eps), 0, 1)
retest_quality    = clip(retest_count / 3.0, 0, 1)
compression_quality = 1 - clip(compression_width / 0.12, 0, 1)
volume_strength   = clip(volume_ratio / 2.0, 0, 1)

strength =
  clip(
      0.35 * neckline_strength
    + 0.25 * retest_quality
    + 0.20 * compression_quality
    + 0.20 * volume_strength,
    0,
    1
  )
```

### 8.7 Pattern Quality Score

当前主线 `pattern_quality_score` 固定由 4 个分量组成：

1. `structure_clarity`
2. `volume_confirmation`
3. `position_advantage`
4. `failure_risk`

总公式冻结为：

```text
pattern_quality_score =
    0.35 * structure_clarity
  + 0.25 * volume_confirmation
  + 0.20 * position_advantage
  + 0.20 * (100 - failure_risk)
```

#### 8.7.1 structure_clarity

`structure_clarity` 是 pattern-specific 指标：

| pattern | 计算规则 |
|---|---|
| `bof` | `100 * (0.45*close_pos + 0.30*body_ratio + 0.25*reclaim_score)` |
| `bpb` | `100 * (0.45*confirm_strength + 0.30*support_hold_score + 0.25*depth_score)` |
| `pb` | `100 * (0.45*rebound_strength + 0.30*depth_quality + 0.25*trend_quality)` |
| `tst` | `100 * (0.45*support_closeness + 0.30*bounce_strength + 0.25*rejection_strength)` |
| `cpb` | `100 * (0.45*neckline_strength + 0.30*retest_quality + 0.25*compression_quality)` |

#### 8.7.2 volume_confirmation

`volume_confirmation` 统一计算为：

```text
required_mult =
  PAS_BOF_VOLUME_MULT   if pattern == "bof"
  PAS_BPB_VOLUME_MULT   if pattern == "bpb"
  PAS_PB_VOLUME_MULT    if pattern == "pb"
  PAS_TST_VOLUME_MULT   if pattern == "tst"
  PAS_CPB_VOLUME_MULT   if pattern == "cpb"

volume_confirmation =
  100 * clip(volume_ratio / max(required_mult, eps), 0, 1.2)
```

再裁剪到 `[0, 100]`。

#### 8.7.3 position_advantage

`position_advantage` 不直接决定是否触发，只衡量当前形态的性价比。

固定计算为：

```text
position_advantage =
  100 * clip((risk_reward_ref - 1.0) / 1.0, 0, 1)
```

含义：

1. `risk_reward_ref <= 1.0` 记 `0`
2. `risk_reward_ref >= 2.0` 记 `100`

#### 8.7.4 failure_risk

`failure_risk` 采用扣分式风险项，累计后裁剪到 `[0, 100]`：

| 风险项 | 规则 | 扣分 |
|---|---|---|
| `LOW_HISTORY_BUFFER` | `history_days < required_window + 5` | `30` |
| `VOLUME_EDGE_TOO_THIN` | `volume_ratio < required_mult * 1.05` | `20` |
| `RR_TOO_THIN` | `risk_reward_ref < 1.5` | `25` |
| `STRUCTURE_TOO_WIDE` | `today_high - today_low` 异常过宽 | `15` |
| `STALE_INPUT` | 若后续出现 stale 标记 | `40` |

### 8.8 交易管理参考层

当前主线 `PAS` 必须输出参考层，但这层先不进入 `Broker` 强依赖。

#### 8.8.1 通用规则

```text
entry_ref = today_close
risk      = max(entry_ref - stop_ref, eps)
risk_reward_ref = (target_ref - entry_ref) / risk
```

#### 8.8.2 BOF 参考层

```text
stop_ref   = min(today_low, lower_bound) * 0.99
target_ref = max(lookback_high_20, entry_ref + 1.5 * risk)
failure_handling_tag ∈ {
  "BOF_NO_FOLLOW_THROUGH",
  "BOF_BACK_BELOW_LOWER_BOUND",
  "BOF_VOLUME_COLLAPSE"
}
```

#### 8.8.3 BPB 参考层

```text
stop_ref   = pullback_low * 0.99
target_ref = max(breakout_peak, entry_ref + 1.5 * risk)
failure_handling_tag ∈ {
  "BPB_LOSE_BREAKOUT_REF",
  "BPB_CONFIRM_FAIL",
  "BPB_WEAK_VOLUME"
}
```

#### 8.8.4 PB 参考层

```text
stop_ref   = pullback_low * 0.99
target_ref = max(trend_peak, entry_ref + 1.5 * risk)
failure_handling_tag ∈ {
  "PB_LOSE_PULLBACK_LOW",
  "PB_TREND_NOT_RESUME",
  "PB_VOLUME_FAIL"
}
```

#### 8.8.5 TST 参考层

```text
stop_ref   = support_level * 0.99
target_ref = max(structure_window.adj_high, entry_ref + 1.5 * risk)
failure_handling_tag ∈ {
  "TST_SUPPORT_LOST",
  "TST_NO_BOUNCE",
  "TST_FALSE_REJECTION"
}
```

#### 8.8.6 CPB 参考层

```text
stop_ref   = support_band_low * 0.99
target_ref = max(neckline_ref + (neckline_ref - support_band_low), entry_ref + 1.5 * risk)
failure_handling_tag ∈ {
  "CPB_NECKLINE_FAIL",
  "CPB_SUPPORT_BAND_LOST",
  "CPB_BREAKOUT_WEAK"
}
```

### 8.9 Formal Signal 与参考层的关系

当前主线明确规定：

1. 形态是否触发，只由 detector 决定。
2. `pattern_quality_score` 不得回写 formal `Signal`。
3. `stop / target / failure` 不得在当前版本直接改写 `Broker` 执行核心。
4. 质量层和参考层先服务于：
   - sidecar 解释
   - 单形态与组合消融验证
   - 后续执行层决策评估

---

## 9. 失败模式与降级规则

### 9.1 检测失败

当前主线必须显式区分：

1. `INSUFFICIENT_HISTORY`
2. `MISSING_REQUIRED_COLUMNS`
3. `INVALID_RANGE`
4. `NOT_TRIGGERED`
5. pattern-specific condition fail

其中：

1. `BOF` 继续沿用现有 `NO_BREAK / NO_RECOVERY / LOW_CLOSE_POSITION / LOW_VOLUME`
2. `BPB` 新增：
   - `NO_BREAKOUT_LEG`
   - `PULLBACK_TOO_DEEP`
   - `SUPPORT_LOST`
   - `NO_CONFIRMATION`
   - `OVEREXTENDED_CONFIRM`
3. `PB` 新增：
   - `TREND_NOT_ESTABLISHED`
   - `PULLBACK_NOT_VALID`
   - `NO_REBOUND_CONFIRM`
4. `TST` 新增：
   - `SUPPORT_TOO_FAR`
   - `NO_REJECTION_CANDLE`
   - `NO_BOUNCE_CONFIRM`
5. `CPB` 新增：
   - `RETEST_NOT_ENOUGH`
   - `SUPPORT_BAND_TOO_WIDE`
   - `NO_NECKLINE_BREAK`

### 9.2 降级规则

当前主线统一采用：

1. 历史窗口不足：不触发，不回填旧 signal。
2. 关键列缺失：不补列，不借别表，直接记 trace。
3. 当日无任何触发：返回空列表，非异常。
4. `pattern_quality_score` 或参考层计算失败：
   - formal `Signal` 仍可保留
   - 但 trace 必须显式记录 `quality_status` 或 `reference_status`

### 9.3 不允许的降级

下面这些做法全部禁止：

1. 用 `IRS / MSS` 分数补形态未触发。
2. 为了凑样本放宽五形态正式条件。
3. 因为当前 schema 还没迁移，就把 `quality / reference / selected_pattern` 继续留在口头上。
4. 因为实现压力大，就把 `PAS mini` 重新压回 `BOF + BPB`。

---

## 10. 验证证据

当前主线 `PAS` 最低必须产出下面 7 组证据：

1. `BOF`
2. `BPB`
3. `PB`
4. `TST`
5. `CPB`
6. `YTC5_ANY`
7. `YTC5_ANY + quality`

每组至少比较：

1. `trade_count`
2. `EV`
3. `PF`
4. `MDD`
5. `rank_diff_days`
6. `execution_diff_days`
7. `pattern_overlap_rate`

当前还必须能解释：

1. 哪些票是因为新增形态而出现。
2. 哪些票是因为 `quality` 变化而被筛下去或排上来。
3. 哪个形态在什么环境桶下有效，哪个形态应该降权或冻结。
4. 单形态和组合形态的执行摩擦是否显著不同。

与 `god_view_8_perspectives` 对齐后，`PAS` 最低要补齐：

1. 视角三：`strength` 分位有效性
2. 视角五：执行摩擦按形态统计
3. 视角六：亏损归因到形态与失败类型
4. 视角七：注册表生态管理

与 `sandbox-review-standard` 对齐后，`PAS` 评审至少要覆盖：

1. Schema 契合
2. 调用链完整性
3. 幂等与确定性
4. 时序语义
5. 边界冲突与去重
6. 报告口径真实性

---

## 11. 当前实现映射与对齐要求

### 11.1 当前已落地

当前代码已与本文一致的部分：

1. `BOF` 正式判定
2. formal `Signal`
3. `pas_trigger_trace_exp`
4. `PAS_COMBINATION` 基础骨架

### 11.2 当前必须对齐

P1 实现时，必须按本文完成：

1. `src/strategy/pas_bpb.py`
2. `src/strategy/pas_pb.py`
3. `src/strategy/pas_tst.py`
4. `src/strategy/pas_cpb.py`
5. `registry.py` 扩展五形态 registry 与单形态启停
6. `strategy.py` 增加多形态选中与优先级逻辑
7. `pas_trigger_trace_exp` 或等价 sidecar 扩展：
   - `selected_pattern`
   - `pattern_quality_score`
   - `quality_breakdown_json`
   - `entry_ref / stop_ref / target_ref / risk_reward_ref`
   - `failure_handling_tag`
   - `registry_run_label`
8. 新增 `scripts/backtest/run_v001_plus_pas_ablation.py`
   - 支持五形态单跑
   - 支持五形态组合跑
   - 支持 registry summary 输出

### 11.3 当前不允许的实现回退

实现层不允许：

1. 因为代码里现在只有 `BOF`，就把本文重新压回“只有 trigger”。
2. 因为 formal schema 还没迁移，就把 `quality / reference / registry` 暂时删除。
3. 因为要快推进，就把 `PB / TST / CPB` 继续挂成“以后再说”。
4. 因为排序层压力大，就把 `PAS` 改写成依赖 `IRS / MSS` 的混合规则。

---

## 12. 冻结结语

从本文生效起，当前主线 `PAS` 的完成标准不再是：

`能跑出 BOF signal`

而是：

`能把 BOF / BPB / PB / TST / CPB + quality + reference + registry ablation 作为一个清晰分层、可解释、可独立回测、可继续扩展的个股形态层跑起来。`

只要五形态、`quality / reference`、单形态证据或 registry 任一块还缺席，当前 `PAS` 就仍然只是 `PAS-trigger`，不算达到本版本的最小可交易强度。
