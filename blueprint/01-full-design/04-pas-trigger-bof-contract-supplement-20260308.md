# PAS-trigger / BOF Contract Supplement

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `PAS-trigger / BOF`  
**上游锚点**:

1. `docs/design-v2/02-modules/strategy-design.md`
2. `blueprint/01-full-design/02-mainline-design-atom-gap-checklist-20260308.md`
3. `src/contracts.py`
4. `src/strategy/pas_bof.py`
5. `src/strategy/registry.py`
6. `src/strategy/strategy.py`
7. `src/strategy/ranker.py`

---

## 1. 用途

本文只补 `PAS-trigger / BOF` 当前主线缺失的契约原子。

它不重写 `PAS-trigger / BOF` 的主线职责，只冻结 6 件事：

1. `BOF-only` 输入快照
2. 正式 `Signal` 契约
3. 兼容期字段映射
4. 检测拒绝与降级语义
5. `BOF trace` 真相源
6. 与 `l3_signal_rank_exp` 的连接边界

一句话说：

`当前主线只在线跑 BOF，但 BOF 到底看哪些字段、什么时候返回空、什么进入 formal signal、什么只进 trace，必须定死。`

---

## 2. 作用边界

本文只覆盖当前主线 `PAS-trigger / BOF`：

```text
StockCandidate
-> load history window
-> BOF detect
-> formal Signal
-> DTT rank sidecar
```

本文不覆盖：

1. `PAS-full` 三因子机会体系
2. `BPB / TST / PB / CPB` 多形态在线
3. `IRS-lite` 排序本身
4. `MSS-lite` 风险覆盖本身
5. `Broker / Risk` 的执行状态机

---

## 3. 设计来源

当前补充文的设计来源是“定向裁原子”：

1. `beta pas-data-models.md`
2. `beta pas-information-flow.md`
3. `beta pas-api.md`
4. `gamma` 当前主线正文
5. `gamma` 当前 `strategy` 代码

其中：

1. `beta` 提供完整 `PasStockSnapshot / StockPasDaily / pipeline` 的表达深度
2. `gamma` 提供当前主线的正确边界：只保留 `BOF trigger`
3. 当前代码提供已落地的字段、幂等键、sidecar 链路现实

---

## 4. BOF 阶段模型

### 4.1 阶段拆分

`PAS-trigger / BOF` 当前主线固定拆成 5 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `P0` | `candidate_accept` | `list[StockCandidate]` | 待检测候选 | 空候选则直接结束 |
| `P1` | `history_load` | `code + asof_date + lookback_days` | 历史窗口 | 历史不足或快照缺列则不生成信号 |
| `P2` | `bof_detect` | `BOF-only snapshot` | `detected / not_detected` | 任一关键条件失败则返回 `None` |
| `P3` | `formal_signal` | 触发结果 | 最小 `Signal` | 只写正式 signal 字段 |
| `P4` | `rank_attach` | `Signal + candidates + IRS/MSS sidecar inputs` | `l3_signal_rank_exp` + selected signals | 不回写 BOF 检测规则 |

### 4.2 当前实现对应

当前代码主要对应：

1. `_load_candidate_histories_batch`
2. `BofDetector.detect`
3. `_combine_signals`
4. `build_dtt_score_frame`
5. `materialize_ranked_signals`

设计层在这里要钉住的是阶段边界，不是绑死函数名。

---

## 5. BOF-only 输入快照

### 5.1 契约定位

当前主线不直接使用 `beta` 的完整 `PasStockSnapshot`。

当前只从中裁出一份 `BOF-only snapshot`，供 `BofDetector` 使用。

它的语义固定为：

`足够支持 BOF 判定的最小历史窗口快照。`

### 5.2 必需字段

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `code` | `str` | `Required` | 6 位股票代码 |
| `signal_date` | `date` | `Required` | 当前候选检测日 |
| `date` | `date` | `Required` | 历史窗口日期列 |
| `adj_low` | `float` | `Required` | 复权最低价 |
| `adj_close` | `float` | `Required` | 复权收盘价 |
| `adj_open` | `float` | `Required` | 复权开盘价 |
| `adj_high` | `float` | `Required` | 复权最高价 |
| `volume` | `float` | `Required` | 当日成交量 |
| `volume_ma20` | `float` | `Required` | 20 日平均成交量 |

### 5.3 运行时约束

`BOF-only snapshot` 必须满足：

1. 历史窗口按 `date` 升序。
2. 至少要有 21 行，且最近 20 根前视窗口可用。
3. 输入列必须完整，否则直接视为检测失败。
4. `signal_date` 固定等于窗口最后一行日期。

### 5.4 当前主线与 beta 的裁剪关系

从 `beta PasStockSnapshot` 中，本轮明确不带入：

1. `stock_name`
2. `industry_code`
3. `limit_up_count_120d / new_high_count_60d`
4. `high_20d / high_60d / high_120d`
5. `quality_flag / sample_days / adaptive_window`

原因很简单：

`这些字段属于 PAS-full 的因子体系，不是当前 BOF trigger 的最小检测输入。`

---

## 6. BOF 判定契约

### 6.1 当前正式条件

当前 `BOF` 判定固定为：

1. `today_low < lower_bound * (1 - break_pct)`
2. `today_close >= lower_bound`
3. `close_pos >= 0.6`
4. `today_volume >= volume_ma20 * volume_mult`

其中：

1. `lower_bound = min(lookback[-20:]["adj_low"])`
2. `close_pos = (today_close - today_low) / (today_high - today_low)`

### 6.2 当前配置项

当前正式配置项只有：

1. `PAS_LOOKBACK_DAYS`
2. `PAS_MIN_HISTORY_DAYS`
3. `PAS_EVAL_BATCH_SIZE`
4. `PAS_BOF_BREAK_PCT`
5. `PAS_BOF_VOLUME_MULT`
6. `PAS_PATTERNS`
7. `PAS_COMBINATION`

### 6.3 主线不变量

无论实现怎么调整，下面这些不变量不能变：

1. 当前只允许 `PAS_PATTERNS=bof`
2. `Signal.action` 固定为 `BUY`
3. `Signal.pattern` 固定为 `bof`
4. 不读取 `IRS / MSS / account state`
5. 不在检测阶段做最终排序或风控截断

---

## 7. 正式 Signal 契约

### 7.1 契约定位

`Signal` 是 `PAS-trigger / BOF -> Broker / Risk` 的正式跨模块结果契约。

在当前主线里，它的语义固定为：

`这只股票在 T 日收盘后触发了一个可进入下游排序与执行链的最小 BUY 信号。`

### 7.2 正式稳定字段

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `signal_id` | `str` | `Required` | 由 `build_signal_id(code, signal_date, pattern)` 生成 |
| `code` | `str` | `Required` | 6 位股票代码 |
| `signal_date` | `date` | `Required` | `T` 日 |
| `action` | `Literal["BUY"]` | `Required` | 当前主线只允许买入触发 |
| `strength` | `float` | `Required` | `0-1`，当前 BOF 最小强度分 |
| `pattern` | `str` | `Required` | 固定为 `bof` |
| `reason_code` | `str` | `Required` | 固定为 `PAS_BOF` |

### 7.3 正式契约不变量

1. 同一 `(code, signal_date, pattern)` 只能生成一个 `signal_id`。
2. 当前主线下 `signal_id` 的格式固定为：
   - `{code}_{signal_date.isoformat()}_{pattern}`
3. 正式 `l3_signals` 只写最小字段，不写 `IRS / MSS / final_rank`。
4. 若一个候选股票当日未触发 BOF，不生成 formal signal 空壳。

---

## 8. 兼容期字段映射

### 8.1 当前代码现实

当前 `Signal` 模型在 `src/contracts.py` 中已经带了迁移期扩展字段：

1. `bof_strength`
2. `irs_score`
3. `mss_score`
4. `final_score`
5. `final_rank`
6. `variant`

但 `to_formal_signal_row()` 只导出：

1. `signal_id`
2. `code`
3. `signal_date`
4. `action`
5. `strength`
6. `pattern`
7. `reason_code`

### 8.2 兼容期映射规则

在当前主线中，统一采用：

| 正式目标字段 | 兼容期字段 | 规则 |
|---|---|---|
| `strength` | `strength` | formal 最小字段 |
| `bof_strength` | `bof_strength` | 若缺失，则回填为 `strength` |
| `variant` | `variant` | 只进 sidecar，不进 formal signal |
| `irs_score / mss_score / final_score / final_rank` | 同名扩展字段 | 只进 sidecar 与下游运行时对象 |

### 8.3 当前实现约束

从本补充文生效起，兼容期必须遵守：

1. `bof_strength` 是 `strength` 的解释性别名，不得另起一套检测逻辑。
2. `final_score / final_rank` 只能来自 `ranker`，不能在 detector 中提前写。
3. `variant` 只描述当前 DTT 变体，不描述 detector 规则版本。

---

## 9. 检测拒绝与降级语义

### 9.1 检测失败分类

当前主线统一把 BOF 未产出分成两类：

| 类别 | 含义 | 去向 |
|---|---|---|
| `DETECT_SKIP` | 输入条件不满足，无法判定 | 只进 trace |
| `DETECT_FAIL` | 输入存在，但 BOF 条件不成立 | 只进 trace |

### 9.2 统一原因

建议统一以下检测原因：

| `detect_reason` | 含义 |
|---|---|
| `EMPTY_HISTORY` | 历史窗口为空 |
| `INSUFFICIENT_HISTORY` | 历史长度不足 `PAS_MIN_HISTORY_DAYS` 或 BOF 最小 21 日窗口 |
| `MISSING_REQUIRED_COLUMNS` | 关键列缺失 |
| `INVALID_RANGE` | `today_high <= today_low`，无法计算 `close_pos` |
| `BREAK_NOT_CONFIRMED` | 下破条件不成立 |
| `RECOVER_NOT_CONFIRMED` | 收盘回收条件不成立 |
| `CLOSE_POS_NOT_CONFIRMED` | 收盘位置不成立 |
| `VOLUME_NOT_CONFIRMED` | 量能放大条件不成立 |

### 9.3 降级规则

当前主线统一采用：

| 场景 | 处理 |
|---|---|
| `history < PAS_MIN_HISTORY_DAYS` | 不生成 signal |
| `history < 21` | 不生成 signal |
| `volume_ma20 <= 0` | 视为 `VOLUME_NOT_CONFIRMED` |
| 缺关键列 | 不做补列，不回退旧表，直接跳过 |
| 同批次无任何触发 | 返回空列表，非异常 |

### 9.4 不允许的降级

下面这些回退不被允许：

1. 用前一日 signal 顶替当日信号
2. 用 `IRS / MSS` 分数替代 BOF 未触发
3. 因为要凑样本而放宽 formal BOF 条件

---

## 10. BOF Trace 真相源

### 10.1 为什么必须单独有 trace

formal signal 只告诉我们：

`触发了。`

但下面这些问题必须单独追：

1. 为什么某只候选没触发
2. 是历史不够，还是条件差一点
3. `strength` 是怎么来的
4. 排序变化来自 BOF 强度，还是来自 IRS 后置增强

### 10.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`pas_trigger_trace_exp`

它不是正式跨模块契约，而是当前 BOF 检测真相源。

### 10.3 建议字段

| 字段 | 说明 |
|---|---|
| `run_id` | 运行唯一标识 |
| `signal_date` | 信号日 |
| `code` | 股票代码 |
| `pattern` | 固定 `bof` |
| `candidate_rank` | 上游候选排名 |
| `history_days` | 可用历史样本数 |
| `lower_bound` | BOF 下界 |
| `today_low` | 当日低点 |
| `today_close` | 当日收盘 |
| `today_open` | 当日开盘 |
| `today_high` | 当日高点 |
| `close_pos` | 收盘位置 |
| `volume_ratio` | `today_volume / volume_ma20` |
| `break_pct` | 当前配置 |
| `volume_mult` | 当前配置 |
| `detected` | 是否触发 |
| `detect_reason` | 若未触发，记录原因 |
| `bof_strength` | 若触发，记录强度 |
| `signal_id` | 若触发，记录正式信号 ID |
| `created_at` | 写入时间 |

### 10.4 Trace 不变量

1. 每个 `(run_id, signal_date, code, pattern)` 最多一行。
2. `detected=True` 的行必须能映射到 formal `Signal`。
3. `detected=False` 的行不得生成 formal `Signal`。
4. `pas_trigger_trace_exp` 只解释检测，不承载最终排序。

---

## 11. 和 DTT rank sidecar 的连接规则

当前主线已经有一个正式的排序真相源：

`l3_signal_rank_exp`

它的职责固定为：

1. 保存已触发 signal 的 `bof_strength`
2. 附着 `irs_score / mss_score / final_score / final_rank`
3. 标记 `selected`

因此连接边界必须固定为：

| 表/对象 | 职责 |
|---|---|
| `pas_trigger_trace_exp` | 解释“为什么触发或不触发” |
| `l3_signal_rank_exp` | 解释“触发之后为什么这样排序 / 是否入选” |
| `l3_signals` | 保存 formal 最小 signal |

三者不能混写。

---

## 12. 和下游的稳定连接

### 12.1 与 IRS-lite

`IRS-lite` 只消费已触发 signal。

因此：

1. `IRS` 不得回写 BOF 检测结论
2. `IRS` 只能附加后置分数

### 12.2 与 Broker / Risk

`Broker / Risk` 只消费 formal signal 和后续排序结果。

因此：

1. `Broker / Risk` 不得根据未触发候选补单
2. `Broker / Risk` 不得重算 BOF

---

## 13. 当前与后续

### 13.1 本文冻结的东西

本文已经冻结了：

1. `BOF-only snapshot` 最小输入
2. formal `Signal` 最小字段
3. 兼容期扩展字段边界
4. 检测失败与降级口径
5. `pas_trigger_trace_exp`
6. 与 `l3_signal_rank_exp` 的职责分界

### 13.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 增加 `pas_trigger_trace_exp` 或同等 artifact
2. 把 `detect_reason / detected` 正式落到 trace
3. 补 `signal_id -> l3_signal_rank_exp` 的完整追溯链
4. 校验 `bof_strength` 与 `strength` 的一致性

### 13.3 本文明确不做什么

本文不授权下面这些回退：

1. 把 `PAS-full` 再塞回当前主线
2. 把 `BPB / TST / PB / CPB` 直接并入当前在线 detector
3. 因为要更快做 MVP，就把 formal signal 压成“只要 code 就算触发”
