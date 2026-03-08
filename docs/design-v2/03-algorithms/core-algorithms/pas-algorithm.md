# PAS-trigger / BOF 当前主线设计

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变当前 DTT 主线边界的前提下，对 PAS-trigger 的 detector 架构、BOF 口径与验证证据做受控修订。`  
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`  
**对应模块**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`  
**理论来源**: `docs/Strategy/PAS/`

---

## 1. 职责

当前主线实现的不是 `PAS-full`，而是：

`PAS-trigger`

当前 `PAS-trigger` 只承担一件事：

`在候选池上检测 BOF，并生成最小正式 Signal。`

它回答的问题是：

`这只候选股票今天是否触发了可执行的 BOF。`

---

## 2. 输入

`PAS-trigger / BOF` 当前读取：

1. `Selector` 输出的 `StockCandidate`
2. `l2_stock_adj_daily`
3. 配置项
   - `PAS_LOOKBACK_DAYS`
   - `break_pct`
   - `volume_mult`
4. 交易日上下文

当前不读取：

1. `IRS` 行业分
2. `MSS` 市场分
3. 账户状态

---

## 3. 输出契约

当前正式输出为最小 `Signal`：

1. `signal_id`
2. `code`
3. `signal_date`
4. `action = BUY`
5. `pattern = bof`
6. `reason_code = PAS_BOF`
7. `strength`

当前主线同时允许把 `strength` 展开为排序解释字段：

1. `bof_strength`
2. `selected`
3. `variant`

这些扩展字段进入 sidecar 真相源，不强制立即并入正式 `Signal` 契约。

---

## 4. 不负责什么

当前主线中，`PAS-trigger / BOF` 不负责：

1. 行业横截面排序
2. 市场级风险预算
3. 最终下单截断
4. 止损、目标位、失败处理的完整交易管理
5. `BPB / TST / PB / CPB` 多形态在线运行

这些能力属于后续恢复范围，不属于当前主线执行边界。

---

## 5. 决策规则 / 算法

当前 `BOF` 的正式触发条件固定为：

1. `low < lower_bound * (1 - break_pct)`
2. `close >= lower_bound`
3. `close_pos >= 0.6`
4. `volume >= volume_ma20 * volume_mult`

满足即在 `T` 日收盘后生成最小 `BUY Signal`，并按固定执行语义进入下游：

`signal_date = T`，`execute_date = T+1`，成交价 = `T+1 Open`

当前主线骨架固定为：

```text
StockCandidate
-> load history window
-> BOF detect
-> formal Signal
-> sidecar bof_strength
```

装配规则：

1. 一形态一 detector
2. `registry` 当前仅在线 `bof`
3. `strategy.py` 负责批量准备窗口和汇总 detector 结果

---

## 6. 失败模式与验证证据

主要失败模式：

1. 候选历史窗口不足，导致假阴性。
2. `BOF` 与后续排序、风控职责重新混写。
3. `strength / bof_strength` 追溯链断裂，无法解释排序来源。
4. 用 `PAS-trigger` 冒充 `PAS-full`，导致设计边界再次膨胀。

当前验证证据：

1. `docs/spec/v0.01-plus/evidence/matrix_summary_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t160708__dtt_matrix.json`
2. `docs/spec/v0.01-plus/evidence/idempotency_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t151843__idempotency_check.json`
3. `docs/spec/v0.01-plus/evidence/rank_decomposition_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t154940__rank_decomposition.json`
4. `docs/spec/v0.01-plus/records/v0.01-plus-short-window-matrix-20260307.md`

当前结论只说明：

1. `BOF` 已经是当前主线的唯一在线触发器
2. `PAS-trigger` 已经和 sidecar 排序链路打通

并不表示 `PAS-full` 已经恢复完成。
