# Phase 2 Card

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `P2 IRS 最小可交易排序层`  
**定位**: `当前主线第三张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
5. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

---

## 1. 目标

把当前 `IRS-lite` 补到：

`最小可交易排序层`

---

## 2. 范围

当前 phase 只做：

1. `RS`
2. `RV`
3. `RT`
4. `BD`
5. `GN`

当前 phase 明确不做：

1. 不做政策 / 主题 / 事件语义层
2. 不让 `IRS` 回到前置过滤
3. 不扩成完整自适应学习系统

### 2.1 机器资源硬约束

当前 `Phase 2 / IRS` 默认按个人开发机约束执行：

1. `27GB RAM ceiling`
2. `temp path discipline`
3. `incremental-first`
4. `DuckDB-first`

这 4 条不是优化建议，而是执行硬约束。

#### 2.1.1 27GB RAM ceiling

1. 默认视为：
   - 机器总内存 `32GB`
   - 运行时硬上限约 `27GB`
   - 实际目标峰值尽量 `<= 25GB`
2. `Phase 2` 任何实现不得以“偶尔会吃满内存”为可接受代价。
3. 禁止：
   - 一次把全市场 × 长窗口 × 多层中间态整体拉进 pandas
   - 为了省代码而把大表全量读入内存后再慢慢筛
   - 让大 DataFrame / 大中间表在内存中长时间常驻

#### 2.1.2 temp path discipline

1. 临时 DuckDB、工作副本、pytest 临时目录、实验缓存统一写入：
   - `G:\EmotionQuant-temp`
2. 长期数据与正式执行库统一位于：
   - `G:\EmotionQuant_data`
3. 仓库根目录 `G:\EmotionQuant-gamma` 禁止落运行时缓存、临时数据库与实验中间文件。

#### 2.1.3 incremental-first

1. 默认先做增量，不做全量。
2. `build_l2 / build_l3 / IRS evidence / IRS ablation` 默认都应优先使用：
   - 按日期窗口增量
   - 按行业分批
   - 按交易日分段
3. 只有在明确需要 `force rebuild` 时，才允许全量重建。
4. 即便全量重建，也必须优先设计成：
   - 分日处理
   - 分批落库
   - 中间结果及时释放

#### 2.1.4 DuckDB-first

1. 能在 DuckDB 内完成的：
   - `join`
   - `group by`
   - `window`
   - `aggregate`
   - `top-n / rank`
   优先留在 DuckDB 做。
2. pandas 只用于：
   - 小规模结果整形
   - 单日/单行业轻量计算
   - 必须在 Python 侧实现的少量状态逻辑
3. 禁止默认把“大表先读出来再 groupby/transform”当作第一实现路径。

#### 2.1.5 明确禁止项

1. 禁止一次读取过多数据。
2. 禁止让大内存占用持续过久。
3. 禁止在仓库内生成临时 DuckDB、副本库、实验缓存。
4. 禁止为了跑通 `Phase 2` 先牺牲机器稳定性。

### 2.2 已知大内存场景与现有防守

当前系统里，最容易把机器拖慢或拖死的不是“某一个大函数”，而是下面 4 类大内存场景。

#### 2.2.1 场景 A：L2 构建期的全市场长窗口展开

主要位置：

1. `src/data/cleaner.py -> clean_stock_adj_daily()`
2. `src/data/cleaner.py -> clean_market_snapshot()`

风险来源：

1. `lookback_start = start - 180/220 days`
2. 全市场长窗口 `groupby + rolling`
3. `limit_up_streak / new_high_streak` 这类逐票累计逻辑

现有防守：

1. `build_l2 / build_l3` 支持按窗口增量，不要求默认全量重建
2. 加工层仍按“窗口 -> 落库 -> 释放”处理，不把整段历史长期常驻运行态
3. 正式执行库与工作副本已分离，避免实验中间态回写仓库目录

Phase 2 额外要求：

1. `P2-A / P2-B` 不允许再引入新的“全市场长窗口宽表常驻内存”路径
2. 新行业层 enrichment 优先 DuckDB 聚合，禁止默认在 pandas 里先全量铺开

#### 2.2.2 场景 B：Selector / IRS 把大表先拉进 pandas 再排序/聚合

主要位置：

1. `src/selector/selector.py -> _load_universe_snapshot()`
2. `src/selector/irs.py -> compute_irs()`

风险来源：

1. 全市场截面 + 行业映射
2. 长窗口行业日线 + 多轮 `groupby / transform`
3. 如果先整段读入 pandas，再做多周期排名，会明显抬高峰值

现有防守：

1. `build_l3` 已改成 `MSS / IRS` 双进度锚，避免为了补一层而全量带起另一层
2. `DuckDB-first` 已写成正式约束，要求 `join / group by / window / rank` 尽量留在库内
3. `incremental-first` 已要求优先增量窗口、分日/分行业处理

Phase 2 额外要求：

1. `IRS scorer rewrite` 禁止默认走“整段全历史常驻 pandas”路线
2. 多周期 `RS / RV / RT / BD / GN` 优先设计成：
   - DuckDB 预聚合
   - 分日迭代
   - 小表 attach

#### 2.2.3 场景 C：PAS 历史加载与多形态评估

主要位置：

1. `src/strategy/strategy.py -> _load_candidate_histories_batch()`
2. `src/strategy/strategy.py -> generate_signals()`

风险来源：

1. 候选股 × `lookback_days` × detector 数量
2. 如果一次把候选全集历史拉满，再逐形态处理，会迅速放大内存与中间态寿命

现有防守：

1. 已有 `pas_eval_batch_size`
2. 已有 `_iter_candidate_batches()`
3. 已有 `_load_candidate_histories_batch()`，一个 batch 只查一次历史
4. `_tmp_dtt_rank_stage` 走 DuckDB temp table，而不是在 Python 里长时间累积排序中间态

结论：

1. 这是系统中已经被有效压住的一类大内存场景
2. `Phase 2` 不允许新逻辑破坏这类“分批 + 短生命周期”模式

#### 2.2.4 场景 D：Ablation / Evidence 重跑时的副本库与长窗口重建

主要位置：

1. `src/backtest/ablation.py`
2. `src/backtest/pas_ablation.py`
3. `scripts/backtest/`

风险来源：

1. 长窗口 `build_layers(..., force=True)`
2. 多场景连续重跑
3. 工作副本库 + trace / evidence 中间产物同时存在

现有防守：

1. `prepare_working_db()` 把工作副本放在外部路径
2. `working_db_path / artifact_root` 已支持写入 `G:\EmotionQuant-temp`
3. `run-scoped trace cleanup` 已避免同一场景内制造无意义大残留

Phase 2 额外要求：

1. `IRS ablation` 默认必须走工作副本库
2. 不允许默认全量重建
3. 必须提供：
   - `start/end`
   - `skip-rebuild`
   - `working-db-path`

#### 2.2.5 当前系统的内存防守结论

当前已经明确落地的防守手段有：

1. `incremental-first`
2. `DuckDB-first`
3. `pas_eval_batch_size` 分批
4. `_load_candidate_histories_batch()` 批量单次拉历史
5. `_tmp_dtt_rank_stage` 把排序中间态留在 DuckDB
6. `prepare_working_db()` + `working_db_path` 把副本库放在 `G:\EmotionQuant-temp`
7. `DUCKDB_MEMORY_LIMIT` 环境变量可进一步限额

接下来 `Phase 2` 的硬要求不是“再想更多优化”，而是：

1. 不新增新的大内存路径
2. 不破坏已有的分批/增量模式
3. 任意新增实现都必须回答：
   - 这一步是不是一次读太多
   - 这一步会不会让大对象占用太久
   - 这一步能不能改成 DuckDB 内聚合或分段处理

---

## 3. 任务

### 3.1 Task P2-A Industry Daily Enrichment

**代码落点**

1. `src/data/cleaner.py`

**测试落点**

1. `tests/unit/data/` 下行业聚合单测

**资源约束**

1. 新增字段与聚合逻辑优先在 DuckDB 完成，不先整段拉入 pandas
2. 长窗口 enrichment 禁止一次全量展开为大宽表常驻内存
3. 必要时按日期段或行业段增量写入 `l2_industry_daily`

### 3.2 Task P2-B Industry Structure Daily

**代码落点**

1. `src/data/cleaner.py`
2. 新增行业结构聚合脚本

**测试落点**

1. `tests/unit/data/` 下结构聚合单测

**资源约束**

1. 行业结构辅助表默认按日或按窗口分段构建
2. 禁止通过“先把全市场原始细表整体读入 pandas，再在 Python 侧多轮 groupby”实现
3. 临时工作副本与中间产物只能落 `G:\EmotionQuant-temp`

### 3.3 Task P2-C IRS Scorer Rewrite

**代码落点**

1. `src/selector/irs.py`
2. `src/strategy/ranker.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. `tests/unit/selector/` 下 IRS scorer 单测

**资源约束**

1. scorer 重写不得引入“整段全历史常驻内存”的默认路径
2. 多周期 / 轮动 / 扩散 / 牛股基因层必须优先考虑：
   - DuckDB 预聚合
   - 分日迭代
   - 小表 attach
3. 若某步必须使用 pandas，中间 DataFrame 生命周期要尽量短，不允许长时间保留大对象

### 3.4 Task P2-D IRS Evidence

**脚本落点**

1. `scripts/backtest/run_v001_plus_irs_ablation.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

**资源约束**

1. IRS ablation 默认使用工作副本库，路径位于 `G:\EmotionQuant-temp`
2. 证据脚本禁止默认触发不受控的全量重建
3. 长窗口实验必须提供可控的：
   - start/end
   - skip-rebuild
   - working-db-path 或等价参数

### 3.5 Task P2-Exit IRS Baseline Decision

**目标**

在 `Phase 2` 正式出场前，先把 `IRS baseline` 的口径定性清楚，避免“排序链已接通”和“绝对分值已完成标定”被混为一谈。

**当前约束**

1. `IRS_BASELINE` 当前仍是占位值，不等同于正式历史标定结果。
2. 本轮 `Phase 2` 已证明的是：
   - `RS / RV / RT / BD / GN` 已接入正式排序链
   - 排序结果会真实变化
   - 当前短窗口下未见明显执行回归
3. 本轮 `Phase 2` 尚未证明的是：
   - `IRS absolute score calibration completed`
   - `IRS_RSRVRTBDGN` 在更长窗口上稳定优于 `IRS_LITE`

**允许的收口方式**

1. 方案 A：补正式 `IRS baseline` 标定，并将标定口径回写到代码与记录
2. 方案 B：在 `Phase 2` 出场记录中明确声明：
   - 当前只证明“排序链接通与稳定性”
   - 不宣称绝对分值已完成正式标定

**执行顺序**

1. 先完成 `IRS baseline` 口径决策
2. 再跑更长窗口 `IRS evidence`
3. 最后才裁决 `Phase 2 Completed`

---

## 4. 出场条件

- [ ] 多周期强度已落地
- [ ] 相对量能已落地
- [ ] 轮动状态已落地
- [ ] 扩散度已落地
- [ ] 牛股基因轻量层已落地
- [ ] IRS 专项 evidence 已生成
- [ ] `IRS baseline` 已完成正式标定，或已在出场记录中明确声明“当前不宣称 absolute score calibration completed”
- [ ] 已补一轮更长窗口 `IRS evidence`（当前推荐窗口：`2025-09-01` 至 `2026-02-24`）
- [ ] `Phase 2` 新实现未违反 `27GB RAM ceiling / temp path discipline / incremental-first / DuckDB-first`

---

## 5. 完成后必须回答的问题

1. 排序变化主要来自哪一层
2. `50.0` 发生在行业层、因子层还是 signal attach 层
3. 哪些票因行业排名映射变化被推上去或压下去
4. 哪些步骤仍然是主要内存热点，当前防守是否足够
5. 是否存在“一次读取太多”或“大内存占用过久”的剩余风险
