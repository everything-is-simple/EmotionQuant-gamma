# MSS 算法设计

**版本**: v0.01 正式版  
**创建日期**: 2026-03-06  
**状态**: Active（算法级 SoT，执行语义仍受 `system-baseline.md` 冻结约束）  
**变更规则**: 允许在不改变 v0.01 执行语义前提下，对算法细案、baseline 口径与证据回写做受控纠偏。  
**对应模块**: `src/selector/mss.py`, `src/selector/baseline.py`, `src/selector/normalize.py`  
**上游文档**: `system-baseline.md`, `selector-design.md`, `architecture-master.md`

---

## 1. 定位

在 v0.01 中，MSS 的职责是：

`回答“今天市场环境是否允许做多形态交易”。`

它是 Selector 的市场级 gate，不是完整的市场状态机产品。

当前输出契约固定为：

- `date`
- `score`
- `signal`（`BULLISH / NEUTRAL / BEARISH`）

不输出旧版研究材料中的：

- `cycle`
- `trend`
- `position_advice`

这些内容属于未来扩展，不属于 v0.01 当前执行范围。

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

### 3.1 六因子

当前实现保留 v0.01 的六因子框架：

1. `market_coefficient`
2. `profit_effect`
3. `loss_effect`
4. `continuity`
5. `extreme`
6. `volatility`

### 3.2 权重

当前权重为：

- 大盘系数：`17%`
- 赚钱效应：`34%`
- 亏钱效应：`34%`（翻转）
- 连续性：`5%`
- 极端因子：`5%`
- 波动因子：`5%`（翻转）

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

当前问题不再是“baseline 还是占位”，而是：

`65 / 35 阈值在真实 baseline 下仍然偏紧。`

---

## 5. 当前已知现实问题

### 5.1 gate 信息量不足

Week2 审计已经证明：

- `ENABLE_MSS_GATE` 打开和关闭几乎没有区别
- `BOF baseline` 与 `BOF + MSS` 结果基本一致

这说明当前 MSS 还没有真正形成强 gate。

### 5.2 score 分布压缩

在真实 baseline 下，分布已不再“全中性”，但仍明显偏紧：

- `65` 阈值下仅 `20 / 757` 天为 `BULLISH`
- `55` 阈值下为 `165 / 757` 天
- `65` 阈值下最长空窗达到 `239` 个交易日

因此当前优先判断为：

`baseline 已完成第一轮纠偏，下一步矛盾集中在 gate 阈值与系统职责。`

---

## 6. v0.01 正式口径

MSS 在 v0.01 的正式定义应为：

`六因子市场温度 + baseline 标准化 + 三态 gate`

而不是旧版研究中的“大一统市场状态机”。

这一定义与当前系统目标一致：

1. 低频
2. 可解释
3. 可消融验证
4. 不把宏观叙事塞进执行链路

---

## 7. 下一步校准路径

### 7.1 baseline 固定

当前 baseline 已可固定为 v0.01 的正式经验基线，后续只允许：

- 用同口径更长样本复核
- 在版本升级时重新估计
- 不允许回退到占位参数

### 7.2 阈值敏感性

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

### 7.3 软硬开关决策

在真实 baseline 已落定后，才进入：

- `RISK_ON / RISK_MID / RISK_OFF`
- 软开关状态机

因为这一步讨论的前提已经从“先校准 baseline”变成了“先确认 MSS 在 55/58/60/62/65 下的系统职责”。

---

## 8. 权威结论

当前 v0.01 的 MSS：

- 框架是对的
- 执行边界是清楚的
- baseline 已完成第一轮经验校准
- 当前 open risk 已切换为 `threshold too tight`

所以 MSS 的下一步不是大改公式，而是：

`围绕真实 baseline 重新跑 +MSS 消融，并决定 gate 是继续硬开关还是进入软开关设计。`
