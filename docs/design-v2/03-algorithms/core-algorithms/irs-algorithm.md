# IRS-lite 当前主线设计

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变当前 DTT 主线边界的前提下，对 IRS-lite 的角色、排序算法与验证证据做受控修订。`  
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`  
**对应模块**: `src/selector/irs.py`, `src/strategy/ranker.py`, `src/data/cleaner.py`  
**理论来源**: `docs/Strategy/IRS/`

---

## 1. 职责

当前主线中的 `IRS-lite` 只负责：

`给 BOF 触发后的正式信号提供行业横截面增强。`

它回答的问题是：

`同一天已经触发 BOF 的信号里，哪些行业背景更强。`

当前主线消费者固定为：

`Strategy / Ranker`

---

## 2. 输入

`IRS-lite` 当前读取：

1. `l2_industry_daily`
2. `l1_index_daily`
3. `l1_sw_industry_member`
4. 配置项
   - `IRS_MIN_INDUSTRIES_PER_DAY`
   - 缺失 fallback 规则

正式行业口径固定为：

`SW2021 一级 31 行业`

无匹配行业时：

1. 行业标记为 `未知`
2. 主线消费按 `IRS=50` 中性处理

---

## 3. 输出契约

`IRS-lite` 在行业层输出：

1. `industry_code`
2. `trade_date`
3. `irs_score`
4. `industry_rank`
5. `quality_flag`

当前主线在个股层消费为：

1. `signal_id`
2. `irs_score`
3. `final_score`
4. `final_rank`

当前排序真相源通过 sidecar 保存，不要求立即改写正式 `Signal` schema。

---

## 4. 不负责什么

当前主线中，`IRS-lite` 不负责：

1. Selector 前置硬过滤
2. 候选池行业拦截
3. 市场级停手判断
4. 个股形态检测
5. 市场级仓位控制

当前未恢复的能力也不视为主线职责：

1. 完整行业轮动状态机
2. 龙头密度与基因层
3. 配置建议与配置模式

---

## 5. 决策规则 / 算法

当前执行版保留两因子框架：

1. `RS`，权重 `55%`
   - `industry_pct_chg - benchmark_pct_chg`
2. `CF`，权重 `45%`
   - `flow_share + amount_delta_10d`

综合得分：

```text
irs_score = 0.55 * rs_score + 0.45 * cf_score
```

主线消费规则：

1. `IRS` 先在行业层产出 `score / rank`
2. `Strategy / Ranker` 在 `BOF` 触发后附加 `irs_score`
3. `bof_strength + irs_score` 形成当前排序依据
4. 若当日 `IRS` 无效，则按 `50` 中性分 fallback，并保留追溯标记

---

## 6. 失败模式与验证证据

主要失败模式：

1. `IRS` 被重新拉回前置过滤，误杀 `BOF` 样本。
2. 行业映射口径漂移，导致行业分不可比。
3. `IRS` 缺失被静默跳过，而不是显式 `50` fallback。
4. 无法区分收益变化来自行业增强还是来自执行约束。

当前验证证据：

1. `docs/spec/v0.01-plus/evidence/coverage_audit_dtt_v0_01_dtt_bof_plus_irs_score_w20260210_20260213_t163939__coverage_audit.json`
2. `docs/spec/v0.01-plus/evidence/rank_decomposition_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t154940__rank_decomposition.json`
3. `docs/spec/v0.01-plus/evidence/trade_attribution_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t165536__trade_attribution.json`
4. `docs/spec/v0.01-plus/records/v0.01-plus-coverage-and-rank-audit-20260307.md`
5. `docs/spec/v0.01-plus/records/v0.01-plus-trade-attribution-and-windowed-sensitivity-20260308.md`

当前证据只说明：

1. `IRS` 已经进入排序层
2. `IRS` 已经能改变 `Top-N / max_positions / BUY` 结果

是否满足默认主线切换，仍以 `development-status.md` 的阶段结论为准。
