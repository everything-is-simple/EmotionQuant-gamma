# Tachibana TACHI_CROWD_FAILURE 最小契约说明

**文档版本**：`Draft v0.01`  
**文档状态**：`Active`  
**创建日期**：`2026-03-12`  
**变更规则**：`允许继续细化字段、边界与失败语义；不直接变成当前主线 formal Signal 契约。`

> **定位说明**：本文只服务 `Normandy / N1.8`。  
> 它的目标不是报告收益结论，而是把 `TACHI_CROWD_FAILURE` 这条最小 contrary detector 的对象定义、触发链和失效点写清楚，避免后续一边改 detector 一边改对象。

---

## 1. 目标

本文当前只做三件事：

1. 把 `TACHI_CROWD_FAILURE` 的最小 formal contract 写清楚
2. 固定第一轮允许使用的日线字段与阈值
3. 写明它和 `BOF_CONTROL` 的边界，以及当前不包含的内容

---

## 2. 理论语义

`TACHI_CROWD_FAILURE` 当前固定代表：

`先有 crowd extreme，再有 failure reclaim。`

它的最小行为链是：

1. 一段明显的一致性下压先形成 crowd extreme
2. 价格被打到近期极端并压在 `ma20` 下方
3. 当日继续下探形成 washout break
4. 下探没有延续，转而出现 reclaim
5. 收盘重新站回短期 reclaim 参考位上方

它不是“逢反向就做”，也不是“任何大阴后反弹都算”。

---

## 3. 正式 Detector 边界

第一轮 `TACHI_CROWD_FAILURE` 当前只允许使用下面这些日线对象：

1. `prior_high`
2. `crowd_low`
3. `selloff_high`
4. `recent_close`
5. `selloff_down_ratio`
6. `stretch_close_pos`
7. `ma20_ref`
8. `today_low / today_open / today_high / today_close`
9. `washout_break`
10. `recent_reclaim_ref`
11. `close_pos`
12. `volume`
13. `volume_ma20`
14. `volume_ratio`

当前 detector 的观察窗口固定为：

1. `prior_window = 最近第 31 ~ 12 根日线`
2. `selloff_window = 最近第 11 ~ 2 根日线`
3. `today = 最新 1 根日线`

---

## 4. 参数表

| 参数 | 当前规则 | 含义 |
|---|---|---|
| `required_window` | `31` | 最小历史窗口长度 |
| `crowd_drawdown_min` | `0.15` | crowd extreme 最小回撤幅度 |
| `crowd_down_ratio_min` | `0.60` | selloff window 内下跌日比例下限 |
| `stretch_close_pos_max` | `0.35` | selloff 末端收盘必须靠近区间低位 |
| `ma20_discount_min` | `0.02` | recent close 至少低于 `ma20` 的折价比例 |
| `washout_break_pct` | `0.01` | 当日低点必须向下刺穿 `crowd_low` 的比例 |
| `reclaim_break_pct` | `0.003` | 当日收盘必须重新站回 `recent_reclaim_ref` 的比例 |
| `close_pos_min` | `0.65` | 当日收盘必须位于日内区间上部 |
| `volume_mult` | `max(1.05, Settings().pas_bof_volume_mult)` | 当前量能确认阈值 |

当前仓库默认配置下：

1. `Settings().pas_bof_volume_mult = 1.20`
2. 因此当前实际生效的 `volume_mult = 1.20`

这意味着：

`volume_mult` 当前仍临时耦合在 `BOF` 的配置口径上，它是工程复用，不是 Tachibana 理论必然。`

---

## 5. 触发链

`TACHI_CROWD_FAILURE` 当前必须依次通过下面八道门：

1. `NO_CROWD_EXTREME`
   `crowd_drawdown = (prior_high - crowd_low) / prior_high >= 0.15`
2. `NO_ONE_SIDE_SELLING`
   `selloff_down_ratio >= 0.60`
3. `SELLING_NOT_STRETCHED`
   `stretch_close_pos = (recent_close - crowd_low) / (selloff_high - crowd_low) <= 0.35`
4. `NOT_BELOW_MA20`
   `recent_close <= ma20_ref * (1 - 0.02)`
5. `NO_WASHOUT_BREAK`
   `today_low < crowd_low * (1 - 0.01)`
6. `NO_RECLAIM_CONFIRM`
   `today_close > recent_reclaim_ref * (1 + 0.003)` 且 `today_close > today_open`
7. `WEAK_CLOSE`
   `close_pos = (today_close - today_low) / (today_high - today_low) >= 0.65`
8. `LOW_VOLUME`
   `today_volume >= volume_ma20 * volume_mult`

只有八道门都通过，当前 detector 才触发。

---

## 6. 当前失效点

下面这些情况当前都应视为这条最小契约的失效来源：

1. 前面的下压并不一致，更多只是随机震荡
2. 所谓 extreme 其实没有把价格压到明确 stretch 状态
3. 当日下探虽然很深，但没有出现有效 reclaim
4. 收盘虽然翻红，但位置不够强，只是弱反弹
5. 放量不足，无法支持“crowd failure 已经被市场确认”这层解释
6. 低流动性、极端消息驱动或连续一字环境下，日线 bar 会失真

再压缩一句：

`没有 crowd extreme、没有 washout、没有 reclaim、没有强收或没有量能确认，当前 contract 都不成立。`

---

## 7. 当前不包含的内容

第一轮 `TACHI_CROWD_FAILURE` 当前明确不包含：

1. 盘口 tape-reading
2. 盘中主观读盘
3. 融券锁单或盘口博弈语义
4. 试单、加减仓、休息纪律
5. 完整仓位管理节奏
6. `IRS / MSS / account state`

这些对象都属于第二层研究，不属于当前 entry minimal contract。

---

## 8. 与 `BOF_CONTROL` 的边界

`TACHI_CROWD_FAILURE` 当前不是：

1. `PAS` 已升格新形态
2. `BOF_CONTROL` 的简单反写
3. 当前主线可直接接入的 baseline detector

它当前只是：

`Normandy 研究线里的独立 contrary detector。`

和 `BOF_CONTROL` 相比，它更强调：

1. 先有一段 crowd extreme
2. 再有 washout failure
3. 最后通过 reclaim 做确认

而不是单纯的“失败后反向加速”。

---

## 9. 当前一句话定义

`TACHI_CROWD_FAILURE` 是 Tachibana contrary doctrine 在当前仓库里的第一条最小可执行 entry 假设：先有 crowd extreme，再有 washout failure，最后由强 reclaim 确认 crowd 已经站错边。`
