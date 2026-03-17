# Selector Contract Annex

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `Selector`  
**上游锚点**:

1. `docs/design-v2/02-modules/selector-design.md`
2. `blueprint/01-full-design/92-mainline-design-atom-closure-record-20260308.md`
3. `src/contracts.py`
4. `src/selector/selector.py`

---

## 1. 用途

本文只补 `Selector` 当前主线缺失的契约原子。

它不重写 `Selector` 的主线职责，只把下面 3 件事冻结下来：

1. 正式 `StockCandidate` 契约
2. 兼容期字段映射
3. `Selector trace` 追溯口径

一句话说：

`Selector` 继续只做候选准备，但候选到底长什么样、为什么进来、为什么被挡掉，必须写死。

---

## 2. 作用边界

本文只覆盖 `DTT` 当前主线下的 `Selector`：

```text
universe snapshot
-> basic filters
-> preselect_score
-> candidate_top_n
-> StockCandidate
```

本文不覆盖：

1. `legacy` 漏斗的 `MSS gate / IRS filter`
2. `BOF` 检测本身
3. `IRS-lite` 排序本身
4. `Broker / Risk` 执行语义

---

## 3. 设计来源

`Selector` 在 `alpha / beta` 中没有完整独立正文，所以本补充文的来源是“反提炼”：

1. `beta system-overview / module-index`
2. `beta` 中 `PAS / IRS / MSS` 文档里关于候选池入口、信息流和契约的零散原子
3. `gamma` 当前主线正文
4. `gamma` 当前代码里的运行时事实

其中：

1. `beta` 提供的是表达结构和漏斗原子
2. `gamma` 提供的是当前正确的职责边界
3. 当前代码提供的是兼容期字段现实

---

## 4. Selector 阶段模型

### 4.1 阶段拆分

`Selector` 当前主线固定拆成 5 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `S0` | `universe_snapshot` | `l2_stock_adj_daily + l1_stock_daily + l1_stock_info + l1_industry_member` | 当日全市场候选快照 | 无当日快照则该股票不进入主链 |
| `S1` | `tradability_filter` | `S0` | 可交易股票子集 | `NOT_LIVE / HALTED / ST` |
| `S2` | `hygiene_filter` | `S1` | 样本卫生合格子集 | `TOO_NEW / LOW_LIQUIDITY` |
| `S3` | `preselect_score` | `S2` | `preselect_score` 排序表 | 不允许混入 `MSS / IRS / PAS` |
| `S4` | `top_n_cut` | `S3` | `list[StockCandidate]` | 超出 `candidate_top_n` 的股票仅出现在 trace，不进正式候选 |

### 4.2 当前实现对应

当前代码中，这 5 段主要对应：

1. `_load_universe_snapshot`
2. `_apply_basic_filters`
3. `_select_dtt_candidates_frame`
4. `select_candidates_frame`
5. `select_candidates`

这层映射的目的不是把设计绑死到函数名，而是保证：

`蓝图字段名和现有实现不会各说各话。`

---

## 5. 正式候选契约

### 5.1 契约定位

`StockCandidate` 是 `Selector -> Strategy` 的正式跨模块结果契约。

它的语义固定为：

`已通过当前主线初选、允许进入 BOF 扫描的候选。`

它不是：

1. 全市场快照
2. 被过滤股票的审计表
3. 最终交易评分

### 5.2 正式稳定字段

下面这些字段应视为 `Selector` 的正式稳定边界：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `code` | `str` | `Required` | 6 位纯代码，`L2+` 口径 |
| `trade_date` | `date` | `Required` | 当前候选所属交易日 |
| `industry` | `str` | `Required` | 行业名称；缺失时为 `未知` |
| `preselect_score` | `float` | `Required` | 当前 `PRESELECT_SCORE_MODE` 下的初选分 |
| `candidate_rank` | `int` | `Required` | `preselect_score` 排名，1 为最高 |
| `candidate_reason` | `str` | `Required` | 进入候选池的原因，当前默认 `PRESELECT_TOP_N` |
| `liquidity_tag` | `str` | `Optional` | `HIGH / MEDIUM / LOW` 分层标签 |

### 5.3 契约不变量

`StockCandidate` 必须满足下面这些不变量：

1. 同一 `trade_date` 内，`code` 唯一。
2. 同一 run 内，`candidate_rank` 必须连续、稳定、可重复计算。
3. `candidate_rank` 的排序规则固定为：
   - `preselect_score` 降序
   - `code` 升序打平
4. `preselect_score` 只代表扫描优先级，不代表最终交易结论。
5. 正式候选里不能出现 `reject_reason`。

---

## 6. 兼容期字段映射

### 6.1 当前代码现实

当前 `src/contracts.py` 中的 `StockCandidate` 还是兼容期形态：

| 当前字段 | 当前状态 |
|---|---|
| `code` | 已存在 |
| `industry` | 已存在 |
| `score` | 已存在 |
| `preselect_score` | 已存在 |
| `filter_reason` | 已存在，但语义混乱 |
| `liquidity_tag` | 已存在 |

### 6.2 兼容期映射规则

在正式 schema 收敛前，统一采用下面的映射规则：

| 正式目标字段 | 兼容期字段 | 规则 |
|---|---|---|
| `preselect_score` | `preselect_score` | 原样保留 |
| `candidate_rank` | 无 | 先进入 trace，不强塞进旧模型 |
| `candidate_reason` | `filter_reason` | 兼容期允许借位，但只能承载“入选原因”，不能再写 `reject_reason` |
| `preselect_score` 别名 | `score` | 在 `DTT` 路径下，`score` 必须等于 `preselect_score` |
| `trade_date` | 无 | 先通过 trace 和上游运行上下文追溯 |

### 6.3 当前实现约束

从本补充文生效起，兼容期必须遵守：

1. `score == preselect_score`
2. `filter_reason` 不得再承载被拒绝原因
3. 被拒绝股票只能进入 `Selector trace`，不能混入正式 `StockCandidate`

这意味着：

`当前代码里把 reject_reason 塞进 filter_reason 的做法，只能视为过渡期残留，不是稳定设计。`

---

## 7. Preselect 模式与不变量

### 7.1 当前允许模式

`PRESELECT_SCORE_MODE` 当前只允许 3 个值：

1. `amount_plus_volume_ratio`
2. `amount_only`
3. `volume_ratio_only`

### 7.2 模式计算

当前主线统一使用：

1. `amount_component = log1p(amount)`
2. `activity_component = volume_ratio`

然后按模式组合：

| 模式 | 公式 |
|---|---|
| `amount_plus_volume_ratio` | `log1p(amount) + volume_ratio` |
| `amount_only` | `log1p(amount)` |
| `volume_ratio_only` | `volume_ratio` |

### 7.3 模式不变量

无论切到哪种模式，都不能改变下面这些边界：

1. 不读取 `MSS / IRS / PAS`
2. 不改基础过滤结果
3. 不把交易语义写回 `Selector`
4. 只改变候选覆盖与扫描优先级
5. 必须进入证据矩阵与默认参数治理

---

## 8. 降级与拒绝语义

### 8.1 拒绝原因

`Selector` 当前主线统一使用以下拒绝原因：

| `reject_reason` | 含义 | 去向 |
|---|---|---|
| `NOT_LIVE` | 非上市正常交易状态 | 只进 trace |
| `HALTED` | 当日停牌 | 只进 trace |
| `ST` | ST 或同类风险状态 | 只进 trace |
| `TOO_NEW` | 上市天数不足 `MIN_LIST_DAYS` | 只进 trace |
| `LOW_LIQUIDITY` | 成交额低于 `MIN_AMOUNT` | 只进 trace |

### 8.2 降级规则

对当前实现已出现的缺失和脏数据，统一按下面处理：

| 场景 | 处理 |
|---|---|
| `industry` 缺失 | `FILL='未知'`，不直接拒绝 |
| `is_halt` 缺失 | `FILL=False` |
| `is_st` 缺失 | `FILL=False` |
| `list_status` 缺失 | `FILL='UNKNOWN'`，随后按 `NOT_LIVE` 拒绝 |
| `list_date` 缺失 | 视为 `TOO_NEW` |
| `amount` 缺失 | 按 `0` 处理，随后通常落入 `LOW_LIQUIDITY` |
| `volume_ratio` 缺失 | 计分时按 `0` 处理，不单独拒绝 |
| 当日 `l2` 快照缺失 | 不做 `T-1` 回填；该股票直接不进入主链 |

### 8.3 Stale 规则

`Selector` 当前主线不允许使用前一日候选快照替代当日快照。

因此：

1. 主链没有 `stale candidate fallback`
2. 若需要诊断 stale 问题，只能在 trace 中记录 `coverage_flag=STALE_SNAPSHOT`
3. 正式 `StockCandidate` 不得从旧日快照补出

---

## 9. Selector Trace 追溯口径

### 9.1 为什么必须单独有 trace

正式 `StockCandidate` 只保留“进入候选池的结果”。

但下面这些问题，必须靠 trace 才能解释：

1. 某只股票为什么没进候选池
2. `candidate_top_n` 截断杀掉了谁
3. `PRESELECT_SCORE_MODE` 改动后，样本覆盖变化来自哪里
4. 后续 `BOF` 样本损失是过滤导致，还是触发失败导致

### 9.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`selector_candidate_trace_exp`

它不是正式跨模块契约，而是当前主线的真相源。

### 9.3 建议字段

| 字段 | 说明 |
|---|---|
| `run_id` | 运行唯一标识 |
| `trade_date` | 交易日 |
| `code` | 股票代码 |
| `industry` | 行业，缺失记 `未知` |
| `preselect_score_mode` | 当前模式 |
| `preselect_score` | 初选分 |
| `candidate_rank` | 截断前排名 |
| `selected_for_bof` | 是否进入正式候选 |
| `filters_passed` | 当前基础过滤链定义 |
| `reject_reason` | 若被拒绝，记录原因 |
| `coverage_flag` | `NORMAL / UNKNOWN_INDUSTRY / STALE_SNAPSHOT / COLD_START` |
| `liquidity_tag` | 流动性标签 |
| `source_snapshot_date` | 候选快照日期 |
| `created_at` | 写入时间 |

### 9.4 Trace 不变量

1. 每个 `(run_id, trade_date, code)` 最多一行。
2. `selected_for_bof=True` 的行，必须能映射到正式 `StockCandidate`。
3. `selected_for_bof=False` 的行，必须至少能解释为：
   - 被过滤
   - 被 `candidate_top_n` 截断
4. trace 可以扩字段，但不能反向污染正式 `StockCandidate`。

---

## 10. 和 BOF 的连接规则

`Selector` 和 `BOF` 的稳定连接规则固定为：

1. `BOF` 只消费正式 `StockCandidate`
2. `BOF` 不回写 `Selector` 过滤结果
3. `BOF` 样本损失归因时，优先查 `selector_candidate_trace_exp`

归因顺序固定为：

```text
universe missing
-> basic filter reject
-> top_n cut
-> BOF detect fail
-> ranked signal not selected
-> Broker / Risk cut
```

只要归因顺序不定，后面所有“为什么没交易到这只票”的讨论都会重新绕回去。

---

## 11. 当前与后续

### 11.1 本文冻结的东西

本文已经冻结了：

1. `Selector` 阶段模型
2. 正式 `StockCandidate` 目标字段
3. 兼容期字段映射
4. 拒绝和降级语义
5. trace 真相源口径

### 11.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 让 `src/contracts.py` 对齐正式字段或给出兼容层
2. 把 `filter_reason <- reject_reason` 的过渡残留清掉
3. 补 `candidate_rank / trade_date / candidate_reason` 的稳定落点
4. 增加 `selector_candidate_trace_exp` 或同等 artifact

### 11.3 本文明确不做什么

本文不授权下面这些回退：

1. 把 `MSS` 拉回 `Selector`
2. 把 `IRS` 拉回行业前置过滤
3. 用“先搞 MVP”理由再次把候选契约压回 `code, industry, score`
