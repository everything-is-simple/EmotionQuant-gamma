from __future__ import annotations

# ---------------------------------------------------------------------------
# matcher.py — T+1 开盘撮合器
# ---------------------------------------------------------------------------
# 职责：按 T+1 开盘价（含滑点）撮合订单，产出 Trade 对象。
# 约束（Frozen）：
#   - 成交价 = 复权开盘价 × (1 ± slippage_bps/10000)
#   - 涨跌停判断用原始价（raw_open），不用复权价，避免除权日误判
#   - 手续费口径与 RiskManager._estimate_fee 保持一致（两处必须同步修改）
#   - slippage_bps 默认 0.0，生产环境建议设为 2-5 bps
# ---------------------------------------------------------------------------

from datetime import date

from src.config import Settings
from src.contracts import Order, Trade, build_trade_id


class Matcher:
    def __init__(self, config: Settings):
        self.config = config

    def _calculate_fee(self, amount: float, action: str) -> float:
        # 费用口径必须与 RiskManager._estimate_fee 保持完全一致。
        # 如果修改这里，必须同步修改 risk.py 
        commission = max(amount * self.config.commission_rate, self.config.min_commission)
        transfer_fee = amount * self.config.transfer_fee_rate
        stamp_duty = amount * self.config.stamp_duty_rate if action.upper() == "SELL" else 0.0
        return commission + transfer_fee + stamp_duty

    def execute(self, order: Order, bar: dict, today: date) -> tuple[Trade | None, str | None]:
        """
        T+1 开盘撮合核心。

        返回 (Trade, None) 表示成交；返回 (None, reason) 表示拒绝。

        拒绝原因枚举：
        - INVALID_ORDER_STATE : 订单状态不是 PENDING 或 execute_date 不是今日
        - NO_MARKET_DATA      : bar 为空（当日无行情）
        - HALTED              : 停牌
        - LIMIT_UP            : 买入时开盘已封涨停（无法买入）
        - LIMIT_DOWN          : 卖出时开盘已封跌停（无法卖出）
        - INVALID_PRICE       : 复权开盘价 <= 0
        """
        # 状态机守卫：只处理当日待执行 PENDING 订单，防止跨日订单误撮合。
        if order.status != "PENDING" or order.execute_date != today:
            return None, "INVALID_ORDER_STATE"

        if not bar:
            return None, "NO_MARKET_DATA"

        if bool(bar.get("is_halt", False)):
            return None, "HALTED"

        # 涨跌停判断必须用原始价（raw_open），不能用复权价。
        # 原因：up_limit / down_limit 字段来自 L1，是未复权价格，用复权价比较会在除权日产生误判。
        open_for_limit = float(bar.get("raw_open", bar.get("open", bar.get("adj_open", 0.0))) or 0.0)
        up_limit = bar.get("up_limit")
        down_limit = bar.get("down_limit")

        if order.action == "BUY" and up_limit is not None and open_for_limit >= float(up_limit) * 0.998:
            return None, "LIMIT_UP"
        if order.action == "SELL" and down_limit is not None and open_for_limit <= float(down_limit) * 1.002:
            return None, "LIMIT_DOWN"

        # 成交价用复权开盘价（adj_open）：保证 PnL 计算口径统一。
        adj_open = float(bar.get("adj_open", 0.0) or 0.0)
        if adj_open <= 0:
            return None, "INVALID_PRICE"

        # 滑点：BUY 向上偏，SELL 向下偏，模拟市价单冲击成本。
        # slippage_bps=0 时退化为纯开盘价成交（回测基准口径）。
        slip = self.config.slippage_bps / 10000.0
        price = adj_open * (1 + slip) if order.action == "BUY" else adj_open * (1 - slip)
        amount = price * order.quantity
        fee = self._calculate_fee(amount, order.action)

        trade = Trade(
            trade_id=build_trade_id(order.order_id),
            order_id=order.order_id,
            code=order.code,
            execute_date=today,
            action=order.action,
            price=price,
            quantity=order.quantity,
            fee=fee,
            pattern=order.pattern,
            is_paper=order.is_paper,
            position_id=order.position_id,
            exit_plan_id=order.exit_plan_id,
            exit_leg_id=order.exit_leg_id,
            exit_leg_seq=order.exit_leg_seq,
            exit_reason_code=order.exit_reason_code,
            is_partial_exit=order.is_partial_exit,
        )
        return trade, None
