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


@dataclass
class RiskDecision:
    order: Order | None
    reject_reason: str | None
    execute_date: date | None
    reserved_cash: float = 0.0


@dataclass(frozen=True)
class MssRiskOverlay:
    signal: str
    score: float
    max_positions: int
    risk_per_trade_pct: float
    max_position_pct: float


class RiskManager:
    def __init__(self, store: Store, config: Settings):
        self.store = store
        self.config = config
        self._mss_overlay_cache: dict[date, MssRiskOverlay] = {}

    def _next_trade_date(self, d: date) -> date | None:
        return self.store.next_trade_date(d)

    def _estimate_price(self, code: str, signal_date: date) -> float | None:
        return self.store.read_scalar(
            "SELECT adj_close FROM l2_stock_adj_daily WHERE code=? AND date=?",
            (code, signal_date),
        )

    def _estimate_fee(self, amount: float, action: str) -> float:
        # 与 matcher 成本口径保持一致，避免预估与撮合不一致。
        commission = max(amount * self.config.commission_rate, self.config.min_commission)
        transfer_fee = amount * self.config.transfer_fee_rate
        stamp_duty = amount * self.config.stamp_duty_rate if action.upper() == "SELL" else 0.0
        return commission + transfer_fee + stamp_duty

    def _estimate_buy_cost(self, price: float, quantity: int) -> float:
        amount = float(price) * int(quantity)
        return amount + self._estimate_fee(amount, "BUY")

    def _max_affordable_quantity(self, est_price: float, cash: float, target_quantity: int) -> int:
        qty = int(target_quantity // 100) * 100
        while qty >= 100:
            if self._estimate_buy_cost(est_price, qty) <= cash + 1e-6:
                return qty
            qty -= 100
        return 0

    def _clamp_effective_max_positions(self, multiplier: float) -> int:
        base = int(self.config.max_positions)
        if base <= 0:
            return 0
        scaled = int(base * max(multiplier, 0.0))
        # 熊市只允许缩容，不默认把系统一刀切到 0 仓，避免把“控仓位”退化回“硬停手”。
        return max(1, scaled)

    def _resolve_mss_signal_label(self, raw_value: object | None) -> str:
        label = str(raw_value or "").strip().upper()
        if label in {"BULLISH", "NEUTRAL", "BEARISH"}:
            return label
        return "NEUTRAL"

    def _resolve_mss_multipliers(self, signal_label: str) -> tuple[float, float, float]:
        if signal_label == "BULLISH":
            return (
                self.config.mss_bullish_max_positions_mult,
                self.config.mss_bullish_risk_per_trade_mult,
                self.config.mss_bullish_max_position_mult,
            )
        if signal_label == "BEARISH":
            return (
                self.config.mss_bearish_max_positions_mult,
                self.config.mss_bearish_risk_per_trade_mult,
                self.config.mss_bearish_max_position_mult,
            )
        return (
            self.config.mss_neutral_max_positions_mult,
            self.config.mss_neutral_risk_per_trade_mult,
            self.config.mss_neutral_max_position_mult,
        )

    def _load_mss_overlay(self, signal_date: date) -> MssRiskOverlay:
        cached = self._mss_overlay_cache.get(signal_date)
        if cached is not None:
            return cached

        if not self.config.mss_risk_overlay_enabled:
            overlay = MssRiskOverlay(
                signal="NEUTRAL",
                score=float(self.config.dtt_score_fill),
                max_positions=int(self.config.max_positions),
                risk_per_trade_pct=float(self.config.risk_per_trade_pct),
                max_position_pct=float(self.config.max_position_pct),
            )
            self._mss_overlay_cache[signal_date] = overlay
            return overlay

        row = self.store.read_df(
            """
            SELECT score, signal
            FROM l3_mss_daily
            WHERE date = ?
            LIMIT 1
            """,
            (signal_date,),
        )
        if row.empty:
            signal_label = "NEUTRAL"
            score = float(self.config.dtt_score_fill)
        else:
            signal_label = self._resolve_mss_signal_label(row.iloc[0]["signal"])
            raw_score = row.iloc[0]["score"]
            score = float(raw_score if raw_score is not None else self.config.dtt_score_fill)

        max_positions_mult, risk_per_trade_mult, max_position_mult = self._resolve_mss_multipliers(
            signal_label
        )
        overlay = MssRiskOverlay(
            signal=signal_label,
            score=score,
            max_positions=self._clamp_effective_max_positions(max_positions_mult),
            # MSS 在 v0.01-plus 当前阶段只压缩执行风险，不反向改写排序层分数。
            risk_per_trade_pct=float(self.config.risk_per_trade_pct) * max(risk_per_trade_mult, 0.0),
            max_position_pct=float(self.config.max_position_pct) * max(max_position_mult, 0.0),
        )
        self._mss_overlay_cache[signal_date] = overlay
        return overlay

    def _calculate_position_size(
        self,
        est_price: float,
        state: BrokerRiskState,
        overlay: MssRiskOverlay,
    ) -> int:
        nav = state.cash + state.portfolio_market_value
        risk_budget = nav * overlay.risk_per_trade_pct
        max_notional = nav * overlay.max_position_pct

        # 用最小止损宽度估算风险仓位，避免分母接近 0。
        est_stop_pct = max(self.config.stop_loss_pct, 0.01)
        qty_by_risk = risk_budget / (est_price * est_stop_pct)
        qty_by_cap = max_notional / est_price
        quantity = int(min(qty_by_risk, qty_by_cap) / 100) * 100
        return max(quantity, 0)

    def assess_signal(self, signal: Signal, state: BrokerRiskState) -> RiskDecision:
        execute_date = self._next_trade_date(signal.signal_date)
        if execute_date is None:
            return RiskDecision(order=None, reject_reason="NO_NEXT_TRADE_DAY", execute_date=None)

        overlay = self._load_mss_overlay(signal.signal_date)

        # 同一股票已有持仓（或已被更强信号占位）时，不重复开仓。
        if signal.code in state.holdings:
            return RiskDecision(order=None, reject_reason="ALREADY_HOLDING", execute_date=execute_date)

        if len(state.holdings) >= overlay.max_positions:
            return RiskDecision(
                order=None,
                reject_reason="MAX_POSITIONS_REACHED",
                execute_date=execute_date,
            )

        est_price = self._estimate_price(signal.code, signal.signal_date)
        if est_price is None or est_price <= 0:
            return RiskDecision(order=None, reject_reason="NO_EST_PRICE", execute_date=execute_date)

        target_quantity = self._calculate_position_size(float(est_price), state, overlay)
        if target_quantity < 100:
            min_lot_cost = self._estimate_buy_cost(float(est_price), 100)
            if min_lot_cost > state.cash + 1e-6:
                return RiskDecision(
                    order=None,
                    reject_reason="INSUFFICIENT_CASH",
                    execute_date=execute_date,
                )
            return RiskDecision(
                order=None,
                reject_reason="SIZE_BELOW_MIN_LOT",
                execute_date=execute_date,
            )

        quantity = self._max_affordable_quantity(float(est_price), state.cash, target_quantity)
        if quantity < 100:
            return RiskDecision(order=None, reject_reason="INSUFFICIENT_CASH", execute_date=execute_date)

        reserved_cash = self._estimate_buy_cost(float(est_price), quantity)
        return RiskDecision(
            order=Order(
                order_id=build_order_id(signal.signal_id),
                signal_id=signal.signal_id,
                code=signal.code,
                action="BUY",
                quantity=quantity,
                execute_date=execute_date,
                pattern=signal.pattern,
                status="PENDING",
            ),
            reject_reason=None,
            execute_date=execute_date,
            reserved_cash=reserved_cash,
        )

    def check_signal(self, signal: Signal, state: BrokerRiskState) -> Order | None:
        # 兼容旧调用方；新代码建议使用 assess_signal 获取拒绝原因。
        return self.assess_signal(signal, state).order
