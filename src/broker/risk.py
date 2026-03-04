from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.config import Settings
from src.contracts import Order, Signal, build_order_id
from src.data.store import Store


@dataclass
class BrokerRiskState:
    cash: float
    portfolio_market_value: float
    holdings: set[str]


class RiskManager:
    def __init__(self, store: Store, config: Settings):
        self.store = store
        self.config = config

    def _next_trade_date(self, d: date) -> date | None:
        return self.store.next_trade_date(d)

    def _estimate_price(self, code: str, signal_date: date) -> float | None:
        return self.store.read_scalar(
            "SELECT adj_close FROM l2_stock_adj_daily WHERE code=? AND date=?",
            (code, signal_date),
        )

    def _calculate_position_size(self, signal: Signal, state: BrokerRiskState) -> int:
        est_price = self._estimate_price(signal.code, signal.signal_date)
        if est_price is None or est_price <= 0:
            return 0

        nav = state.cash + state.portfolio_market_value
        risk_budget = nav * self.config.risk_per_trade_pct
        max_notional = nav * self.config.max_position_pct

        # 用最小止损宽度估算风险仓位，避免分母接近 0。
        est_stop_pct = max(self.config.stop_loss_pct, 0.01)
        qty_by_risk = risk_budget / (est_price * est_stop_pct)
        qty_by_cap = max_notional / est_price
        quantity = int(min(qty_by_risk, qty_by_cap) / 100) * 100
        return max(quantity, 0)

    def check_signal(self, signal: Signal, state: BrokerRiskState) -> Order | None:
        # 同一股票已有持仓时，不重复开仓。
        if signal.code in state.holdings:
            return None

        quantity = self._calculate_position_size(signal, state)
        if quantity < 100:
            return None

        execute_date = self._next_trade_date(signal.signal_date)
        if execute_date is None:
            return None

        return Order(
            order_id=build_order_id(signal.signal_id),
            signal_id=signal.signal_id,
            code=signal.code,
            action="BUY",
            quantity=quantity,
            execute_date=execute_date,
            pattern=signal.pattern,
            status="PENDING",
        )

