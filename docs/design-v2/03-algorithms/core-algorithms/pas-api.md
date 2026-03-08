# PAS API 接口

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变 detector / registry / strategy 主骨架的前提下，对 PAS 的模块接口与批处理入口做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/pas-data-models.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容附录。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的接口整理结果，不再构成仓库现行设计权威。现行 `PAS-trigger / BOF` 正文以 `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 接口定位

当前仓库里的 `PAS` 没有独立 pipeline 包，也没有 HTTP API。

当前正式接口就是 `strategy` 子模块里的三层接口：

1. `PatternDetector` 抽象接口
2. `BofDetector` 单形态实现
3. `strategy.generate_signals()` 批处理主入口

---

## 2. Detector 接口

### 2.1 抽象基类

```python
class PatternDetector(ABC):
    name: str

    @abstractmethod
    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        ...
```

约束：

- 输入历史窗口必须按 `date` 升序
- 检测器只返回 `Signal | None`
- 检测器不做排序、不做风控、不做落库

### 2.2 当前唯一正式实现

```python
class BofDetector(PatternDetector):
    name = "bof"

    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        ...
```

当前 `BOF` 使用参数：

- `pas_bof_break_pct`
- `pas_bof_volume_mult`

---

## 3. Registry 接口

### 3.1 装配入口

```python
def get_active_detectors(config: Settings) -> list[PatternDetector]
```

当前行为：

- 只允许 `PAS_PATTERNS = ["bof"]`
- 若不是 `bof`，直接抛错

这意味着当前主线仍是：

- 单形态
- 单 detector
- 单一入口

---

## 4. Strategy 主入口

### 4.1 批处理接口

```python
def generate_signals(
    store: Store,
    candidates: list[StockCandidate],
    asof_date: date,
    config: Settings | None = None,
    run_id: str | None = None,
) -> list[Signal]
```

职责：

1. 为候选池分批加载历史窗口
2. 调 detector
3. 合并多 detector 结果
4. legacy 路径直接写 formal `l3_signals`
5. `DTT` 路径写 `_tmp_dtt_rank_stage -> l3_signal_rank_exp` 并回写入选 formal 信号

### 4.2 辅助接口

当前 `strategy.py` 内部还包含：

- `_combine_signals(...)`
- `_load_candidate_histories_batch(...)`
- `_ensure_dtt_stage_table(...)`

这些是当前 PAS 主线批处理骨架的一部分。

---

## 5. 当前 API 边界

### 5.1 正式支持

- `BOF` 单形态 detector
- `ANY` 组合规则
- `DTT` 路径下的 sidecar 排序落地
- legacy formal schema 兼容输出

### 5.2 当前不支持

- `BPB / TST / PB / CPB` 在线 detector
- 对外 HTTP API
- detector 直接消费 `IRS / MSS`
- detector 直接产生订单或仓位

---

## 6. 异常处理

| 场景 | 当前行为 |
|---|---|
| 候选池为空 | 返回空列表 |
| detector 列表为空 | 返回空列表 |
| 历史窗口不足 | 不生成信号 |
| BOF 必需字段缺失 | 不生成信号 |
| `DTT` 模式但 `run_id` 缺失 | 抛 `ValueError` |
| `PAS_PATTERNS != ["bof"]` | 抛 `ValueError` |

---

## 7. 权威结论

当前 `PAS API` 的真实核心只有一句：

`detector 负责触发，strategy.generate_signals() 负责批处理、兼容落库和 DTT sidecar 对接。`

只要记住这条，当前主线的 PAS 接口就不会再写歪。

---

## 8. 相关文档

- `pas-algorithm.md`
- `pas-data-models.md`
- `pas-information-flow.md`
- `down-to-top-integration.md`
