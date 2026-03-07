# MSS 算法设计

**版本**: v0.01 正式版  
**创建日期**: 2026-03-06  
**最后更新**: 2026-03-07  
**状态**: Active（算法级 SoT，执行语义仍受 `system-baseline.md` 冻结约束）  
**变更规则**: 允许在不改变 v0.01 执行语义前提下，对算法细案、baseline 口径与证据回写做受控纠偏。  
**对应模块**: `src/selector/mss.py`, `src/selector/baseline.py`, `src/selector/normalize.py`  
**上游文档**: `system-baseline.md`, `selector-design.md`, `architecture-master.md`  
**理论来源**: `docs/Strategy/MSS/`

---

## 1. 定位与理论基础

### 1.1 系统定位

在 v0.01 中，MSS 的职责是：

`回答"今天市场环境是否允许做多形态交易"。`

它是 Selector 的市场级 gate，不是完整的市场状态机产品。

当前输出契约固定为：

- `date`
- `score`（0-100 温度值）
- `signal`（`BULLISH / NEUTRAL / BEARISH`）

不输出旧版研究材料中的：

- `cycle`（七阶段周期）
- `trend`（趋势方向）
- `position_advice`（仓位建议）

这些内容属于未来扩展，不属于 v0.01 当前执行范围。

### 1.2 理论来源

MSS 的核心理论来自两个实践积累：

1. **《2024.大盘情绪交易系统》**（`docs/Strategy/MSS/market-sentiment-system-2024-analysis.md`）
   - 三维观测框架（广度/强度/持续性）
   - 七阶段情绪周期模型
   - 对称性设计（赚钱效应 vs 亏钱效应）
   - A股特色考量（涨跌停制度、T+1、散户主导）

2. **《市场情绪表-手工》5年实践**（`docs/Strategy/MSS/manual-sentiment-tracking-experience.md`）
   - 2020-2025年手工记录经验
   - 从手工到自动化的演进路径
   - 实战验证的有效性

**核心设计原则**：
- 情绪优先于技术指标
- 对称性设计（赚钱效应与亏钱效应等权）
- 适配A股特色（涨跌停、T+1、散户情绪）

### 1.3 三维观测框架映射

| 理论维度 | 对应因子 | 观测指标 |
|---------|---------|---------|
| 市场广度（Breadth） | market_coefficient | 涨跌家数比、上涨占比 |
| 情绪强度（Intensity） | profit_effect + loss_effect | 涨停/跌停/新高/新低/炸板 |
| 持续性（Continuity） | continuity | 连续涨停、连续新高 |
| 极端分化（Extreme） | extreme | 高开低收、低开高收 |
| 波动性（Volatility） | volatility | 涨跌幅标准差、成交额波动 |

---

## 2. 输入边界

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

## 3. 当前算法定义

### 3.1 六因子框架

当前实现保留 v0.01 的六因子框架：

1. **market_coefficient**（大盘系数，17%）
   - 涨跌家数比
   - 对应"市场广度"维度

2. **profit_effect**（赚钱效应，34%）
   - 涨停占比
   - 新高占比
   - 强势上涨占比
   - 连续涨停效应
   - 对应"正向情绪强度"

3. **loss_effect**（亏钱效应，34%，翻转）
   - 炸板率（touched_limit_up 但未 limit_up）
   - 跌停占比
   - 强势下跌占比
   - 新低占比
   - 对应"负向情绪强度"

4. **continuity**（连续性，5%）
   - 连续涨停2日
   - 连续涨停3日+
   - 连续新高2日+
   - 对应"持续性"维度

5. **extreme**（极端因子，5%）
   - 高开低收占比
   - 低开高收占比
   - 对应"分化程度"

6. **volatility**（波动因子，5%，翻转）
   - 涨跌幅标准差
   - 成交额波动
   - 对应"市场稳定性"

### 3.2 权重设计

当前权重为：

- 大盘系数：`17%`
- 赚钱效应：`34%`
- 亏钱效应：`34%`（翻转）
- 连续性：`5%`
- 极端因子：`5%`
- 波动因子：`5%`（翻转）

**权重设计原则**：
- 赚钱效应与亏钱效应等权（对称性设计）
- 情绪强度（68%）> 市场广度（17%）> 辅助因子（15%）
- 负向因子翻转后参与计算（100 - loss_effect, 100 - volatility）

### 3.3 三态阈值

- `score >= 65` -> `BULLISH`
- `score <= 35` -> `BEARISH`
- 其余 -> `NEUTRAL`

### 3.4 归一化

当前使用统一的 `zscore -> 0~100` 归一化：

```text
z = (value - mean) / std
score = clip((z + 3) / 6 * 100, 0, 100)
```

`std == 0` 时返回 `50`。

---

## 4. baseline 口径

当前 baseline 存放在 `src/selector/baseline.py`。

自 `2026-03-06` 起，当前事实是：

- 已有 zscore 归一化框架
- `MSS_BASELINE` 已基于 `2023-02-01 ~ 2026-02-24` 的真实 `l2_market_snapshot`（`757` 个交易日）做经验校准

当前问题不再是"baseline 还是占位"，而是：

`65 / 35 阈值在真实 baseline 下仍然偏紧。`

---

## 5. 当前已知现实问题

### 5.1 gate 信息量不足

Week2 审计已经证明：

- `ENABLE_MSS_GATE` 打开和关闭几乎没有区别
- `BOF baseline` 与 `BOF + MSS` 结果基本一致

这说明当前 MSS 还没有真正形成强 gate。

### 5.2 score 分布压缩

在真实 baseline 下，分布已不再"全中性"，但仍明显偏紧：

- `65` 阈值下仅 `20 / 757` 天为 `BULLISH`
- `55` 阈值下为 `165 / 757` 天
- `65` 阈值下最长空窗达到 `239` 个交易日

因此当前优先判断为：

`baseline 已完成第一轮纠偏，下一步矛盾集中在 gate 阈值与系统职责。`

---

## 6. v0.01 正式口径

MSS 在 v0.01 的正式定义应为：

`六因子市场温度 + baseline 标准化 + 三态 gate`

而不是旧版研究中的"大一统市场状态机"。

这一定义与当前系统目标一致：

1. 低频
2. 可解释
3. 可消融验证
4. 不把宏观叙事塞进执行链路

---

## 7. 版本演进路径（v0.01-v0.06）

### 7.1 v0.01：三态硬门控 + BOF单形态

**当前状态**：
- MSS 作为硬门控（BEARISH → 不出手）
- 六因子框架
- 固定阈值（65/35）
- 仅 BOF 形态

**已知问题**：
- 阈值过紧，BULLISH 天数过少
- 硬门控误杀机会
- 与 baseline 结果差异不大

### 7.2 v0.02：软评分模式 + BPB形态

**计划改进**：
- MSS 从硬门控改为软评分（参考 `down-to-top-integration.md`）
- 新增 BPB 形态
- MSS/IRS 作为后置评分项，不再前置过滤
- 阈值敏感性测试（55/58/60/62/65）

**验收标准**：
- BOF + BPB 单形态回测均通过
- soft_gate 模式改善 baseline 指标
- trade_count >= 60

### 7.3 v0.03：七阶段周期识别

**计划改进**：
- 新增 `cycle` 字段（萌芽/发酵/加速/分歧/高潮/扩散/退潮）
- 基于 score + 趋势方向判定周期阶段
- 不同周期阶段调整仓位权重
- 新增 TST/PB 形态

**验收标准**：
- 周期识别准确率 >= 70%
- 不同周期阶段的策略表现差异显著
- 组合形态回测通过

### 7.4 v0.04：趋势方向识别

**计划改进**：
- 新增 `trend` 字段（UP/DOWN/SIDEWAYS）
- 基于连续 N 日 score 变化判定趋势
- 趋势与周期联合判断
- 新增 CPB 形态

**验收标准**：
- 趋势识别准确率 >= 65%
- 趋势反转信号及时性
- 五形态组合回测通过

### 7.5 v0.05：动态仓位建议

**计划改进**：
- 新增 `position_advice` 字段（0-100%）
- 基于 cycle + trend + score 综合判断
- 动态调整最大持仓数
- 引入 Gene 分析（事后）

**验收标准**：
- 动态仓位相对固定仓位改善 MDD >= 20%
- 牛市/震荡/熊市分环境验证
- Gene 分析覆盖历史交易

### 7.6 v0.06：自适应阈值

**计划改进**：
- 阈值不再固定，基于滚动窗口 percentile
- 自适应调整 BULLISH/BEARISH 判定标准
- 引入市场状态机（RISK_ON/RISK_MID/RISK_OFF）
- Gene 前置过滤（可选）

**验收标准**：
- 自适应阈值相对固定阈值改善 EV >= 15%
- 状态机转换逻辑清晰可复现
- Gene 过滤通过消融验证

---

## 8. 下一步校准路径（v0.01 → v0.02）

### 8.1 baseline 固定

当前 baseline 已可固定为 v0.01 的正式经验基线，后续只允许：

- 用同口径更长样本复核
- 在版本升级时重新估计
- 不允许回退到占位参数

### 8.2 阈值敏感性

下一步必须围绕真实 baseline 重跑：

- `55`
- `58`
- `60`
- `62`
- `65`

并比较：

- `BULLISH` 占比
- 连续 `BULLISH` 天数
- 空窗期长度
- `BOF baseline -> BOF + MSS` 的结果变化

### 8.3 软硬开关决策

在真实 baseline 已落定后，才进入：

- `RISK_ON / RISK_MID / RISK_OFF`
- 软开关状态机

因为这一步讨论的前提已经从"先校准 baseline"变成了"先确认 MSS 在 55/58/60/62/65 下的系统职责"。

---

## 9. 权威结论

当前 v0.01 的 MSS：

- 框架是对的（六因子 + 三维观测）
- 理论基础清晰（5年手工实践 + 2024系统设计）
- 执行边界是清楚的（市场级 gate，不碰行业和个股）
- baseline 已完成第一轮经验校准
- 当前 open risk 已切换为 `threshold too tight`

所以 MSS 的下一步不是大改公式，而是：

`围绕真实 baseline 重新跑 +MSS 消融，并决定 gate 是继续硬开关还是进入软开关设计（v0.02）。`

---

## 10. 参考文献

1. `docs/Strategy/MSS/market-sentiment-system-2024-analysis.md` - 理论框架
2. `docs/Strategy/MSS/manual-sentiment-tracking-experience.md` - 实践经验
3. `docs/design-v2/system-baseline.md` - 执行语义
4. `docs/design-v2/down-to-top-integration.md` - v0.02 软评分模式
5. `docs/spec/v0.01/evidence/v0.01-evidence-review-20260306.md` - 消融证据
