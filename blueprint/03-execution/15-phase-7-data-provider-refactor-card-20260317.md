# Phase 7 Data Provider Refactor Card

- Status: `Completed`
- Date: `2026-03-17`
- Closeout: `2026-03-18`
- Scope: `data ingress and raw/L1 local-first contract cutover`

## 1. Goal

Replace the old data ingress posture:

`TuShare-first + old raw db reuse`

with the current truthful posture:

`TDX local-first + BaoStock light incremental + TuShare emergency fallback`

This package belongs to the first battlefield because it changes the shared system spine:

`raw -> L1 -> L2`

not a private research battlefield implementation.

## 2. Formal Boundary

### 2.1 Historical base

The formal historical base is now:

`vipdoc historical base`

It owns:

1. `raw_daily`
2. `raw_index_daily`
3. `raw_trade_cal`

### 2.2 Static local assets

The formal local static-asset ingress is now:

`T0002/hq_cache + mootdx`

It owns:

1. `raw_stock_basic`
2. `raw_index_classify`
3. `raw_index_member`

### 2.3 Incremental patch source

The formal incremental patch source is now:

`BaoStock light incremental only`

It is allowed to do:

1. small post-close gap patching
2. emergency patching for a few stock or index series
3. limited stock-list fallback when local snapshots are abnormal

It is not allowed to do:

1. whole-history market-wide refresh
2. oversized brute-force windows
3. daily primary-source ownership

### 2.4 Emergency fallback

The formal emergency fallback is now:

`TuShare emergency fallback only`

It is no longer the default daily ingress.

### 2.5 Industry and price-limit semantics

The formal active runtime contract is now:

1. `l1_industry_member` is the active industry membership contract
2. `l1_sw_industry_member` survives only as migration/history compatibility
3. `up_limit / down_limit` are derived locally on `l1_stock_daily`
4. active industry semantics are `generic industry bucket`, not `SW2021-only`

## 3. Package Decomposition

### 3.1 Phase 7A

Tool-layer refactor only:

1. `scripts/data/import_tdx_vipdoc.py`
2. `scripts/data/import_tdx_static_assets.py`
3. `scripts/data/bulk_download_baostock.py`
4. `scripts/data/bulk_download_tushare.py`
5. `scripts/data/load_l1_from_raw_duckdb.py`
6. `scripts/data/repair_l1_partitions_from_raw_duckdb.py`

Delivered:

1. local TDX history ingress
2. local static asset ingress
3. BaoStock safety-mode incremental patching
4. TuShare fallback preservation

### 3.2 Phase 7B

Active data-contract cutover:

1. `src/data/fetcher.py`
2. `src/data/cleaner.py`
3. `src/data/sw_industry.py`
4. `src/selector/selector.py`
5. `tests/unit/data/*`
6. related selector regression coverage

Delivered:

1. `L1` no longer depends on online `stk_limit`
2. `L1 -> L2` no longer assumes `SW2021-only`
3. industry membership now flows through `l1_industry_member`
4. local rules now own `up_limit / down_limit`

## 4. Minimum Data Set

The current default runtime minimum data set is frozen as:

1. `trade_calendar`
2. `stock_basic`
3. `stock_daily`
4. `price_limit_rules`
5. `optional market / industry reference`

Explicit downgrades:

1. `raw_daily_basic` is no longer a primary runtime dependency
2. `raw_limit_list` is retired from the default path
3. `SW2021-only` industry semantics are retired from the active path

## 5. Current Truth

The truthful current system data posture is:

`TDX local-first -> raw db -> L1 -> L2 -> selector / broker / backtest`

with:

1. `mootdx` as a formal local-ingress dependency
2. `BaoStock` as patch/fallback helper
3. `TuShare` as emergency-only fallback

## 6. Delivered Evidence

The package has now been verified with:

1. raw db refreshed to `2026-03-17`
2. execution db `L1` refreshed to `2026-03-17`
3. local industry contract cut over to `l1_industry_member`
4. local price-limit derivation active on `l1_stock_daily`
5. full repository `pytest` passing
6. `preflight` passing

Formal records:

1. `docs/spec/v0.01-plus/records/v0.01-plus-phase-7b-local-data-contract-regression-audit-20260318.md`
2. `docs/spec/v0.01-plus/records/v0.01-plus-phase-7-data-provider-refactor-closeout-20260318.md`
3. `docs/reference/a-stock-rules/a-share-local-price-limit-runtime-rules-20260318.md`

## 7. Done

This package is complete when:

1. raw ingress is local-first
2. active execution contract is local-first
3. industry membership active name is `l1_industry_member`
4. price-limit rules are locally derived and documented
5. regression audit is recorded
6. closeout record is written

All six conditions are now satisfied.

## 8. Formal Ruling

`Phase 7` is now closed with:

1. `Phase 7A = completed`
2. `Phase 7B = completed`
3. `active data provider posture = TDX local-first`
4. `BaoStock = light incremental only`
5. `TuShare = emergency fallback only`
6. `future data contract rewrite requires = new formal package`
