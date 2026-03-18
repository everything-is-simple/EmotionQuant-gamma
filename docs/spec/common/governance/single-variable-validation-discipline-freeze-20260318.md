# Single-Variable Validation Discipline Freeze

## Position

This file freezes one operating rule for all future mainline promotion work:

`every formal validation may change only one primary variable at a time; combination validation is forbidden until each component variable has already passed isolated validation.`

The answer is:

`mandatory`

---

## Frozen Rule

As of `2026-03-18`, the system freezes the following discipline:

1. Any idea must first appear as a `single-variable candidate`.
2. Each formal validation round may modify only one primary variable.
3. Everything else must stay fixed to the current `validated baseline`.
4. Combination validation is allowed only after each component variable has already passed isolated validation.
5. Promotion is allowed only after isolated validation and, when needed, later combination validation both have formal records.

---

## Four Candidate States

Every future candidate must be placed into one of these four states:

1. `validated baseline`
   Current approved operating baseline.
2. `single-variable candidate`
   The one variable being formally tested in the current round.
3. `pending candidate`
   Not yet opened for validation; queued only.
4. `combination candidate`
   A composed package whose components have already passed isolated validation.

The following are explicitly forbidden:

1. Testing two or more primary changes in one validation round.
2. Quietly mixing `pending candidate` variables into a live experiment.
3. Treating a better-looking combined result as evidence for each component variable.

---

## Formal Order

The formal order is fixed as:

1. freeze the current `validated baseline`
2. open one `single-variable` card
3. run isolated validation
4. write record and ruling
5. either promote to `validated baseline` or reject
6. only then open a `combination candidate`

Without step `4`, steps `5` and `6` do not exist.

---

## Battlefield Constraints

### First Battlefield

The first battlefield must:

1. state the current validated runtime baseline
2. state the single variable under test
3. state the rollback target

### Second Battlefield

If the second battlefield reopens, it may not change more than one of:

1. entry family
2. quality split
3. cooldown semantics
4. exit semantics

### Third Battlefield

If the third battlefield reopens, it may not change more than one of:

1. sizing formula
2. stop semantics
3. partial-exit family
4. symbol discipline state machine

### Fourth Battlefield

The fourth battlefield may not change more than one of:

1. trend hierarchy
2. runtime Gene subset
3. warning-to-filter semantics
4. mirror or conditioning promotion

Definition repair must come before runtime promotion.

---

## Immediate Impact

This discipline applies immediately to:

1. `Phase 9 / Gene mainline integration package`
2. `Phase 10 / BOF risk-unit lifecycle package`
3. any future targeted reopening in `normandy/`
4. any future targeted reopening in `positioning/`

In practice this means:

1. `Phase 9` may not push multiple Gene fields into runtime in one shot.
2. `Phase 10` may not test `1R + time stop + half-off + trailing + symbol ladder + Gene warning` as one undifferentiated bundle.

---

## Acceptance Standard

A package follows this discipline only if it explicitly states:

1. the current `validated baseline`
2. the one primary variable changed in this round
3. the `pending variables` forbidden from joining this round
4. the rollback target
5. a record that can answer: `what exact single variable changed?`

---

## One-Line Conclusion

The system no longer accepts:

`many ideas changed together, result looks better, therefore promote`

The frozen operating rule is:

`first isolate, then combine; first validate, then promote; validated and pending must remain strictly separated`
