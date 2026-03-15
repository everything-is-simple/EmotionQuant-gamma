from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_INPUT = Path(
    "g:/EmotionQuant-gamma/normandy/03-execution/evidence/"
    "tachibana_book_monthly_tables_1976_02_1976_12_event_extract_20260315.csv"
)
DEFAULT_OUTPUT = Path(
    "g:/EmotionQuant-gamma/normandy/03-execution/evidence/"
    "tachibana_replay_ledger_1976_02_1976_12_20260315.csv"
)


def parse_int(value: str) -> int:
    text = (value or "").strip()
    if not text:
        return 0
    return int(text)


def classify_state(open_long_units: int, open_short_units: int) -> str:
    if open_long_units == 0 and open_short_units == 0:
        return "flat"
    if open_long_units > 0 and open_short_units == 0:
        return "long_only"
    if open_long_units == 0 and open_short_units > 0:
        return "short_only"
    return "locked"


def describe_transition(
    prev_long: int,
    prev_short: int,
    next_long: int,
    next_short: int,
) -> tuple[str, bool]:
    prev_state = classify_state(prev_long, prev_short)
    next_state = classify_state(next_long, next_short)
    delta_long = next_long - prev_long
    delta_short = next_short - prev_short
    reversal = False

    if prev_state == "flat" and next_state == "long_only":
        return "enter_long", reversal
    if prev_state == "flat" and next_state == "short_only":
        return "enter_short", reversal
    if prev_state == "flat" and next_state == "locked":
        return "enter_locked", reversal

    if prev_state == "long_only" and next_state == "long_only":
        if delta_long > 0:
            return "add_long", reversal
        if delta_long < 0:
            return "reduce_long", reversal
        return "hold_long_adjustment", reversal

    if prev_state == "short_only" and next_state == "short_only":
        if delta_short > 0:
            return "add_short", reversal
        if delta_short < 0:
            return "cover_short_partial", reversal
        return "hold_short_adjustment", reversal

    if prev_state == "long_only" and next_state == "flat":
        return "exit_long_to_flat", reversal
    if prev_state == "short_only" and next_state == "flat":
        return "cover_short_to_flat", reversal
    if prev_state == "locked" and next_state == "flat":
        return "exit_locked_to_flat", reversal

    if prev_state == "short_only" and next_state == "long_only":
        reversal = True
        return "reverse_short_to_long", reversal
    if prev_state == "long_only" and next_state == "short_only":
        reversal = True
        return "reverse_long_to_short", reversal

    if prev_state == "short_only" and next_state == "locked":
        return "lock_long_against_short", reversal
    if prev_state == "long_only" and next_state == "locked":
        return "lock_short_against_long", reversal

    if prev_state == "locked" and next_state == "long_only":
        return "unlock_short", reversal
    if prev_state == "locked" and next_state == "short_only":
        return "unlock_long", reversal

    if prev_state == "locked" and next_state == "locked":
        if delta_long > 0 and delta_short == 0:
            return "add_long_locked", reversal
        if delta_long < 0 and delta_short == 0:
            return "reduce_long_locked", reversal
        if delta_short > 0 and delta_long == 0:
            return "add_short_locked", reversal
        if delta_short < 0 and delta_long == 0:
            return "reduce_short_locked", reversal
        return "rebalance_locked", reversal

    return f"{prev_state}_to_{next_state}", reversal


def build_replay_ledger(input_path: Path) -> list[dict[str, object]]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        events = list(csv.DictReader(handle))

    events.sort(key=lambda row: row["date"])
    rows: list[dict[str, object]] = []
    current_position_id = ""
    current_leg_id = 0
    position_seq = 0
    prev_long = 0
    prev_short = 0

    for index, event in enumerate(events, start=1):
        next_long = parse_int(event["open_long_units"])
        next_short = parse_int(event["open_short_units"])
        prev_state = classify_state(prev_long, prev_short)
        next_state = classify_state(next_long, next_short)
        transition, reversal = describe_transition(prev_long, prev_short, next_long, next_short)

        position_id_before = current_position_id if prev_state != "flat" else ""

        starts_new_position = False
        if prev_state == "flat" and next_state != "flat":
            starts_new_position = True
        elif reversal and next_state != "flat":
            starts_new_position = True

        if starts_new_position:
            position_seq += 1
            position_id_after = f"TACHI_PIONEER_1976_{position_seq:03d}"
            leg_id_after = 1
        elif next_state == "flat":
            position_id_after = ""
            leg_id_after = ""
        else:
            position_id_after = current_position_id
            leg_id_after = current_leg_id + 1

        rows.append(
            {
                "event_id": f"TACHI_EVT_{index:03d}",
                "date": event["date"],
                "month": event["month"],
                "source_page": event["source_page"],
                "confidence": event["confidence"],
                "close": event["close"],
                "execution_price": event["execution_price"],
                "buy_units": event["buy_units"],
                "sell_units": event["sell_units"],
                "prev_open_long_units": prev_long,
                "prev_open_short_units": prev_short,
                "next_open_long_units": next_long,
                "next_open_short_units": next_short,
                "prev_state": prev_state,
                "next_state": next_state,
                "state_transition": transition,
                "position_id_before": position_id_before,
                "position_id_after": position_id_after,
                "leg_id_after": leg_id_after,
                "reversal_flag": int(reversal),
                "lock_state_flag": int(next_state == "locked"),
                "raw_trade": event["raw_trade"],
                "raw_open_position": event["raw_open_position"],
                "note": event["note"],
            }
        )

        current_position_id = position_id_after
        current_leg_id = int(leg_id_after) if leg_id_after != "" else 0
        prev_long = next_long
        prev_short = next_short

    return rows


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Tachibana replay ledger from event extract.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_replay_ledger(input_path=args.input_csv)
    write_csv(rows=rows, output_path=args.output_csv)
    print(f"Input: {args.input_csv}")
    print(f"Output: {args.output_csv}")
    print(f"Rows written: {len(rows)}")


if __name__ == "__main__":
    main()
