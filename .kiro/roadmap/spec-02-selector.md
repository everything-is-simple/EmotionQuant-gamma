# Spec 02: Selector

> **版本**: v0.01 | **状态**: Draft | **基线**: `docs/design-v2/rebuild-v0.01.md` | **评审标准**: `docs/design-v2/sandbox-review-standard.md`

## 需求摘要
从全市场 ~5000 股中筛选 50-100 只候选股。

v0.01 固定采用两阶段扫描（SoT：`docs/design-v2/selector-design.md`）：
- **Stage 1 粗筛**（~5000 → ~200）：停牌/上市天数/流动性/基础波动 等基础过滤（目标是降低计算规模与 API 压力）
- **Stage 2 精筛**（~200 → 50-100）：在粗筛池内执行 MSS 门控 + IRS 行业过滤（v0.01 的 `gene` 仅保留接口，不进实时漏斗）→ 输出候选池给 Strategy

说明：PAS 形态触发器扫描由 `strategy.py` 在候选池上执行，不在全市场扫描，也不在 selector 内实现。

**设计文档**: `docs/design-v2/selector-design.md`, `docs/design-v2/architecture-master.md` §4.2

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/selector/__init__.py` | 包初始化 |
| `src/selector/normalize.py` | zscore_normalize 共用归一化函数 |
| `src/selector/baseline.py` | MSS/IRS baseline 硬编码（第1迭代） |
| `src/selector/mss.py` | MSS 六因子市场温度评分 |
| `src/selector/irs.py` | IRS 二因子行业轮动评分 |
| `src/selector/gene.py` | 牛股基因画像（第2迭代，先建骨架） |
| `src/selector/selector.py` | 漏斗编排 → 输出候选池 |

## 设计要点

### zscore_normalize（三系统共用）
```
zscore_normalize(value, mean, std) → 0-100
  std == 0 → 50（中性分）
  z = (value - mean) / std
  return clip((z + 3) / 6 × 100, 0, 100)
```
第1迭代 mean/std 硬编码在 baseline.py，后续改为 120 日滚动窗口。

### MSS 六因子
- 基础三因子（85%）：大盘系数(17%) + 赚钱效应(34%) + 亏钱效应(34%)
- 增强三因子（15%）：连续性(5%) + 极端因子(5%) + 波动因子(5%)
- 亏钱效应和波动因子是负面指标，温度公式中取 `100 - x` 翻转
- 输出：score(0-100), signal(≥65 BULLISH / ≤35 BEARISH / else NEUTRAL)
- 所有 ratio 必须用 safe_ratio（分母为零保护）

### IRS 二因子
- 相对强度(55%)：industry_pct_chg - benchmark_pct_chg(000001.SH)
- 资金流向(45%)：10日滚动净流入 + 资金占比
- 输出：每日 31 个行业评分 + 排名
- 后续迭代预留 4 个函数签名（返回 0）

### selector.py 漏斗
1. Stage 1：粗筛（_apply_basic_filters）→ 停牌/次新/流动性/基础波动 等过滤，约 5000→200
2. Stage 2：MSS 开关（ENABLE_MSS_GATE）→ BEARISH 当日不出手（可在实现中前置以便早退，但口径归入 Stage 2）
3. Stage 2：IRS 过滤（ENABLE_IRS_FILTER）→ 在粗筛池内仅保留 Top-N 强势行业
4. 基因过滤（ENABLE_GENE_FILTER=False）→ 第2迭代（v0.01 默认禁用）
5. 候选排序与截断：构造 `list[StockCandidate]`，按 score 排序，取 Top-N 输出给 Strategy
- 候选池为内存 `list[StockCandidate]`，不落库

## 实现任务

### 共用工具
- [ ] 实现 `normalize.py`（zscore_normalize，向量化版本 + 单值版本）
- [ ] 实现 `baseline.py`（MSS_BASELINE、IRS_BASELINE 硬编码占位值）
- [ ] 实现 safe_ratio（单值 + 向量化 np.where 版本）

### mss.py
- [ ] 实现 `compute_mss(store, start, end)`（批量读 l2_market_snapshot，向量化计算）
- [ ] 实现 `compute_mss_single(row, baseline)` → MarketScore（纯函数，便于单测）
- [ ] 六因子管线：各 ratio 计算 → zscore → 温度合成 → 信号判定
- [ ] 批量写入 l3_mss_daily
- [ ] 单测：构造 mock l2_market_snapshot 行，验证分数和信号

### irs.py
- [ ] 实现 `compute_irs(store, start, end)`（读 l2_industry_daily + l1_index_daily）
- [ ] 实现 `compute_irs_single(industry_df, benchmark_df, date, baseline)` → IndustryScore
- [ ] 相对强度：industry_pct_chg - benchmark_pct_chg → zscore
- [ ] 资金流向：amount_delta 10日滚动 + flow_share → 加权
- [ ] 行业排名：groupby(date).rank(ascending=False)
- [ ] 批量写入 l3_irs_daily
- [ ] 预留 4 个扩展因子函数签名（返回 0）
- [ ] 单测：构造 mock 行业数据+基准，验证排名正确性

### gene.py（骨架）
- [ ] 实现 `compute_gene(store, start, end)` 函数签名（内部 pass，第2迭代填充）
- [ ] 在 config.py 中设置 `ENABLE_GENE_FILTER = False`

### selector.py（两阶段扫描：粗筛 5000→~200 + 精筛 MSS/IRS（~200→50-100））
- [ ] 实现 `select_candidates(store, calc_date)` → list[StockCandidate]
- [ ] Stage 1: 粗筛（_apply_basic_filters：停牌/上市天数/ST/次新/流动性/基础波动/市值）得到 ~200
- [ ] Stage 2: MSS 开关检查（读 l3_mss_daily，BEARISH 当日不出手）
- [ ] Stage 2: IRS 过滤（读 l3_irs_daily，取 Top-N 行业，并与粗筛池取交集）
- [ ] 基因过滤（预留，ENABLE_GENE_FILTER=False 时跳过）
- [ ] 构造候选 `score`（流动性40%+结构稳定30%+行业优先30%，仅用于候选排序，不参与PAS触发）
- [ ] 按 score 降序排序，取 Top-N（50-100）输出给 Strategy
- [ ] 各步日志输出过滤数量
- [ ] 单测：mock Store 返回预设数据，验证每级过滤

### 集成验证
- [ ] 用真实 L2 数据运行 compute_mss + compute_irs，验证分数分布合理
- [ ] 运行 select_candidates，验证候选池 50-100 只
- [ ] 消融对照A：关闭 MSS/IRS，仅 BOF baseline（输出指标）
- [ ] 消融对照B：开启 MSS，关闭 IRS（输出指标）
- [ ] 消融对照C：开启 MSS+IRS（输出指标）
- [ ] 三组结果按同口径对比（胜率/盈亏比/期望值/最大回撤/分环境中位数）

## 验收标准
1. `compute_mss_single` 输入全零 → score ≈ 50（中性）
2. `compute_irs` 输出 31 个行业排名无重复
3. MSS=BEARISH 时 selector 返回空列表
4. limit_up_count=0 时 broken_rate=0（不是 NaN）
5. 全市场无交易数据时返回空候选池，不报错
6. 漏斗消融实验三组结果可复现且可比较

## 已知风险与偏差

| 级别 | 问题 | Owner | 截止日期 | 状态 |
|------|------|-------|----------|------|
| — | 当前无已知 S2+ 偏差 | — | — | — |
