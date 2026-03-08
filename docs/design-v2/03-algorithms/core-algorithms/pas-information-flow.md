# PAS 信息流

**版本**: `v0.01-plus 主线替代版`
**状态**: `Active`
**封版日期**: `不适用（Active SoT）`
**变更规则**: `允许在不改变当前 DTT 主线语义的前提下，对 PAS 的输入、触发、排序对接与 sidecar 链路做受控修订。`
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
**创建日期**: `2026-03-08`
**最后更新**: `2026-03-08`
**对应代码**: `src/strategy/pas_bof.py`, `src/strategy/strategy.py`, `src/strategy/ranker.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容附录。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的信息流整理结果，不再构成仓库现行设计权威。现行 `PAS-trigger / BOF` 正文以 `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 当前主线信息流总览

```text
Selector candidate pool
-> load price history in batches
-> BOF detect
-> minimal formal Signal
-> DTT rank sidecar
-> selected formal signals
-> Broker execute
```

这就是当前主线 `PAS` 的信息流。

它不是 beta 时代的：

`个股全量评分 -> 三三制集成 -> 机会等级输出`

---

## 2. 分阶段信息流

### 2.1 Step 1：接收候选池

输入：

- `list[StockCandidate]`

来源：

- `Selector` 基础过滤 + `preselect_score + candidate_top_n`

说明：

- 当前 `PAS` 不再自己构造候选池
- 当前 `PAS` 不读取 `MSS / IRS` 做前置过滤

### 2.2 Step 2：分批加载历史窗口

`strategy.generate_signals()` 会按 batch：

1. 提取候选代码列表
2. 从 `l2_stock_adj_daily` 批量加载历史
3. 按 `code` 分组形成 detector 输入窗口

### 2.3 Step 3：BOF 触发

当前 `BofDetector` 对每只股票执行：

1. 下破历史下边界
2. 收盘回结构内
3. 收盘位置位于当日振幅上部
4. 成交量高于 `volume_ma20 * volume_mult`

满足后生成最小 `Signal`。

### 2.4 Step 4：合并 detector 结果

当前虽然保留 `_combine_signals()` 框架，但在线 detector 只有 `bof`。

因此当前主线实际等价于：

- `ANY`
- `bof`

### 2.5 Step 5：DTT 对接排序层

在 `DTT` 模式下：

1. `strategy.generate_signals()` 把 detector 输出准备成 `prepared_signals`
2. 写 `_tmp_dtt_rank_stage`
3. 调 `ranker.py` 读取 `IRS`
4. 形成 `final_score / final_rank`
5. 写 `l3_signal_rank_exp`
6. 只把入选 signal 回写 formal `l3_signals`

### 2.6 Step 6：执行层消费

输出结果分成两条链：

1. `formal l3_signals`
   - 给 legacy 兼容层、Broker 正式执行层使用

2. `l3_signal_rank_exp`
   - 给 `DTT` 排序解释、归因和 evidence 使用

---

## 3. 与 IRS / MSS 的边界

### 3.1 与 IRS

当前主线关系：

- `PAS` 先触发
- `IRS` 后排序
- `IRS` 不是 detector 输入

### 3.2 与 MSS

当前主线关系：

- `PAS` 触发阶段不消费 `MSS`
- `MSS` 只在 Broker / Risk 层影响执行容量

### 3.3 与 Selector

当前主线关系：

- `Selector` 决定谁进入 BOF 扫描
- `PAS` 不反向改写候选池

---

## 4. 当前信息流的设计意义

当前 `PAS` 信息流的设计意义是：

1. 把形态触发和排序增强拆开
2. 把排序和执行拆开
3. 把 formal schema 和 DTT sidecar 拆开

这样才能分别回答：

- `BOF` 有没有触发
- `IRS` 有没有改排序
- `MSS` 有没有改执行

---

## 5. 权威结论

当前主线里，`PAS` 的正确信息流只有一条：

`候选池 -> BOF 触发 -> 最小 formal Signal -> DTT sidecar 排序 -> Broker 执行`

只要信息流偏离这条，说明系统又在往旧混合式设计回退。

---

## 6. 相关文档

- `pas-algorithm.md`
- `pas-data-models.md`
- `pas-api.md`
- `down-to-top-integration.md`
