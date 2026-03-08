from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ActionType = Literal["BUY", "SELL"]
SignalActionType = Literal["BUY"]
# v0.01 勘误补充：订单生命周期允许 EXPIRED，避免 PENDING 无穷挂单。
OrderStatusType = Literal["PENDING", "FILLED", "REJECTED", "EXPIRED"]


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
    preselect_score: float | None = None
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
    bof_strength: float | None = None
    irs_score: float | None = None
    mss_score: float | None = None
    final_score: float | None = None
    final_rank: int | None = None
    variant: str | None = None

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
