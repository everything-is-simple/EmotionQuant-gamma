# Selector 详细设计

**版本**: `v0.01 正式版`  
**状态**: `Frozen`（与 `system-baseline.md` 对齐）  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误与说明性修订；执行语义变更需进入独立实验包或后续正式版本。`  
**上游文档**: `docs/design-v2/01-system/architecture-master.md` §4.2  
**创建日期**: `2026-03-01`  
**对应模块**: `src/selector/`（mss.py, irs.py, gene.py, selector.py）  
**算法细案入口**: `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`, `docs/design-v2/03-algorithms/core-algorithms/irs-algorithm.md`

> 自 `2026-03-06` 起，本文件负责 Selector 的系统边界与漏斗职责；MSS / IRS 的算法细案、baseline 口径与数据分类口径以对应 `*-algorithm.md` 为准。

## 当前主开发线映射（非本文件执行口径）

当前主开发线中的 `Selector` 不再消费 `MSS gate` 或 `IRS filter`，而是收口为：

1. 基础过滤
2. `preselect_score`
3. `candidate_top_n`

当前主开发线入口见：

- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
- `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`

本文件正文继续保留 `v0.01 Frozen` 的历史漏斗口径，用于对照与回退理解。

## 冻结区与冲突处理

1. 本文档属于冻结区；默认只允许勘误、链接修复与说明性澄清。若涉及执行语义、模块边界或口径调整，必须进入后续版本处理。
2. 若本文档与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准，并应同步回写本文档。
3. 当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本证据、回归结果与阶段记录，统一归档到 `docs/spec/<version>/`。
---

## 历史正文说明

除前文“当前主开发线映射”外，下文各节默认描述的是 `v0.01 Frozen` 历史漏斗口径：

- 粗筛
- `MSS gate`
- `IRS filter`
- 候选池输出

当前主开发线不再直接采用这套正文语义；若与当前实现冲突，以：

- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`
- `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`

为准。

## 1. 设计目标

Selector 回答一个问题：**从全市场 ~5000 只股票中，今天应该关注哪 200 只候选池？**

**v0.01 执行口径**：
1. **基础过滤**：流动性/ST/停牌/市值 → 粗筛输出约 200 只候选。
2. **MSS/IRS 漏斗**：在粗筛池内执行 MSS gate + IRS filter，输出 50-100 只候选池给 Strategy。

> 说明：
> - `Frozen` 设计文档只记录 v0.01 正式执行口径。
> - `down-to-top` 后置评分主线替代方案已单独迁移到 `docs/spec/v0.01-plus/` 与 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`。
> - `gene` 在 v0.01 不进入实时漏斗，仅保留接口用于事后分析

### 1.2 v0.01 强制验证顺序（防假设漂移）

MSS/IRS 在 v0.01 视为待验证假设，不得直接视为“默认有效”。回测/评审必须按以下顺序输出同口径结果：

1. `BOF baseline`：`ENABLE_MSS_GATE=False` 且 `ENABLE_IRS_FILTER=False`
2. `BOF + MSS`：`ENABLE_MSS_GATE=True` 且 `ENABLE_IRS_FILTER=False`
3. `BOF + MSS + IRS`：`ENABLE_MSS_GATE=True` 且 `ENABLE_IRS_FILTER=True`

比较指标必须一致：胜率、盈亏比、期望值、最大回撤、分环境中位数路径。

### 1.1 v0.01 扫描策略（两阶段）

为控制全市场扫描成本并避免 API 压力，Selector 固定采用两阶段：

1. 粗筛阶段：全市场约5000只 -> 约200只（流动性/上市天数/停牌/基础波动过滤）。
2. 精筛阶段：在约200只内执行 MSS/IRS 漏斗并输出 50-100 候选池给 Strategy。

说明：
- 粗筛目标是降低计算规模，不改变因子边界。
- 形态触发器扫描不在全市场做，只对候选池做。

---

## 2. 共用工具：zscore_normalize

MSS / IRS / gene 三套因子共用同一个归一化函数，定义在 `selector/` 包级别：

```python
# selector/__init__.py 或 selector/normalize.py

def zscore_normalize(value: float, mean: float, std: float) -> float:
    """
    Z-Score 归一化，映射到 0-100。
    [-3σ, +3σ] → [0, 100]，超出范围 clip。
    """
    if std == 0:
        return 50.0                          # 零波动 → 中性分
    z = (value - mean) / std
    return max(0.0, min(100.0, (z + 3) / 6 * 100))
```

**mean / std 来源**：
- **第1迭代**：硬编码离线 baseline（2015-2025 历史样本统计）
- **后续迭代**：每日收盘后按滚动窗口（默认 120 交易日）增量更新
- **缺失兜底**：某因子缺 mean/std → 返回 50（中性分）

### baseline 数据结构

```python
# selector/baseline.py

# 第1迭代硬编码，后续改为从数据库读取滚动统计
MSS_BASELINE = {
    "market_coefficient_raw": {"mean": 0.48, "std": 0.08},
    "profit_effect_raw":      {"mean": 0.015, "std": 0.008},
    "loss_effect_raw":        {"mean": 0.012, "std": 0.006},
    "continuity_raw":         {"mean": 0.10, "std": 0.05},
    "extreme_raw":            {"mean": 0.06, "std": 0.03},
    "volatility_raw":         {"mean": 0.35, "std": 0.12},
}

IRS_BASELINE = {
    "relative_strength":  {"mean": 0.0, "std": 0.015},
    "net_inflow_10d":     {"mean": 0.0, "std": 5e8},
    "flow_share":         {"mean": 1/31, "std": 0.01},
}
```

> baseline 值需要在第1周拉完 3 年历史数据后，跑一次统计脚本生成。上面是占位示例。

---

## 3. mss.py — 市场情绪评分

### 3.1 函数签名

```python
def compute_mss(store: Store, start: date, end: date) -> None:
    """
    读 l2_market_snapshot，计算 MSS 六因子评分，写 l3_mss_daily。
    向量化处理整段日期范围。
    """

def compute_mss_single(row: dict, baseline: dict) -> MarketScore:
    """
    单日评分（纯函数，便于单测）。
    输入：l2_market_snapshot 的一行（dict）。
    输出：MarketScore 契约对象。
    """
```

### 3.2 六因子计算管线

```text
l2_market_snapshot 一行 →

  ┌─ 基础三因子（总权重 85%）─────────────────────────┐
  │                                                    │
  │  大盘系数（17%）                                    │
  │    raw = rise_count / total_stocks                 │
  │    market_coefficient = zscore(raw)                 │
  │                                                    │
  │  赚钱效应（34%）                                    │
  │    limit_up_ratio  = limit_up_count / total_stocks │
  │    new_high_ratio  = new_100d_high_count / total   │
  │    strong_up_ratio = strong_up_count / total       │
  │    raw = 0.4×limit_up_ratio + 0.3×new_high_ratio  │
  │        + 0.3×strong_up_ratio                       │
  │    profit_effect = zscore(raw)                      │
  │                                                    │
  │  亏钱效应（34%，方向翻转）                           │
  │    broken_rate    = touched_limit_up / limit_up     │
  │    limit_down_r   = limit_down_count / total       │
  │    strong_down_r  = strong_down_count / total      │
  │    new_low_ratio  = new_100d_low_count / total     │
  │    raw = 0.3×broken_rate + 0.2×limit_down_r       │
  │        + 0.3×strong_down_r + 0.2×new_low_ratio    │
  │    loss_effect = zscore(raw)                        │
  └────────────────────────────────────────────────────┘

  ┌─ 增强三因子（总权重 15%）─────────────────────────┐
  │                                                    │
  │  连续性（5%）                                       │
  │    cont_limit_up_r = continuous_limit_up_2d        │
  │                    / limit_up_count                │
  │    cont_new_high_r = continuous_new_high_2d_plus   │
  │                    / new_100d_high_count           │
  │    raw = 0.5×cont_limit_up_r + 0.5×cont_new_high_r│
  │    continuity = zscore(raw)                         │
  │                                                    │
  │  极端因子（5%）                                     │
  │    panic_tail_r   = high_open_low_close / total    │
  │    squeeze_tail_r = low_open_high_close / total    │
  │    raw = panic_tail_r + squeeze_tail_r             │
  │    extreme = zscore(raw)                            │
  │                                                    │
  │  波动因子（5%，方向翻转）                            │
  │    amount_vol_ratio = amount_volatility             │
  │                     / (amount_volatility + 1e6)    │
  │    raw = 0.5×pct_chg_std + 0.5×amount_vol_ratio   │
  │    volatility = zscore(raw)                         │
  └────────────────────────────────────────────────────┘

  温度合成：
    temperature = 0.17 × market_coefficient
               + 0.34 × profit_effect
               + 0.34 × (100 - loss_effect)
               + 0.05 × continuity
               + 0.05 × extreme
               + 0.05 × (100 - volatility)

  信号判定：
    temperature >= 65 → BULLISH
    temperature <= 35 → BEARISH
    else              → NEUTRAL
```

### 3.3 分母为零保护

```python
def safe_ratio(numerator, denominator, default=0.0):
    """分母为零时返回 default。向量化版本用 np.where。"""
    if denominator == 0:
        return default
    return numerator / denominator
```

所有 ratio 计算必须经过此函数。场景：
- `limit_up_count = 0` → `broken_rate = 0`（没有涨停就没有炸板）
- `total_stocks = 0` → 当天无交易数据，整行跳过
- `new_100d_high_count = 0` → `continuous_new_high_ratio = 0`

### 3.4 向量化实现要点

```python
def compute_mss(store, start, end):
    # 一次读整段日期的 market_snapshot
    df = store.read_table("l2_market_snapshot", date_range=(start, end))

    # 向量化计算所有 ratio（pandas 列运算）
    df["limit_up_ratio"] = df["limit_up_count"] / df["total_stocks"].replace(0, np.nan)
    # ... 其余 ratio 同理

    # 向量化 zscore
    df["market_coefficient"] = df["market_coefficient_raw"].apply(
        lambda x: zscore_normalize(x, baseline["mean"], baseline["std"])
    )
    # 或用 np.clip((z + 3) / 6 * 100, 0, 100) 全列一次性算

    # 合成温度
    df["score"] = (0.17 * df["market_coefficient"]
                 + 0.34 * df["profit_effect"]
                 + 0.34 * (100 - df["loss_effect"])
                 + 0.05 * df["continuity"]
                 + 0.05 * df["extreme"]
                 + 0.05 * (100 - df["volatility"]))

    df["signal"] = np.where(df["score"] >= 65, "BULLISH",
                   np.where(df["score"] <= 35, "BEARISH", "NEUTRAL"))

    # 批量写入
    store.bulk_upsert("l3_mss_daily", df[MSS_COLUMNS])
```

### 3.5 输出契约

```python
class MarketScore(BaseModel):    # contracts.py
    date: date
    score: float                 # 0-100
    signal: str                  # BULLISH / NEUTRAL / BEARISH
```

### 3.6 信号阈值配置

```python
# config.py
MSS_BULLISH_THRESHOLD = 65       # ≥ 此值 → BULLISH
MSS_BEARISH_THRESHOLD = 35       # ≤ 此值 → BEARISH
MSS_NORMALIZE_WINDOW = 120       # 滚动归一化窗口（交易日）
```

---

## 4. irs.py — 行业轮动评分

### 4.1 函数签名

```python
def compute_irs(store: Store, start: date, end: date) -> None:
    """
    读 l2_industry_daily + l1_index_daily，计算 IRS 评分，写 l3_irs_daily。
    """

def compute_irs_single(industry_df: pd.DataFrame,
                       benchmark_df: pd.DataFrame,
                       calc_date: date,
                       baseline: dict) -> IndustryScore:
    """
    单行业单日评分（纯函数，便于单测）。
    """
```

### 4.2 二因子计算管线

```text
l2_industry_daily + l1_index_daily(000001.SH) →

  相对强度（权重 55%）：
    relative_strength = industry_pct_chg - benchmark_pct_chg
    rs_score = zscore(relative_strength)

  资金流向（权重 45%）：
    industry_amount_delta = amount - lag(amount, 1)
    net_inflow_10d = SUM(industry_amount_delta, window=10)
    market_amount_total = SUM(ALL industries amount on date)
    flow_share = industry_amount / market_amount_total
    cf_score = 0.6 × zscore(net_inflow_10d) + 0.4 × zscore(flow_share)

  综合评分：
    industry_score = 0.55 × rs_score + 0.45 × cf_score

  排名：
    rank = 按 industry_score 降序排名（1 = 最强）
```

### 4.3 向量化实现要点

```python
def compute_irs(store, start, end):
    # 读行业日线（需要 start-10 天的数据算 10 日滚动）
    lookback_start = get_trade_date_offset(start, -15)
    ind_df = store.read_table("l2_industry_daily", date_range=(lookback_start, end))

    # 读基准指数（上证综指）
    bench_df = store.read_df(
        "SELECT date, pct_chg FROM l1_index_daily WHERE ts_code = '000001.SH'"
        " AND date BETWEEN ? AND ?", (lookback_start, end)
    )

    # 合并
    df = ind_df.merge(bench_df, on="date", suffixes=("", "_bench"))

    # 相对强度
    df["relative_strength"] = df["pct_chg"] - df["pct_chg_bench"]
    df["rs_score"] = vectorized_zscore(df["relative_strength"], baseline)

    # 资金流向：10 日滚动
    df["amount_delta"] = df.groupby("industry")["amount"].diff(1)
    df["net_inflow_10d"] = df.groupby("industry")["amount_delta"].rolling(10).sum().reset_index(0, drop=True)

    # 每日全市场成交额
    daily_total = df.groupby("date")["amount"].sum().rename("market_total")
    df = df.merge(daily_total, on="date")
    df["flow_share"] = df["amount"] / df["market_total"]

    df["cf_score"] = (0.6 * vectorized_zscore(df["net_inflow_10d"], baseline_nf)
                    + 0.4 * vectorized_zscore(df["flow_share"], baseline_fs))

    # 综合评分
    df["score"] = 0.55 * df["rs_score"] + 0.45 * df["cf_score"]

    # 排名（按日分组）
    df["rank"] = df.groupby("date")["score"].rank(ascending=False, method="min").astype(int)

    # 只写 [start, end] 范围
    result = df[df["date"].between(start, end)]
    store.bulk_upsert("l3_irs_daily", result[IRS_COLUMNS])
```

### 4.4 输出契约

```python
class IndustryScore(BaseModel):  # contracts.py
    date: date
    industry: str
    score: float
    rank: int
```

### 4.5 IRS 配置

```python
# config.py
IRS_TOP_N = 5                    # 取 Top-N 行业放行
IRS_RS_WEIGHT = 0.55
IRS_CF_WEIGHT = 0.45
IRS_INFLOW_WINDOW = 10           # 资金流向滚动窗口（交易日）
IRS_BENCHMARK = "000001.SH"      # 基准指数
```

### 4.6 后续迭代预留

第1迭代只用 2 因子。后续 4 因子的接口预留：

```python
# irs.py 中预留函数签名，第1迭代返回 0
def _compute_continuity_score(df) -> pd.Series:
    """连续性因子（第2迭代）"""
    return pd.Series(0, index=df.index)

def _compute_valuation_score(df) -> pd.Series:
    """估值因子（第2迭代）"""
    return pd.Series(0, index=df.index)

def _compute_leader_score(df) -> pd.Series:
    """龙头因子（第3迭代）"""
    return pd.Series(0, index=df.index)

def _compute_gene_score(df) -> pd.Series:
    """基因库因子（第3迭代）"""
    return pd.Series(0, index=df.index)
```

---

## 5. gene.py — 牛股基因/衰股基因画像（第2迭代）

### 5.1 函数签名

```python
def compute_gene(store: Store, start: date, end: date) -> None:
    """
    读 l2_stock_adj_daily（250 日窗口），计算基因画像，写 l3_stock_gene。
    第2迭代实现，第1迭代只建表不算。
    """
```

### 5.2 五牛五衰基因计算

```text
输入：单只股票 250 个交易日的 l2_stock_adj_daily

牛股基因（越高 = 历史行为越强势）：
  limit_up_freq   = 涨停次数 / 250
  streak_up_avg   = 所有连涨段平均长度（连涨段 = 连续 pct_chg > 0 的天数）
  new_high_freq   = 创 60 日新高的交易日数 / 250
  strength_ratio  = 收盘 > ma20 的交易日比例
  resilience      = 1 / avg(回调>5%后恢复前高的天数)，无回调 → 1.0

衰股基因（对称镜像）：
  limit_down_freq = 跌停次数 / 250
  streak_down_avg = 所有连跌段平均长度
  new_low_freq    = 创 60 日新低的频率
  weakness_ratio  = 收盘 < ma20 的比例
  fragility       = 反弹后再次跌破前低的频率

综合评分：
  bull_score = 等权平均(5 个牛股基因各自 zscore) → 0-100
  bear_score = 等权平均(5 个衰股基因各自 zscore) → 0-100
  gene_score = bull_score - bear_score             → -100 ~ +100
```

### 5.3 selector 中的使用方式

```python
# selector.py 中的基因过滤（v0.02+ 且验证通过后开启）
if config.ENABLE_GENE_FILTER:
    gene_df = store.read_table("l3_stock_gene", date_range=(calc_date, calc_date))
    candidates = candidates.merge(gene_df[["code", "gene_score"]], on="code")
    candidates = candidates[candidates["gene_score"] > config.GENE_SCORE_THRESHOLD]
```

### 5.4 配置

```python
# config.py
ENABLE_GENE_FILTER = False        # v0.01-v0.02 默认关闭（未验证前不启用）
GENE_SCORE_THRESHOLD = -30        # 宽松阈值，只排除最差的
GENE_LOOKBACK_DAYS = 250          # 基因计算窗口
```

---

## 6. selector.py — 候选池生成（v0.01 正式口径）

### 6.1 函数签名

```python
def select_candidates(store: Store, calc_date: date) -> list[StockCandidate]:
    """
    主入口：基础过滤 + MSS/IRS 漏斗，返回候选池。
    候选池为内存对象，不落库。
    """
```

### 6.2 标准流程（v0.01）

```python
def select_candidates(store, calc_date):
    # ── Step 1: 全市场股票池 ──
    all_stocks = store.read_df(
        "SELECT DISTINCT code FROM l2_stock_adj_daily WHERE date = ?",
        (calc_date,),
    )
    logger.info(f"全市场 {len(all_stocks)} 只")

    # ── Step 2: 基础过滤（流动性/ST/停牌/市值）──
    candidates = _apply_basic_filters(store, all_stocks["code"].tolist(), calc_date)
    logger.info(f"基础过滤后 {len(candidates)} 只")

    # ── Step 3: MSS gate（市场级硬门控，可配置关闭）──
    if config.ENABLE_MSS_GATE:
        market_score = store.read_df(
            "SELECT score, signal FROM l3_mss_daily WHERE date = ?",
            (calc_date,),
        )
        if market_score.empty or market_score.iloc[0]["signal"] == "BEARISH":
            logger.info("MSS gate 拒绝当日交易")
            return []

    # ── Step 4: IRS filter（行业 Top-N）──
    if config.ENABLE_IRS_FILTER:
        top_industries = _get_top_irs_industries(store, calc_date, config.IRS_TOP_N)
        candidates = [
            code for code in candidates
            if _get_industry(store, code, calc_date) in top_industries
        ]
        logger.info(f"IRS 过滤后 {len(candidates)} 只")

    # ── Step 5: 基因库过滤（第2迭代，v0.01 禁用）──
    if config.ENABLE_GENE_FILTER:
        gene = store.read_df(
            "SELECT code, gene_score FROM l3_stock_gene WHERE calc_date = ?",
            (calc_date,),
        )
        gene_pass = set(gene[gene["gene_score"] > config.GENE_SCORE_THRESHOLD]["code"])
        candidates = [c for c in candidates if c in gene_pass]
        logger.info(f"基因过滤后 {len(candidates)} 只")

    # ── Step 6: 候选池评分 + 截断 ──
    ranked = _rank_candidates(store, candidates, calc_date)

    # ── 构造输出 ──
    result = []
    for code, score in ranked[:config.SELECTOR_TOP_N]:
        result.append(StockCandidate(
            code=code,
            industry=_get_industry(store, code, calc_date),
            score=score,
        ))

    return result
```

**当前冻结口径**：
- MSS 仅作为市场级硬门控，不参与个股打分。
- IRS 仅作为行业级过滤，不跨层承担 PAS 触发职责。
- `score` 只用于 Selector 候选池排序，不改变 Strategy 的 BOF 触发条件。
- `down-to-top` 后置评分主线替代方案已迁出冻结区，详见 `docs/spec/v0.01-plus/` 与 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`。

### 6.3 基础条件过滤

```python
def _apply_basic_filters(store, candidates, calc_date) -> list[str]:
    """
    过滤掉不满足基本交易条件的股票。
    """
    # 读取当日数据
    df = store.read_df(
        "SELECT code, volume, amount FROM l2_stock_adj_daily WHERE date = ? AND code IN (?)",
        (calc_date, candidates)
    )
    info = store.read_df(
        "SELECT ts_code, is_st, list_date, total_mv, circ_mv FROM l1_stock_daily "
        "NATURAL JOIN l1_stock_info WHERE date = ?"
        , (calc_date,)
    )

    passed = []
    for code in candidates:
        # 排除 ST
        if _is_st(info, code):
            continue
        # 排除次新股（上市不足 60 交易日）
        if _is_new_stock(info, code, calc_date, min_days=60):
            continue
        # 流动性过滤：日均成交额 > 阈值
        if _daily_amount(df, code) < config.MIN_DAILY_AMOUNT:
            continue
        # 市值过滤（可选）
        if config.MIN_MARKET_CAP and _market_cap(info, code) < config.MIN_MARKET_CAP:
            continue
        passed.append(code)

    return passed
```

### 6.4 基础过滤配置

```python
# config.py
MIN_DAILY_AMOUNT = 5_000          # 最低日成交额（千元），过滤僵尸股
MIN_MARKET_CAP = None             # 最低总市值（万元），None=不过滤
NEW_STOCK_MIN_DAYS = 60           # 次新股排除：上市不足 N 交易日
EXCLUDE_ST = True                 # 排除 ST/*ST
```

### 6.4.1 候选池排序（v0.01）

Selector 对通过过滤的标的计算 `score` 并排序，默认 Top-N 输出：

1. 流动性分（40%）：20日平均成交额分位值。
2. 结构稳定分（30%）：近20日波动与停牌情况。
3. 行业优先分（30%）：IRS 行业排名映射分。

该分数只用于候选池排序，不参与 PAS 形态触发判定。

### 6.5 输出契约

```python
class StockCandidate(BaseModel):  # contracts.py
    code: str
    industry: str
    score: float                  # selector 阶段评分
```

`liquidity_tier` / `attention_tier` 仅作为 selector 内部调度元数据，不进入跨模块契约。
候选池为内存 `list[StockCandidate]`，**不落库**。selector 每日运行时生成，传给 strategy 消费。若需复盘，从 L3 表重放 selector 逻辑还原。

---

## 7. config 开关矩阵

```python
# config.py — Selector 漏斗开关

ENABLE_MSS_GATE    = True    # 关闭 → 不管大盘情绪，全天候交易
ENABLE_IRS_FILTER  = True    # 关闭 → 不限行业，全市场选股
ENABLE_GENE_FILTER = False   # v0.01-v0.02 禁止在实时漏斗启用（仅事后分析）
```

**对照实验组合**：

| MSS | IRS | Gene | 效果 |
|-----|-----|------|------|
| ✓ | ✓ | ✓ | v0.02+ 可选（需先完成反推验证） |
| ✗ | ✗ | ✗ | 纯 PAS 形态交易 |
| ✓ | ✗ | ✗ | 管大盘时机，不限行业 |
| ✗ | ✓ | ✗ | 管行业轮动，不管大盘 |
| ✓ | ✓ | ✗ | 第1迭代默认配置 |

### 7.1 消融回退门（强制）

按 `system-baseline.md` 统一口径执行：

1. 只允许按 `BOF baseline -> BOF+MSS -> BOF+MSS+IRS` 顺序加漏斗。
2. 新配置相对前一配置若出现以下任一情况，必须回退：
   1. `expected_value` 下降超过 10%
   2. `max_drawdown` 恶化超过 20%
   3. 任一市场环境中位数路径由正转负且连续两个评估窗未恢复

---

## 8. 单测要点

每个模块可独立单测，不依赖其他模块：

| 模块 | 测试方式 |
|------|---------|
| mss.py | 构造 l2_market_snapshot 的 mock 行，验证 `compute_mss_single()` 输出分数和信号 |
| irs.py | 构造 l2_industry_daily + benchmark mock，验证排名正确性 |
| gene.py | 构造 250 日 mock 数据，验证各基因计算公式 |
| selector.py | mock Store 返回预设 MSS/IRS/基因数据，验证漏斗每级过滤数量 |

**关键边界用例**：
- MSS 全部因子为零 → 温度应该在 50 附近
- IRS 只有 1 个行业有数据 → rank=1，无异常
- 全市场无股票交易（节假日后第一天）→ 返回空候选池
- limit_up_count=0 → broken_rate=0（不是 NaN）
- **分板块阈值强制用例**：创业板股票涨 8% → 不应被计入 strong_up_count（创业板阈值=10%）；北交所股票涨 12% → 不应被计入 strong_up_count（北交所阈值=15%）；ST 股票涨 2% → 不应被计入（ST 阈值=2.5%）。实现时必须有此单测用例而非仅靠 code review。



