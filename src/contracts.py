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


class Signal(ContractBase):
    signal_id: str
    code: str
    signal_date: date
    action: SignalActionType
    strength: float
    pattern: str
    reason_code: str


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
