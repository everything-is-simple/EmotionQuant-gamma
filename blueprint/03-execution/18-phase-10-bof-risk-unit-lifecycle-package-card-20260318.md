# Phase 10 BOF Risk-Unit Lifecycle Package Card

- Status: `Planned`
- Date: `2026-03-18`
- Type: `cross-battlefield mainline migration package`
- Scope: `BOF entry retained, but post-entry lifecycle rebuilt into a governed runtime package`

## 1. Goal

This package answers one question:

`can the current mainline be upgraded from "BOF baseline + fixed notional + full exit" into a risk-unit lifecycle trading system that still keeps BOF as entry, but formalizes stop, time-stop, scale-out, Gene warning, and per-symbol discipline?`

The purpose is not to replace BOF.
The purpose is to rebuild what happens truthfully after BOF entry appears.

## 2. Why This Package Exists

The current truthful runtime is still:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL`

That is stable and replayable, but it does not yet express the desired trading model:

1. `T+0 BOF signal-day low` as initial structural stop anchor
2. `T+1 open` as executed entry and therefore true locked-in risk point
3. structural point-stop and time-stop as non-negotiable failure exits
4. half-off at `+1R`, then trailing management of the remaining half
5. daily Gene lifespan re-evaluation as warning layer
6. per-symbol trade-state downgrade and recovery discipline

The gap is no longer `how to detect BOF`.
The gap is:

`how to run the trade truthfully after the BOF entry appears`

## 3. Validation Discipline

This package must obey [`single-variable-validation-discipline-freeze-20260318.md`](../../docs/spec/common/governance/single-variable-validation-discipline-freeze-20260318.md).

That means:

1. `validated baseline` remains `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
2. each formal Phase 10 validation round may modify only one primary lifecycle variable
3. the full desired trading style may not be tested as one undifferentiated bundle on the first pass

Explicitly forbidden in the first validation rounds:

1. `1R + time stop + half-off + trailing` all tested together
2. `Gene warning + symbol ladder + trailing` all tested together
3. entry changes mixed into lifecycle validation

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

Gene may only enter runtime here through the formal `Phase 9` boundary, not by verbal shortcut.

## 5. Formal Design Translation

The trading model to be evaluated in this package is frozen as follows.

### 5.1 Entry anchor

1. `T+0` generates `BOF` signal
2. the `T+0 low` becomes the initial structural stop anchor
3. `T+1 open` remains the actual entry price

### 5.2 Risk unit

The package must formalize:

`1R = executed entry price + fees - initial stop anchor`

This risk unit becomes the base unit for:

1. position sizing
2. first partial take-profit
3. later trailing logic

### 5.3 Structural failure stop

The package must test the rule:

1. if post-entry price breaches the initial stop anchor
2. the trade is treated as failed
3. liquidation happens on the next trade-day open

### 5.4 Time stop

The package must test the rule:

1. if the initial stop has not failed
2. but the position experiences two consecutive non-rising closes
3. then the trade is liquidated on the third trade-day open

### 5.5 Partial profit and trailing remainder

The package must test the rule:

1. once unrealized profit reaches `+1R`
2. half the position is closed
3. the remaining half is managed with trailing logic

### 5.6 Gene warning

The package must test whether daily Gene reassessment may act as:

1. warning or dashboard signal
2. negative filter on new risk expansion
3. optional exit-preparation signal

### 5.7 Per-symbol discipline ladder

The package must formalize:

1. `TRADE`
2. `CAUTIOUS_TRADE`
3. `PAPER_ONLY`
4. `OBSERVE_ONLY`

And define:

1. downgrade triggers
2. recovery triggers
3. reset window, currently proposed as `120` calendar days or trade-plan review window

## 6. Hard Dependencies

This package may be opened now, but may not claim runtime promotion complete until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) is completed
2. [`17-phase-9-gene-mainline-integration-package-card-20260318.md`](./17-phase-9-gene-mainline-integration-package-card-20260318.md) has frozen the allowed Gene runtime subset
3. Phase 10 contract and state-machine changes are replayable
4. rollback to the current truthful baseline remains intact

## 7. Package Decomposition

### 7.1 Phase 10A

`risk-unit lifecycle contract freeze`

This sub-phase must freeze:

1. stop anchor semantics
2. `1R` semantics
3. time-stop semantics
4. half-off semantics
5. trailing remainder semantics

### 7.2 Phase 10B

`single-variable lifecycle validation`

This sub-phase must validate one item at a time, for example:

1. structural stop only
2. time stop only
3. half-off at `+1R` only
4. trailing remainder only

### 7.3 Phase 10C

`symbol discipline state machine`

This sub-phase must add:

1. per-symbol operating state
2. downgrade rules
3. recovery rules
4. paper-only and observe-only semantics

This sub-phase may not start until the earlier lifecycle variables have isolated evidence.

### 7.4 Phase 10D

`combination lifecycle replay`

This sub-phase may open only after the component lifecycle variables have already passed isolated validation.

### 7.5 Phase 10E

`integrated promotion ruling`

This sub-phase must decide:

1. promote
2. retain as research
3. split into narrower follow-up packages

## 8. Non-Goals

This package explicitly does not:

1. replace BOF with a new entry family
2. reopen legacy `IRS-lite / MSS-lite`
3. promote the full Gene surface into runtime
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
3. Gene stays within the subset allowed by `Phase 9`
4. rollback to the current truthful baseline remains possible
5. no promotion is real until a formal closeout record says so
