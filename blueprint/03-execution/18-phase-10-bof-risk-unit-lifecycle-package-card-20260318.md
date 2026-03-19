# Phase 10 BOF Risk-Unit Lifecycle Package Card

- Status: `Blocked`
- Date: `2026-03-18`
- Type: `cross-battlefield mainline migration package`
- Scope: `BOF entry retained, but post-entry lifecycle rebuilt only after Phase 9 truly closes`

## 1. Goal

This package still answers one question:

`can the current mainline be upgraded from "BOF baseline + fixed notional + full exit" into a risk-unit lifecycle trading system that still keeps BOF as entry, but formalizes stop, time-stop, scale-out, Gene warning, and per-symbol discipline?`

The purpose is not to replace BOF.
The purpose is to rebuild what happens truthfully after BOF entry appears.

## 2. Why This Package Is Not The Next Move

The current truthful runtime is still:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

That is stable and replayable, but it is also intentionally coarse.

Right now, the more urgent unresolved problem is not lifecycle polish.
The more urgent unresolved problem is:

`Gene itself is still too coarse at package level, especially on the lifespan axis and the trend-axis combination surface.`

Therefore `Phase 10` is not the truthful next move.
`Phase 9` must finish Gene refinement first.

## 3. Validation Discipline

This package must obey [`single-variable-validation-discipline-freeze-20260318.md`](../../docs/spec/common/governance/single-variable-validation-discipline-freeze-20260318.md).

That means:

1. `validated baseline` currently remains `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
2. each formal Phase 10 validation round may modify only one primary lifecycle variable
3. the full desired trading style may not be tested as one undifferentiated bundle on the first pass
4. Phase 10 may not quietly absorb unfinished Phase 9 Gene questions

## 4. Battlefield Ownership

This package spans four battlefields, but belongs to the first battlefield because it changes default runtime behavior.

### 4.1 Second battlefield ownership

The second battlefield still owns:

1. `BOF` as the entry family
2. signal provenance and trigger truth

This package does not reopen:

`what to buy / when to buy`

### 4.2 Third battlefield ownership

The third battlefield contributes:

1. risk-unit sizing semantics
2. half-off and remainder management
3. per-symbol downgrade ladder
4. paper-only and observe-only discipline

### 4.3 Fourth battlefield ownership

The fourth battlefield contributes:

1. lifespan warning
2. current-wave context
3. daily sidecar re-evaluation
4. any future Gene runtime subset that may later survive Phase 9 follow-up evidence

For now, Gene still enters Phase 10 only as:

`sidecar only`

## 5. Formal Design Translation

The trading model to be evaluated here remains the same, but this package is blocked from active execution until Phase 9 closes truthfully.

The intended lifecycle topics remain:

1. `T+0 BOF signal-day low` as initial structural stop anchor
2. `T+1 open` as executed entry and therefore true locked-in risk point
3. structural point-stop and time-stop as non-negotiable failure exits
4. half-off at `+1R`, then trailing management of the remaining half
5. daily Gene lifespan re-evaluation as warning layer
6. per-symbol trade-state downgrade and recovery discipline

## 6. Hard Dependencies

This package may not move out of `Blocked` until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) remains completed
2. [`17-phase-9-gene-mainline-integration-package-card-20260318.md`](./17-phase-9-gene-mainline-integration-package-card-20260318.md) reaches truthful package closeout
3. [`17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](./17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md) is completed
4. [`17.9-phase-9f-frozen-combination-replay-card-20260319.md`](./17.9-phase-9f-frozen-combination-replay-card-20260319.md) is completed or formally ruled unnecessary by a later package record
5. the resulting allowed Gene runtime subset, if any, is frozen again in a truthful package-level record
6. rollback to the current truthful baseline remains intact

## 7. Package Decomposition

The intended internal decomposition remains:

1. `Phase 10A = risk-unit lifecycle contract freeze`
2. `Phase 10B = single-variable lifecycle validation`
3. `Phase 10C = symbol discipline state machine`
4. `Phase 10D = combination lifecycle replay`
5. `Phase 10E = integrated promotion ruling`

But none of these sub-phases is the current active move.

## 8. Non-Goals

This package explicitly does not:

1. replace BOF with a new entry family
2. reopen legacy `IRS-lite / MSS-lite`
3. absorb unfinished Phase 9 Gene research by verbal shortcut
4. verbally cut over the system without replay and formal gate

## 9. Deliverables

This package is complete only when it leaves:

1. a formal contract freeze
2. isolated replay evidence for each promoted lifecycle variable
3. combination replay evidence only where justified
4. runtime state-machine design
5. promotion or rejection record
6. updated operating runbook if promoted

## 10. Acceptance Criteria

1. the new lifecycle semantics are traceable at order, trade, and report level
2. the package improves behavior without turning runtime into discretionary free-form judgment
3. Gene stays within the subset truthfully allowed by the finally closed `Phase 9`
4. rollback to the current truthful baseline remains possible
5. no promotion is real until a formal closeout record says so
