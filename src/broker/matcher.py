from __future__ import annotations

from datetime import date

from src.config import Settings
from src.contracts import Order, Trade, build_trade_id


class Matcher:
    def __init__(self, config: Settings):
        self.config = config

    def _calculate_fee(self, amount: float, action: str) -> float:
        commission = max(amount * self.config.commission_rate, self.config.min_commission)
        transfer_fee = amount * self.config.transfer_fee_rate
        stamp_duty = amount * self.config.stamp_duty_rate if action.upper() == "SELL" else 0.0
        return commission + transfer_fee + stamp_duty

    def execute(self, order: Order, bar: dict, today: date) -> tuple[Trade | None, str | None]:
        """
        订单撮合：
        - 返回 (trade, reject_reason)
        - 若 reject，则 trade=None 且 reject_reason 非空
        """
        # 状态机守卫：只处理当日待执行订单，防止跨日误撮合。
        if order.status != "PENDING" or order.execute_date != today:
            return None, "INVALID_ORDER_STATE"

        if not bar:
            return None, "NO_MARKET_DATA"

        if bool(bar.get("is_halt", False)):
            return None, "HALTED"

        open_for_limit = float(bar.get("raw_open", bar.get("open", bar.get("adj_open", 0.0))) or 0.0)
        up_limit = bar.get("up_limit")
        down_limit = bar.get("down_limit")

        # 涨跌停口径按原始价，不与复权价混比。
        if order.action == "BUY" and up_limit is not None and open_for_limit >= float(up_limit) * 0.998:
            return None, "LIMIT_UP"
        if order.action == "SELL" and down_limit is not None and open_for_limit <= float(down_limit) * 1.002:
            return None, "LIMIT_DOWN"

        adj_open = float(bar.get("adj_open", 0.0) or 0.0)
        if adj_open <= 0:
            return None, "INVALID_PRICE"

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
        )
        return trade, None

