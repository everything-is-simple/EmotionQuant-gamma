# MSS API 接口

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变当前主线模块边界的前提下，对 MSS 的模块接口、批处理入口与 Broker 消费方式做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/mss-data-models.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/selector/mss.py`, `src/broker/risk.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容附录。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的接口整理结果，不再构成仓库现行设计权威。现行 `MSS-lite` 正文以 `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 接口定位

当前仓库没有单独的 `MSS` Web API。

当前有效接口只有两类：

1. 算法计算接口：`src/selector/mss.py`
2. 执行消费接口：`src/broker/risk.py`

本文描述的是这两类 Python 模块接口，不讨论 HTTP 封装。

---

## 2. 算法计算接口

### 2.1 单日纯函数

```python
def compute_mss_single(
    row: pd.Series,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> MarketScore:
```

职责：

- 输入一行 `l2_market_snapshot`
- 输出单日 `MarketScore`

返回：

- `MarketScore(date, score, signal)`

### 2.2 批量计算入口

```python
def compute_mss(
    store: Store,
    start: date,
    end: date,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> int:
```

职责：

1. 读取 `l2_market_snapshot`
2. 批量计算 `MSS`
3. 幂等写入 `l3_mss_daily`

返回：

- 写入行数

### 2.3 辅助接口

```python
def build_mss_raw_frame(snapshot_df: pd.DataFrame) -> pd.DataFrame

def calibrate_mss_baseline(raw_df: pd.DataFrame) -> dict[str, float]

def score_mss_raw_frame(
    raw_df: pd.DataFrame,
    baseline: dict[str, float] | None = None,
    bullish_threshold: float = 65.0,
    bearish_threshold: float = 35.0,
) -> pd.DataFrame
```

用途：

- 生成原始因子表
- 重新校准 baseline
- 对原始因子表离线打分

这些接口主要用于：

- 研究
- 消融
- baseline 重算
- 证据回放

---

## 3. 执行消费接口

### 3.1 RiskManager 入口

当前 `MSS` 的正式消费方是：

```python
class RiskManager:
    def assess_signal(self, signal: Signal, state: BrokerRiskState) -> RiskDecision:
    def check_signal(self, signal: Signal, state: BrokerRiskState) -> Order | None:
```

### 3.2 内部消费路径

`RiskManager` 会在 `assess_signal()` 内部：

1. 按 `signal.signal_date` 读取 `l3_mss_daily`
2. 生成 `MssRiskOverlay`
3. 动态调整：
   - `max_positions`
   - `risk_per_trade_pct`
   - `max_position_pct`
4. 再完成最小 lot、现金、持仓占用等风险判断

### 3.3 当前约束

当前主线中，`RiskManager` 只允许把 `MSS` 用作：

- 风险预算倍率
- 持仓上限倍率
- 单笔仓位倍率

不允许把 `MSS` 用作：

- 排序分数
- 前置停手
- 候选池裁剪

---

## 4. 异常与兜底

### 4.1 计算层

| 场景 | 当前行为 |
|---|---|
| 输入快照为空 | 返回空结果或 0 行写入 |
| baseline 缺失 | 回退到 `MSS_BASELINE` |
| 总股票数为 0 | 用 `safe_ratio(..., default=0.0)` 兜底 |
| 分母为 0 | 回退到 0 或中性值 |

### 4.2 执行层

| 场景 | 当前行为 |
|---|---|
| `mss_risk_overlay_enabled = false` | 直接使用基础风险参数 |
| `l3_mss_daily` 缺失 | 按 `NEUTRAL + DTT_SCORE_FILL` 兜底 |
| `signal` 非法 | 强制落回 `NEUTRAL` |

---

## 5. 当前接口边界

### 5.1 正式支持

当前正式支持：

- `MSS` 计算到 `l3_mss_daily`
- `RiskManager` 读取 `l3_mss_daily`
- `MSS` 调节执行风险参数

### 5.2 明确不支持

当前不支持：

- `MSS` 直接参与 `ranker.py` 横截面排序
- `MSS` 作为 `Selector` 过滤器
- 对外 HTTP API
- 市场状态事件订阅流

---

## 6. 权威结论

当前 `MSS API` 的真正边界是：

`compute_mss(...) 负责把市场快照变成 l3_mss_daily；RiskManager 负责把 l3_mss_daily 变成执行层风险折扣。`

这就是当前主线接口，不多也不少。

---

## 7. 相关文档

- `mss-algorithm.md`
- `mss-data-models.md`
- `mss-information-flow.md`
- `down-to-top-integration.md`
