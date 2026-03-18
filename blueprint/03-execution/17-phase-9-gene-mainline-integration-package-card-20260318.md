# Phase 9 Gene Mainline Integration Package Card

- Status: `Planned`
- Date: `2026-03-18`
- Type: `mainline migration package`
- Scope: `formal Gene runtime integration boundary`

## 1. Goal

This package answers one question:

`after GX4 ~ GX8 have hardened Gene semantics, which Gene outputs may be formally promoted from sidecar into current mainline runtime behavior, in what order, and under what rollback boundary?`

It does not assume that `Gene` should become a full runtime gate.
It defines the formal promotion boundary and the proof required before any runtime cutover.

## 2. Why This Package Exists

The current truthful boundary is still:

`Gene = sidecar / dashboard / attribution only`

That boundary was correct when:

1. `trend_level` was still single-layer proxy
2. `mainstream / countertrend` was still proxy
3. `2B` used fixed short window semantics
4. `1-2-3` still behaved like a three-wave approximation

After `GX4 ~ GX7`, and with `GX8` now opened as the final trend-hierarchy hard problem, the question is no longer whether Gene has value.
The new question is:

`what is the smallest truthful subset of Gene that can be promoted into mainline runtime without turning Gene into an ungoverned "new boss indicator"?`

## 3. Hard Dependency Gate

This package may be opened now, but may not declare runtime promotion complete until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) is completed
2. [`19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](../../gene/03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md) is completed or formally ruled non-blocking
3. `Gene` runtime candidate subset is frozen in a formal governance document
4. end-to-end replay proves improvement over the current truthful baseline

Without all four conditions, `Gene` remains sidecar only.

## 4. Formal Promotion Order

This package freezes the only allowed promotion order:

1. `shadow / annotation only`
2. `negative filter only`
3. `sizing or exit modulation`
4. `full runtime hard-gate` only if all earlier layers fail to be sufficient and a new explicit package says so

Current status before this package starts:

1. step `1` is already true
2. steps `2 ~ 4` remain unapproved

## 5. Candidate Runtime Subset

The initial candidate subset is intentionally narrow.
At minimum, this package must evaluate whether the following may enter runtime:

1. `duration_percentile`
2. `current_wave_age_band`
3. `wave_role`
4. `reversal_state`
5. `context_trend_direction_before`

The following are frozen as non-default unless explicit evidence later proves otherwise:

1. `mirror_gene_rank` as a direct runtime gate
2. `conditioning` buckets as a direct runtime gate
3. any composite `gene_score` as a default hard filter

## 6. Package Decomposition

### 6.1 Phase 9A

`Gene promoted subset freeze`

This sub-phase must answer:

1. which fields are runtime candidates
2. which fields remain sidecar only
3. which fields are permanently forbidden from default runtime use

### 6.2 Phase 9B

`Gene runtime integration validation`

This sub-phase must run:

1. negative-filter replay
2. optional sizing/exit modulation replay
3. comparative validation against current truthful baseline
4. attribution on gain/loss source, not just headline return

### 6.3 Phase 9C

`promotion ruling or retention ruling`

This sub-phase must produce one of only three outputs:

1. `promote narrow Gene subset`
2. `retain Gene as sidecar only`
3. `defer and open a smaller follow-up package`

## 7. Non-Goals

This package explicitly does not:

1. replace `BOF baseline` with a Gene-native entry engine
2. reactivate legacy `IRS-lite / MSS-lite`
3. promote all Gene labels into runtime switches
4. verbally declare that four-battlefield integration has already reached runtime cutover

## 8. Deliverables

This package is complete only when it leaves:

1. a formal promoted-subset freeze
2. replay evidence and comparative metrics
3. a runtime ruling record
4. an updated operating runbook if promotion happens
5. an explicit rollback target

## 9. Acceptance Criteria

1. the promoted subset, if any, is smaller than the full Gene surface
2. replay proves the subset improves behavior without destroying traceability
3. no uncoded human interpretation leaks into runtime
4. rollback to `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only` remains possible
5. no promotion is considered real until a formal closeout record says so
