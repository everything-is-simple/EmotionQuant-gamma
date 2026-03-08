# Current Mainline Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `当前主线唯一实现方案`  
**上游锚点**:

1. `blueprint/01-full-design/03-selector-contract-supplement-20260308.md`
2. `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md`
3. `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md`
4. `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md`
5. `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md`
6. `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`
7. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
8. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`
9. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`
10. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`
11. `docs/spec/common/records/development-status.md`

---

## 1. 定位

本文是 `blueprint/` 下的第一份实现方案正文。

它只回答 5 件事：

1. 当前版本到底实现什么
2. 当前版本明确不实现什么
3. 每个实现包使用什么正式契约
4. 每个实现包需要产出什么 artifact / test / evidence
5. 什么条件满足才算当前版本 done

它不是：

1. 新版设计 SoT
2. 路线图散文
3. 历史 spec 汇总贴

一句话说：

`01-full-design` 已经冻结“该做成什么样”，本文只冻结“这一版具体做哪一刀”。 

---

## 2. 当前版本目标

当前版本的唯一目标不是“把 DTT 再跑通一次”，而是把当前主线补到：

`最小可交易强度 MVP`

当前链路固定为：

```text
Selector 初选
-> PAS-trigger / BOF
-> IRS 排序
-> MSS 控仓位
-> Broker 执行
```

本版完成的定义固定为：

1. `Selector` 不再改语义，只补契约和 trace
2. `PAS` 不再只是 `BOF trigger`
3. `IRS` 不再只是 `IRS-lite`
4. `MSS` 不再只是 `MSS-lite`
5. `Broker / Risk` 能解释容量变化和订单生命周期
6. `legacy` 回退路径仍然可重跑

---

## 3. 当前版本明确不做什么

下面这些内容，本版一律不做：

1. 不把当前工作改名塞进 `v0.02`
2. 不恢复旧 `Integration -> TradeSignal -> Trading` 整套桥接
3. 不把 `MSS` 拉回前置 gate
4. 不把 `IRS` 拉回前置行业硬过滤
5. 不做 `TST / PB / CPB` 全生态恢复
6. 不做政策 / 事件 / 主题语义层
7. 不做 formal `Signal` 全量 schema migration
8. 不做部分成交、拆单、分批执行状态机
9. 不做 GUI
10. 不为“先有东西跑”再裁掉核心算法语义

---

## 4. 当前版本的实现裁剪

### 4.1 已冻结，不再扩写的部分

下面这些内容，本版只做实现对齐，不再扩设计：

| 对象 | 本版策略 |
|---|---|
| `Selector` | 保持当前职责不变，只补正式字段落点与 `trace` |
| `BOF` | 保持为当前在线基形态 |
| `Signal / Order / Trade` | 保持 formal 最小契约，不做大迁移 |
| `legacy_bof_baseline` | 只保留 compare / rollback，不再增强 |
| `Broker` T+1 Open | 保持不变，不引入盘中主动交易 |

### 4.2 本版必须补齐的 5 个实现包

本版只做下面 5 个实现包，而且必须按顺序推进：

1. `P0` 契约与 trace 收口
2. `P1` PAS 最小可交易形态层
3. `P2` IRS 最小可交易排序层
4. `P3` MSS 最小可交易风控层
5. `P4` 全链回归与 Gate 收口

原因很直接：

`没有 P0，后面没有真相源；没有 P1/P2/P3，后面没有真正的 MVP；没有 P4，前面全都不能切主线。`

---

## 5. 五个实现包

### 5.1 P0 契约与 trace 收口

**本包目标**

把当前主线 5 个对象的正式契约、兼容字段和真相源先落到代码与 artifact。

**本包必须做**

1. `Selector`：
   - 清理 `filter_reason <- reject_reason` 过渡残留
   - 增加 `selector_candidate_trace_exp` 或同等 artifact
2. `PAS-trigger / BOF`：
   - 增加 `pas_trigger_trace_exp`
   - 固定 `formal Signal` 与 trace 边界
3. `IRS-lite`：
   - 增加 `irs_industry_trace_exp`
   - 固定行业层分数和 signal 层附着分的分层命名
4. `MSS-lite`：
   - 增加 `mss_risk_overlay_trace_exp`
   - 固定 `MarketScore / mss_score / overlay` 三层边界
5. `Broker / Risk`：
   - 增加 `broker_order_lifecycle_trace_exp`
   - 固定风控拒绝、撮合拒绝、执行拒绝、过期四类原因

**本包明确不做**

1. 不在这个包里升级算法逻辑
2. 不在这个包里改主线排序规则
3. 不在这个包里动默认参数

**本包主要落点**

1. `src/contracts.py`
2. `src/selector/selector.py`
3. `src/strategy/strategy.py`
4. `src/strategy/ranker.py`
5. `src/selector/irs.py`
6. `src/selector/mss.py`
7. `src/broker/risk.py`
8. `src/broker/broker.py`
9. `src/data/store.py`

**本包验收**

1. 当前 5 个对象各自都有独立 trace 真相源
2. `run_id + signal_id` 能完整追到候选、触发、排序、控仓、执行
3. 单测覆盖契约边界与关键拒绝语义

---

### 5.2 P1 PAS 最小可交易形态层

**本包目标**

把当前 `PAS-trigger` 补到“最小可交易形态层”，而不是继续停留在纯 `BOF trigger`。

**本包必须做**

1. 保持 `BOF` 为在线基形态
2. 恢复 `BPB`，作为本版唯一新增形态
3. 增加 `pattern_quality_score`
4. 增加 `stop / target / failure` 参考层输出

**本包明确不做**

1. 不恢复 `TST / PB / CPB`
2. 不把形态质量层直接写回 formal `Signal`
3. 不让 Broker 直接依赖 PAS 参考止损/目标位做强耦合执行

**本包主要落点**

1. `src/strategy/` 下的 PAS detector / registry / quality 相关文件
2. `src/strategy/strategy.py`
3. `src/contracts.py` 或 sidecar 写入层
4. `tests/unit/strategy/`
5. `scripts/backtest/` 下 PAS 相关消融脚本

**本包验收**

1. 至少能跑：
   - `BOF`
   - `BOF + BPB`
   - `BOF + quality`
   - `BOF + BPB + quality`
2. 能输出 `pattern_quality_score` 与参考层字段
3. 能解释新增形态/质量层改变了哪些票、哪些日子、哪些执行结果

---

### 5.3 P2 IRS 最小可交易排序层

**本包目标**

把当前 `IRS-lite` 补到“最小可交易行业排序层”。

**本包必须做**

1. `RS` 从单日升级为多周期相对强度
2. `CF` 升级为真正的相对量能层 `RV`
3. 增加 `RT`：轮动状态层
4. 增加 `BD`：行业扩散度层
5. 增加 `GN`：牛股基因轻量层

**本包明确不做**

1. 不做政策 / 主题 / 事件语义层
2. 不让 `IRS` 回到前置过滤
3. 不把 `IRS` 扩到完整自适应学习系统

**本包主要落点**

1. `src/data/cleaner.py`
2. `src/selector/irs.py`
3. `src/strategy/ranker.py`
4. 新增或补齐行业内部结构聚合脚本 / 表
5. `tests/unit/data/`
6. `tests/unit/selector/`
7. `scripts/backtest/run_v001_plus_irs_ablation.py`

**本包验收**

1. 至少能跑：
   - `IRS-lite`
   - `IRS-RSRV`
   - `IRS-RSRVRTBDGN`
2. 能输出：
   - `rs_score`
   - `rv_score`
   - `rt_score`
   - `bd_score`
   - `gn_score`
   - `rotation_status`
3. 能解释排序变化来自哪一层，而不是只看到总分变化

---

### 5.4 P3 MSS 最小可交易风控层

**本包目标**

把当前 `MSS-lite` 补到“最小可交易市场风控层”。

**本包必须做**

1. 增加 `phase`
2. 增加 `phase_trend`
3. 增加 `phase_days`
4. 增加 `position_advice`
5. 增加 `risk_regime`
6. 让 `Broker / Risk` 由 `risk_regime` 或等价映射稳定消费

**本包明确不做**

1. 不把 `MSS` 拉回 `Selector`
2. 不把 `MSS` 写回 `final_score`
3. 不在这一版就追求完整自适应周期模型

**本包主要落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`
3. `src/data/store.py`
4. `tests/unit/selector/`
5. `tests/unit/broker/`
6. `scripts/backtest/run_v001_plus_mss_regime_sensitivity.py`

**本包验收**

1. `l3_mss_daily` 能追溯：
   - `score`
   - `signal`
   - `phase`
   - `phase_trend`
   - `phase_days`
   - `position_advice`
   - `risk_regime`
2. `Broker` 的容量变化能解释为：
   - `risk_regime -> overlay -> quantity`
3. 长窗口证据能比较不同 regime 对 `EV / PF / MDD` 的影响

---

### 5.5 P4 全链回归与 Gate 收口

**本包目标**

在 `P0-P3` 完成后，重跑主线证据矩阵，判断当前主线是否从 `NO-GO` 进入可切默认路径。

**本包必须做**

1. 保留 `legacy_bof_baseline` 对照
2. 重跑固定矩阵：
   - `legacy_bof_baseline`
   - `v0_01_dtt_bof_only`
   - `v0_01_dtt_bof_plus_irs_score`
   - `v0_01_dtt_bof_plus_irs_mss_score`
3. 重跑 `PAS / IRS / MSS` 各自专项消融
4. 补齐 trade attribution / windowed sensitivity / regime sensitivity
5. 明确给出 `GO / NO-GO`

**本包明确不做**

1. 不为了过 Gate 临时改默认参数掩盖问题
2. 不删除 legacy 回退路径
3. 不把“收益偶然变好”直接当成可切主线结论

**本包主要落点**

1. `scripts/backtest/`
2. `docs/spec/v0.01-plus/evidence/`
3. `docs/spec/v0.01-plus/records/`
4. `docs/spec/common/records/development-status.md`

**本包验收**

1. 同一数据快照下矩阵可重跑
2. `legacy` 仍可用
3. 当前主链收益结构变化可解释
4. 最终 `GO / NO-GO` 结论可写进状态文档

---

## 6. 当前版本使用的正式契约

本版统一遵守下面这些正式契约与真相源边界：

| 层级 | 正式契约 | 当前真相源 |
|---|---|---|
| Selector | `StockCandidate` | `selector_candidate_trace_exp` |
| PAS / Strategy | `Signal` | `pas_trigger_trace_exp + l3_signal_rank_exp` |
| IRS | `IndustryScore` | `irs_industry_trace_exp + l3_irs_daily` |
| MSS | `MarketScore` | `mss_risk_overlay_trace_exp + l3_mss_daily` |
| Broker | `Order / Trade` | `broker_order_lifecycle_trace_exp + l4_orders + l4_trades` |

当前硬约束：

1. formal 契约优先保持兼容
2. 细节与解释优先放 sidecar / trace
3. 模块间只传结果契约，不传内部中间特征

---

## 7. 当前版本的实施顺序

当前顺序固定为：

1. `P0 契约与 trace 收口`
2. `P1 PAS`
3. `P2 IRS`
4. `P3 MSS`
5. `P4 全链回归与 Gate`

不允许跳成：

1. 先改默认参数
2. 先跑大矩阵
3. 再回头补契约和 trace

原因很直接：

`没有真相源，后面的收益变化全都解释不清。`

---

## 8. Done 标准

当前版本只有同时满足下面条件，才算 done：

1. `P0-P4` 五个实现包全部完成
2. 当前主线 5 个对象都已从“lite / trigger / 口头约束”升级为“可追溯实现”
3. `legacy` 回退路径仍然可跑
4. docs gate、核心 unit/integration tests、专项 evidence 全部通过
5. `development-status.md` 能明确给出新的 `GO / NO-GO`

当前特别强调：

`如果 PAS / IRS / MSS 任何一个仍然停留在 lite 骨架，本版就不算完成。`

---

## 9. 和旧 spec 的关系

当前 `docs/spec/v0.01-plus/roadmap/spec-01~04` 仍保留，但从本补充文生效起，它们的角色应视为：

1. 历史实现材料
2. 当前实现方案的来源输入
3. 后续需要被收口和对齐的对象

本文当前在 `blueprint/` 中的角色是：

`当前主线唯一实现方案首稿`

下一步不是再写第二份实现 spec，而是：

1. 把后续 roadmap / phase / task 只从本文往下拆
2. 再把 `docs/spec/v0.01-plus/` 收口成只承担实现职责的正式入口
