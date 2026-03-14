from datetime import date

from src.contracts import (
    IndustryScore,
    MarketScore,
    Order,
    Signal,
    StockCandidate,
    Trade,
    build_exit_leg_id,
    build_exit_order_id,
    build_exit_plan_id,
    build_exit_signal_id,
    build_force_close_order_id,
    build_order_id,
    build_signal_id,
    build_trade_id,
    resolve_order_origin,
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


def test_resolve_order_origin_distinguishes_upstream_exit_and_force_close() -> None:
    d = date(2026, 3, 4)
    upstream_signal_id = build_signal_id("000001", d, "bof")
    stop_loss_signal_id = build_exit_signal_id("000001", d, "STOP_LOSS")
    trailing_signal_id = build_exit_signal_id("000001", d, "TRAILING_STOP")
    force_close_order_id = build_force_close_order_id("000001", d)

    assert resolve_order_origin(build_order_id(upstream_signal_id), upstream_signal_id) == "UPSTREAM_SIGNAL"
    assert resolve_order_origin(build_exit_order_id("000001", d, "STOP_LOSS"), stop_loss_signal_id) == "EXIT_STOP_LOSS"
    assert (
        resolve_order_origin(build_exit_order_id("000001", d, "TRAILING_STOP"), trailing_signal_id)
        == "EXIT_TRAILING_STOP"
    )
    assert resolve_order_origin(force_close_order_id, force_close_order_id) == "FORCE_CLOSE"


def test_partial_exit_identity_builders_and_contract_fields_roundtrip() -> None:
    d = date(2026, 3, 4)
    position_id = "BUY_000001"
    exit_plan_id = build_exit_plan_id(position_id, d, "TRAILING_STOP")
    exit_leg_id = build_exit_leg_id(exit_plan_id, 1)
    order_id = build_exit_order_id("000001", d, "TRAILING_STOP", exit_plan_id=exit_plan_id, exit_leg_seq=1)

    order = Order(
        order_id=order_id,
        signal_id=build_exit_signal_id("000001", d, "TRAILING_STOP"),
        code="000001",
        action="SELL",
        quantity=100,
        execute_date=d,
        pattern="bof",
        position_id=position_id,
        exit_plan_id=exit_plan_id,
        exit_leg_id=exit_leg_id,
        exit_leg_seq=1,
        exit_leg_count=2,
        exit_reason_code="TRAILING_STOP",
        is_partial_exit=True,
        remaining_qty_before=200,
        target_qty_after=100,
    )
    trade = Trade(
        trade_id=build_trade_id(order_id),
        order_id=order_id,
        code="000001",
        execute_date=d,
        action="SELL",
        price=10.0,
        quantity=100,
        fee=5.0,
        pattern="bof",
        position_id=position_id,
        exit_plan_id=exit_plan_id,
        exit_leg_id=exit_leg_id,
        exit_leg_seq=1,
        exit_reason_code="TRAILING_STOP",
        is_partial_exit=True,
        remaining_qty_after=100,
    )

    assert exit_plan_id == "BUY_000001_2026-03-04_trailing_stop"
    assert exit_leg_id == "BUY_000001_2026-03-04_trailing_stop_L01"
    assert order.exit_leg_id == exit_leg_id
    assert trade.exit_leg_id == exit_leg_id
