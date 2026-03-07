# 编码规范

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与说明性澄清；若治理口径调整，必须先修订上游 baseline。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 冻结区与冲突处理

1. 本文档属于冻结区；默认只允许勘误、链接修复与说明性澄清。若涉及执行语义、模块边界或口径调整，必须进入后续版本处理。
2. 若本文档与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准，并应同步回写本文档。
3. 当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本证据、回归结果与阶段记录，统一归档到 `docs/spec/<version>/`。

## Python 版本
≥ 3.10（使用 `X | Y` 联合类型语法）

## OOP vs 纯函数的分工

**用 OOP（有多态 / 有状态）**：

| 类 | 原因 |
|----|------|
| `DataFetcher`(ABC) → `TuShareFetcher` / `AKShareFetcher` | 多态：主备切换 |
| `Store` | 有状态：持有 DuckDB 连接 |
| `PatternDetector`(ABC) → `BofDetector` / `BpbDetector` / ... | 多态：形态可装配 |
| `Broker`（组合 `RiskManager` + `Matcher`） | 有状态：持仓/资金 |

**用纯函数（无状态、无多态）**：

| 模块 | 原因 |
|------|------|
| mss.py（`compute_mss`/`compute_mss_single`） | 输入 DataFrame → 输出 MarketScore |
| irs.py（`compute_irs`/`compute_irs_single`） | 同上 |
| gene.py（`compute_gene`） | 输入 250日 DataFrame → 输出基因评分 |
| selector.py（`select_candidates`） | 读 L3 + 过滤，纯编排 |
| reporter.py | 数据聚合输出 |

原则：有多态或有状态的用 OOP，纯计算的用函数。不强制全 OOP，也不强制全函数式。

## 计算规范

### 禁止逐行循环
```python
# ❌ 禁止
for row in df.iterrows():
    ...

# ✅ 用 pandas 向量化 或 DuckDB SQL
df["ma5"] = df.groupby("code")["adj_close"].rolling(5).mean()
```

### 大块处理
- 一次读一段日期的全市场数据，向量化算完，批量写入
- 不是一天一天、一只一只处理

### 优先级
- 聚合类计算（l2_market_snapshot、l2_industry_daily）→ DuckDB SQL
- 滚动窗口（均线、量比）→ pandas `df.rolling().mean()`
- 写入 → `store.bulk_upsert(table, df)`，不边算边写

### 分母为零保护
所有 ratio 计算必须处理分母为零：
```python
def safe_ratio(numerator, denominator, default=0.0):
    if denominator == 0:
        return default
    return numerator / denominator
```

## pydantic 用法

- **只校验模块边界对象**（contracts.py 中的 6 个契约类）
- **不逐行校验 DataFrame**
- 关键 id 字段采用确定性规则（重跑覆盖而非追加）：
  - `signal_id = f"{code}_{signal_date}_{pattern}"`
  - `order_id = signal_id`（BUY），`order_id = f"RISK_{code}_{date}"`（止损/止盈SELL），`order_id = f"DRAWDOWN_{code}_{date}"`（组合回撤清仓SELL）
  - `trade_id = f"{order_id}_T"`
  - 强平：`trade_id = f"FC_{code}_{date}_T"`
- 时间戳用 `Field(default_factory=lambda: datetime.now(timezone.utc))`（禁用已弃用的 `datetime.utcnow()`）

## 配置管理

- 全局配置统一在 `config.py`
- 漏斗开关：`ENABLE_MSS_GATE`, `ENABLE_IRS_FILTER`, `ENABLE_GENE_FILTER`
- PAS 形态：`PAS_PATTERNS = ["bof"]`（v0.01 默认）
- 数据根目录：`DATA_PATH` 环境变量注入，config.py 读取

## 测试策略

- 每个模块可独立单测，不依赖其他模块启动
- 纯函数（如 `compute_mss_single`）→ 构造 mock dict/DataFrame，验证输出
- OOP（如 `BofDetector.detect`）→ 构造 mock K线数据
- Store → 测试时注入 `:memory:` DuckDB
- 关键边界用例必须覆盖：分母为零、数据不足、全部盈利/全部亏损

## 日志

- 使用 loguru，不用标准库 logging
- 每次运行生成 run_id：`{trade_date}_{uuid[:8]}`
- 模块抛异常时写 `logs/{run_id}.log`，包含 traceback + 输入参数
- 预警用 `logger.warning`，不搞监控平台

## 命名约定

| 场景 | 约定 | 示例 |
|------|------|------|
| DuckDB 表名 | `l{层}_{实体}_{粒度}` | `l2_stock_adj_daily` |
| 因子原始值 | `{名称}_raw` | `profit_effect_raw` |
| 因子归一化值 | 无后缀 | `profit_effect` |
| 比率 | `{名称}_ratio` | `volume_ratio` |
| 计数 | `{名称}_count` | `limit_up_count` |
| 配置开关 | `ENABLE_{功能}` | `ENABLE_MSS_GATE` |
| 形态检测器 | `pas_{形态缩写}.py` | `pas_bof.py`（v0.01） |
| 信号原因码 | `PAS_{形态}` | `PAS_BOF` |
| 触发器标识 | `pattern_id` | `bof_spring_v1` |
| 触发记录标识 | `trigger_id` | `bof_000001_20260302` |
| 形态大类 | `setup_type` | `range_bof` |
| 环境标签 | `env_regime` | `bull / sideways / bear` |





