from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# 类型别名
# ---------------------------------------------------------------------------
# ActionType 覆盖买卖两侧，用于 Order / Trade 层。
# SignalActionType 仅允许 BUY：v0.01 主线信号只产生买入，退出由 Broker 独立管理。
ActionType = Literal["BUY", "SELL"]
SignalActionType = Literal["BUY"]
# v0.01 勘误：订单生命周期允许 EXPIRED，避免 PENDING 无穷挂单。
OrderStatusType = Literal["PENDING", "FILLED", "REJECTED", "EXPIRED"]
PositionStateType = Literal["OPEN", "PARTIAL_EXIT_PENDING", "OPEN_REDUCED", "FULL_EXIT_PENDING", "CLOSED"]
# origin 与 event_stage 正交：
#   event_stage = 生命周期阶段（接受/撮合/过期）
#   origin      = 业务来源（上游信号 / 止损退出 / 末日强平）
OrderOriginType = Literal["UPSTREAM_SIGNAL", "EXIT_STOP_LOSS", "EXIT_TRAILING_STOP", "FORCE_CLOSE"]


# ---------------------------------------------------------------------------
# ID 构造函数：所有 ID 必须通过这里生成，禁止业务代码手拼字符串。
# 格式稳定是 trace 可回放的前提——ID 格式一变，所有历史 trace 的 JOIN 都会断。
# ---------------------------------------------------------------------------

def build_signal_id(code: str, signal_date: date, pattern: str) -> str:
    """信号 ID = code_date_pattern，跨表 JOIN 的全局唯一键。"""
    return f"{code}_{signal_date.isoformat()}_{pattern}"


def build_order_id(signal_id: str) -> str:
    """订单 ID 与信号 ID 同构，便于按 signal_id 直接追溯对应订单。"""
    return signal_id


def build_trade_id(order_id: str) -> str:
    """成交 ID = order_id + '_T'，简化 order -> trade 关联查询。"""
    return f"{order_id}_T"


def build_exit_signal_id(code: str, signal_date: date, reason: str) -> str:
    """退出信号 ID，reason 为 STOP_LOSS / TRAILING_STOP 等，全小写。"""
    return f"{code}_{signal_date.isoformat()}_{reason.strip().lower()}"


def build_exit_plan_id(position_id: str, signal_date: date, reason: str) -> str:
    """退出计划 ID：同一 position 下一次退出计划的稳定身份。"""
    return f"{position_id}_{signal_date.isoformat()}_{reason.strip().lower()}"


def build_exit_leg_id(exit_plan_id: str, exit_leg_seq: int) -> str:
    """退出腿 ID：同一退出计划下的稳定腿身份。"""
    return f"{exit_plan_id}_L{int(exit_leg_seq):02d}"


def build_exit_order_id(
    code: str,
    signal_date: date,
    reason: str,
    *,
    exit_plan_id: str | None = None,
    exit_leg_seq: int | None = None,
) -> str:
    """退出订单 ID，partial-exit 时升级为 leg-aware 格式。"""
    if exit_plan_id is not None and exit_leg_seq is not None:
        return f"EXIT_{exit_plan_id}_L{int(exit_leg_seq):02d}"
    return f"EXIT_{build_exit_signal_id(code, signal_date, reason)}"


def build_force_close_order_id(code: str, trade_date: date) -> str:
    """回测末日强平订单 ID，带 FC_ 前缀供 resolve_order_origin 识别。"""
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


# ---------------------------------------------------------------------------
# Pydantic 契约基类
# ---------------------------------------------------------------------------
# frozen=True：契约对象一旦创建即不可变。
# 这保证了在 Broker / Ranker 等多处消费同一 Signal 时不会产生副作用。
class ContractBase(BaseModel):
    model_config = ConfigDict(frozen=True)


# MSS 计算输出：市场级评分，当前主线消费者为 Broker / Risk。
# signal 是三段式定性标签，score 是 0-100 连续分，两者都要持久化到 l3_mss_daily。
class MarketScore(ContractBase):
    date: date
    score: float
    signal: Literal["BULLISH", "NEUTRAL", "BEARISH"]


# IRS 计算输出：行业级排序，当前主线消费者为 Strategy / Ranker。
# rank 是当日唯一整数排名（1=最强），score 是行业层总分（0-100）。
# 注意：rank 和 score 是两个不同的数，Ranker 只消费 rank 做线性映射，不直接透传 score。
class IndustryScore(ContractBase):
    date: date
    industry: str
    score: float
    rank: int


# Selector -> Strategy 的候选股契约。
# score 是 preselect 阶段的初选分（流动性/活跃度），不是 PAS/IRS 的交易决策分。
# preselect_score 与 score 当前同值；保留两个字段是为了让消费方明确意图。
class StockCandidate(ContractBase):
    code: str = Field(..., description="6位纯股票代码，不含交易所后缀")
    industry: str
    score: float
    trade_date: date | None = None
    preselect_score: float | None = None   # 初选打分，仅服务于算力调度
    candidate_rank: int | None = None      # Selector 层排名，1=最高
    candidate_reason: str | None = None
    liquidity_tag: str | None = None       # HIGH / MEDIUM / LOW，描述流动性分层


# Strategy -> Broker 的交易信号契约。
#
# 字段分两层：
# - 核心层（signal_id ~ reason_code）：写入 l3_signals，frozen schema，不随实验变化。
# - 扩展层（pattern_strength ~ variant）：仅在 DTT 主线使用，写入 l3_signal_rank_exp。
#   这些字段在 Signal 对象上是只读的，不得被下游修改（frozen=True 保证）。
#
# 关键语义区分：
# - strength：PAS detector 原始强度，[0,1] 范围
# - pattern_strength：经 quality 修正后的形态强度（当前 P4 前仍等于 strength）
# - irs_score：行业排名映射后的后置增强分（0-100），由 Ranker 附着
# - final_score：DTT 加权综合分，用于同日信号排序
class Signal(ContractBase):
    signal_id: str
    code: str
    signal_date: date
    action: SignalActionType
    strength: float
    pattern: str
    reason_code: str
    # 迁移期扩展字段：正式 l3_signals 仍只落核心层，DTT 真相源写 l3_signal_rank_exp。
    pattern_strength: float | None = None
    irs_score: float | None = None
    mss_score: float | None = None
    final_score: float | None = None
    final_rank: int | None = None
    variant: str | None = None

    def resolved_pattern_strength(self) -> float:
        """取 pattern_strength（若有）或回退到原始 strength。"""
        if self.pattern_strength is not None:
            return float(self.pattern_strength)
        return float(self.strength)

    def to_formal_signal_row(self) -> dict[str, object]:
        """只导出核心层字段，写入 l3_signals；扩展字段不进入 frozen schema。"""
        return {
            "signal_id": self.signal_id,
            "code": self.code,
            "signal_date": self.signal_date,
            "action": self.action,
            "strength": self.strength,
            "pattern": self.pattern,
            "reason_code": self.reason_code,
        }


# Broker 内部订单契约：由 RiskManager 生成，Matcher 消费。
# execute_date 是实际执行日（T+1），不是信号日（T）。
# quantity 单位为股，A 股最小单位 100 股（一手）。
class Order(ContractBase):
    order_id: str
    signal_id: str
    code: str
    action: ActionType
    quantity: int         # 股数，必须是 100 的整数倍（A 股规则）
    execute_date: date    # T+1 开盘执行日，由 next_trade_date 推算
    pattern: str
    is_paper: bool = False
    status: OrderStatusType = "PENDING"
    reject_reason: str | None = None
    position_id: str | None = None
    exit_plan_id: str | None = None
    exit_leg_id: str | None = None
    exit_leg_seq: int | None = None
    exit_leg_count: int | None = None
    exit_reason_code: str | None = None
    is_partial_exit: bool = False
    remaining_qty_before: int | None = None
    target_qty_after: int | None = None


# Broker 内部成交契约：由 Matcher.execute 产生，写入 l4_trades。
# price 是含滑点的复权开盘价，fee 是单边手续费（含印花税/过户费/佣金）。
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
    position_id: str | None = None
    exit_plan_id: str | None = None
    exit_leg_id: str | None = None
    exit_leg_seq: int | None = None
    exit_reason_code: str | None = None
    is_partial_exit: bool = False
    remaining_qty_after: int | None = None
