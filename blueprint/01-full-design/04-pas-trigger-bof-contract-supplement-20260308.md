# PAS Trigger Contract Supplement

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `PAS Trigger / Registry`  
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

本文只补 `PAS Trigger / Registry` 当前主线缺失的契约原子。

它不重写 `PAS` 主正文，只冻结 6 件事：

1. 统一输入快照
2. 正式 `Signal` 契约
3. 兼容期字段映射
4. 检测拒绝与降级语义
5. `pas_trigger_trace_exp` 真相源
6. 与 `l3_signal_rank_exp` 的连接边界

一句话说：

`当前主线 formal signal、trace、sidecar 怎么切层，必须定死；至于五形态算法本体，统一以上游 PAS 主正文为准。`

---

## 2. 作用边界

本文只覆盖当前主线 `PAS Trigger / Registry`：

```text
StockCandidate
-> load history window
-> pattern registry (BOF / BPB / PB / TST / CPB)
-> formal Signal
-> DTT rank sidecar
```

本文不覆盖：

1. `PAS-full` 三因子机会体系
2. `pattern_quality_score / reference layer` 具体算法
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
2. `gamma` 提供当前主线正确边界：formal `Signal`、trace 与 sidecar 分层
3. 当前代码提供已落地的字段、幂等键、sidecar 链路现实

---

## 4. PAS Trigger 阶段模型

### 4.1 阶段拆分

`PAS Trigger / Registry` 当前主线固定拆成 5 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `P0` | `candidate_accept` | `list[StockCandidate]` | 待检测候选 | 空候选则直接结束 |
| `P1` | `history_load` | `code + asof_date + lookback_days` | 历史窗口 | 历史不足或快照缺列则不生成信号 |
| `P2` | `registry_detect` | `PAS snapshot + PAS_PATTERNS` | `detected / not_detected` | 任一 detector 失败只记 trace，不造信号 |
| `P3` | `formal_signal` | 触发结果 | 最小 `Signal` | 只写正式 signal 字段 |
| `P4` | `rank_attach` | `Signal + candidates + IRS/MSS sidecar inputs` | `l3_signal_rank_exp` + selected signals | 不回写 detector 规则 |

### 4.2 当前实现对应

当前代码主要对应：

1. `_load_candidate_histories_batch`
2. `BofDetector.detect`
3. `get_active_detectors`
4. `_combine_signals`
5. `build_dtt_score_frame`
6. `materialize_ranked_signals`

设计层在这里要钉住的是阶段边界，不是绑死函数名。

---

## 5. PAS 输入快照

### 5.1 契约定位

当前主线不直接使用 `beta` 的完整 `PasStockSnapshot`。

当前只从中裁出一份统一 `PAS snapshot`，供五形态 detector 使用。

它的语义固定为：

`足够支持当前 PAS 五形态判定的最小历史窗口快照。`

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

`PAS snapshot` 必须满足：

1. 历史窗口按 `date` 升序
2. 至少要有 `PAS_MIN_HISTORY_DAYS` 行
3. 输入列必须完整，否则直接视为检测失败
4. `signal_date` 固定等于窗口最后一行日期

### 5.4 当前主线与 beta 的裁剪关系

从 `beta PasStockSnapshot` 中，本轮明确不带入：

1. `stock_name`
2. `industry_code`
3. `quality_flag / sample_days / adaptive_window`
4. 任何需要跨模块才能补齐的派生列

原因很简单：

`这些字段要么属于 PAS 主正文里的质量层，要么属于历史全量生态，不是当前 formal trigger 契约的最小输入。`

---

## 6. Trigger 判定契约

### 6.1 当前正式 pattern 范围

当前 `PAS Trigger` 在契约层固定支持：

1. `bof`
2. `bpb`
3. `pb`
4. `tst`
5. `cpb`

### 6.2 当前配置项

当前正式配置项至少包括：

1. `PAS_LOOKBACK_DAYS`
2. `PAS_MIN_HISTORY_DAYS`
3. `PAS_EVAL_BATCH_SIZE`
4. `PAS_PATTERNS`
5. `PAS_COMBINATION`
6. pattern-specific 参数组

### 6.3 主线不变量

无论实现怎么调整，下面这些不变量不能变：

1. `Signal.action` 固定为 `BUY`
2. `Signal.pattern` 必须属于 `{bof,bpb,pb,tst,cpb}`
3. `Signal.reason_code` 必须为 `PAS_<PATTERN>` 风格
4. 不读取 `IRS / MSS / account state`
5. 不在检测阶段做最终排序或风控截断

### 6.4 当前代码现实

截至 `2026-03-09`，当前代码现实仍是：

1. 只正式落了 `BOF detector`
2. `registry` 当前只启 `bof`

这属于实现滞后，不构成契约边界本身。

---

## 7. 正式 Signal 契约

### 7.1 契约定位

`Signal` 是 `PAS Trigger -> Broker / Risk` 的正式跨模块结果契约。

在当前主线里，它的语义固定为：

`这只股票在 T 日收盘后触发了一个可进入下游排序与执行链的最小 BUY 信号。`

### 7.2 正式稳定字段

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `signal_id` | `str` | `Required` | 由 `build_signal_id(code, signal_date, pattern)` 生成 |
| `code` | `str` | `Required` | 6 位股票代码 |
| `signal_date` | `date` | `Required` | `T` 日 |
| `action` | `Literal["BUY"]` | `Required` | 当前主线只允许买入触发 |
| `strength` | `float` | `Required` | `0-1`，当前选中 pattern 的通用强度分 |
| `pattern` | `str` | `Required` | 当前命中的 pattern |
| `reason_code` | `str` | `Required` | `PAS_BOF / PAS_BPB / PAS_PB / PAS_TST / PAS_CPB` |

### 7.3 正式契约不变量

1. 同一 `(code, signal_date, pattern)` 只能生成一个 `signal_id`
2. 当前主线下 `signal_id` 的格式固定为：
   - `{code}_{signal_date.isoformat()}_{pattern}`
3. 正式 `l3_signals` 只写最小字段，不写 `IRS / MSS / final_rank`
4. 若一个候选股票当日未触发任何 pattern，不生成 formal signal 空壳

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
| `bof_strength` | `bof_strength` | 历史别名；仅在 `selected_pattern=bof` 时可保留语义 |
| `variant` | `variant` | 只进 sidecar，不进 formal signal |
| `irs_score / mss_score / final_score / final_rank` | 同名扩展字段 | 只进 sidecar 与下游运行时对象 |

### 8.3 当前实现约束

从本补充文生效起，兼容期必须遵守：

1. `bof_strength` 不得再被理解成“所有 PAS signal 的正式强度”
2. `final_score / final_rank` 只能来自 `ranker`，不能在 detector 中提前写
3. `variant` 只描述当前 DTT 变体，不描述 detector 规则版本

---

## 9. 检测拒绝与降级语义

### 9.1 检测失败分类

当前主线统一把 PAS 未产出分成两类：

| 类别 | 含义 | 去向 |
|---|---|---|
| `DETECT_SKIP` | 输入条件不满足，无法判定 | 只进 trace |
| `DETECT_FAIL` | 输入存在，但当前 pattern 条件不成立 | 只进 trace |

### 9.2 统一原因

建议统一以下通用检测原因：

| `detect_reason` | 含义 |
|---|---|
| `EMPTY_HISTORY` | 历史窗口为空 |
| `INSUFFICIENT_HISTORY` | 历史长度不足 `PAS_MIN_HISTORY_DAYS` |
| `MISSING_REQUIRED_COLUMNS` | 关键列缺失 |
| `INVALID_RANGE` | `today_high <= today_low`，无法计算结构观测 |
| `NOT_TRIGGERED` | 当前 pattern 未满足正式条件 |

pattern-specific 原因允许继续扩，但必须落到 trace 中，而不是只存在代码常量里。

### 9.3 降级规则

当前主线统一采用：

| 场景 | 处理 |
|---|---|
| `history < PAS_MIN_HISTORY_DAYS` | 不生成 signal |
| 缺关键列 | 不做补列，不回退旧表，直接跳过 |
| 同批次无任何触发 | 返回空列表，非异常 |

### 9.4 不允许的降级

下面这些回退不被允许：

1. 用前一日 signal 顶替当日信号
2. 用 `IRS / MSS` 分数替代 pattern 未触发
3. 因为要凑样本而放宽 formal trigger 条件

---

## 10. PAS Trace 真相源

### 10.1 为什么必须单独有 trace

formal signal 只告诉我们：

`触发了。`

但下面这些问题必须单独追：

1. 为什么某只候选没触发
2. 是历史不够，还是条件差一点
3. `strength` 是怎么来的
4. 排序变化来自哪一个 pattern
5. 五形态有没有互相重叠

### 10.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`pas_trigger_trace_exp`

它不是正式跨模块契约，而是当前 PAS 检测真相源。

### 10.3 建议字段

| 字段 | 说明 |
|---|---|
| `run_id` | 运行唯一标识 |
| `signal_date` | 信号日 |
| `code` | 股票代码 |
| `pattern` | 当前 detector 名称 |
| `selected_pattern` | 若多形态同时触发，最终入选者 |
| `candidate_rank` | 上游候选排名 |
| `history_days` | 可用历史样本数 |
| `detected` | 是否触发 |
| `detect_reason` | 若未触发，记录原因 |
| `pattern_strength` | 若触发，记录强度 |
| `signal_id` | 若触发，记录正式信号 ID |
| `created_at` | 写入时间 |

### 10.4 Trace 不变量

1. 每个 `(run_id, signal_date, code, pattern)` 最多一行
2. `detected=True` 的行必须能映射到 formal `Signal`
3. `detected=False` 的行不得生成 formal `Signal`
4. `pas_trigger_trace_exp` 只解释检测，不承载最终排序

---

## 11. 和 DTT rank sidecar 的连接规则

当前主线已经有一个正式的排序真相源：

`l3_signal_rank_exp`

它的职责固定为：

1. 保存已触发 signal 的 `strength`
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

1. `IRS` 不得回写 PAS 检测结论
2. `IRS` 只能附加后置分数

### 12.2 与 Broker / Risk

`Broker / Risk` 只消费 formal signal 和后续排序结果。

因此：

1. `Broker / Risk` 不得根据未触发候选补单
2. `Broker / Risk` 不得重算 PAS

---

## 13. 当前与后续

### 13.1 本文冻结的东西

本文已经冻结了：

1. 统一 `PAS snapshot` 最小输入
2. formal `Signal` 最小字段
3. 兼容期扩展字段边界
4. 检测失败与降级口径
5. `pas_trigger_trace_exp`
6. 与 `l3_signal_rank_exp` 的职责分界

### 13.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 完成五形态 detector 的 registry 接入
2. 把 `detect_reason / detected / selected_pattern` 正式落到 trace
3. 补 `signal_id -> l3_signal_rank_exp` 的完整追溯链
4. 校验历史 `bof_strength` 字段的兼容边界

### 13.3 本文明确不做什么

本文不授权下面这些回退：

1. 把 `PAS-full` 再塞回当前主线
2. 把 formal signal 压成“只要 code 就算触发”
3. 因为当前代码只落 `BOF`，就把契约边界重新缩回 `BOF-only`
