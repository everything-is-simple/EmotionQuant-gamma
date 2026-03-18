# Phase 10 BOF Risk-Unit Lifecycle Package Card

- Status: `Planned`
- Date: `2026-03-18`
- Type: `cross-battlefield mainline migration package`
- Scope: `BOF entry retained, but sizing / exit / per-symbol state / Gene warning are rebuilt into one governed runtime package`

## 1. Goal

This package answers one question:

`can the current mainline be upgraded from "BOF baseline + fixed notional + full exit" into a risk-unit lifecycle trading system that still keeps BOF as entry, but formalizes stop, time-stop, scale-out, Gene warning, and per-symbol discipline?`

The purpose is not to replace BOF.
The purpose is to replace the current overly flat post-entry lifecycle with a truthful trading model.

## 2. Why This Package Exists

The current truthful runtime is still:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL`

That is stable and replayable, but it does not yet express the user's actual trading model:

1. `T+0 BOF signal-day low` as the initial structural stop anchor
2. `T+1 open` as the executed entry and therefore the true locked-in risk point
3. point-stop and time-stop as non-negotiable failure exits
4. half-off at `+1R`, then trailing management of the remaining half
5. daily Gene lifespan re-evaluation as warning layer
6. per-symbol trade-state downgrade / recovery discipline

That means the gap is no longer "how to detect BOF".
The gap is:

`how to run the trade truthfully after the BOF entry appears`

## 3. Battlefield Ownership

This package spans four battlefields, but belongs to the first battlefield because it changes default runtime behavior.

### 3.1 Second battlefield ownership

The second battlefield still owns:

1. `BOF` as the entry family
2. signal provenance and trigger truth

This package does not reopen the question:

`what to buy / when to buy`

### 3.2 Third battlefield ownership

The third battlefield contributes:

1. risk-unit sizing semantics
2. half-off / remainder management
3. per-symbol downgrade ladder
4. test/paper/observe discipline

### 3.3 Fourth battlefield ownership

The fourth battlefield contributes:

1. lifespan warning
2. current-wave context
3. daily sidecar re-evaluation

Gene may only enter runtime here through the formal `Phase 9` boundary, not by verbal shortcut.

## 4. Formal Design Translation

The trading model to be evaluated in this package is frozen as follows.

### 4.1 Entry anchor

1. `T+0` generates `BOF` signal
2. the `T+0 low` becomes the initial structural stop anchor
3. `T+1 open` remains the actual entry price

### 4.2 Risk unit

The package must formalize:

`1R = executed entry price + fees - initial stop anchor`

This risk unit becomes the base unit for:

1. position sizing
2. first partial take-profit
3. later trailing logic

### 4.3 Structural failure stop

The package must test the rule:

1. if post-entry price breaches the initial stop anchor
2. the trade is treated as failed
3. liquidation happens on the next trade-day open

The exact day-boundary semantics must be frozen in code and report output, not inferred verbally.

### 4.4 Time stop

The package must test the rule:

1. if the initial stop has not failed
2. but the position experiences two consecutive non-rising closes
3. then the trade is liquidated on the third trade-day open

### 4.5 Partial profit and trailing remainder

The package must test the rule:

1. once unrealized profit reaches `+1R`
2. half the position is closed
3. the remaining half is managed with trailing logic

### 4.6 Gene warning

The package must test whether daily Gene reassessment may act as:

1. warning / dashboard signal
2. negative filter on new risk expansion
3. optional exit-preparation signal

It may not be treated as a free-form human override.

### 4.7 Per-symbol discipline ladder

The package must formalize a per-symbol operating ladder:

1. `TRADE`
2. `CAUTIOUS_TRADE`
3. `PAPER_ONLY`
4. `OBSERVE_ONLY`

And must define:

1. downgrade triggers
2. recovery triggers
3. reset window, currently proposed as `120` calendar days / trade-plan review window

## 5. Hard Dependencies

This package may be opened now, but may not claim runtime promotion complete until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) is completed
2. [`17-phase-9-gene-mainline-integration-package-card-20260318.md`](./17-phase-9-gene-mainline-integration-package-card-20260318.md) has frozen the allowed Gene runtime subset
3. `Phase 10` contract and state-machine changes are replayable
4. rollback to the current truthful baseline remains intact

## 6. Package Decomposition

### 6.1 Phase 10A

`risk-unit lifecycle contract freeze`

This sub-phase must freeze:

1. stop anchor semantics
2. `1R` semantics
3. time-stop semantics
4. half-off semantics
5. trailing remainder semantics

### 6.2 Phase 10B

`broker lifecycle extension`

This sub-phase must implement:

1. multi-leg exit support needed by the package
2. explicit stop/time-stop/partial/trailing reason codes
3. clear order / trade / lifecycle trace outputs

### 6.3 Phase 10C

`symbol discipline state machine`

This sub-phase must add:

1. per-symbol operating state
2. downgrade rules
3. recovery rules
4. paper-only and observe-only semantics

### 6.4 Phase 10D

`integrated replay and promotion ruling`

This sub-phase must decide:

1. promote
2. retain as research
3. split into narrower follow-up packages

## 7. Non-Goals

This package explicitly does not:

1. replace BOF with a new entry family
2. reopen legacy `IRS-lite / MSS-lite`
3. promote the full Gene surface into runtime
4. verbally cut over the system without replay and formal gate

## 8. Deliverables

This package is complete only when it leaves:

1. a formal contract freeze
2. runtime state-machine design
3. replay evidence
4. promotion or rejection record
5. updated operating runbook if promoted

## 9. Acceptance Criteria

1. the new lifecycle semantics are traceable at order/trade/report level
2. the package improves behavior without turning runtime into discretionary free-form judgment
3. Gene stays within the subset allowed by `Phase 9`
4. rollback to the current truthful baseline remains possible
5. no promotion is real until a formal closeout record says so
