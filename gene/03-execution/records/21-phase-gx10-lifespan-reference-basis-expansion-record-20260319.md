# GX10 Record: 寿命参考基础扩充
**状态**: `Completed`
**日期**: `2026-03-19`

---

## 1. 记录目的

这份 record 只记录四件事：

1. `GX10` 这轮到底补了哪些寿命基础
2. 这些基础具体落到了哪些正式字段
3. 这轮没有做哪些事
4. 当前验证到底到什么程度

---

## 2. 本轮正式结论

### 2.1 历史深度已从单一结构窗口拆成双口径

当前实现不再把所有 Gene lookback 都偷写成同一个 `260` 日窗口。

现在正式拆成：

1. `GENE_STRUCTURE_LOOKBACK_TRADE_DAYS = 260`
2. `GENE_LIFESPAN_REFERENCE_TRADE_DAYS = 1260`
3. `GENE_LOOKBACK_TRADE_DAYS = max(structure, lifespan_reference)`

这意味着第四战场现在至少能诚实区分：

1. 结构识别所需的最小回看深度
2. 寿命尺自历史分位所需的参考深度

### 2.2 历史深度与样本跨度现在对下游可见

当前 snapshot / wave ledger 已正式新增：

1. `history_reference_trade_days`
2. `history_span_trade_days`

对应 snapshot 字段为：

1. `current_wave_history_reference_trade_days`
2. `current_wave_history_span_trade_days`

因此下游现在可以看到两件事：

1. 这把寿命尺理论上想看多深
2. 当前这只股票实际上已经覆盖了多长的历史跨度

### 2.3 相对前一主要波段的折返宽度已机械化

当前 countertrend 语义不再只停留在口头解释。

现在正式新增：

1. `prior_mainstream_wave_id`
2. `prior_mainstream_magnitude_pct`
3. `retracement_vs_prior_mainstream_pct`

对应 snapshot 字段为：

1. `current_wave_prior_mainstream_wave_id`
2. `current_wave_prior_mainstream_magnitude_pct`
3. `current_wave_retracement_vs_prior_mainstream_pct`

这让系统现在至少能回答：

`当前这段逆流波段，已经走到了前一主要波段宽度的多少百分比。`

### 2.4 宽度 + 时间联合寿命读数已正式落地

当前实现没有只把旧 `duration_percentile` 换个名字，而是补了联合寿命层：

1. `lifespan_joint_percentile`
2. `lifespan_joint_band`

对应 snapshot 字段为：

1. `current_wave_lifespan_joint_percentile`
2. `current_wave_lifespan_joint_band`

因此当前寿命轴可以同时回答：

1. 只看时间有多老：`duration_percentile`
2. 只看宽度有多深：`magnitude_percentile`
3. 宽度 + 时间一起看有多靠后：`lifespan_joint_percentile`

---

## 3. 本轮明确没有做

`GX10` 这轮仍然刻意没有做下面这些事：

1. 没有直接改写 `Phase 9` runtime gate
2. 没有清理 `age_band / context / reversal` 的运行面合同
3. 没有对 `mirror / conditioning / gene_score` 重开研究
4. 没有把第四战场从 `sidecar / dashboard / attribution` 升格为 hard gate

这不是遗漏，而是卡边界：

`GX10` 只负责把寿命参考基础补对，不负责决定运行面怎么消费。`

---

## 4. 验证口径

本轮验证当前写定为：

1. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py` 已通过
2. `tests/unit/selector/test_gene.py` 已补入新字段和新语义断言
3. 在当前 Windows 会话里，正式 `pytest` 仍受 `basetemp` 权限问题影响，session finish 会报 `PermissionError`
4. 为避免把环境问题误写成逻辑问题，本轮已额外执行等价手工 smoke，用独立 `tmp_path` 逐个调用 5 个单测函数，结果全部通过

因此当前最诚实的结论是：

`GX10` 的实现逻辑和单测语义已经站住，但正式 pytest 仍存在环境级 basetemp 权限噪音。`

---

## 5. 下一步

当前固定进入：

[`../22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md`](../22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md)

也就是：

1. 清理 `age_band` 的误导性展示别名
2. 清理 `context` 命名和层级暴露
3. 把 `reversal_state` 的运行面口径写得更透明

---

## 6. 一句话收口

`GX10` 现在已经把寿命轴从“只有时间年龄尺”推进到了“历史深度可见、折返宽度可见、宽度+时间联合寿命可见”的正式状态，但它仍只是第四战场历史尺，不是直接交易决策。`
