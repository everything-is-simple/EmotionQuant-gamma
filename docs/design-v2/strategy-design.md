# Strategy 详细设计

**版本**: v1.0
**创建日期**: 2026-03-01
**对应模块**: `src/strategy/`（pattern_base.py, pas_bpb.py, registry.py, strategy.py）
**上游文档**: `architecture-master.md` §4.3，`volman-ytc-mapping.md`

---

## 1. 设计目标

Strategy 回答一个问题：**候选池中的这只股票，今天该买吗？**

核心原则：
- **只看个股 OHLCV**：不把 MSS/IRS 分数当输入（铁律 #4）
- **形态检测器模式**：每个形态一个检测器，签名统一，可独立回测
- **可装配**：形态通过 registry 注册，config 控制启停，支持自由组合

---

## 2. PatternDetector 基类（pattern_base.py）

```python
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from datetime import date
from contracts import Signal

class PatternDetector(ABC):
    """
    PAS 形态检测器抽象基类。
    每个具体形态继承此类，实现 detect() 方法。
    """
    name: str                        # 形态唯一标识，如 "bpb"

    @abstractmethod
    def detect(self, df: pd.DataFrame, code: str,
               signal_date: date) -> Optional[Signal]:
        """
        检测指定股票在指定日期是否触发该形态。

        参数：
          df: 该股票的 l2_stock_adj_daily 历史数据（已按 date 升序排列）
              至少包含 signal_date 之前 60 个交易日 + signal_date 当天
          code: 股票代码（纯6位）
          signal_date: 信号日期（T 日）

        返回：
          触发 → Signal 对象
          未触发 → None

        约束：
          - 只读 df 中的 OHLCV + 均线 + 量比数据
          - 不访问 MSS/IRS/外部数据
          - signal.action 只产出 BUY（PAS 不产生 SELL，SELL 由 broker 止损触发）
        """
        ...
```

### 2.1 df 输入规范

strategy.py 在调用 detect() 前负责准备 df：

```text
df 列要求（全部来自 l2_stock_adj_daily）：
  code, date, adj_open, adj_high, adj_low, adj_close,
  volume, amount, pct_chg, ma5, ma10, ma20, ma60,
  volume_ma5, volume_ma20, volume_ratio

df 行要求：
  - 按 date 升序
  - 至少包含 signal_date 前 config.PAS_LOOKBACK_DAYS 个交易日（默认 60）
  - signal_date 当天的数据必须存在（T 日收盘后产生信号）
```

---

## 3. pas_bpb.py — BPB 突破回踩检测器（第1迭代）

### 3.1 类定义

```python
class BpbDetector(PatternDetector):
    name = "bpb"

    def __init__(self, config):
        self.lookback = config.PAS_BPB_LOOKBACK        # N 日区间（默认 20）
        self.price_pos_threshold = 0.8                  # 价格位置阈值
        self.volume_ratio_threshold = 1.5               # 放量确认阈值
        self.pullback_ideal_range = (0.4, 0.6)          # Volman 理想回调深度

    def detect(self, df, code, signal_date) -> Optional[Signal]:
        ...
```

### 3.2 检测算法详细步骤

```text
输入：df（单只股票历史日线），signal_date（T日）

Step 1 — 计算三个核心观测
  today = df[df.date == signal_date].iloc[0]
  lookback = df[df.date < signal_date].tail(self.lookback)
  high_Nd = lookback['adj_high'].max()
  low_Nd  = lookback['adj_low'].min()

  price_position     = (today.adj_close - low_Nd) / (high_Nd - low_Nd)
  volume_ratio       = today.volume / today.volume_ma20   # 直接用 L2 已有字段
  breakout_strength  = (today.adj_close - high_Nd) / high_Nd

Step 2 — 基础触发条件检查
  if price_position <= 0.8:     return None   # 未突破
  if volume_ratio <= 1.5:       return None   # 未放量
  if breakout_strength <= 0:    return None   # 突破无效

Step 3 — 回调深度检查
  pullback_depth = 1 - price_position   # 0 = 在最高点，1 = 在最低点
  # 注意：突破后回踩的深度，需要检查近 5 日是否有回调
  recent_5d = df[df.date <= signal_date].tail(5)
  had_pullback = any(recent_5d['adj_close'] < recent_5d['ma20'] * 1.03)
  near_ma20 = abs(today.adj_close - today.ma20) / today.adj_close < 0.03

Step 4 — Volman 增强检测
  is_first_pullback = _check_first_pullback(df, signal_date)
  has_cup_handle    = _detect_cup_handle(df, signal_date)

Step 5 — 不利条件评估
  market_score = _evaluate_market_conditions(df, signal_date)
  if market_score < -1:     return None   # 不利条件过多，放弃

Step 6 — 计算 signal_strength
  body_ratio = abs(today.adj_close - today.adj_open) / (today.adj_high - today.adj_low)
  base = 0.4 * normalize(breakout_strength, 0, 0.1)
       + 0.3 * normalize(volume_ratio, 1.0, 3.0)
       + 0.3 * body_ratio

  multiplier = 1.0
  if is_first_pullback:                    multiplier *= 1.2
  if has_cup_handle:                       multiplier *= 1.3
  if 0.4 <= pullback_depth <= 0.6:         multiplier *= 1.1
  if market_score > 1:                     multiplier *= 1.1

  final_strength = min(base * multiplier, 1.0)

Step 7 — 构造 Signal
  return Signal(
      code=code,
      signal_date=signal_date,
      action="BUY",
      strength=final_strength,
      pattern="bpb",
      reason_code="PAS_BPB"
  )
```

### 3.3 辅助函数

#### _check_first_pullback — FB首次回撤检测（Volman）

```python
def _check_first_pullback(self, df, signal_date) -> bool:
    """
    检测是否为趋势启动后的首次回踩。
    Volman FB 结构核心：首次回撤成功率更高。

    判断逻辑：前 20 日内，adj_close 穿越 ma20 的次数 ≤ 1。
    穿越次数多 = 反复缠绕 = 非首次回撤。
    """
    recent = df[df.date <= signal_date].tail(20)
    above_ma20 = recent['adj_close'] > recent['ma20']
    crossovers = above_ma20.diff().abs().sum()  # 每次穿越 diff=1
    return crossovers <= 2  # ≤1次穿越（diff产生2个1）
```

#### _detect_cup_handle — IRB杯柄形态检测（Volman）

```python
def _detect_cup_handle(self, df, signal_date, lookback=20) -> bool:
    """
    检测杯柄形态（Volman IRB 结构）。
    茶杯 = 大 U 形回调，手柄 = 小幅盘整，突破手柄时入场。

    返回 True 时 signal_strength × 1.3。
    """
    recent = df[df.date <= signal_date].tail(lookback)
    if len(recent) < lookback:
        return False

    # 1. 茶杯：左高 → 低谷 → 右高
    cup_low = recent['adj_low'].min()
    cup_left = recent.iloc[:lookback//2]['adj_close'].mean()
    cup_right = recent.iloc[-5:]['adj_close'].mean()
    is_cup = (cup_right > cup_low * 1.02) and (cup_left > cup_low * 1.02)

    # 2. 手柄：最后 5 根 K 线窄幅震荡
    handle = recent.tail(5)
    handle_width = (handle['adj_high'].max() - handle['adj_low'].min()) / handle['adj_low'].min()
    is_handle = handle_width < 0.03  # 宽度 < 3%

    # 3. 手柄在 ma20 附近
    last_ma20 = handle['ma20'].iloc[-1]
    near_ma20 = abs(handle['adj_low'].min() - last_ma20) / last_ma20 < 0.02

    return is_cup and is_handle and near_ma20
```

#### _evaluate_market_conditions — 不利条件评估（Volman 第15章）

```python
def _evaluate_market_conditions(self, df, signal_date) -> int:
    """
    评估个股微观市场条件。返回 -3 到 +3 的评分。
    score < -1 → 放弃交易。

    四类不利条件：
    1. 前方阻力位 (-1 to -3)
    2. 冲击效应 (-2)：连续大阳线后立即回撤
    3. 真空效应 (-1)：未测试整数价位
    4. 不利结构位置 (-1 to -2)
    """
    score = 0
    today = df[df.date <= signal_date].iloc[-1]
    recent = df[df.date <= signal_date].tail(10)

    # 1. 底部抬高 (+2)
    lows = recent['adj_low'].values
    if len(lows) >= 3 and all(lows[i] >= lows[i-1] * 0.99 for i in range(1, len(lows))):
        score += 2

    # 2. 前方阻力 (-1 to -3)
    lookback_20 = df[df.date < signal_date].tail(20)
    prev_high = lookback_20['adj_high'].max()
    if today['adj_close'] > prev_high * 0.97:  # 距前高 < 3%
        score -= 2

    # 3. 冲击效应 (-2)：最近 3 天均涨幅 > 5%
    if recent.tail(3)['pct_chg'].mean() > 0.05:
        score -= 2

    # 4. 整数价位支撑 (+1)
    price = today['adj_close']
    if price % 10 < 0.5 or price % 10 > 9.5:
        score += 1

    return score
```

#### normalize — 线性归一化（strength 计算用）

```python
def _normalize(self, value: float, low: float, high: float) -> float:
    """将 value 从 [low, high] 线性映射到 [0, 1]，clip 两端。"""
    if high == low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))
```

---

## 4. registry.py — 形态注册表

### 4.1 设计

```python
from strategy.pattern_base import PatternDetector
from strategy.pas_bpb import BpbDetector
# 第2迭代
# from strategy.pas_pb import PbDetector
# 第3迭代
# from strategy.pas_tst import TstDetector
# from strategy.pas_bof import BofDetector
# from strategy.pas_cpb import CpbDetector

# 所有已实现的检测器（全量注册表）
ALL_DETECTORS: dict[str, type[PatternDetector]] = {
    "bpb": BpbDetector,
    # "pb":  PbDetector,      # 第2迭代取消注释
    # "tst": TstDetector,     # 第3迭代
    # "bof": BofDetector,     # 第3迭代
    # "cpb": CpbDetector,     # 第3迭代
}

def get_active_detectors(config) -> list[PatternDetector]:
    """
    根据 config.PAS_PATTERNS 返回当前活跃的检测器实例列表。
    """
    detectors = []
    for name in config.PAS_PATTERNS:
        if name not in ALL_DETECTORS:
            raise ValueError(f"未知形态: {name}，可用: {list(ALL_DETECTORS.keys())}")
        detectors.append(ALL_DETECTORS[name](config))
    return detectors
```

### 4.2 新增形态的完整流程

```text
1. 写 pas_xxx.py，继承 PatternDetector，实现 detect()
2. 在 PAS 观测归属表登记观测，确认不与已有观测重复计分
3. 在 registry.py ALL_DETECTORS 中注册
4. 在 config.py PAS_PATTERNS 中加入 "xxx"
5. 跑 python main.py backtest --patterns=xxx 验证独立表现
6. 确认正期望后加入组合
```

---

## 5. strategy.py — 信号汇总

### 5.1 函数签名

```python
def generate_signals(store: Store, candidates: list[StockCandidate],
                     signal_date: date, config) -> list[Signal]:
    """
    主入口：对候选池中每只股票运行所有活跃形态检测器。
    返回触发的 Signal 列表。
    """
```

### 5.2 执行流程

```python
def generate_signals(store, candidates, signal_date, config):
    detectors = get_active_detectors(config)
    signals = []

    for candidate in candidates:
        # 准备该股票的历史数据
        lookback_start = get_trade_date_offset(signal_date, -config.PAS_LOOKBACK_DAYS)
        df = store.read_df(
            "SELECT * FROM l2_stock_adj_daily "
            "WHERE code = ? AND date BETWEEN ? AND ? ORDER BY date",
            (candidate.code, lookback_start, signal_date)
        )

        if len(df) < config.PAS_MIN_HISTORY_DAYS:
            continue  # 历史数据不足，跳过

        # 对每个活跃检测器运行
        stock_signals = []
        for detector in detectors:
            signal = detector.detect(df, candidate.code, signal_date)
            if signal is not None:
                stock_signals.append(signal)

        # 组合模式处理
        combined = _combine_signals(stock_signals, config)
        if combined:
            signals.extend(combined)

    # 写 l3_signals
    if signals:
        signals_df = pd.DataFrame([s.model_dump() for s in signals])
        store.bulk_insert("l3_signals", signals_df)

    logger.info(f"{signal_date}: {len(candidates)} 候选 → {len(signals)} 信号")
    return signals
```

### 5.3 组合模式

```python
def _combine_signals(stock_signals: list[Signal], config) -> list[Signal]:
    """
    根据 PAS_COMBINATION 配置合并同一只股票的多形态信号。
    """
    if not stock_signals:
        return []

    mode = config.PAS_COMBINATION

    if mode == "ANY":
        # 任一形态触发 → 出信号（取 strength 最高的）
        return [max(stock_signals, key=lambda s: s.strength)]

    elif mode == "ALL":
        # 全部活跃形态都触发才出信号
        active_count = len(config.PAS_PATTERNS)
        if len(stock_signals) == active_count:
            # 取平均 strength
            avg_strength = sum(s.strength for s in stock_signals) / len(stock_signals)
            best = max(stock_signals, key=lambda s: s.strength)
            best.strength = avg_strength
            return [best]
        return []

    elif mode == "VOTE":
        # 加权投票：每个形态的 strength 作为票数
        total_strength = sum(s.strength for s in stock_signals)
        if total_strength > config.PAS_VOTE_THRESHOLD:
            best = max(stock_signals, key=lambda s: s.strength)
            best.strength = min(total_strength, 1.0)
            return [best]
        return []

    return stock_signals
```

### 5.4 配置

```python
# config.py — Strategy 配置

# PAS 形态
PAS_PATTERNS = ["bpb"]            # 当前活跃形态列表
PAS_COMBINATION = "ANY"           # 组合模式：ANY / ALL / VOTE
PAS_VOTE_THRESHOLD = 0.6          # VOTE 模式阈值
PAS_LOOKBACK_DAYS = 60            # 检测器输入的历史窗口
PAS_MIN_HISTORY_DAYS = 30         # 最少历史数据天数
PAS_BPB_LOOKBACK = 20             # BPB N日区间

# 单形态独立回测
# python main.py backtest --patterns=bpb --start=2023-01-01
# python main.py backtest --patterns=bpb,pb --combination=ANY
```

---

## 6. Signal 生命周期

```text
T 日 15:00 收盘
    │
    ▼ builder 更新 L2（当日数据写入）
    │
    ▼ builder 更新 L3（MSS/IRS 评分）
    │
    ▼ selector.select_candidates(T) → 候选池
    │
    ▼ strategy.generate_signals(候选池, T) → Signal 列表
    │                                        写入 l3_signals
    │
    ▼ broker.process_signals(signals) → Order 列表
    │                                   execute_date = T+1
    │                                   写入 l4_orders (PENDING)
    │
T+1 日 09:30 开盘
    │
    ▼ matcher.execute_orders() → Trade 列表
    │                            price = T+1 Open
    │                            写入 l4_trades
    │                            更新 l4_orders (FILLED / REJECTED)
```

---

## 7. 第2/3迭代形态接口预览

### 7.1 pas_pb.py（第2迭代）

```python
class PbDetector(PatternDetector):
    name = "pb"

    def detect(self, df, code, signal_date) -> Optional[Signal]:
        """
        PB = 趋势中简单回调。
        触发条件：
          trend_alignment > 0.05     # ma5 > ma20 > ma60
          pullback_depth in [0.3, 0.5]
          pullback_exhaustion > 0.5
          close > ma20
        """
        ...
```

### 7.2 pas_tst.py（第3迭代）

```python
class TstDetector(PatternDetector):
    name = "tst"

    def detect(self, df, code, signal_date) -> Optional[Signal]:
        """
        TST = 支撑位测试。
        触发条件：
          support_distance < 0.02
          decline_exhaustion > 0.8
          hold_candle < 0.3          # 小实体K线
          close > support_level
        """
        ...
```

### 7.3 pas_bof.py / pas_cpb.py（第3迭代）

签名相同，具体检测逻辑见 `architecture-master.md` §4.3.4 和 §4.3.5。

---

## 8. 观测唯一性约束

15 个观测分属 5 个检测器，语义不重复：

| 检测器 | 观测 | 底层字段 |
|--------|------|---------|
| BPB | price_position, volume_ratio, breakout_strength | adj_close, adj_high, adj_low, volume |
| PB | trend_alignment, pullback_depth, pullback_exhaustion | ma5, ma20, adj_close |
| TST | support_distance, decline_exhaustion, hold_candle | adj_close, adj_low, adj_open |
| BOF | false_break, reversal_quality, volume_surge | adj_high, adj_close, adj_open, volume |
| CPB | trend_context, consolidation_pattern, trap_breakout | ma10, ma60, adj_close, adj_high, adj_low |

**计算复用 vs 观测独立**：tst/bof 共用 support_level 计算，pb/cpb 共享趋势方向判断，但各自观测语义不同，不构成重复计分。

---

## 9. 单测要点

| 模块 | 测试方式 |
|------|---------|
| BpbDetector | 构造突破后回踩的 mock K线数据，验证信号触发和 strength 值 |
| _check_first_pullback | 构造首次/非首次穿越 ma20 的数据，验证返回值 |
| _detect_cup_handle | 构造 U 形+小箱体的数据，验证检测结果 |
| _evaluate_market_conditions | 构造各种不利/有利条件，验证评分 |
| _combine_signals | 多信号输入，验证 ANY/ALL/VOTE 三种模式的合并结果 |

**关键边界用例**：
- lookback 数据不足 20 天 → 跳过，返回 None
- high_Nd == low_Nd → price_position 分母为零，返回 None
- volume_ma20 = 0 → volume_ratio 无穷大，跳过
- 所有条件满足但 market_score < -1 → 放弃交易
- 候选池为空 → 直接返回空 Signal 列表
