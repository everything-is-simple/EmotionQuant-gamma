# MSS-lite 数据模型（当前执行版）

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变 v0.01 Frozen 历史口径的前提下，对 MSS 当前主线的数据依赖、输出字段与执行层消费方式做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/selector/mss.py`, `src/contracts.py`, `src/broker/risk.py`

---

## 1. 定位

本文只回答三件事：

1. `MSS` 当前主线读哪些数据。
2. `MSS` 当前主线产出哪些字段。
3. `Broker / Risk` 当前主线如何消费这些字段。

它不讨论：
- `v0.01 Frozen` 旧 gate 语义。
- `MSS-full` 的完整周期系统最终定稿。
- GUI 或 HTTP 展示协议。

当前主线下，`MSS` 的角色已经收口为：

`市场级风险调节因子。`

但需要明确：

- 当前在线的是 `MSS-lite`
- 原始理论中的 `phase / trend / phase_days / position_advice` 仍然有效
- 这些字段已在 `Spec-04` 中恢复为正式扩展目标

参见：

- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`

---

## 2. 输入模型

### 2.1 主输入表

当前实现只读取：

- `l2_market_snapshot`

### 2.2 当前依赖字段

| 字段 | 用途 |
|---|---|
| `date` | 交易日 |
| `total_stocks` | 全市场股票总数 |
| `rise_count` | 上涨家数 |
| `limit_up_count` | 涨停家数 |
| `touched_limit_up_count` | 触及涨停家数 |
| `strong_up_count` | 强上涨家数 |
| `limit_down_count` | 跌停家数 |
| `strong_down_count` | 强下跌家数 |
| `new_100d_high_count` | 100 日新高家数 |
| `new_100d_low_count` | 100 日新低家数 |
| `continuous_limit_up_2d` | 连续 2 日涨停家数 |
| `continuous_limit_up_3d_plus` | 连续 3 日及以上涨停家数 |
| `continuous_new_high_2d_plus` | 连续 2 日及以上新高家数 |
| `high_open_low_close_count` | 高开低走极端家数 |
| `low_open_high_close_count` | 低开高走极端家数 |
| `pct_chg_std` | 全市场涨跌幅标准差 |
| `amount_volatility` | 成交额波动 |

### 2.3 输入对象

当前运行时输入对象不是单独 dataclass，而是：

- `l2_market_snapshot` 的单日行记录
- 经 `src/selector/mss.py` 内部转换后形成原始因子字典

可视为逻辑输入模型：

```python
class MssSnapshot:
    date: date
    total_stocks: int
    rise_count: int
    limit_up_count: int
    touched_limit_up_count: int
    strong_up_count: int
    limit_down_count: int
    strong_down_count: int
    new_100d_high_count: int
    new_100d_low_count: int
    continuous_limit_up_2d: int
    continuous_limit_up_3d_plus: int
    continuous_new_high_2d_plus: int
    high_open_low_close_count: int
    low_open_high_close_count: int
    pct_chg_std: float
    amount_volatility: float
```

---

## 3. 中间因子模型

### 3.1 原始因子

当前 `src/selector/mss.py` 会先计算 6 个原始因子：

- `market_coefficient_raw`
- `profit_effect_raw`
- `loss_effect_raw`
- `continuity_raw`
- `extreme_raw`
- `volatility_raw`

### 3.2 标准化后因子

随后映射成当前主线使用的 6 个标准化因子：

- `market_coefficient`
- `profit_effect`
- `loss_effect`
- `continuity`
- `extreme`
- `volatility`

这些字段当前不会通过正式契约向外暴露，但会写入 `l3_mss_daily` 供追溯和解释。

---

## 4. 输出模型

### 4.1 当前结果契约对象

当前正式结果契约仍是 `src/contracts.py` 中的 `MarketScore`：

```python
class MarketScore(BaseModel):
    date: date
    score: float
    signal: Literal["BULLISH", "NEUTRAL", "BEARISH"]
```

### 4.2 当前主表

当前主线写入：

- `l3_mss_daily`

当前写入字段包括：

| 字段 | 含义 |
|---|---|
| `date` | 交易日 |
| `score` | 0-100 市场温度 |
| `signal` | `BULLISH / NEUTRAL / BEARISH` |
| `market_coefficient` | 标准化后大盘系数 |
| `profit_effect` | 标准化后赚钱效应 |
| `loss_effect` | 标准化后亏钱效应 |
| `continuity` | 标准化后连续性 |
| `extreme` | 标准化后极端因子 |
| `volatility` | 标准化后波动因子 |

### 4.3 Spec-04 扩展字段（正式预留）

为恢复原始 `MSS-full` 中的周期系统，`l3_mss_daily` 需要正式预留以下字段：

| 字段 | 含义 |
|---|---|
| `phase` | 七阶段周期：`EMERGENCE / FERMENTATION / ACCELERATION / DIVERGENCE / CLIMAX / DIFFUSION / RECESSION` |
| `phase_trend` | 周期方向：`UP / DOWN / SIDEWAYS` |
| `phase_days` | 当前阶段持续天数 |
| `position_advice` | 原始仓位建议区间，如 `60%-80%` |
| `risk_regime` | 执行层风险状态，如 `OPEN / MODERATE / DEFENSIVE / MINIMAL` |

说明：

1. `score / signal` 继续保留，作为兼容字段。
2. `phase / phase_trend / phase_days / position_advice` 主要服务解释层与证据层。
3. `risk_regime` 主要服务 `Broker / Risk`。

### 4.4 执行层派生对象

`Broker / Risk` 当前会基于 `l3_mss_daily + config` 派生运行时对象：

```python
@dataclass(frozen=True)
class MssRiskOverlay:
    signal: str
    score: float
    phase: str | None
    phase_trend: str | None
    phase_days: int | None
    position_advice: str | None
    risk_regime: str | None
    max_positions: int
    risk_per_trade_pct: float
    max_position_pct: float
```

这个对象不落正式表，但它是当前主线真正的执行层消费模型。

说明：

- 当前代码层已稳定消费 `signal / score`
- `phase / phase_trend / phase_days / position_advice / risk_regime` 属于本轮正式预留的下一批扩展消费面

---

## 5. 消费边界

### 5.1 当前主线消费者

当前主线中，`MSS` 的唯一正式消费者是：

- `src/broker/risk.py`

### 5.2 不再允许的消费者

以下消费方式已不属于当前主线：

- `Selector` 读取 `MSS` 做前置 gate
- `Selector` 根据 `MSS` 缩小 `candidate_top_n`
- `Strategy / Ranker` 把 `MSS` 写进横截面 `final_score`

### 5.3 当前消费语义

当前主线语义为：

`MSS -> 风险折扣 -> 实际执行容量`

具体落点：

- `max_positions`
- `risk_per_trade_pct`
- `max_position_pct`

---

## 6. 缺失值与兜底

当前实现口径：

1. 若 `l3_mss_daily` 当日无记录：
   - `signal = NEUTRAL`
   - `score = DTT_SCORE_FILL`

2. 若 `signal` 非法：
   - 强制回落为 `NEUTRAL`

3. 当前主线不允许因为 `MSS` 缺失而中断 `DTT` 链路。

---

## 7. 预留扩展字段

若后续继续增强 `MSS` 风控层，可在不破坏当前主线的前提下扩展：

- `gross_exposure_cap`
- `entry_cooldown`
- `rebalance_bias`
- `position_band`
- `cycle_confidence`
- `trend_quality`

但这些字段目前都不属于当前主线正式契约。

---

## 8. 权威结论

当前 `MSS` 数据模型的核心结论只有两条：

1. 正式结果契约仍然是 `MarketScore(date, score, signal)`。
2. 当前主线真正使用的是它在执行层派生出的 `MssRiskOverlay`，而不是旧时代的 Selector gate 语义。
3. `phase / phase_trend / phase_days / position_advice / risk_regime` 已正式进入当前数据模型的扩展目标，不再只是口头上的“以后可补”。

---

## 9. 相关文档

- `mss-algorithm.md`
- `mss-api.md`
- `mss-information-flow.md`
- `down-to-top-integration.md`

