# MSS-lite 算法设计（当前执行版）

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变 v0.01 Frozen 历史基线的前提下，对当前主线中的 MSS 角色、算法细案与证据回写做受控修订。`  
**上游文档**: `docs/spec/v0.01-plus/README.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`  
**创建日期**: `2026-03-06`  
**最后更新**: `2026-03-08`  
**对应模块**: `src/selector/mss.py`, `src/broker/risk.py`  
**理论来源**: `docs/Strategy/MSS/`

---

## 1. 文档定位

本文定义的是 `v0.01-plus` 当前已经落地并在线消费的 `MSS-lite`，不是 `docs/Strategy/MSS/` 中的原始完整 `MSS-full`。

两者边界如下：

- `MSS-full`：强调情绪周期、趋势方向、周期持续天数、仓位建议与状态机。
- `MSS-lite`：强调当前主线可执行的市场温度、三态信号与 `Broker / Risk` 风险覆盖。

当前主线先落地 `MSS-lite`，后续补全见：

- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`

---

## 2. 当前主线定位

在 `v0.01-plus` 当前主线中，MSS 的职责是：

`回答“今天该用多大的风险预算去执行排序信号”。`

它当前不再承担：

- Selector 前置 gate
- 候选池收缩控制
- 个股横截面排序增强

当前输出契约仍保持：

- `date`
- `score`（0-100 温度值）
- `signal`（`BULLISH / NEUTRAL / BEARISH`）

但主线消费方已经切换为：

`Broker / Risk`

---

## 3. 理论基础与被裁剪部分

MSS 的理论基础仍来自：

1. `docs/Strategy/MSS/market-sentiment-system-2024-analysis.md`
2. `docs/Strategy/MSS/manual-sentiment-tracking-experience.md`

核心设计原则不变：
- 情绪优先于技术指标
- 对称性设计（赚钱效应与亏钱效应等权）
- 适配 A 股特色（涨跌停、T+1、散户情绪）

变化只在系统职责：
- 过去：主打前置停手
- 现在：主打市场级风险折扣

原始 `MSS-full` 中仍然成立、但当前执行版尚未完整恢复的部分包括：

- 七阶段情绪周期
- 周期趋势方向（上升 / 下降 / 横盘）
- 周期持续天数
- 周期到仓位建议的正式映射
- 更完整的市场风险状态机

这些内容当前没有被否定，只是尚未作为 `v0.01-plus` 当前执行口径完整落地。

---

## 4. 输入边界

MSS 只读 `l2_market_snapshot`，不读行业、不读个股、不读 PAS。

当前依赖字段包括：

- `total_stocks`
- `rise_count / fall_count`
- `strong_up_count / strong_down_count`
- `limit_up_count / limit_down_count`
- `touched_limit_up_count`
- `new_100d_high_count / new_100d_low_count`
- `continuous_limit_up_2d / continuous_limit_up_3d_plus`
- `continuous_new_high_2d_plus`
- `high_open_low_close_count / low_open_high_close_count`
- `pct_chg_std`
- `amount_volatility`

---

## 5. 当前算法定义

### 4.1 六因子框架

当前实现仍保留六因子框架：

1. `market_coefficient`
2. `profit_effect`
3. `loss_effect`
4. `continuity`
5. `extreme`
6. `volatility`

### 4.2 权重设计

- 大盘系数：`17%`
- 赚钱效应：`34%`
- 亏钱效应：`34%`（翻转）
- 连续性：`5%`
- 极端因子：`5%`
- 波动因子：`5%`（翻转）

### 4.3 三态阈值

- `score >= 65` -> `BULLISH`
- `score <= 35` -> `BEARISH`
- 其余 -> `NEUTRAL`

---

## 6. 当前主线消费方式

### 5.1 主线约束

在 `v0.01-plus` 当前主线中，MSS 不再进入个股横截面 `final_score`。

当前主线使用方式是：

- `BULLISH`：维持基础风险预算
- `NEUTRAL`：缩减风险预算
- `BEARISH`：进一步缩减风险预算

### 5.2 风险覆盖项

当前 `Broker / Risk` 读取 `l3_mss_daily` 后，动态调节：

- `max_positions`
- `risk_per_trade_pct`
- `max_position_pct`

这意味着 `MSS` 的作用被收口为：

`市场环境 -> 风险折扣 -> 实际执行容量`

而不是：

`市场环境 -> 候选池拦截` 或 `市场环境 -> 个股排序加分`

---

## 7. 当前已知现实问题

### 6.1 前置 gate 已经不再是主线职责

过去 `MSS gate` 的问题是：

- 容易把样本压得过 sparse
- 容易把“停手”和“排序”混在一起
- 很难解释收益改善到底来自删样本还是来自执行质量变化

因此在当前主线中，`MSS gate` 已降级为历史对照逻辑。

### 6.2 执行层价值仍需证据继续证明

虽然 `MSS` 现在已经接入 `Broker / Risk`，但还需要更长窗口证据确认：

- 是否稳定改善 `MDD`
- 是否稳定改善收益结构
- 哪种倍率最合适

### 6.3 周期层被裁剪得过薄

当前执行版只保留了：

- `score`
- `signal`
- 风险倍率映射

它还不能完整回答原始 `MSS-full` 里的几个关键问题：

- 当前市场处于哪一个情绪周期阶段
- 当前阶段是在上升、下降还是横盘
- 该阶段已经持续了多久
- 推荐仓位区间与执行倍率应如何对齐

因此，当前文档必须被理解为：

`MSS-lite 当前执行版`

而不是：

`MSS 完整算法设计`

---

## 8. 版本演进路径

### 7.1 v0.01 Frozen（历史）

- MSS 作为 gate / soft gate 的历史实验口径
- 保留为对照与回退参考

### 7.2 v0.01-plus（当前主线）

- MSS 改为市场级风险调节因子
- 不再前置停手
- 不再进入横截面总分
- 当前重点是验证其对仓位管理和回撤控制的价值
- 当前在线实现仍是 `MSS-lite`

### 7.3 后续版本

若后续证据支持，MSS 将按 `Spec-04` 恢复：

- 七阶段周期模型
- 趋势方向与周期持续天数
- 周期到仓位建议的正式映射
- 更细的风险状态机
- 动态持仓上限
- 动态单笔风险预算

但这些都应建立在当前主线证据稳定之后。

---

## 9. 权威结论

当前主线里的 MSS：

- 算法框架仍然有效
- 理论基础不变
- 执行职责已经从“前置门控”切换到“市场级控仓位”
- 当前落地的是 `MSS-lite`，不是原始 `MSS-full`
- 下一步不是把它重新塞回排序公式，而是先恢复周期 / 趋势 / 仓位建议层，再继续验证其对执行层风险控制是否稳定有益

---

## 10. 参考文献

1. `docs/Strategy/MSS/market-sentiment-system-2024-analysis.md`
2. `docs/Strategy/MSS/manual-sentiment-tracking-experience.md`
3. `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
4. `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`
5. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`
