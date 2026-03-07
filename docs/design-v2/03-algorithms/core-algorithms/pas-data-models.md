# PAS 数据模型

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变当前 PAS detector 架构与 v0.01-plus 主线边界的前提下，对 PAS 输入、输出与 sidecar 追溯字段做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/strategy.py`, `src/contracts.py`

---

## 1. 定位

当前 `gamma` 主线里的 `PAS`，不是 beta 时代的“个股机会总分系统”。

当前它的正式定位是：

`价格行为触发器框架。`

在 `v0.01-plus` 当前主线里，`PAS` 只负责回答：

`候选池中的这只股票，今天是否触发 BOF。`

---

## 2. 输入模型

### 2.1 Detector 输入接口

当前所有形态检测器都遵守：

```python
class PatternDetector(ABC):
    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
```

输入包括：

- `code`
- `asof_date`
- `df`：按 `date` 升序排列的历史窗口数据

### 2.2 BOF 当前依赖字段

当前 `BofDetector` 依赖以下列：

| 字段 | 用途 |
|---|---|
| `code` | 股票代码 |
| `date` | 交易日 |
| `adj_low` | 假突破与下边界判断 |
| `adj_close` | 收回判断 |
| `adj_open` | 实体占比 |
| `adj_high` | 收盘位置判断 |
| `volume` | 当日成交量 |
| `volume_ma20` | 量能确认 |

### 2.3 历史窗口约束

当前 `BOF` 最小窗口要求：

- 至少 `21` 条记录
- 其中最近 20 日用于构造 `lower_bound`

---

## 3. 正式输出模型

### 3.1 Formal Signal

当前 PAS detector 的正式输出仍是 `src/contracts.py` 的 `Signal`：

```python
class Signal(BaseModel):
    signal_id: str
    code: str
    signal_date: date
    action: Literal["BUY"]
    strength: float
    pattern: str
    reason_code: str
    bof_strength: float | None = None
    irs_score: float | None = None
    mss_score: float | None = None
    final_score: float | None = None
    final_rank: int | None = None
    variant: str | None = None
```

### 3.2 当前正式落库字段

`Signal.to_formal_signal_row()` 当前只保留兼容字段写入 `l3_signals`：

- `signal_id`
- `code`
- `signal_date`
- `action`
- `strength`
- `pattern`
- `reason_code`

### 3.3 当前 sidecar 扩展字段

当前主线中，以下字段只在运行时和 `l3_signal_rank_exp` 中使用：

- `bof_strength`
- `irs_score`
- `mss_score`
- `final_score`
- `final_rank`
- `variant`

这就是当前 PAS / DTT 的兼容迁移策略。

---

## 4. 当前 BOF 输出语义

### 4.1 输出对象

当前 `BofDetector.detect()` 触发后返回：

- `action = BUY`
- `pattern = bof`
- `reason_code = PAS_BOF`
- `strength`：0-1 的 BOF 强度

### 4.2 `strength` 与 `bof_strength`

当前实现中：

- detector 先产出 `strength`
- `strategy.generate_signals()` 在 `DTT` 路径下把它显式抬升为 `bof_strength`

因此当前应理解为：

`strength` 是 formal 兼容字段，`bof_strength` 是排序解释字段。

---

## 5. 运行时中间模型

### 5.1 Candidate 输入

`Strategy.generate_signals()` 当前接收：

```python
class StockCandidate(BaseModel):
    code: str
    industry: str
    score: float
    preselect_score: float | None = None
    filter_reason: str | None = None
    liquidity_tag: str | None = None
```

当前主线里，`PAS` 只依赖：

- `code`
- `industry`（供后续 `IRS` 映射）
- `preselect_score`（仅用于候选准备追溯，不参与 BOF 判定）

### 5.2 排序 sidecar

`strategy.generate_signals()` 在 `DTT` 模式下会先写 `_tmp_dtt_rank_stage`，再生成 `l3_signal_rank_exp`。

逻辑字段包括：

- `run_id`
- `signal_id`
- `signal_date`
- `code`
- `industry`
- `variant`
- `bof_strength`
- `irs_score`
- `mss_score`
- `final_score`
- `final_rank`
- `selected`

---

## 6. 边界约束

### 6.1 PAS 当前只做触发

当前主线里，`PAS` 不负责：

- 行业评分
- 市场评分
- 仓位控制
- 最终订单数

### 6.2 不允许重新回到旧 PAS 评分系统

以下能力不属于当前 `PAS` 数据模型：

- 牛股基因总分
- 个股机会总分
- MSS/IRS 混合进 detector 输入
- detector 直接输出仓位建议

这些能力如果未来恢复，必须作为新版本专项，不得混入当前主线。

---

## 7. 权威结论

当前 `PAS` 数据模型的核心结论只有一句：

`PAS 当前只产出最小 BUY 触发信号；排序解释和执行扩展一律走 sidecar，不污染 formal schema。`

---

## 8. 相关文档

- `pas-algorithm.md`
- `pas-api.md`
- `pas-information-flow.md`
- `down-to-top-integration.md`

