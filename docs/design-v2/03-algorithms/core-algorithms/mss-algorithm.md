# MSS-lite 桥接稿（design-v2 -> blueprint）

**版本**: `v0.01-plus 桥接稿`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `本文仅保留 design-v2 阶段的兼容桥接说明；现行设计修订必须进入 blueprint/，本文只允许导航、勘误与桥接说明更新。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md`  
**对应模块**: `src/selector/mss.py`, `src/broker/risk.py`  
**理论来源**: `docs/Strategy/MSS/`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容桥接稿。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的整理结果，不再构成仓库现行设计权威。现行 `MSS-lite` 正文以 `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 职责

当前主线中的 `MSS-lite` 只负责：

`回答今天该用多大的风险预算去执行排序信号。`

它回答的问题是：

`市场环境允许多大执行容量。`

当前主线消费者固定为：

`Broker / Risk`

---

## 2. 输入

`MSS-lite` 只读取：

1. `l2_market_snapshot`
2. 配置项
   - 分数阈值
   - 风险倍率映射

当前依赖字段包括：

1. `rise_count / fall_count`
2. `strong_up_count / strong_down_count`
3. `limit_up_count / limit_down_count`
4. `touched_limit_up_count`
5. `new_100d_high_count / new_100d_low_count`
6. `continuous_limit_up_2d / continuous_limit_up_3d_plus`
7. `continuous_new_high_2d_plus`
8. `high_open_low_close_count / low_open_high_close_count`
9. `pct_chg_std`
10. `amount_volatility`

---

## 3. 输出契约

`MSS-lite` 当前输出最小市场契约：

1. `trade_date`
2. `score`
3. `signal`

其中：

1. `score` 为 `0-100`
2. `signal` 为 `BULLISH / NEUTRAL / BEARISH`

主线消费时，这些结果进一步映射为执行层风险覆盖参数。

---

## 4. 不负责什么

当前主线中，`MSS-lite` 不负责：

1. Selector 前置 gate
2. 候选池收缩控制
3. 个股横截面排序
4. 行业评分
5. 形态检测

当前未恢复的 `MSS-full` 能力也不视为主线职责：

1. 完整情绪周期阶段
2. 周期趋势方向
3. 周期持续天数
4. 完整市场风险状态机

---

## 5. 决策规则 / 算法

当前执行版保留六因子框架：

1. `market_coefficient`
2. `profit_effect`
3. `loss_effect`
4. `continuity`
5. `extreme`
6. `volatility`

当前权重固定为：

1. 大盘系数 `17%`
2. 赚钱效应 `34%`
3. 亏钱效应 `34%`，翻转
4. 连续性 `5%`
5. 极端因子 `5%`
6. 波动因子 `5%`，翻转

三态阈值固定为：

1. `score >= 65` -> `BULLISH`
2. `score <= 35` -> `BEARISH`
3. 其余 -> `NEUTRAL`

主线消费规则：

1. `MSS` 不进入 `final_score`
2. `BULLISH / NEUTRAL / BEARISH` 只映射执行层风险预算
3. 风险覆盖当前至少调节：
   - `max_positions`
   - `risk_per_trade_pct`
   - `max_position_pct`

---

## 6. 失败模式与验证证据

主要失败模式：

1. `MSS` 被重新拉回前置停手，破坏职责分离。
2. `MSS` 被错误并入横截面总分。
3. 风险倍率变化无法追溯到市场分。
4. 只看短窗收益，不看更长窗口 `MDD / EV / PF` 结构。

当前验证证据：

1. `docs/spec/v0.01-plus/evidence/execution_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t162521__execution_sensitivity.json`
2. `docs/spec/v0.01-plus/evidence/windowed_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20251222_20260224_t_after_opt__windowed_sensitivity.json`
3. `docs/spec/v0.01-plus/records/v0.01-plus-trade-attribution-and-windowed-sensitivity-20260308.md`

当前证据只说明：

1. `MSS-lite` 已进入执行层
2. `MSS-lite` 已能改变实际执行容量

是否满足默认主线路径切换，仍以 `development-status.md` 的阶段状态为准。
