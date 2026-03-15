# Current Mainline Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `当前主线唯一实现方案`  
**上游锚点**:

1. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
2. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
3. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
5. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
6. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
7. `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
8. `blueprint/01-full-design/08-mss-minimal-tradable-design-20260309.md`
9. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
10. `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`
11. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
12. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`
13. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`
14. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md`
15. `docs/spec/common/records/development-status.md`

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

当前还必须额外强调一条：

`P1 / P2 / P3` 不是只从 contract annex 往下做，而是必须同时受对应算法正文约束。

---

## 2. 当前执行前提（继承，不在本文内重写）

当前实现方案默认继承一组固定执行前提，后续实现不得绕开：

1. 三目录纪律固定为：
   - `G:\EmotionQuant-gamma` = 代码 / 文档 / 配置
   - `G:\EmotionQuant_data` = 正式数据库 / 日志 / 长期产物
   - `G:\EmotionQuant-temp` = 临时文件 / 工作副本 / 实验缓存
2. 当前默认执行库固定为 `G:\EmotionQuant_data\emotionquant.duckdb`。
3. 当前默认旧库候选固定为 `G:\EmotionQuant_data\duckdb\emotionquant.duckdb`。
4. 数据补齐顺序固定为“先复用本地旧库，再用 TuShare 双通道补缺”。
5. 截至 `2026-03-11`，当前正式开工顺序固定为 `Phase 3 / MSS -> Phase 4 / Gate`。

完整口径统一见：

`blueprint/03-execution/00-current-dev-data-baseline-20260311.md`

---

## 3. 当前版本目标

当前版本的唯一目标不是“把 DTT 再跑通一次”，而是把当前主线补到：

`最小可交易强度 MVP`

当前链路固定为：

```text
Selector 初选
-> PAS trigger / registry
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

## 4. 当前版本明确不做什么

下面这些内容，本版一律不做：

1. 不把当前工作改名塞进 `v0.02`
2. 不恢复旧 `Integration -> TradeSignal -> Trading` 整套桥接
3. 不把 `MSS` 拉回前置 gate
4. 不把 `IRS` 拉回前置行业硬过滤
5. 不做非 `YTC` 额外 `PAS` 形态扩张
6. 不做政策 / 事件 / 主题语义层
7. 不做 formal `Signal` 全量 schema migration
8. 不做部分成交、拆单、分批执行状态机
9. 不做 GUI
10. 不为“先有东西跑”再裁掉核心算法语义

---

## 5. 当前版本的实现裁剪

### 5.1 已冻结，不再扩写的部分

下面这些内容，本版只做实现对齐，不再扩设计：

| 对象 | 本版策略 |
|---|---|
| `Selector` | 保持当前职责不变，只补正式字段落点与 `trace` |
| `BOF` | 保持为当前在线基形态 |
| `Signal / Order / Trade` | 保持 formal 最小契约，不做大迁移 |
| `legacy_bof_baseline` | 只保留 compare / rollback，不再增强 |
| `Broker` T+1 Open | 保持不变，不引入盘中主动交易 |

### 5.2 本版必须补齐的 5 个实现包

本版只做下面 5 个实现包，而且必须按顺序推进：

1. `P0` 契约与 trace 收口
2. `P1` PAS 最小可交易五形态层
3. `P2` IRS 最小可交易排序层
4. `P3` MSS 最小可交易风控层
5. `P4` 全链回归与 Gate 收口

原因很直接：

`没有 P0，后面没有真相源；没有 P1/P2/P3，后面没有真正的 MVP；没有 P4，前面全都不能切主线。`

### 5.3 实现包和 Full Design 的绑定关系

| 实现包 | 必须绑定的 Full Design 文档 | 说明 |
|---|---|---|
| `P0` | `01 / 02 / 03 / 04 / 05` | 只做 contract、trace、truth-source 收口 |
| `P1` | `02 + 06` | `02` 钉住 PAS formal 边界，`06` 钉住五形态算法正文 |
| `P2` | `03 + 07` | `03` 钉住 IRS contract 边界，`07` 钉住排序层算法正文 |
| `P3` | `04 + 08` | `04` 钉住 MSS contract 边界，`08` 钉住风控层算法正文 |
| `P4` | `01-08` | 只负责把已冻结主线重跑、归因、判定 `GO / NO-GO` |

执行期若发现 `02-implementation-spec/` 与 `01-full-design/01-08` 表述冲突，必须先回到上游正文消歧，不能在实现层私自解释。

---

## 6. 五个实现包

### 6.1 P0 契约与 trace 收口

**本包目标**

把当前主线 5 个对象的正式契约、兼容字段和真相源先落到代码与 artifact。

**本包必须做**

1. `Selector`：
   - 清理 `filter_reason <- reject_reason` 过渡残留
   - 增加 `selector_candidate_trace_exp` 或同等 artifact
2. `PAS trigger / registry`：
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

### 6.2 P1 PAS 最小可交易形态层

**本包目标**

把当前 `PAS-trigger` 补到“最小可交易五形态层”，而不是继续停留在纯 `BOF trigger`。

**本包必须做**

1. 保持 `BOF` 为在线基形态
2. 恢复 `BPB / PB / TST / CPB`
3. 建立五形态 registry 与单形态启停
4. 增加 `pattern_quality_score`
5. 增加 `stop / target / failure` 参考层输出
6. 增加单形态独立回测与 registry summary

**本包明确不做**

1. 不恢复 `PAS-full` 机会等级体系
2. 不把形态质量层直接写回 formal `Signal`
3. 不让 Broker 直接依赖 PAS 参考止损/目标位做强耦合执行
4. 不在没有专项证据的前提下继续扩非 `YTC` 额外形态

**本包主要落点**

1. `src/strategy/` 下的 PAS detector / registry / quality 相关文件
2. `src/strategy/strategy.py`
3. `src/contracts.py` 或 sidecar 写入层
4. `tests/unit/strategy/`
5. `scripts/backtest/` 下 PAS 相关消融脚本

**本包验收**

1. 至少能跑：
   - `BOF`
   - `BPB`
   - `PB`
   - `TST`
   - `CPB`
   - `YTC5_ANY`
   - `YTC5_ANY + quality`
2. 能输出 `pattern_quality_score` 与参考层字段
3. 能输出 registry summary，并解释新增形态/质量层改变了哪些票、哪些日子、哪些执行结果

---

### 6.3 P2 IRS 最小可交易排序层

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

**本包资源硬约束**

1. `Phase 2` 默认按 `27GB RAM ceiling` 设计与验证；`27GB` 是硬上限，目标峰值尽量 `<= 25GB`。
2. 临时 DuckDB、工作副本、实验缓存必须落在 `G:\EmotionQuant-temp`，不得写入仓库根目录。
3. `IRS` 实现默认采用 `incremental-first`：优先增量窗口、分日/分行业处理，不默认全量重建。
4. `IRS` 实现默认采用 `DuckDB-first`：能在 DuckDB 做的 `join / group by / window / rank`，不先搬到 pandas。
5. 禁止：
   - 一次读取过多数据
   - 让大 DataFrame / 大中间态长时间常驻内存
   - 为了省代码而牺牲机器稳定性

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

### 6.4 P3 MSS 最小可交易风控层

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

### 6.5 P4 全链回归与 Gate 收口

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

## 7. 当前版本使用的正式契约

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

## 8. 当前版本的实施顺序

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

## 9. Done 标准

当前版本只有同时满足下面条件，才算 done：

1. `P0-P4` 五个实现包全部完成
2. 当前主线 5 个对象都已从“lite / trigger / 口头约束”升级为“可追溯实现”
3. `legacy` 回退路径仍然可跑
4. docs gate、核心 unit/integration tests、专项 evidence 全部通过
5. `development-status.md` 能明确给出新的 `GO / NO-GO`

当前特别强调：

`如果 PAS / IRS / MSS 任何一个仍然停留在 lite 骨架，本版就不算完成。`

---

## 10. 和旧 spec 的关系

当前 `docs/spec/v0.01-plus/roadmap/spec-01~04` 仍保留，但从本补充文生效起，它们的角色应视为：

1. 历史实现材料
2. 当前实现方案的来源输入
3. 后续需要被收口和对齐的对象

本文当前在 `blueprint/` 中的角色是：

`当前主线唯一实现方案`

下一步不是再写第二份实现 spec，而是：

1. 把后续 roadmap / phase / task 只从本文往下拆
2. 再把 `docs/spec/v0.01-plus/` 收口成只承担实现职责的正式入口

---

## 11. Phase 5A 继承的 Normandy 实现约束

`Phase 5A` 生效后，当前实现方案新增继承以下 Normandy 边界：

1. 当前默认运行口径仍然是 `legacy_bof_baseline`；实现层不把 `BOF_CONTROL` 改写成主线默认运行标签。
2. 当前主线只允许以 3 种形态复用 Normandy 产物：
   - `baseline governance conclusion`
   - `existing BOF stack wrapper / optional hook scaffold`
   - `Tachibana pilot-pack negative constraints`
3. 当前主线允许引用的 Tachibana 面，只限于：
   - `R4 + R5 + R6 + R7 + R10 only`
   - `existing BOF stack + thin runner`
   - `same-code cooldown signal_filter hook` 作为 `off-by-default` 的可选挂点
   - `TRAIL_SCALE_OUT_25_75` 作为 `reduce_to_core engineering proxy`
4. `Phase 5A` 明确不实现：
   - `R2 / R3 / R8 / R9`
   - 完整 Tachibana system 叙事
   - `CD5 / CD10` 默认 cooldown
   - noncanonical side references
   - `reduced_unit_scale` executable sizing
5. `Phase 5A` 只吸收 Normandy 边界，不改写当前 Broker / Risk 默认 control；`FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / FULL_EXIT_CONTROL` 的主线吸收留到 `Phase 5B`。

---

## 12. Phase 5B 继承的 Positioning 实现约束

`Phase 5B` 生效后，当前实现方案新增继承以下 Positioning 边界：

1. 当前实现层允许把 `FIXED_NOTIONAL_CONTROL` 写成 `current operating control baseline`，但不允许把它写成主线默认仓位公式。
2. 当前实现层允许把 `SINGLE_LOT_CONTROL` 写成 `floor sanity baseline`，但不允许把它写成第二 operating lane 或新的部署默认值。
3. 当前实现层允许把 `FULL_EXIT_CONTROL` 写成 `partial-exit canonical control baseline`，但不允许把 retained queue 误写成 formal control promotion。
4. 当前实现层若引用 `TRAIL_SCALE_OUT_25_75`，必须同时满足两条：
   - 在 Positioning 语境下，它只能叫 `partial-exit provisional leader`
   - 在 Tachibana 语境下，它继续只能叫 `reduce_to_core engineering proxy`
5. 当前实现层明确不实现：
   - `WILLIAMS_FIXED_RISK / FIXED_RATIO` 的主线 promotion
   - `TRAIL_SCALE_OUT_33_67 / 50_50 / 67_33 / 75_25` 的主线 promotion
   - `PX1` 自动打开
   - `PX2` 自动打开
   - 任何“partial-exit 替 sizing lane 补救”的隐含 baseline
6. `Phase 5B` 只吸收 Positioning 边界，不改写当前 Broker 默认执行语义，不切换主线默认 exit formula；统一的 no-fake governance patch 留到 `Phase 5C`。
