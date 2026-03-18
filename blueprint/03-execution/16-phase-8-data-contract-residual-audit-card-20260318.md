# Phase 8 Data Contract Residual Audit Card

- Status: `Completed`
- Date: `2026-03-18`
- Type: `mainline audit package`
- Scope: `post-Phase-7 residual contract cleanup`

## 1. Goal

This card answers one question:

`after the Phase 7 local-first data cutover, which old data-contract assumptions still remain in code, tests, docs, and downstream battlefield logic?`

## 2. Why This Card Exists

`Phase 7` already completed the major direction shift:

1. `vipdoc + hq_cache + mootdx` became the primary local data base
2. `BaoStock` became light incremental fallback
3. `TuShare` became emergency fallback
4. `industry_member / l1_industry_member` became the active industry contract
5. `up_limit / down_limit` became locally-derived runtime facts

The remaining risk is no longer `data layer not built`.
The remaining risk is:

`old contract assumptions still scattered across code, tests, docs, and battlefield interfaces`

## 3. Validation Role

`Phase 8` is the floor-cleaning audit that must happen before later runtime promotion work.

It freezes:

1. `validated baseline` = `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
2. `single variable under test` = `residual data-contract assumptions only`
3. `forbidden variables` = any new entry rule, sizing rule, exit rule, Gene runtime rule, or research promotion

This card is complete only when later packages can safely say:

`the baseline data contract is known, truthful, and stable enough for isolated runtime experiments`

## 4. Scope

This card may modify:

1. [`../../src/data`](../../src/data)
2. [`../../src/selector`](../../src/selector)
3. [`../../src/broker`](../../src/broker)
4. [`../../src/backtest`](../../src/backtest)
5. [`../../tests`](../../tests)
6. [`../../docs/reference`](../../docs/reference)
7. [`../../docs/spec/v0.01-plus`](../../docs/spec/v0.01-plus)

This card explicitly does not:

1. reopen new provider research
2. change the Phase 7 local-first direction
3. reactivate legacy `IRS / MSS`
4. promote any sidecar research result into runtime

## 5. Audit Targets

This card must explicitly check at least:

1. assumptions that industry semantics still strictly equal `SW2021`
2. assumptions that `l1_sw_industry_member` is still the active runtime contract
3. assumptions that price limits still come from an online fact table
4. assumptions that `raw_daily_basic` is still a mainline hard dependency
5. assumptions that online sources still outrank local sources
6. docs that still describe an old contract while code already runs a new contract

## 6. Deliverables

This card is complete only when it leaves:

1. a formal residual-audit record
2. a residual-assumption checklist
3. a remediation checklist, if any residuals remain
4. updated truthful operating wording
5. an explicit statement of which later packages are now unblocked

## 7. Acceptance Criteria

1. the active runtime contract and the active runbook agree
2. old contract assumptions remain only in migration compatibility or historical records
3. no active doc still presents a retired contract as the live truth
4. `preflight` passes
