# EmotionQuant / 低频量化项目：上帝之眼八大视角评审报告（v0.01 附录）

> **文档定位**: 研究附录（非强制执行条款）
> **从属基线**: `docs/design-v2/system-baseline.md`（Frozen）
> **冲突规则**: 本文与冻结基线冲突时，以基线为准（与 `system-baseline.md` §8.2 一致）
> **纳入执行口径的前提**: 各视角仅在对应版本评审通过后纳入执行口径

---

## 0. 背景与定位

低频量化项目的骨架设计已完成：
- **Selector 漏斗**（MSS + IRS + 基础过滤）把全市场压缩到候选池（50–100）。
- **PAS / Pattern Registry** 将 YTC 五形态（区间3、趋势2）注册在册，并支持单形态独立回测与淘汰。
- **Broker 内核**统一回测/纸上/实盘撮合与风控语义（T+1）。

“上帝之眼”并不是再加新策略，而是：
- 用更高维度的**统计与运营视角**去监控系统健康度；
- 用分桶与归因消除“感觉”；
- 用执行摩擦与组合风险把回测优势转化为真实可持续收益。

### 八大视角分类

八个视角按实现性质分为两类：

- **Type-A：监控覆盖层**（可作为统计指标增量叠加到现有 report，不需要独立设计周期）
  - 视角一：闭环健康度
  - 视角二：环境分桶
  - 视角三：信号质量因子
  - 视角五：执行摩擦
  - 视角六：风险归因

- **Type-B：核心功能阶段**（需要独立设计+实现卡+评审周期）
  - 视角四：候选池分层
  - 视角七：注册表生态管理
  - 视角八：组合系统

### 视角落地映射总表

| 视角 | 类型 | 状态 | 对应 spec / 版本 | 核心验收指标 |
|------|------|------|-----------------|-------------|
| 一：闭环健康度 | Type-A | v0.01 部分覆盖 | spec-05 reporter | hold_days, consecutive_loss, signals_per_day |
| 二：环境分桶 | Type-A | v0.01 部分覆盖 | spec-02 MSS + spec-05 分环境统计 | 分环境胜率/期望值 |
| 三：信号质量因子 | Type-A | v0.04 计划 | spec-05 reporter 扩展 | strength Top20% vs Bottom20% 胜率差 |
| 四：候选池分层 | Type-B | v0.06 计划 | 待定（Selector 扩展） | 不同 tier 的胜率/摩擦/期望值 |
| 五：执行摩擦 | Type-A | v0.01 部分覆盖 | spec-04 Matcher | REJECTED 率, slippage_bps |
| 六：风险归因 | Type-A | v0.01 部分覆盖 | spec-05 pattern_stats | 逐形态/分环境亏损贡献 |
| 七：注册表生态管理 | Type-B | v0.05 计划 | 待定（Registry 扩展） | 滚动期望值, 重叠度, 淘汰率 |
| 八：组合系统 | Type-B | v0.01 部分覆盖 | spec-04 risk.py | max_drawdown, 连亏熔断触发次数 |

---

## 1) 视角一：闭环健康度（系统是否按预期工作） 【Type-A 监控覆盖层】

### 关注点
不是先问“赚不赚钱”，而是先问“系统有没有在正常产出”。

### 放置模块
- Report / Ops

### v0.01 已覆盖项
- `hold_days` → spec-05 `_pair_trades` 输出 `holding_days`
- `consecutive_loss` → spec-05 `_max_consecutive(is_loss)`
- `signals_per_day` → spec-05 `generate_daily_report` + `l4_pattern_stats`

### 待后续版本实现的指标
- **触发→确认转化率**：`trigger_to_confirm_rate`（v0.01 BOF 无确认期，此指标在 v0.02 BPB 时才有意义）
- **信号拥堵度**：同日 Top-N 信号强度分布、同票同日多形态重叠率（v0.03 多形态组合时才有意义）

### 产出物
- 每日/每周“系统体征表”

---

## 2) 视角二：环境分桶（真正的上帝开关） 【Type-A 监控覆盖层】

### 关注点
形态不是任何时候都有效。要回答：**BOF/BPB 在什么市场环境下才有正期望？**

### 放置模块
- MSS / Backtest Stats

### v0.01 已覆盖项
- MSS 三挡开关 (BULLISH/BEARISH/NEUTRAL) → spec-02 `selector.py`
- 分环境统计（牛/震荡/熊）→ spec-05 `reporter.py` 分环境胜率/期望值

### 待后续版本深化（v0.04 监控覆盖层）
- 更细分桶维度：**流动性周期** `amount_sma20 >= amount_sma60`，**波动周期** `ATR%` 分位
- 按桶统计：`win_rate, expectancy, max_dd, avg_hold_days, fail_type_share`
- 产出物：“环境—形态有效性矩阵”（heatmap 或表格）

---

## 3) 视角三：信号质量因子（强度可解释性） 【Type-A 监控覆盖层】

### 关注点
strength 不是装饰品：它必须能把“好信号”与“差信号”拉开表现。

### 放置模块
- PAS / Report

### 必备指标
- **强度分位回测**：Top20% vs Bottom20% 的胜率/期望值/回撤
- **组成因子贡献**：ClosePos、VolMult、触边次数等分层统计
- **参数敏感性**：break/touch_band/Vmult 在 ±20% 下的稳健性

### 产出物
- “strength 是否有效”的结论（有效→保留；无效→删减/重构）

---

## 4) 视角四：候选池分层（避免拥挤赛道的核心工具） 【Type-B 核心功能阶段】

### 关注点
你要“避开主流量化绞杀”，必须能量化“拥挤”。

### 放置模块
- Selector

### 分层字段（v0.06 组合层闭环时实现）
- `liquidity_tier`：按 20 日平均成交额分位（L1/L2/L3）
- `attention_tier`：HOT/MID/COLD（指数成分、成交额Top分位、行业热度代理）
- `scan_batch`：A/B/C 批次（每日A+B，周末C）

### 必备指标
- 不同 tier 的：信号数、成交摩擦、胜率/期望值、最大回撤

### 产出物
- “拥挤度—表现”对照表（用数据回答：中腰部是否更适合你）

---

## 5) 视角五：执行摩擦（回测到真钱的最大鸿沟） 【Type-A 监控覆盖层】

### 关注点
任何策略一旦遇到：涨停买不到、跌停卖不出、滑点扩大，都会变形。

### 放置模块
- Broker / Backtest Engine / Report

### v0.01 已覆盖项
- 停牌/涨停/跌停 → spec-04 Matcher REJECTED(HALTED/LIMIT_UP/LIMIT_DOWN)
- 滑点 → spec-04 `slippage_bps` 参数化
- REJECTED 订单记录 → spec-04 Order.reject_reason + l4_orders 审计链

### 待后续版本深化（v0.04 监控覆盖层）
- `unfilled_rate` 按原因分组统计（涨停/跌停/停牌/流动性不足）
- `slippage_p50/p95`（实际成交 vs 理论成交）
- `delay_fill_days`

### 产出物
- “执行可行性报告”（决定是否需要提高流动性阈值或改撮合假设）

---

## 6) 视角六：风险归因（亏损来自哪里） 【Type-A 监控覆盖层】

### 关注点
不是看亏损总和，而是回答：亏损主要来自哪类错误？

### 放置模块
- Report（归因模块）

### v0.01 已覆盖项
- 逐形态统计 → spec-05 `_compute_pattern_stats`
- 分环境统计（牛/震荡/熊）→ spec-05 reporter

### 归因标签建议
- **失败类型**（对 BOF 特别重要）：
  - `confirm_failed`（触发后未确认）
  - `no_follow_through`（确认后不延续）
  - `true_breakdown`（假破位其实是真破位）
- **环境**：MSS/流动性/波动桶
- **分层**：attention/liquidity tier
- **形态**：BOF/BPB/…

### 产出物
- “亏损贡献表”（Pareto：前20%原因解释80%亏损）

---

## 7) 视角七：注册表生态管理（策略插件的生死规则） 【Type-B 核心功能阶段】

### 关注点
你要的是“注册表可迭代”，不是“堆形态”。必须有淘汰机制。

### 放置模块
- Registry + Stats

### 建议规则（v0.05 策略生态可进化）
- **滚动窗口淘汰**：某形态滚动100笔期望值为负 → 降权/冻结
- **重叠度控制**：同日同票多形态命中率过高 → 合并或只保留更强者
- **环境启用**：某形态只在特定 MSS/流动性桶启用（开关矩阵）

### 产出物
- “形态生命周期面板”（新增→验证→上线→降权→淘汰）

---

## 8) 视角八：组合系统（买多少卖多少的最终解） 【Type-B 核心功能阶段】

### 关注点
单策略能赚钱不等于组合能活。组合层解决：仓位、暴露、连亏降仓。

### 放置模块
- Portfolio/Risk Layer（在 broker/risk.py 之上）

### v0.01 已覆盖项
- 单笔账户风险 0.8% + 单只仓位上限 10% → spec-04 risk.py
- 组合回撤 15% 清仓 + 连亏熔断 → spec-04 第二/三级止损

### 待 v0.06 实现的完整规则（可量化）
- 总风险预算（每日/每周 R 限额）
- 同行业/同主题最大暴露（避免单一风险）
- 强度加权仓位（分数凯利上限 + R 风险制）
- 连亏降仓、回撤暂停（系统自我保护）

### 产出物
- “组合风控报告”（暴露、回撤、R 使用效率）

---

## 版本演化建议（对齐冻结基线 `system-baseline.md` §7）

> 以下版本号与冻结基线一致，v0.01-v0.03 为核心形态扩展，v0.04-v0.06 为上帝视角覆盖层与组合层。

### v0.01（单形态闭环 — 已定义于路线图第1迭代）
- BOF 单形态跑通全链路
- 输出 signals/trades/pattern_stats + 分环境统计 + 消融对照
- **已覆盖的上帝视角：** 基础闭环健康度、MSS 三挡分桶、基础执行摩擦判定、基础风险控制

### v0.02（多形态并行评估 — 已定义于路线图第2迭代）
- BPB + BOF 独立回测、基因库事后反推、IRS 4因子
- 可增量叠加：触发→确认转化率（BPB 有确认期，BOF 无）

### v0.03（组合模式评估 — 已定义于路线图第3迭代）
- TST/PB/CPB + PAS_COMBINATION + 临界点管理
- 可增量叠加：信号拥堵度、多形态重叠率

### v0.04（监控覆盖层 — Type-A 视角深化）
- 环境分桶矩阵深化（流动性周期 + 波动周期）
- 执行摩擦统计深化（unfilled_rate/slippage/delay）
- 风险归因深化（失败类型标签 + Pareto 归因）

### v0.05（策略生态可进化 — Type-B）
- 注册表生态管理：滚动期望值、重叠度、环境启用矩阵
- 信号强度有效性验证：Top20% vs Bottom20% 分位回测
- 稳健性：walk-forward、参数敏感性、成本压力测试

### v0.06（组合层闭环 — Type-B）
- 总风险预算、行业/主题暴露限制、分数凯利/动态降仓
- 候选池分层（liquidity/attention tier）

---

## 附：最简“上帝仪表盘”字段清单（建议落库/落表）

- `daily_health`: date, signals_total, signals_by_pattern, candidates_total, confirm_rate, hold_days_p50, consecutive_loss_p95
- `env_bucket_stats`: bucket_id, pattern_id, sample_size, win_rate, expectancy, max_dd
- `execution_stats`: date, unfilled_rate, slippage_p95, delay_fill_p95
- `loss_attribution`: pattern_id, fail_type, env_bucket, tier, loss_sum
- `pattern_lifecycle`: pattern_id, status, rolling_expectancy, overlap_rate, enabled_env_buckets

---

## 结语

这八个视角的意义不是“把系统复杂化”，而是把你脑子里模糊的方向——
- 何时做
- 做哪类票
- 信号质量怎样
- 为什么亏
- 能不能成交

全部变成**统计与规则**。

最终目标只有一句：
> **避开拥挤赛道，用低频结构优势活下去，并持续进化。**




