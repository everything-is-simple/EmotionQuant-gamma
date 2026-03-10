from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ActionType = Literal["BUY", "SELL"]
SignalActionType = Literal["BUY"]
# v0.01 勘误补充：订单生命周期允许 EXPIRED，避免 PENDING 无穷挂单。
OrderStatusType = Literal["PENDING", "FILLED", "REJECTED", "EXPIRED"]
OrderOriginType = Literal["UPSTREAM_SIGNAL", "EXIT_STOP_LOSS", "EXIT_TRAILING_STOP", "FORCE_CLOSE"]


def build_signal_id(code: str, signal_date: date, pattern: str) -> str:
    return f"{code}_{signal_date.isoformat()}_{pattern}"


def build_order_id(signal_id: str) -> str:
    return signal_id


def build_trade_id(order_id: str) -> str:
    return f"{order_id}_T"


def build_exit_signal_id(code: str, signal_date: date, reason: str) -> str:
    return f"{code}_{signal_date.isoformat()}_{reason.strip().lower()}"


def build_exit_order_id(code: str, signal_date: date, reason: str) -> str:
    return f"EXIT_{build_exit_signal_id(code, signal_date, reason)}"


def build_force_close_order_id(code: str, trade_date: date) -> str:
    return f"FC_{code}_{trade_date.isoformat()}"


def resolve_order_origin(order_id: str, signal_id: str | None = None) -> OrderOriginType:
    """
    Broker lifecycle trace 中的 origin 表示“订单来源”，不是处理阶段。

    event_stage 负责描述风控/撮合/过期/强平等生命周期阶段；
    origin 只负责回答这笔订单来自：
    - 上游买入信号
    - 退出单（止损 / 回撤）
    - 回测末日强平
    """
    order_token = (order_id or "").strip().upper()
    signal_token = (signal_id or "").strip().upper()
    combined = f"{order_token} {signal_token}"

    if order_token.startswith("FC_") or signal_token.startswith("FC_"):
        return "FORCE_CLOSE"
    if order_token.startswith("EXIT_"):
        if "_STOP_LOSS" in combined:
            return "EXIT_STOP_LOSS"
        if "_TRAILING_STOP" in combined:
            return "EXIT_TRAILING_STOP"
    return "UPSTREAM_SIGNAL"


class ContractBase(BaseModel):
    model_config = ConfigDict(frozen=True)


class MarketScore(ContractBase):
    date: date
    score: float
    signal: Literal["BULLISH", "NEUTRAL", "BEARISH"]


class IndustryScore(ContractBase):
    date: date
    industry: str
    score: float
    rank: int


class StockCandidate(ContractBase):
    code: str = Field(..., description="6-digit pure stock code")
    industry: str
    score: float
    trade_date: date | None = None
    preselect_score: float | None = None
    candidate_rank: int | None = None
    candidate_reason: str | None = None
    liquidity_tag: str | None = None


class Signal(ContractBase):
    signal_id: str
    code: str
    signal_date: date
    action: SignalActionType
    strength: float
    pattern: str
    reason_code: str
    # 兼容迁移期运行时扩展字段：正式 l3_signals 仍只落旧字段，DTT 额外真相源写 sidecar。
    pattern_strength: float | None = None
    irs_score: float | None = None
    mss_score: float | None = None
    final_score: float | None = None
    final_rank: int | None = None
    variant: str | None = None

    def resolved_pattern_strength(self) -> float:
        if self.pattern_strength is not None:
            return float(self.pattern_strength)
        return float(self.strength)

    def to_formal_signal_row(self) -> dict[str, object]:
        """只导出正式 l3_signals 兼容字段，避免迁移期扩展字段污染 frozen schema。"""
        return {
            "signal_id": self.signal_id,
            "code": self.code,
            "signal_date": self.signal_date,
            "action": self.action,
            "strength": self.strength,
            "pattern": self.pattern,
            "reason_code": self.reason_code,
        }


class Order(ContractBase):
    order_id: str
    signal_id: str
    code: str
    action: ActionType
    quantity: int
    execute_date: date
    pattern: str
    is_paper: bool = False
    status: OrderStatusType = "PENDING"
    reject_reason: str | None = None


class Trade(ContractBase):
    trade_id: str
    order_id: str
    code: str
    execute_date: date
    action: ActionType
    price: float
    quantity: int
    fee: float
    pattern: str
    is_paper: bool = False
