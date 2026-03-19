# Phase 9 Gene Mainline Integration Package Card

- Status: `Active`
- Date: `2026-03-18`
- Type: `mainline refinement package`
- Scope: `Gene refinement first before any truthful runtime promotion`

## 1. Goal

This package answers one question:

`after GX4 ~ GX8 have hardened Gene semantics, which Gene outputs may truthfully move from sidecar into current mainline runtime behavior, in what order, and under what rollback boundary?`

It still does **not** assume that `Gene` should become a full runtime gate.
But it also no longer pretends that the package has already truthfully closed.

## 2. Why This Package Is Still Open

At package open, the truthful boundary was:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

That remains the truthful current runtime boundary today.

The package has already identified meaningful candidates, but it has **not** yet earned package closeout because:

1. `duration_percentile` has not yet completed a truthful, book-aligned lifespan distribution rerun
2. the frozen `Phase 9C` combinations have not completed formal replay
3. package-level promotion would therefore jump ahead of the evidence needed for a refined Gene conclusion

Current package truth after the current `Phase 9D` ruling is:

`Phase 9 stays active, current runtime remains baseline + Gene sidecar only, and Gene refinement must continue before any package-level promotion claim.`

## 3. Validation Discipline

This package must obey [`single-variable-validation-discipline-freeze-20260318.md`](../../docs/spec/common/governance/single-variable-validation-discipline-freeze-20260318.md).

That means:

1. `validated baseline` remains `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
2. each formal Phase 9 validation round may change only one primary Gene runtime variable
3. multi-field Gene bundles are forbidden until each component field has already passed isolated validation
4. package closeout may not jump ahead of missing threshold-sweep or combination-replay evidence

Explicitly forbidden:

1. `duration_percentile + wave_role + reversal_state` tested together
2. `Gene filter + Gene sizing overlay` tested together
3. `mirror + conditioning + age band` tested together
4. verbally treating isolated winners as if they had already become package-promoted runtime logic

## 4. Hard Dependency Gate

This package may remain open now, but may not declare runtime promotion complete until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) is completed
2. [`19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](../../gene/03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md) is completed or formally ruled non-blocking
3. the Gene runtime candidate subset is frozen in a formal governance document
4. isolated replay proves improvement over the current validated baseline
5. any claimed entry-side Gene promotion is supported by the missing duration-sweep and/or combination-replay evidence it actually depends on

Without all five conditions, `Gene` remains sidecar only at package level.

## 5. Promotion Order

The only allowed promotion order is:

1. `shadow / annotation only`
2. `single-variable negative filter`
3. `single-variable sizing or exit modulation`
4. `combination package` only after prior isolated validations succeed
5. `full runtime hard gate` only if a later explicit package says so

Current truthful status:

1. step `1` is already true
2. parts of step `2` and step `3` have isolated winners
3. no step has yet earned package-level default runtime promotion

## 6. Current Candidate Surface

The package has already passed its first isolated-screening round.
The current truthful runtime-candidate surface is:

1. `duration_percentile`
2. `reversal_state`
3. `context_trend_direction_before`

The following remain frozen outside the active combination surface:

1. `current_wave_age_band = shadow-only`
2. `wave_role = retain_sidecar_only`
3. `mirror_gene_rank` as a direct runtime gate
4. `conditioning` buckets as a direct runtime gate
5. any composite `gene_score` as a default hard filter

## 7. Package Decomposition

### 7.1 Phase 9A

`Gene promoted subset freeze`

This sub-phase answered:

1. which fields are runtime candidates
2. which fields remain sidecar only
3. which fields are permanently forbidden from default runtime use

Current `Phase 9A` status:

1. [`17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md`](./17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md) = `Completed`
2. the package later widened the truthful candidate surface through completed isolated rounds
3. `Gene sidecar only` remains the package-level baseline until later evidence proves otherwise

### 7.2 Phase 9B

`single-variable Gene runtime validation`

Current completed isolated rounds:

1. [`17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md`](./17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md)
2. isolated ruling = `promote_duration_percentile_negative_filter`
3. the historical isolated round tested `p95`
4. `p65` was reviewed only as legacy sensitivity reference
5. [`17.3-phase-9b-isolated-wave-role-validation-card-20260318.md`](./17.3-phase-9b-isolated-wave-role-validation-card-20260318.md)
6. isolated ruling = `retain_sidecar_only`
7. [`17.4-phase-9b-isolated-reversal-state-validation-card-20260318.md`](./17.4-phase-9b-isolated-reversal-state-validation-card-20260318.md)
8. isolated ruling = `promote_reversal_state_exit_preparation`
9. [`17.5-phase-9b-isolated-context-trend-direction-before-validation-card-20260318.md`](./17.5-phase-9b-isolated-context-trend-direction-before-validation-card-20260318.md)
10. isolated ruling = `promote_context_trend_direction_negative_guard`
11. the package therefore has `3` isolated winners:
    `duration_percentile`, `reversal_state`, and `context_trend_direction_before`

Important governance note:

`isolated win != package-level default runtime promotion`

### 7.3 Phase 9C

`formal combination freeze before any combination replay`

Current freeze boundary:

1. allowed source fields = `duration_percentile`, `reversal_state`, `context_trend_direction_before`
2. allowed exact combinations = `duration_percentile + reversal_state`, `duration_percentile + context_trend_direction_before`, `reversal_state + context_trend_direction_before`, and `duration_percentile + reversal_state + context_trend_direction_before`
3. explicitly forbidden from the Phase 9C surface = `wave_role`, `current_wave_age_band`, `mirror`, `conditioning`, and `gene_score`
4. no runtime / SQL alias expansion is allowed inside this card; it must use canonical field names only

Current `Phase 9C` ruling:

1. [`17.6-phase-9c-formal-combination-freeze-card-20260318.md`](./17.6-phase-9c-formal-combination-freeze-card-20260318.md) = `Completed`
2. formal output = `no combination replay opened`
3. `Phase 9C has no formal combination winner`
4. this freeze result is now consumed by later smaller follow-up cards rather than being treated as package closeout proof

### 7.4 Phase 9D

`promotion ruling or retention ruling`

This sub-phase still only allows:

1. `promote narrow Gene subset`
2. `retain Gene as sidecar only`
3. `defer and open a smaller follow-up package`

Current `Phase 9D` ruling:

1. [`17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md`](./17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md) = `Completed`
2. current output = `defer and open a smaller follow-up package`
3. current truthful runtime remains:
   `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
4. `Phase 10` remains blocked
5. package closeout remains pending

### 7.5 Phase 9E

`book-aligned duration / lifespan distribution rerun`

This sub-phase now becomes the immediate next truthful move.

It must answer:

1. whether the historical `p95` isolated win survives only as legacy archive or still has forward meaning
2. whether the remediated duration axis, when read as a continuous quartile distribution of intermediate mainstream waves, still supports runtime candidacy
3. whether any truthful runtime interpretation sits at a quartile boundary rather than a tail threshold
4. whether duration should continue forward into `17.9` at all

Current status:

1. [`17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](./17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md) = `Active`

### 7.6 Phase 9F

`frozen combination replay`

This sub-phase exists because the package still lacks formal replay across the `Phase 9C` frozen surface.

It may only consume:

1. the exact frozen combinations from `17.6`
2. the duration-threshold conclusion that comes out of `17.8`

Current status:

1. [`17.9-phase-9f-frozen-combination-replay-card-20260319.md`](./17.9-phase-9f-frozen-combination-replay-card-20260319.md) = `Planned`
2. current gate = `blocked-by-17.8`

## 8. Non-Goals

This package explicitly does not:

1. replace `BOF baseline` with a Gene-native entry engine
2. reactivate legacy `IRS-lite / MSS-lite`
3. verbally promote isolated winners into runtime without the missing evidence they depend on
4. declare `Phase 10` active before `Phase 9` finishes truthful Gene refinement

## 9. Deliverables

This package is complete only when it leaves:

1. a formal promoted-subset freeze
2. isolated replay evidence per candidate field
3. duration-sweep evidence if duration promotion is still under discussion
4. combination replay evidence where that discussion actually depends on combinations
5. a truthful package-level ruling record
6. an updated operating runbook if and only if package promotion truly happens
7. an explicit rollback target

## 10. Acceptance Criteria

1. the promoted subset, if any, is smaller than the full Gene surface
2. replay proves the subset improves behavior without destroying traceability
3. no uncoded human interpretation leaks into runtime
4. rollback to `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only` remains possible
5. no package promotion is considered real until the missing duration/combination evidence has been settled truthfully
