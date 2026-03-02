# Broker 详细设计

**版本**: v1.0
**创建日期**: 2026-03-01
**对应模块**: `src/broker/`（risk.py, matcher.py）
**上游文档**: `architecture-master.md` §4.4

---

## 1. 设计目标

Broker 是系统中唯一有"钱"的模块：**接收信号 → 风控检查 → 下单 → 撮合成交**。回测和纸上交易共用此内核（铁律 #9）。

核心约束：
- **T+1 语义**：signal_date=T，execute_date=T+1，成交价=T+1 Open（铁律 #10）
- **有状态**：持有持仓、资金、信任分级，需要持久化
- **幂等**：同一信号不重复下单（signal_id 唯一约束）
- **v0.01 失效优先**：入场后首个可评估日不延续则退出（避免低频钝刀消耗）

---

## 2. 类结构

```python
class Broker:
    """
    交易执行引擎。回测和纸上交易共用同一实例。
    组合 RiskManager + Matcher。
    """
    def __init__(self, store: Store, config, initial_cash: float = 1_000_000):
        self.store = store
        self.config = config
        self.risk = RiskManager(store, config)
        self.matcher = Matcher(store, config)
        self.cash = initial_cash
        self.portfolio: dict[str, Position] = {}  # code → Position
        self.max_nav = initial_cash               # 净值峰值（回撤计算用）
        self.force_bearish_until: date | None = None  # 回撤熔断冷却截止日

    def process_signals(self, signals: list[Signal], trade_date: date) -> list[Order]:
        """
        主入口：接收信号列表，经过风控检查，生成订单。
        trade_date = signal_date 的下一交易日（execute_date）
        """

    def execute_orders(self, orders: list[Order], market_data: pd.DataFrame,
                       today: date) -> list[Trade]:
        """
        撮合订单。回测模式下由 engine 调用，纸上交易模式下由 main.py 调用。
        today: 当前交易日，传递给 matcher.execute(order, market_data, today)。
        """

    def update_daily(self, trade_date: date, market_data: pd.DataFrame) -> list[Order]:
        """
        每日收盘后更新：检查止损/止盈/信任降级，生成 SELL 订单。
        内部调用 self.risk.check_positions(..., broker_state=self)。
        """
```

### Position 数据结构

```python
@dataclass
class Position:
    code: str
    entry_date: date              # 买入成交日
    entry_price: float            # 买入成交价
    quantity: int                  # 持仓数量
    current_price: float          # 最新收盘价
    max_price: float              # 持仓期间最高价（移动止盈用）
    stop_loss: float              # 当前止损价
    pattern: str                   # 形态名（如 "bof"），来自 Trade.pattern
    signal_type: str              # reason_code（如 "PAS_BOF"）
    is_paper: bool = False        # 是否模拟持仓
```

---

## 3. risk.py — 风控管理

### 3.1 RiskManager 类

```python
class RiskManager:
    def __init__(self, store: Store, config):
        self.store = store
        self.config = config

    # ── 开仓前检查 ──
    def check_signal(self, signal: Signal, broker_state, today_date: date) -> Order | None:
        """
        对 BUY 信号执行全部风控检查，通过则生成 Order。
        today_date: 回测当前模拟日期（不可用 date.today()）。
        返回 None = 拒绝开仓。
        """

    # ── 持仓期检查（每日收盘后）──
    def check_positions(self, portfolio: dict, market_data: pd.DataFrame,
                        trade_date: date, broker_state) -> list[Order]:
        """
        检查所有持仓的止损/止盈/熔断条件。
        broker_state: Broker 实例（组合回撤检查需要 cash/max_nav/force_bearish_until）。
        返回需要执行的 SELL Order 列表。
        """

    # ── 信任分级 ──
    def get_trust_tier(self, code: str) -> str:
        """读取个股信任等级：ACTIVE / OBSERVE / BACKUP"""

    def update_trust(self, code: str, trade_result: Trade):
        """交易完成后更新信任状态。"""
```

### 3.2 开仓前检查流程

```python
def check_signal(self, signal, broker_state, today_date: date) -> Order | None:
    # 0. BACKUP 自动升级检查（冷藏 120 交易日到期 → OBSERVE）
    self._check_auto_promote(signal.code, today_date)

    # 1. 信任分级检查
    tier = self.get_trust_tier(signal.code)
    if tier == "BACKUP":
        logger.info(f"{signal.code} 信任=BACKUP，跳过")
        return None
    is_paper = (tier == "OBSERVE")

    # 2. 连续亏损熔断检查
    if self._is_loss_circuit_breaker_active(broker_state, today_date):
        logger.info("连续亏损熔断生效，暂停开仓")
        return None

    # 3. 组合回撤熔断检查
    if self._is_drawdown_circuit_breaker_active(broker_state, today_date):
        logger.info("组合回撤熔断生效，暂停开仓")
        return None

    # 4. 重复持仓检查（同一只股票不重复开仓）
    if signal.code in broker_state.portfolio:
        logger.info(f"{signal.code} 已有持仓，跳过重复开仓")
        return None

    # 5. 最大持仓数量检查
    active_positions = sum(1 for p in broker_state.portfolio.values() if not p.is_paper)
    if active_positions >= self.config.MAX_POSITIONS:
        logger.info(f"持仓已满 {active_positions}/{self.config.MAX_POSITIONS}")
        return None

    # 6. 计算仓位大小
    quantity = self._calculate_position_size(signal, broker_state)
    if quantity < 100:  # 不足 1 手
        return None

    # 7. 生成 Order（order_id = signal_id，确定性幂等键，重跑覆盖而非追加）
    execute_date = self._next_trade_date(signal.signal_date)
    return Order(
        order_id=signal.signal_id,        # 确定性：一个 signal 至多产一个 order
        signal_id=signal.signal_id,
        code=signal.code,
        action="BUY",
        pattern=signal.pattern,           # 冗余传递，归因链直连
        quantity=quantity,
        execute_date=execute_date,
        is_paper=is_paper,
        status="PENDING"
    )
```

### 3.3 仓位计算

```python
def _calculate_position_size(self, signal, broker_state) -> int:
    """
    v0.01 采用 R 风险仓位：单笔账户风险固定 0.8%，
    再叠加单只仓位上限（10%）做硬约束。
    向下取整到 100 股（1 手）。
    """
    nav = broker_state.cash + sum(
        p.current_price * p.quantity for p in broker_state.portfolio.values()
        if not p.is_paper
    )
    risk_budget = nav * self.config.RISK_PER_TRADE_PCT
    max_notional = nav * self.config.MAX_POSITION_PCT
    # 用信号日收盘价估算（实际成交价是 T+1 Open，有滑点）
    est_price = self.store.read_scalar(
        "SELECT adj_close FROM l2_stock_adj_daily WHERE code=? AND date=?",
        (signal.code, signal.signal_date)
    )
    if est_price is None or est_price <= 0:
        return 0
    est_stop_pct = max(self.config.STOP_LOSS_PCT, 0.01)  # 无 stop 信息时按配置止损估算
    qty_by_risk = risk_budget / (est_price * est_stop_pct)
    qty_by_cap = max_notional / est_price
    quantity = int(min(qty_by_risk, qty_by_cap) / 100) * 100
    return quantity
```

### 3.4 四级止损体系

每日收盘后 `check_positions()` 按优先级检查：

```text
优先级（高→低）：
  第零级：日内浮亏即走  > 第一级：个股止损 > 移动止盈 > 第二级：组合回撤 > 第三级：连亏熔断
  同一天触发多个规则时，按最高优先级执行。
```

#### 第零级：日内浮亏即走

```python
def _check_intraday_loss(self, position, trade_date: date, today_close) -> bool:
    """
    T+1 买入当天，收盘价 < 买入价 → T+2 开盘强制卖出。
    入场当天就水下 = 时机判断错误。
    trade_date: 当前交易日（回测模拟日期）。
    """
    # 持仓第二个交易日才能卖
    holding_days = self._trading_days_between(position.entry_date, trade_date)
    if holding_days == 1 and today_close < position.entry_price:
        return True  # 标记 T+2 开盘卖出
    return False
```

#### 第一级：个股止损

```python
def _check_stop_loss(self, position, today_close) -> bool:
    """持仓浮亏 ≥ STOP_LOSS_PCT → 强制卖出"""
    loss_pct = (today_close - position.entry_price) / position.entry_price
    return loss_pct <= -self.config.STOP_LOSS_PCT  # 默认 -5%
```

#### 移动止盈

```python
def _check_trailing_stop(self, position, today_close, today_high) -> bool:
    """
    追踪最高价，回落超过 TRAILING_STOP_PCT → 卖出。
    不设固定止盈线：涨多少跟多少，回头了才走。
    """
    # 更新最高价
    position.max_price = max(position.max_price, today_high)
    # 回落检查
    drawdown = (position.max_price - today_close) / position.max_price
    return drawdown >= self.config.TRAILING_STOP_PCT  # 默认 8%
```

#### 第二级：组合回撤止损

```python
def _check_portfolio_drawdown(self, broker_state, today_date) -> bool:
    """
    组合净值从峰值回撤 ≥ MAX_DRAWDOWN_PCT → 全部清仓。
    触发后强制 MSS=BEARISH，冷却 N 个交易日。
    """
    nav = broker_state.cash + sum(
        p.current_price * p.quantity for p in broker_state.portfolio.values()
        if not p.is_paper                    # 与仓位计算一致：只算真实持仓
    )
    broker_state.max_nav = max(broker_state.max_nav, nav)
    drawdown = (broker_state.max_nav - nav) / broker_state.max_nav

    if drawdown >= self.config.MAX_DRAWDOWN_PCT:  # 默认 15%
        broker_state.force_bearish_until = self._offset_trade_date(
            today_date, self.config.DRAWDOWN_COOLDOWN_DAYS  # 默认 5
        )
        return True
    return False
```

#### 第三级：连续亏损熔断

```python
def _is_loss_circuit_breaker_active(self, broker_state, today_date: date) -> bool:
    """
    连续 N 笔亏损 → 暂停开新仓 M 个交易日。
    注意：必须传入回测当前日期，禁止使用 date.today()（回测时为真实日期，会导致熔断永远不触发）。
    """
    recent_trades = self.store.read_df(
        "SELECT * FROM l4_trades WHERE is_paper = false AND action = 'SELL' "
        "ORDER BY execute_date DESC LIMIT ?",
        (self.config.CONSECUTIVE_LOSS_LIMIT,)  # 默认 5
    )
    if len(recent_trades) < self.config.CONSECUTIVE_LOSS_LIMIT:
        return False

    # 检查是否全部亏损
    all_loss = all(
        self._is_trade_loss(t) for _, t in recent_trades.iterrows()
    )
    if not all_loss:
        return False

    # 检查冷却期
    last_loss_date = recent_trades.iloc[0]["execute_date"]
    cooldown_end = self._offset_trade_date(
        last_loss_date, self.config.LOSS_COOLDOWN_DAYS  # 默认 3
    )
    return today_date <= cooldown_end
```

#### 回撤熔断冷却检查

```python
def _is_drawdown_circuit_breaker_active(self, broker_state, today_date: date) -> bool:
    """
    组合回撤熔断后冷却期内 → 暂停开新仓。
    由 _check_portfolio_drawdown 触发时设置 broker_state.force_bearish_until。
    注意：必须传入回测当前日期，禁止使用 date.today()。
    """
    if broker_state.force_bearish_until is None:
        return False
    return today_date <= broker_state.force_bearish_until
```

### 3.5 SELL 订单生成

```python
def check_positions(self, portfolio, market_data, trade_date, broker_state):
    sell_orders = []

    for code, position in portfolio.items():
        # paper 持仓也执行止损/止盈检查（生成 paper SELL 订单，
        # 经 matcher 执行后触发 update_trust → OBSERVE→ACTIVE 信任升级路径）

        today = market_data[market_data.code == code].iloc[0]

        # 按优先级检查
        should_sell = False
        reason = ""

        if self._check_intraday_loss(position, trade_date, today["adj_close"]):
            should_sell, reason = True, "INTRADAY_LOSS"
        elif self._check_stop_loss(position, today["adj_close"]):
            should_sell, reason = True, "STOP_LOSS"
        elif self._check_trailing_stop(position, today["adj_close"], today["adj_high"]):
            should_sell, reason = True, "TRAILING_STOP"

        if should_sell:
            sell_signal_id = f"RISK_{code}_{trade_date}"
            execute_date = self._next_trade_date(trade_date)
            sell_orders.append(Order(
                order_id=sell_signal_id,        # 确定性：signal_id 即 order_id
                signal_id=sell_signal_id,
                code=code,
                action="SELL",
                pattern=position.pattern,      # 沿用原始 BUY 形态
                quantity=position.quantity,
                execute_date=execute_date,
                is_paper=position.is_paper,    # 继承持仓的 paper 标记
                status="PENDING"
            ))
            logger.info(f"SELL {code}: {reason} (paper={position.is_paper})")

    # 组合回撤检查（全局，NAV 仅计真实持仓，但 paper 持仓也需清出 portfolio）
    if self._check_portfolio_drawdown(broker_state, trade_date):
        already_selling = {o.code for o in sell_orders}  # 个股止损已生成 SELL，避免同日重复卖出
        for code, position in portfolio.items():
            if code not in already_selling:
                dd_signal_id = f"DRAWDOWN_{code}_{trade_date}"
                sell_orders.append(Order(
                    order_id=dd_signal_id,     # 确定性：signal_id 即 order_id
                    signal_id=dd_signal_id,
                    code=code, action="SELL",
                    pattern=position.pattern,  # 沿用原始 BUY 形态
                    quantity=position.quantity,
                    execute_date=self._next_trade_date(trade_date),
                    is_paper=position.is_paper,  # 继承持仓的 paper 标记
                    status="PENDING"
                ))
        logger.warning("组合回撤超限，全部清仓（含 paper 持仓）")

    return sell_orders
```

---

## 4. 个股信任分级（Stock Trust Tier）

### 4.1 状态转换图

```text
            3连亏                真买又亏
  ACTIVE ────────→ OBSERVE ────────────→ BACKUP
    ↑                  ↑                     │
    │ 模拟盈利≥1次      │ 冷藏120个交易日       │
    └──────────────────┘←────────────────────┘
```

### 4.2 降级规则

```python
def update_trust(self, code, trade_result):
    trust = self._load_trust(code)

    is_loss = trade_result.price < self._get_entry_price(trade_result.order_id)

    if trust.tier == "ACTIVE":
        if trust.on_probation:
            # 升级试用期（OBSERVE→ACTIVE 后首笔真实交易）
            if is_loss:
                # 架构铁律：「升级后再亏 → 立即降回」，直接 BACKUP
                trust.tier = "BACKUP"
                trust.on_probation = False
                trust.consecutive_losses = 0
                trust.last_demote_date = trade_result.execute_date
                logger.warning(f"{code}: ACTIVE(试用) → BACKUP（升级后首笔即亏）")
            else:
                # 试用通过，转为正式 ACTIVE
                trust.on_probation = False
                trust.consecutive_losses = 0
        else:
            # 正常 ACTIVE：3 连亏才降级
            if is_loss:
                trust.consecutive_losses += 1
                if trust.consecutive_losses >= self.config.TRUST_DEMOTE_THRESHOLD:
                    trust.tier = "OBSERVE"
                    trust.consecutive_losses = 0
                    trust.last_demote_date = trade_result.execute_date
                    logger.warning(f"{code}: ACTIVE → OBSERVE（3连亏）")
            else:
                trust.consecutive_losses = 0  # 有一笔盈利就归零

    elif trust.tier == "OBSERVE":
        if not trade_result.is_paper and is_loss:
            # OBSERVE 期间真买又亏 → BACKUP
            trust.tier = "BACKUP"
            trust.last_demote_date = trade_result.execute_date
            logger.warning(f"{code}: OBSERVE → BACKUP（真买又亏）")
        elif trade_result.is_paper and not is_loss:
            # 模拟盈利 → 升回 ACTIVE（进入试用期）
            trust.tier = "ACTIVE"
            trust.on_probation = True          # 试用期标记
            trust.last_promote_date = trade_result.execute_date
            trust.consecutive_losses = 0

    self._save_trust(trust)
```

### 4.3 升级规则

```python
def _check_auto_promote(self, code, today_date):
    """BACKUP → OBSERVE：冷藏 N 个交易日自动升级（v0.01 默认 120）"""
    trust = self._load_trust(code)
    if trust.tier == "BACKUP" and trust.last_demote_date:
        days_since = self._trading_days_between(trust.last_demote_date, today_date)
        if days_since >= self.config.TRUST_BACKUP_COOLDOWN:
            trust.tier = "OBSERVE"
            trust.last_promote_date = today_date
            self._save_trust(trust)
```

### 4.4 信号处理

```text
信号到达 broker.process_signals() 时：
  ACTIVE  → 正常执行真单（is_paper=false）
  OBSERVE → 模拟执行（is_paper=true），记录但不用真钱
  BACKUP  → 跳过（不生成任何单）
```

---

## 5. matcher.py — 撮合引擎

### 5.1 Matcher 类

```python
class Matcher:
    def __init__(self, store: Store, config):
        self.store = store
        self.config = config

    def execute(self, order: Order, market_data: pd.DataFrame,
                today: date) -> Trade | None:
        """
        撮合单个订单。
        today: 当前交易日（回测模拟日期，用于断言 execute_date == today）。
        返回 Trade（成交）或 None（REJECTED）。
        """
```

### 5.2 撮合流程

```python
def execute(self, order, market_data, today: date) -> Trade | None:
    # ── 前置断言：只撮合当日到期的 PENDING 订单 ──
    assert order.status == "PENDING", f"非 PENDING 订单不可撮合: {order.order_id} status={order.status}"
    assert order.execute_date == today, f"execute_date 不匹配: {order.execute_date} != {today}"

    row = market_data[
        (market_data.code == order.code) &
        (market_data.date == order.execute_date)
    ]
    if row.empty:
        order.status = "REJECTED"
        order.reject_reason = "NO_DATA"
        return None

    bar = row.iloc[0]

    # 1. 停牌检查
    if bar.get("is_halt", False):
        order.status = "REJECTED"
        order.reject_reason = "HALTED"
        return None

    # 2. 涨跌停检查（口径一致：原始价 open vs up/down_limit）
    open_for_limit = bar.get("raw_open", bar.get("open", bar["adj_open"]))
    if order.action == "BUY" and open_for_limit >= bar.get("up_limit", float("inf")) * 0.998:
        order.status = "REJECTED"
        order.reject_reason = "LIMIT_UP"
        return None

    if order.action == "SELL" and open_for_limit <= bar.get("down_limit", 0) * 1.002:
        order.status = "REJECTED"
        order.reject_reason = "LIMIT_DOWN"
        return None

    # 3. 成交价 = T+1 Open + 滑点
    price = bar["adj_open"]
    if self.config.SLIPPAGE_BPS > 0:
        if order.action == "BUY":
            price *= (1 + self.config.SLIPPAGE_BPS / 10000)
        else:
            price *= (1 - self.config.SLIPPAGE_BPS / 10000)

    # 4. 计算手续费
    amount = price * order.quantity
    fee = self._calculate_fee(amount, order.action)

    # 5. 生成 Trade（trade_id = order_id + "_T"，确定性幂等键）
    order.status = "FILLED"
    return Trade(
        trade_id=f"{order.order_id}_T",  # 确定性：一个 order 至多产一笔 trade
        order_id=order.order_id,
        code=order.code,
        execute_date=order.execute_date,
        action=order.action,
        pattern=order.pattern,          # 冗余传递，报告阶段直接读取
        price=price,
        quantity=order.quantity,
        fee=fee,
        slippage_bps=self.config.SLIPPAGE_BPS,
        is_paper=order.is_paper if hasattr(order, "is_paper") else False,
    )
```

### 5.3 手续费计算

```python
def _calculate_fee(self, amount: float, action: str) -> float:
    """
    A股标准费率：
      佣金: max(amount × 0.0003, 5)    万三，最低 5 元
      印花税: amount × 0.001            千一，仅卖出
      过户费: amount × 0.00002          万 0.2，买卖双边
    """
    commission = max(amount * self.config.COMMISSION_RATE, self.config.MIN_COMMISSION)
    stamp_duty = amount * self.config.STAMP_DUTY_RATE if action == "SELL" else 0
    transfer_fee = amount * self.config.TRANSFER_FEE_RATE
    return commission + stamp_duty + transfer_fee
```

### 5.4 配置

```python
# config.py — Broker 配置

# 仓位管理
MAX_POSITIONS = 10                # 最大持仓数量
MAX_POSITION_PCT = 0.10           # 单只仓位上限（占总资产）
RISK_PER_TRADE_PCT = 0.008        # 单笔账户风险（v0.01 固定 0.8%）

# 止损体系
STOP_LOSS_PCT = 0.05              # 个股止损线（-5%）
TRAILING_STOP_PCT = 0.08          # 移动止盈回撤线（-8%）
MAX_DRAWDOWN_PCT = 0.15           # 组合最大回撤（-15%）
DRAWDOWN_COOLDOWN_DAYS = 5        # 回撤熔断冷却期（交易日）
CONSECUTIVE_LOSS_LIMIT = 5        # 连续亏损熔断笔数
LOSS_COOLDOWN_DAYS = 3            # 连亏熔断冷却期（交易日）

# 撮合参数
COMMISSION_RATE = 0.0003          # 佣金率（万三）
MIN_COMMISSION = 5.0              # 最低佣金（元）
STAMP_DUTY_RATE = 0.001           # 印花税率（千一，仅卖出）
TRANSFER_FEE_RATE = 0.00002       # 过户费率（万 0.2）
SLIPPAGE_BPS = 0                  # 滑点（基点），默认 0

# 信任分级
TRUST_DEMOTE_THRESHOLD = 3        # 连亏 N 次降级
TRUST_BACKUP_COOLDOWN = 120       # BACKUP 冷藏天数（交易日，v0.01）

# 初始资金
INITIAL_CASH = 1_000_000          # 初始资金（元）
```

---

## 6. Order / Trade 生命周期

### 6.1 完整流程

```text
Signal (T日收盘后)
    │
    ▼ risk.check_signal()
    │   ├─ 信任=BACKUP → 跳过
    │   ├─ 熔断生效 → 跳过
    │   ├─ 持仓已满 → 跳过
    │   └─ 通过 → 生成 Order (PENDING)
    │
Order (PENDING, execute_date=T+1)
    │
    ▼ matcher.execute()  [T+1 日]
    │   ├─ 停牌 → REJECTED (HALTED)
    │   ├─ 涨停 → REJECTED (LIMIT_UP)
    │   ├─ 跌停 → REJECTED (LIMIT_DOWN)
    │   └─ 成交 → FILLED
    │            → 生成 Trade
    │            → 更新 portfolio
    │            → 更新 cash
    │
Trade (写入 l4_trades)
    │
    ▼ risk.update_trust()
    │   更新 l4_stock_trust
    │
    ▼ 持仓期间每日 risk.check_positions()
    │   ├─ 第零级：日内浮亏 → SELL Order
    │   ├─ 第一级：止损 → SELL Order
    │   ├─ 移动止盈 → SELL Order
    │   ├─ 第二级：组合回撤 → 全部 SELL
    │   └─ 无触发 → 继续持有
    │
SELL Order → matcher.execute() → SELL Trade → 更新 portfolio/cash/trust
```

### 6.2 数据持久化

```text
Order → l4_orders（每次生成/更新状态时写入）
Trade → l4_trades（成交时写入，is_paper 标记模拟单）
Trust → l4_stock_trust（降级/升级时更新）
```

---

## 7. T+1 约束实现

### 7.1 约束清单

| 约束 | 实现位置 | 逻辑 |
|------|---------|------|
| 当日买入次日才能卖出 | risk.check_positions | 检查 holding_days ≥ 1 |
| 信号日=T，执行日=T+1 | risk.check_signal | execute_date = next_trade_date(signal_date) |
| 成交价=T+1 Open | matcher.execute | price = bar["adj_open"] |
| 禁止 T 日 Close 成交 | 架构保证 | signal 和 execute 分两天 |
| 停牌日不成交 | matcher.execute | is_halt 检查 |
| 一字板不成交 | matcher.execute | 原始价口径：raw_open/open 与 up_limit/down_limit 对比 |

### 7.2 交易日历依赖

```python
def _next_trade_date(self, current_date: date) -> date:
    """查 l1_trade_calendar 取下一交易日。"""
    result = self.store.read_df(
        "SELECT next_trade_day FROM l1_trade_calendar WHERE date = ?",
        (current_date,)
    )
    return result.iloc[0]["next_trade_day"]

def _trading_days_between(self, start: date, end: date) -> int:
    """计算两个日期之间的交易日数。"""
    result = self.store.read_df(
        "SELECT COUNT(*) as cnt FROM l1_trade_calendar "
        "WHERE date > ? AND date <= ? AND is_trade_day = true",
        (start, end)
    )
    return result.iloc[0]["cnt"]

def _offset_trade_date(self, base_date: date, n_days: int) -> date:
    """从 base_date 向后偏移 n_days 个交易日，返回目标交易日。"""
    result = self.store.read_df(
        "SELECT date FROM l1_trade_calendar "
        "WHERE date > ? AND is_trade_day = true "
        "ORDER BY date LIMIT 1 OFFSET ?",
        (base_date, n_days - 1)
    )
    return result.iloc[0]["date"]
```

---

## 8. 回测 vs 纸上交易 vs 实盘

```text
三种模式共用 Broker 内核，区别仅在数据来源和执行方式：

回测模式（backtest/engine.py 调用）：
  - market_data = L1/L2 历史数据
  - 全部在内存中模拟，一次跑完
  - 结果写入 l4_trades (is_paper=false)

纸上交易模式（main.py 每日调用）：
  - market_data = 当日真实数据
  - 不连接券商，全部为模拟成交（is_paper=true）
  - 信任分级仅影响是否允许生成模拟单（BACKUP 可直接跳过）

实盘模式（后续迭代）：
  - matcher 接入券商 API，真实下单
  - Broker 类不变，只替换 Matcher 实现
```

---

## 9. 单测要点

| 模块 | 测试方式 |
|------|---------|
| RiskManager.check_signal | mock 各种状态（满仓/熔断/信任降级），验证是否正确拒绝 |
| _check_stop_loss | 构造浮亏场景，验证止损触发 |
| _check_trailing_stop | 构造先涨后跌场景，验证移动止盈 |
| _check_portfolio_drawdown | 构造净值回撤，验证全部清仓 |
| Matcher.execute | 构造停牌/涨跌停/正常成交，验证 REJECTED/FILLED |
| _calculate_fee | 验证买入/卖出手续费计算正确性 |
| update_trust | 模拟 3 连亏 → OBSERVE，真买又亏 → BACKUP |

**关键边界用例**：
- 买入日即停牌 → REJECTED
- T+1 买入后当天无法卖出（即使浮亏 >5%）→ T+2 才能卖
- 一字涨停无法买入 → REJECTED (LIMIT_UP)
- 信任=OBSERVE 的真单盈利 → 升回 ACTIVE
- 组合回撤清仓 + 连亏熔断同时触发 → 优先组合回撤
- 手续费不足 5 元 → 按 5 元收取

