# Current Mainline Execution Breakdown

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `当前主线执行拆解首稿`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/01-full-design/03-selector-contract-supplement-20260308.md`
3. `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md`
4. `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md`
5. `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md`
6. `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md`
7. `docs/spec/common/records/development-status.md`

---

## 1. 定位

本文只做一件事：

`把唯一当前实现方案，拆成可以直接执行的 phase / task / checklist。`

它不回答设计是什么，也不重新定义实现目标。

它只回答：

1. 先做哪一包
2. 每包拆成哪些任务
3. 每个任务改哪些文件
4. 每包怎么验收和出场
5. 下一包什么时候允许开始

---

## 2. 执行铁律

执行期固定遵守下面 6 条：

1. 只从 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` 往下拆。
2. 不允许在执行文里重新发明算法定义。
3. 每次只推进一个 `phase` 到“可验收”状态，再进入下一个。
4. 每个 `phase` 必须同时包含：
   - 代码落点
   - 测试落点
   - artifact 落点
   - done checklist
5. `legacy_bof_baseline` 必须始终保持可重跑。
6. 所有新增 trace / sidecar / artifact 都必须可通过 `run_id` 或 `signal_id` 回溯。

---

## 3. 总执行顺序

当前顺序固定为：

1. `Phase 0 = P0 契约与 trace 收口`
2. `Phase 1 = P1 PAS 最小可交易形态层`
3. `Phase 2 = P2 IRS 最小可交易排序层`
4. `Phase 3 = P3 MSS 最小可交易风控层`
5. `Phase 4 = P4 全链回归与 Gate 收口`

当前不允许跳步：

1. 不允许先改默认参数再补 trace
2. 不允许先跑大矩阵再补契约
3. 不允许同时并行改 `PAS / IRS / MSS` 三条主线

---

## 4. Phase 0：契约与 Trace 收口

### 4.1 目标

先把 5 个关键对象的正式契约落点和真相源补齐。

这一 phase 的价值不是提升收益，而是：

`让后面的收益变化终于能解释清楚。`

### 4.2 任务

#### Task P0-A Selector Trace

**目标**

1. 清理 `filter_reason <- reject_reason` 过渡残留
2. 为 `Selector` 增加稳定 trace

**代码落点**

1. `src/selector/selector.py`
2. `src/contracts.py`
3. `src/data/store.py`

**测试落点**

1. `tests/unit/selector/test_selector_strategy.py`

**产物**

1. `selector_candidate_trace_exp`

**检查项**

- [ ] `StockCandidate.score == preselect_score`
- [ ] 正式候选不再混入 `reject_reason`
- [ ] `candidate_top_n` 截断可在 trace 中解释

#### Task P0-B PAS Trigger Trace

**目标**

1. 增加 `pas_trigger_trace_exp`
2. 固定 `formal Signal` 和触发 trace 的边界

**代码落点**

1. `src/strategy/strategy.py`
2. `src/strategy/registry.py`
3. `src/contracts.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. 需要新增 `tests/unit/strategy/` 下 PAS 相关单测

**产物**

1. `pas_trigger_trace_exp`

**检查项**

- [ ] `l3_signals` 只保留 formal 最小字段
- [ ] trigger reason 和 rank sidecar 不再混写
- [ ] `signal_id` 幂等稳定

#### Task P0-C IRS Trace

**目标**

1. 增加 `irs_industry_trace_exp`
2. 固定行业层分数和 signal 层 `irs_score` 的分层命名

**代码落点**

1. `src/selector/irs.py`
2. `src/strategy/ranker.py`
3. `src/data/store.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. 需要新增 `tests/unit/selector/` 下 IRS 相关单测

**产物**

1. `irs_industry_trace_exp`

**检查项**

- [ ] `l3_irs_daily.score` 与 signal 层 `irs_score` 明确分离
- [ ] 未知行业与缺匹配行业统一 `FILL=50.0`
- [ ] 每日行业层 `SKIP / FILL` 可追溯

#### Task P0-D MSS Trace

**目标**

1. 增加 `mss_risk_overlay_trace_exp`
2. 固定 `MarketScore / mss_score / overlay` 三层边界

**代码落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`
3. `src/strategy/ranker.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`
2. `tests/unit/broker/test_broker.py`

**产物**

1. `mss_risk_overlay_trace_exp`

**检查项**

- [ ] `mss_score` 只作为 sidecar 解释位
- [ ] 真正执行容量变化能追到 `MssRiskOverlay`
- [ ] 覆盖关闭/缺失/正常三种路径能区分

#### Task P0-E Broker Lifecycle Trace

**目标**

1. 增加 `broker_order_lifecycle_trace_exp`
2. 固定订单全生命周期追溯口径

**代码落点**

1. `src/broker/broker.py`
2. `src/broker/risk.py`
3. `src/broker/matcher.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/broker/test_broker.py`
2. `tests/integration/backtest/test_backtest_engine.py`

**产物**

1. `broker_order_lifecycle_trace_exp`

**检查项**

- [ ] 风控拒绝、撮合拒绝、执行拒绝、过期四类原因可区分
- [ ] `signal_id -> order_id -> trade_id` 可完整追踪
- [ ] `origin` 能区分 `UPSTREAM_SIGNAL / EXIT_* / FORCE_CLOSE`

### 4.3 Phase 0 出场清单

- [ ] 5 个对象各自都有 trace 真相源
- [ ] 关键拒绝语义已有单测
- [ ] `run_id + signal_id` 可以串起全链
- [ ] 不改当前默认参数
- [ ] docs gate 通过

---

## 5. Phase 1：PAS 最小可交易形态层

### 5.1 目标

把 `PAS-trigger` 补到最小可交易形态层。

本 phase 只做：

1. `BPB`
2. `pattern_quality_score`
3. `stop / target / failure` 参考层

### 5.2 任务

#### Task P1-A BPB Detector

**代码落点**

1. `src/strategy/`
2. `src/strategy/registry.py`
3. `src/strategy/strategy.py`

**测试落点**

1. 新增 `tests/unit/strategy/` 下 BPB detector 单测

**检查项**

- [ ] `BPB` 已进入 registry
- [ ] 单形态幂等稳定
- [ ] 不破坏 `BOF` 当前路径

#### Task P1-B Pattern Quality

**代码落点**

1. `src/strategy/`
2. `src/strategy/strategy.py`
3. `src/contracts.py` 或 sidecar 写入层

**测试落点**

1. 新增 `tests/unit/strategy/` 下 quality 单测

**检查项**

- [ ] `pattern_quality_score` 可稳定产出
- [ ] `quality_breakdown` 可解释
- [ ] formal `Signal` 不被污染

#### Task P1-C PAS Reference Layer

**代码落点**

1. `src/strategy/strategy.py`
2. `src/data/store.py`

**测试落点**

1. 新增 `tests/unit/strategy/` 下 reference layer 单测

**检查项**

- [ ] `stop / target / failure` 已进入 sidecar 或 trace
- [ ] Broker 当前不强依赖这些参考字段

#### Task P1-D PAS Evidence

**脚本落点**

1. 新增 `scripts/backtest/run_v001_plus_pas_ablation.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 能跑 `BOF`
- [ ] 能跑 `BOF + BPB`
- [ ] 能跑 `BOF + quality`
- [ ] 能跑 `BOF + BPB + quality`

### 5.3 Phase 1 出场清单

- [ ] `BPB` 已落地
- [ ] `pattern_quality_score` 已落地
- [ ] 参考层字段已落地
- [ ] `PAS` 专项 evidence 已生成
- [ ] 不破坏当前 `BOF` 基线

---

## 6. Phase 2：IRS 最小可交易排序层

### 6.1 目标

把 `IRS-lite` 补到最小可交易排序层。

本 phase 只做：

1. `RS`
2. `RV`
3. `RT`
4. `BD`
5. `GN`

### 6.2 任务

#### Task P2-A Industry Daily Enrichment

**代码落点**

1. `src/data/cleaner.py`

**测试落点**

1. 新增 `tests/unit/data/` 下行业聚合单测

**检查项**

- [ ] `return_5d / return_20d`
- [ ] `amount_ma20 / volume_ma20`
- [ ] 相对量能基础字段

#### Task P2-B Industry Structure Daily

**代码落点**

1. `src/data/cleaner.py`
2. 新增行业结构聚合脚本

**测试落点**

1. 新增 `tests/unit/data/` 下结构聚合单测

**检查项**

- [ ] `leader_count`
- [ ] `leader_strength`
- [ ] `strong_stock_ratio`
- [ ] `bof_hit_density_5d`

#### Task P2-C IRS Scorer Rewrite

**代码落点**

1. `src/selector/irs.py`
2. `src/strategy/ranker.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. 新增 `tests/unit/selector/` 下 IRS scorer 单测

**检查项**

- [ ] `rs_score / rv_score / rt_score / bd_score / gn_score`
- [ ] `rotation_status`
- [ ] 兼容当前 rank sidecar

#### Task P2-D IRS Evidence

**脚本落点**

1. 新增 `scripts/backtest/run_v001_plus_irs_ablation.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 能跑 `IRS-lite`
- [ ] 能跑 `IRS-RSRV`
- [ ] 能跑 `IRS-RSRVRTBDGN`

### 6.3 Phase 2 出场清单

- [ ] 多周期强度已落地
- [ ] 相对量能已落地
- [ ] 轮动状态已落地
- [ ] 扩散度已落地
- [ ] 牛股基因轻量层已落地
- [ ] IRS 专项 evidence 已生成

---

## 7. Phase 3：MSS 最小可交易风控层

### 7.1 目标

把 `MSS-lite` 补到最小可交易风控层。

本 phase 只做：

1. `phase`
2. `phase_trend`
3. `phase_days`
4. `position_advice`
5. `risk_regime`

### 7.2 任务

#### Task P3-A MSS Phase Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

**检查项**

- [ ] `phase`
- [ ] `phase_trend`
- [ ] `phase_days`

#### Task P3-B Position Advice Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

**检查项**

- [ ] `position_advice`
- [ ] 周期与建议仓位映射可回放

#### Task P3-C Risk Regime Integration

**代码落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`

**测试落点**

1. `tests/unit/broker/test_broker.py`

**检查项**

- [ ] `risk_regime`
- [ ] `risk_regime -> overlay` 映射
- [ ] Broker 容量变化可解释

#### Task P3-D MSS Evidence

**脚本落点**

1. 新增 `scripts/backtest/run_v001_plus_mss_regime_sensitivity.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 输出 `phase / position_advice / risk_regime` 分布
- [ ] 输出不同 regime 下的 `EV / PF / MDD`

### 7.3 Phase 3 出场清单

- [ ] `phase / phase_trend / phase_days` 已落地
- [ ] `position_advice` 已落地
- [ ] `risk_regime` 已落地
- [ ] Broker 已稳定消费 `risk_regime`
- [ ] MSS 专项 evidence 已生成

---

## 8. Phase 4：全链回归与 Gate 收口

### 8.1 目标

把 `P0-P3` 的结果真正回到主线矩阵里，给出新的 `GO / NO-GO`。

### 8.2 任务

#### Task P4-A Matrix Replay

**脚本落点**

1. `scripts/backtest/run_v001_plus_dtt_matrix.py`
2. `scripts/backtest/check_idempotency.py`

**检查项**

- [ ] 4 组矩阵可重跑
- [ ] `legacy` 可回退
- [ ] 幂等稳定

#### Task P4-B Attribution Bundle

**脚本落点**

1. `scripts/backtest/run_v001_plus_trade_attribution.py`
2. `scripts/backtest/run_v001_plus_windowed_sensitivity.py`
3. `scripts/backtest/run_v001_plus_rank_decomposition.py`

**检查项**

- [ ] trade attribution
- [ ] windowed sensitivity
- [ ] rank decomposition

#### Task P4-C Mainline Decision

**文档落点**

1. `docs/spec/common/records/development-status.md`
2. `docs/spec/v0.01-plus/records/`

**检查项**

- [ ] 明确 `GO / NO-GO`
- [ ] 明确回退条件
- [ ] 明确默认参数是否调整

### 8.3 Phase 4 出场清单

- [ ] 主线矩阵重跑完成
- [ ] 专项 evidence 补齐
- [ ] `GO / NO-GO` 已写回状态文档
- [ ] 当前版本 done / not done 已可明确判定

---

## 9. 每个 Phase 的统一交付模板

后续每推进一个 phase，都必须补齐下面 4 类内容：

### 9.1 代码

- [ ] 修改文件明确
- [ ] 新增文件明确
- [ ] 不改本 phase 非目标对象

### 9.2 测试

- [ ] 至少一组 unit test
- [ ] 必要时补 integration test
- [ ] 回归现有关键测试不破坏

### 9.3 Artifact / Evidence

- [ ] sidecar / trace / script 输出明确
- [ ] evidence json 落地
- [ ] records markdown 落地

### 9.4 治理同步

- [ ] `development-status.md` 同步进度
- [ ] `README / gate / roadmap` 如有必要同步
- [ ] docs gate 通过

---

## 10. 下一步

从本执行文生效起，下一步不再继续写新的执行散文。

直接进入：

1. `Phase 0 / Task P0-A ~ P0-E`

也就是：

`先把契约与 trace 收口做完，再谈 PAS / IRS / MSS 的升级。`
