# A-Share Local Price-Limit Runtime Rules (2026-03-18)

## 1. Purpose

This document freezes the active runtime rule used by the current mainline to populate:

1. `l1_stock_daily.up_limit`
2. `l1_stock_daily.down_limit`

It documents the rule that is already implemented in:

`src/data/fetcher.py::_apply_local_price_limits()`

This is a runtime contract document, not a historical market-reference note.

## 2. Why this exists

After `Phase 7B`, the mainline no longer treats online `stk_limit` style downloads as the default source of truth.

The current truthful posture is:

`price_limit boundary = locally derived from A-share rules + stock metadata + trade calendar`

## 3. Inputs

The local derivation consumes:

1. `l1_stock_daily.pre_close`
2. `l1_stock_info.is_st`
3. `l1_stock_info.list_date`
4. `l1_trade_calendar`
5. security code suffix / board prefix

## 4. Active Rule

### 4.1 ST

If `is_st = true`, use:

1. `up_limit = round(pre_close * 1.05, 2)`
2. `down_limit = round(pre_close * 0.95, 2)`

### 4.2 Beijing exchange

If code suffix is `.BJ`, use:

1. limit band = `30%`
2. first listed trading day: `no limit`

### 4.3 STAR / ChiNext

If code prefix is one of:

1. `688`
2. `689`
3. `300`
4. `301`

use:

1. limit band = `20%`
2. first `5` listed trading days: `no limit`

### 4.4 Other A-share boards

Use:

1. limit band = `10%`
2. first `5` listed trading days: `no limit`

## 5. Null Cases

`up_limit / down_limit` remain null when:

1. `pre_close` is null or non-positive
2. local listed-trading-day count falls inside the no-limit window
3. local metadata is insufficient to derive a truthful boundary

These nulls are treated as honest missing boundaries, not backfilled guesses.

## 6. Contract Scope

This rule is frozen for:

1. current default broker realism
2. current backtest execution realism
3. current `L1 -> L2` data contract

It does not claim to be:

1. a complete historical exchange-law archive
2. a guarantee that every historical exception is modeled
3. a substitute for future formal rule-package upgrades

## 7. Known Boundary

The current rule is designed for the truthful mainline and covers the dominant boards and listing-window behavior.

Residual edge risk remains around:

1. rare historical regime transitions
2. uncommon security types outside the active stock universe
3. metadata-quality gaps in legacy local snapshots

Those are acceptable under the current runtime boundary and must be handled by a new formal package if promoted further.
