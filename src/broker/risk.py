from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

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
    overlay: "MssRiskOverlay | None" = None


@dataclass(frozen=True)
class MssRiskOverlay:
    state: str
    signal: str
    score: float
    max_positions_mult: float
    risk_per_trade_mult: float
    max_position_mult: float
    max_positions: int
    risk_per_trade_pct: float
    max_position_pct: float
    overlay_enabled: bool
    coverage_flag: str
    market_coefficient_raw: float | None = None
    profit_effect_raw: float | None = None
    loss_effect_raw: float | None = None
    continuity_raw: float | None = None
    extreme_raw: float | None = None
    volatility_raw: float | None = None
    market_coefficient: float | None = None
    profit_effect: float | None = None
    loss_effect: float | None = None
    continuity: float | None = None
    extreme: float | None = None
    volatility: float | None = None


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
        # Phase 0-2 兼容口径仍按 MarketScore.signal 选倍率。
        # Phase 3 的正式目标是切到 risk_regime；在那之前，这里不应擅自发明第二套状态机。
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

    @staticmethod
    def _safe_optional_float(value: object | None) -> float | None:
        if value is None or pd.isna(value):
            return None
        return float(value)

    @staticmethod
    def _empty_mss_components() -> dict[str, float | None]:
        return {
            "market_coefficient_raw": None,
            "profit_effect_raw": None,
            "loss_effect_raw": None,
            "continuity_raw": None,
            "extreme_raw": None,
            "volatility_raw": None,
            "market_coefficient": None,
            "profit_effect": None,
            "loss_effect": None,
            "continuity": None,
            "extreme": None,
            "volatility": None,
        }

    def _load_mss_overlay(self, signal_date: date) -> MssRiskOverlay:
        """
        加载 MSS 风控覆盖层（Phase 0 核心）：
        
        三种状态：
        - DISABLED: 配置关闭，使用基线参数
        - MISSING: 当日无 MSS 快照，用 fill_score 兜底
        - NORMAL: 正常读取 MSS 分数与信号
        
        根据市场信号调整：
        - BULLISH: 放大仓位容量与单笔风险
        - BEARISH: 压缩仓位容量与单笔风险
        - NEUTRAL: 保持基线参数
        
        覆盖层只影响执行风险，不改写排序层分数
        """
        cached = self._mss_overlay_cache.get(signal_date)
        if cached is not None:
            return cached

        if not self.config.mss_risk_overlay_enabled:
            overlay = MssRiskOverlay(
                state="DISABLED",
                signal="NEUTRAL",
                score=float(self.config.dtt_score_fill),
                max_positions_mult=1.0,
                risk_per_trade_mult=1.0,
                max_position_mult=1.0,
                max_positions=int(self.config.max_positions),
                risk_per_trade_pct=float(self.config.risk_per_trade_pct),
                max_position_pct=float(self.config.max_position_pct),
                overlay_enabled=False,
                coverage_flag="OVERLAY_DISABLED",
            )
            self._mss_overlay_cache[signal_date] = overlay
            return overlay

        row = self.store.read_df(
            """
            SELECT
                score,
                signal,
                market_coefficient_raw,
                profit_effect_raw,
                loss_effect_raw,
                continuity_raw,
                extreme_raw,
                volatility_raw,
                market_coefficient,
                profit_effect,
                loss_effect,
                continuity,
                extreme,
                volatility
            FROM l3_mss_daily
            WHERE date = ?
            LIMIT 1
            """,
            (signal_date,),
        )
        mss_components = self._empty_mss_components()
        if row.empty:
            # 当日缺 MSS 快照时，不阻断交易流；回落到 fill_score + NEUTRAL，由 coverage_flag 记录原因。
            overlay_state = "MISSING"
            signal_label = "NEUTRAL"
            score = float(self.config.dtt_score_fill)
            coverage_flag = "SNAPSHOT_MISSING"
        else:
            overlay_state = "NORMAL"
            row_data = row.iloc[0]
            raw_signal = row_data["signal"]
            raw_signal_label = str(raw_signal or "").strip().upper()
            signal_label = self._resolve_mss_signal_label(raw_signal)
            raw_score = row_data["score"]
            score = float(raw_score if raw_score is not None else self.config.dtt_score_fill)
            coverage_flag = "NORMAL"
            if raw_score is None or pd.isna(raw_score):
                score = float(self.config.dtt_score_fill)
                coverage_flag = "SCORE_FILL"
            if raw_signal_label not in {"BULLISH", "NEUTRAL", "BEARISH"} and coverage_flag == "NORMAL":
                coverage_flag = "SIGNAL_NORMALIZED"
            # Broker 只消费 MSS 的最终产物；raw / normalized 都从 l3_mss_daily 读取，不再回头重算。
            mss_components = {
                "market_coefficient_raw": self._safe_optional_float(row_data["market_coefficient_raw"]),
                "profit_effect_raw": self._safe_optional_float(row_data["profit_effect_raw"]),
                "loss_effect_raw": self._safe_optional_float(row_data["loss_effect_raw"]),
                "continuity_raw": self._safe_optional_float(row_data["continuity_raw"]),
                "extreme_raw": self._safe_optional_float(row_data["extreme_raw"]),
                "volatility_raw": self._safe_optional_float(row_data["volatility_raw"]),
                "market_coefficient": self._safe_optional_float(row_data["market_coefficient"]),
                "profit_effect": self._safe_optional_float(row_data["profit_effect"]),
                "loss_effect": self._safe_optional_float(row_data["loss_effect"]),
                "continuity": self._safe_optional_float(row_data["continuity"]),
                "extreme": self._safe_optional_float(row_data["extreme"]),
                "volatility": self._safe_optional_float(row_data["volatility"]),
            }

        max_positions_mult, risk_per_trade_mult, max_position_mult = self._resolve_mss_multipliers(
            signal_label
        )
        overlay = MssRiskOverlay(
            state=overlay_state,
            signal=signal_label,
            score=score,
            max_positions_mult=float(max_positions_mult),
            risk_per_trade_mult=float(risk_per_trade_mult),
            max_position_mult=float(max_position_mult),
            max_positions=self._clamp_effective_max_positions(max_positions_mult),
            # MSS 在 v0.01-plus 当前阶段只压缩执行风险，不反向改写排序层分数。
            risk_per_trade_pct=float(self.config.risk_per_trade_pct) * max(risk_per_trade_mult, 0.0),
            max_position_pct=float(self.config.max_position_pct) * max(max_position_mult, 0.0),
            overlay_enabled=True,
            coverage_flag=coverage_flag,
            market_coefficient_raw=mss_components["market_coefficient_raw"],
            profit_effect_raw=mss_components["profit_effect_raw"],
            loss_effect_raw=mss_components["loss_effect_raw"],
            continuity_raw=mss_components["continuity_raw"],
            extreme_raw=mss_components["extreme_raw"],
            volatility_raw=mss_components["volatility_raw"],
            market_coefficient=mss_components["market_coefficient"],
            profit_effect=mss_components["profit_effect"],
            loss_effect=mss_components["loss_effect"],
            continuity=mss_components["continuity"],
            extreme=mss_components["extreme"],
            volatility=mss_components["volatility"],
        )
        self._mss_overlay_cache[signal_date] = overlay
        return overlay

    def _calculate_position_size(
        self,
        est_price: float,
        state: BrokerRiskState,
        overlay: MssRiskOverlay,
    ) -> int:
        # 头寸大小同时受两层约束：
        # - 风险预算：risk_per_trade_pct
        # - 单票容量：max_position_pct
        # Broker 侧永远以 NAV 估算，不直接吃 PAS reference stop/target，
        # 避免形态解释层和执行风险层在当前阶段发生强耦合。
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
        """
        信号风控评估（Phase 0 核心）：
        
        拒绝原因：
        - NO_NEXT_TRADE_DAY: 无下一交易日
        - ALREADY_HOLDING: 已持仓（避免重复开仓）
        - MAX_POSITIONS_REACHED: 达到最大持仓数（受 MSS 动态调整）
        - NO_EST_PRICE: 无估价数据
        - SIZE_BELOW_MIN_LOT: 仓位不足一手
        - INSUFFICIENT_CASH: 现金不足
        
        通过时返回 Order + 预占现金
        """
        overlay = self._load_mss_overlay(signal.signal_date)
        execute_date = self._next_trade_date(signal.signal_date)
        if execute_date is None:
            return RiskDecision(
                order=None,
                reject_reason="NO_NEXT_TRADE_DAY",
                execute_date=None,
                overlay=overlay,
            )

        # 同一股票已有持仓（或已被更强信号占位）时，不重复开仓。
        # 这里的 holdings 同时包含“已有持仓”和“本批次更靠前 signal 已预占的名额”，
        # 这是为了让同日竞争顺序真正影响结果，而不是让后续信号假装还能再次开仓。
        if signal.code in state.holdings:
            return RiskDecision(
                order=None,
                reject_reason="ALREADY_HOLDING",
                execute_date=execute_date,
                overlay=overlay,
            )

        if len(state.holdings) >= overlay.max_positions:
            return RiskDecision(
                order=None,
                reject_reason="MAX_POSITIONS_REACHED",
                execute_date=execute_date,
                overlay=overlay,
            )

        est_price = self._estimate_price(signal.code, signal.signal_date)
        if est_price is None or est_price <= 0:
            return RiskDecision(
                order=None,
                reject_reason="NO_EST_PRICE",
                execute_date=execute_date,
                overlay=overlay,
            )

        target_quantity = self._calculate_position_size(float(est_price), state, overlay)
        if target_quantity < 100:
            min_lot_cost = self._estimate_buy_cost(float(est_price), 100)
            if min_lot_cost > state.cash + 1e-6:
                return RiskDecision(
                    order=None,
                    reject_reason="INSUFFICIENT_CASH",
                    execute_date=execute_date,
                    overlay=overlay,
                )
            return RiskDecision(
                order=None,
                reject_reason="SIZE_BELOW_MIN_LOT",
                execute_date=execute_date,
                overlay=overlay,
            )

        # 目标仓位先按风控预算算出来，再按真实现金缩到买得起的一手整数倍。
        quantity = self._max_affordable_quantity(float(est_price), state.cash, target_quantity)
        if quantity < 100:
            return RiskDecision(
                order=None,
                reject_reason="INSUFFICIENT_CASH",
                execute_date=execute_date,
                overlay=overlay,
            )

        # 这里预占的是“按 T 日估价估出来的预算”，不是最终成交成本；
        # Broker 会在 T+1 Open 真成交前再做一次现金校验，防守隔夜跳空。
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
            overlay=overlay,
        )

    def check_signal(self, signal: Signal, state: BrokerRiskState) -> Order | None:
        # 兼容旧调用方；新代码建议使用 assess_signal 获取拒绝原因。
        return self.assess_signal(signal, state).order
