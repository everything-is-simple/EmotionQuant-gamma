# IRS-lite Contract Annex

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `IRS-lite`  
**上游锚点**:

1. `docs/design-v2/02-modules/selector-design.md`
2. `blueprint/01-full-design/92-mainline-design-atom-closure-record-20260308.md`
3. `src/contracts.py`
4. `src/selector/irs.py`
5. `src/strategy/ranker.py`
6. `src/data/cleaner.py`
7. `src/data/sw_industry.py`

---

## 1. 用途

本文只补 `IRS-lite` 当前主线缺失的契约原子。

它不重写 `IRS-lite` 的主线职责，只冻结 6 件事：

1. `IRS-lite` 的最小输入快照
2. 行业层正式 `IndustryScore` 契约
3. 兼容期和 `l3_irs_daily` 的字段映射
4. 信号层 `irs_score` 的附着规则
5. `fallback / skip / fill` 语义
6. `IRS trace` 真相源

一句话说：

`当前 IRS-lite 只做行业后置增强，但行业怎么评分、行业结果怎么附着到 signal、什么时候记 50 分、什么时候整天跳过，必须写死。`

---

## 2. 作用边界

本文只覆盖当前主线 `IRS-lite`：

```text
l2_industry_daily
-> benchmark attach
-> RS / CF score
-> per-day rank
-> l3_irs_daily
-> signal-level irs_score attach
```

本文不覆盖：

1. `Selector` 前置行业过滤
2. `MSS-lite` 风险覆盖
3. `PAS-trigger / BOF` 形态检测
4. `IRS-full` 六因子与轮动状态机
5. `allocation_advice / rotation_mode` 的完整恢复

---

## 3. 设计来源

当前补充文的设计来源是“定向裁原子”：

1. `beta irs-data-models.md`
2. `beta irs-information-flow.md`
3. `beta irs-api.md`
4. `gamma` 当前主线正文
5. `gamma` 当前 `src/selector/irs.py` 和 `src/strategy/ranker.py`

其中：

1. `beta` 提供完整 `IrsIndustrySnapshot / IrsIndustryDaily / pipeline` 的表达深度
2. `gamma` 提供当前主线正确边界：只做后置行业增强
3. 当前代码提供已落地的表结构、fallback 和信号附着现实

---

## 4. IRS-lite 阶段模型

### 4.1 阶段拆分

`IRS-lite` 当前主线固定拆成 5 段：

| 阶段 | 名称 | 输入 | 输出 | 失败语义 |
|---|---|---|---|---|
| `I0` | `industry_snapshot_load` | `l2_industry_daily` | 行业日线快照 | 无快照则无输出 |
| `I1` | `benchmark_attach` | `l1_index_daily + I0` | 带基准的日快照 | 基准缺失时按 `0.0` 处理 |
| `I2` | `rs_cf_score` | `I1 + baseline` | `rs_score / cf_score / total_score` | 因子异常时按各自规则兜底 |
| `I3` | `daily_rank` | `I2` | `l3_irs_daily` | 当日行业数低于阈值则整日 `SKIP` |
| `I4` | `signal_attach` | `l3_irs_daily + candidates + signals` | `l3_signal_rank_exp.irs_score` | 未匹配行业时 `FILL=50.0` |

### 4.2 当前实现对应

当前代码主要对应：

1. `compute_irs`
2. `compute_irs_single`
3. `_load_irs_score_map`
4. `build_dtt_score_frame`

设计层在这里要钉住的是阶段边界，而不是把实现绑死到某个函数名。

---

## 5. IRS-lite 最小输入快照

### 5.1 契约定位

当前主线不直接使用 `beta` 的完整 `IrsIndustrySnapshot`。

当前只从中裁出一份 `IRS-lite snapshot`。

它的语义固定为：

`足够支持当前两因子 IRS-lite 计算的最小行业日快照。`

### 5.2 必需字段

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `date` | `date` | `Required` | 交易日 |
| `industry` | `str` | `Required` | 当前行业名称 |
| `pct_chg` | `float` | `Required` | 行业日收益 |
| `amount` | `float` | `Required` | 行业成交额 |
| `stock_count` | `int` | `Optional` | 行业成分股数 |
| `rise_count` | `int` | `Optional` | 上涨家数 |
| `fall_count` | `int` | `Optional` | 下跌家数 |

### 5.3 派生字段

当前 `IRS-lite` 运行时还会派生：

| 字段 | 来源 | 语义 |
|---|---|---|
| `benchmark_pct` | `l1_index_daily(000001.SH)` | 基准日收益 |
| `market_total_amount` | 当日行业成交额求和 | 资金占比的分母 |
| `amount_delta_10d` | 行业内 10 日成交额变化 | 当前 CF 因子增量项 |

### 5.4 当前与 beta 的裁剪关系

从 `beta IrsIndustrySnapshot` 中，本轮明确不带入：

1. `industry_code`
2. `industry_turnover`
3. `limit_up_count / limit_down_count`
4. `new_100d_high_count / new_100d_low_count`
5. `top5_pct_chg / top5_limit_up`
6. `style_bucket / pe / pb`

原因很直接：

`这些字段属于 IRS-full 的六因子体系，不是当前 IRS-lite 两因子的最小输入。`

---

## 6. 行业映射与口径

### 6.1 当前正式口径

当前主线行业口径固定为：

`SW2021 一级行业`

但当前运行时现实是：

1. `l1_sw_industry_member` 保存 `industry_code + industry_name`
2. `l2_industry_daily` 当前只落 `industry` 名称
3. `l3_irs_daily` 当前也只落 `industry` 名称

### 6.2 当前冻结结论

因此本轮冻结如下：

1. 行业层正式跨模块契约先以 `industry` 名称为准
2. `industry_code` 暂视为 trace / future migration 字段
3. 若后续要把 `industry_code` 升为正式字段，必须单独做 schema migration

### 6.3 未知行业规则

当前主线统一采用：

1. `Selector` 阶段行业缺失时填 `未知`
2. `compute_irs` 阶段会把 `industry='未知'` 的行业行从行业评分表中剔除
3. `ranker` 在 signal attach 阶段若匹配不到行业，则 `FILL=50.0`

这三步必须分开看，不能混成一句“未知行业按 50 处理”。

---

## 7. 行业层正式契约

### 7.1 契约定位

`IndustryScore` 是 `IRS-lite -> Strategy / Ranker` 的正式跨模块结果契约。

它的语义固定为：

`某个交易日内，行业横截面的后置增强结果。`

### 7.2 正式稳定字段

当前正式稳定字段先冻结为 `src/contracts.py` 中的最小形态：

| 字段 | 类型 | 必需性 | 语义 |
|---|---|---|---|
| `date` | `date` | `Required` | 行业结果所属交易日 |
| `industry` | `str` | `Required` | 行业名称，当前按 SW2021 一级名称口径 |
| `score` | `float` | `Required` | 行业层总分；语义别名为 `irs_score` |
| `rank` | `int` | `Required` | 当日行业唯一排名；语义别名为 `industry_rank` |

### 7.3 当前持久化表 reality

当前 `l3_irs_daily` 已经比最小契约多落了两列解释字段：

1. `rs_score`
2. `cf_score`

因此当前正式层次要分开看：

| 层次 | 字段 |
|---|---|
| 跨模块结果契约 | `date / industry / score / rank` |
| 当前持久化现实 | `date / industry / score / rank / rs_score / cf_score` |

### 7.4 契约不变量

1. 同一 `(date, industry)` 只能有一行。
2. 同一天内 `rank` 必须唯一且连续。
3. 日内排序固定为：
   - `score` 降序
   - `industry` 升序打平
4. `score` 是行业层总分，不等于 signal 层附着分。

---

## 8. 因子与 baseline 语义

### 8.1 当前两因子

当前 `IRS-lite` 只保留两因子：

1. `RS`
   - `rs_raw = industry_pct_chg - benchmark_pct`
2. `CF`
   - `cf_raw = flow_share + amount_delta_10d`
   - `flow_share = amount / market_total_amount`

综合得分固定为：

```text
total_score = 0.55 * rs_score + 0.45 * cf_score
```

### 8.2 当前标准化现实

当前代码不是用滚动样本实时估 mean/std，而是用 `IRS_BASELINE`：

1. `rs_score_mean = 0.0`
2. `rs_score_std = 1.0`
3. `cf_score_mean = 0.0`
4. `cf_score_std = 1.0`

然后调用 `zscore_single()`：

```text
score = clip((z + 3) / 6 * 100, 0, 100)
```

### 8.3 当前冻结结论

本轮必须冻结下面这个现实：

1. `l3_irs_daily.score` 是行业层两因子综合分
2. `rs_score / cf_score` 是行业层解释字段
3. 当前 baseline 是固定锚，不是滚动学习基线

---

## 9. 信号层附着规则

### 9.1 当前最重要的现实

当前 signal 层使用的 `irs_score`，不是 `l3_irs_daily.score` 原样透传。

当前 `ranker` 的真实逻辑是：

1. 读取 `l3_irs_daily.industry + rank`
2. 按行业 `rank` 线性映射成 `0-100`
3. 再把这个 signal-level `irs_score` 写入 `l3_signal_rank_exp`

### 9.2 当前映射公式

若当日有 `N` 个行业：

```text
irs_score = 100 * (1 - (rank - 1) / (N - 1))
```

若当日仅 1 个行业：

```text
irs_score = 100
```

### 9.3 当前冻结结论

因此必须把两个分数分开命名理解：

| 名称 | 所在层 | 含义 |
|---|---|---|
| `IndustryScore.score` | 行业层 | IRS-lite 行业总分 |
| `Signal.irs_score` / `l3_signal_rank_exp.irs_score` | 信号层 | 行业排名映射后的后置增强分 |

这两个数：

`不是同一个数。`

---

## 10. 兼容期字段映射

### 10.1 当前代码现实

当前 `IndustryScore` 模型仍是最小版本：

1. `date`
2. `industry`
3. `score`
4. `rank`

而旧 `IRS bridge` 稿里提到的：

1. `quality_flag`
2. `industry_code`
3. `sample_days`
4. `industry_rank`

目前还没有进入正式跨模块 schema。

### 10.2 兼容期映射规则

当前统一采用：

| 目标语义 | 当前正式字段 | 规则 |
|---|---|---|
| `trade_date` | `date` | 语义别名 |
| `industry_name` | `industry` | 当前正式落点 |
| `irs_score` | `score` | 仅指行业层总分 |
| `industry_rank` | `rank` | 语义别名 |
| `quality_flag` | 无 | 先进入 trace 或 future migration |
| `industry_code` | 无 | 先进入 trace 或 future migration |

### 10.3 当前实现约束

从本补充文生效起，兼容期必须遵守：

1. `IndustryScore.score` 只能表示行业层总分
2. signal-level `irs_score` 只能放在 `Signal` 扩展字段和 `l3_signal_rank_exp`
3. `quality_flag` 不得靠口头存在，若未正式入 schema，就必须进 trace

---

## 11. Skip / Fallback / Fill 语义

### 11.1 行业层 `SKIP`

下面这些情况属于行业层 `SKIP`：

| 场景 | 处理 |
|---|---|
| `l2_industry_daily` 无数据 | 当日无输出 |
| 过滤掉 `未知` 后没有行业 | 当日无输出 |
| 当日行业数 `< IRS_MIN_INDUSTRIES_PER_DAY` | 整日跳过，不写 `l3_irs_daily` |

### 11.2 行业层 `FILL`

下面这些情况属于行业层 `FILL`：

| 场景 | 处理 |
|---|---|
| 基准指数缺失 | `benchmark_pct = 0.0` |
| `market_total_amount = 0` | `flow_share = 0.0` |
| `amount_delta_10d` 窗口不足 | `0.0` |
| `std = 0` 或 `NaN` | `zscore_single -> 50.0` |
| 日内 `score` 非有限值 | 先转数值，再 `fillna(0.0)` 排序 |

### 11.3 信号层 `FILL`

下面这些情况属于 signal 层 `FILL`：

| 场景 | 处理 |
|---|---|
| candidate 行业未匹配到 `l3_irs_daily` | `irs_score = 50.0` |
| 当前变体不使用 IRS | `irs_score = 50.0` |

### 11.4 当前冻结结论

本轮必须把这三类动作分开：

1. 行业层 `SKIP`
2. 行业层 `FILL`
3. signal 层 `FILL`

否则实现时很容易把“当日没算出来”混成“所有股票统一 50”。

---

## 12. IRS Trace 真相源

### 12.1 为什么必须单独有 trace

`l3_irs_daily` 只能告诉我们：

`行业今天得了多少分、排第几。`

但下面这些问题必须单独追：

1. 为什么某天 `l3_irs_daily` 没有 31 行
2. 某行业的 `score` 主要来自 `RS` 还是 `CF`
3. 为什么某个 signal 最后只拿了 `50`
4. 行业口径是不是仍然属于 `SW2021`

### 12.2 建议 sidecar

建议在实现层保留一个实验性 sidecar：

`irs_industry_trace_exp`

它不是正式跨模块契约，而是当前 `IRS-lite` 行业层真相源。

### 12.3 建议字段

| 字段 | 说明 |
|---|---|
| `date` | 交易日 |
| `industry` | 当前正式行业名称 |
| `industry_code` | 若可得则记录 |
| `source_classification` | 当前固定为 `SW2021` |
| `benchmark_code` | 当前固定为 `000001.SH` |
| `benchmark_pct` | 基准日收益 |
| `industry_pct_chg` | 行业日收益 |
| `amount` | 行业成交额 |
| `market_total_amount` | 全市场行业成交额合计 |
| `amount_delta_10d` | 10 日成交额变化 |
| `rs_raw` | 原始相对强度 |
| `cf_raw` | 原始资金流 |
| `rs_score` | 标准化后的 RS |
| `cf_score` | 标准化后的 CF |
| `industry_score` | 行业层总分 |
| `industry_rank` | 当日排名 |
| `coverage_flag` | `NORMAL / UNKNOWN_DROPPED / MIN_INDUSTRIES_SKIP / BENCHMARK_FILL` |
| `created_at` | 写入时间 |

### 12.4 和 `l3_signal_rank_exp` 的边界

| 表/对象 | 职责 |
|---|---|
| `irs_industry_trace_exp` | 解释行业层是怎么打分和排序的 |
| `l3_irs_daily` | 保存行业层正式结果 |
| `l3_signal_rank_exp` | 解释 signal 层如何附着和排序 |

三者不能混写。

---

## 13. 和上下游的稳定连接

### 13.1 与 Selector

当前主线下：

1. `Selector` 不读取 `l3_irs_daily`
2. `IRS` 不得再回到前置行业硬过滤

### 13.2 与 PAS-trigger / BOF

当前主线下：

1. `IRS` 只消费已触发 BOF 的 signal
2. `IRS` 不得回写 BOF 检测结论

### 13.3 与 Broker / Risk

当前主线下：

1. `Broker / Risk` 不直接读 `l3_irs_daily`
2. 它只消费 signal 层已经附着好的 `irs_score` 或 `final_score`

---

## 14. 当前与后续

### 14.1 本文冻结的东西

本文已经冻结了：

1. `IRS-lite snapshot` 最小输入
2. `IndustryScore` 最小正式字段
3. `l3_irs_daily` 与 `IndustryScore` 的映射
4. signal-level `irs_score` 的当前附着逻辑
5. `skip / fill / fallback` 语义
6. `irs_industry_trace_exp`

### 14.2 后续 Implementation Spec 该做什么

实现层下一步只该做下面这些事：

1. 增加 `irs_industry_trace_exp` 或同等 artifact
2. 把 `industry_code / quality_flag / sample_days` 的迁移方案单独写清楚
3. 补“行业层 score”和“signal 层 irs_score”两层分数的命名隔离
4. 若要推进 `IRS-upgrade`，必须在此补充文之上扩，不允许回头改义当前 `IRS-lite`

### 14.3 本文明确不做什么

本文不授权下面这些回退：

1. 把 `IRS` 拉回 `Selector` 前置过滤
2. 把 `signal.irs_score` 误写成 `l3_irs_daily.score` 原样透传
3. 因为要更快推进实现，就继续把 `industry_code / quality_flag / sample_days` 留在口头上
