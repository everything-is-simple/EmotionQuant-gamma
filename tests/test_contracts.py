from datetime import date

from src.contracts import (
    IndustryScore,
    MarketScore,
    Order,
    Signal,
    StockCandidate,
    Trade,
    build_order_id,
    build_signal_id,
    build_trade_id,
)


def test_contracts_roundtrip() -> None:
    d = date(2026, 3, 4)
    signal_id = build_signal_id("000001", d, "bof")
    order_id = build_order_id(signal_id)
    trade_id = build_trade_id(order_id)

    mss = MarketScore(date=d, score=66.6, signal="BULLISH")
    irs = IndustryScore(date=d, industry="银行", score=59.1, rank=3)
    candidate = StockCandidate(code="000001", industry="银行", score=0.8)
    signal = Signal(
        signal_id=signal_id,
        code="000001",
        signal_date=d,
        action="BUY",
        strength=0.77,
        pattern="bof",
        reason_code="PAS_BOF",
    )
    order = Order(
        order_id=order_id,
        signal_id=signal_id,
        code="000001",
        action="BUY",
        quantity=100,
        execute_date=d,
        pattern="bof",
        status="PENDING",
    )
    trade = Trade(
        trade_id=trade_id,
        order_id=order_id,
        code="000001",
        execute_date=d,
        action="BUY",
        price=10.0,
        quantity=100,
        fee=5.0,
        pattern="bof",
    )

    assert mss.model_dump()["signal"] == "BULLISH"
    assert irs.rank == 3
    assert candidate.code == "000001"
    assert signal.signal_id.endswith("_bof")
    assert order.order_id == signal.signal_id
    assert trade.trade_id.endswith("_T")

