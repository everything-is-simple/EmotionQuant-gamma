# Phase 9 Gene Mainline Integration Package Card

- Status: `Active`
- Date: `2026-03-18`
- Type: `mainline migration package`
- Scope: `formal Gene runtime promotion boundary`

## 1. Goal

This package answers one question:

`after GX4 ~ GX8 have hardened Gene semantics, which Gene outputs may be truthfully promoted from sidecar into current mainline runtime behavior, in what order, and under what rollback boundary?`

It does not assume that `Gene` should become a full runtime gate.
It defines the narrowest truthful promotion path.

## 2. Why This Package Exists

The current truthful boundary is still:

`Gene = sidecar / dashboard / attribution only`

That was the correct boundary while Gene semantics were still incomplete.
Now the question is no longer whether Gene has value.
The new question is:

`what is the smallest truthful Gene subset that can enter runtime without turning Gene into an ungoverned new boss indicator?`

## 3. Validation Discipline

This package must obey [`single-variable-validation-discipline-freeze-20260318.md`](../../docs/spec/common/governance/single-variable-validation-discipline-freeze-20260318.md).

That means:

1. `validated baseline` remains `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
2. each formal Phase 9 validation round may promote only one Gene runtime variable
3. multi-field Gene bundles are forbidden until each component field has already passed isolated validation

Explicitly forbidden in the first validation rounds:

1. `duration_percentile + wave_role + reversal_state` tested together
2. `Gene filter + Gene sizing overlay` tested together
3. `mirror + conditioning + age band` tested together

## 4. Hard Dependency Gate

This package may be opened now, but may not declare runtime promotion complete until:

1. [`16-phase-8-data-contract-residual-audit-card-20260318.md`](./16-phase-8-data-contract-residual-audit-card-20260318.md) is completed
2. [`19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](../../gene/03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md) is completed or formally ruled non-blocking
3. the Gene runtime candidate subset is frozen in a formal governance document
4. isolated replay proves improvement over the current validated baseline

Without all four conditions, `Gene` remains sidecar only.

## 5. Promotion Order

The only allowed promotion order is:

1. `shadow / annotation only`
2. `single-variable negative filter`
3. `single-variable sizing or exit modulation`
4. `combination package` only after prior isolated validations succeed
5. `full runtime hard gate` only if a later explicit package says so

Current status before this package starts:

1. step `1` is already true
2. steps `2 ~ 5` remain unapproved

## 6. Candidate Surface

The initial candidate surface is intentionally narrow.
At minimum, this package must examine these fields one by one:

1. `duration_percentile`
2. `current_wave_age_band`
3. `wave_role`
4. `reversal_state`
5. `context_trend_direction_before`

The following are frozen as non-default unless later evidence proves otherwise:

1. `mirror_gene_rank` as a direct runtime gate
2. `conditioning` buckets as a direct runtime gate
3. any composite `gene_score` as a default hard filter

## 7. Package Decomposition

### 7.1 Phase 9A

`Gene promoted subset freeze`

This sub-phase must answer:

1. which fields are runtime candidates
2. which fields remain sidecar only
3. which fields are permanently forbidden from default runtime use

Current `Phase 9A` ruling:

1. `duration_percentile` is the only opened `single-variable candidate`
2. its allowed next-step role is `negative filter only`
3. `current_wave_age_band`, `wave_role`, `reversal_state`, `context_trend_direction_before`, `mirror`, `conditioning`, and any composite `gene_score` remain outside the first runtime round

Formal outputs:

1. [`17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md`](./17.1-phase-9a-gene-promoted-subset-freeze-card-20260318.md)
2. [`phase-9a-gene-promoted-subset-freeze-evidence-20260318.md`](./evidence/phase-9a-gene-promoted-subset-freeze-evidence-20260318.md)
3. [`phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./records/phase-9a-gene-promoted-subset-freeze-record-20260318.md)
4. [`v0.01-plus-phase-9a-gene-promoted-subset-freeze-20260318.md`](../../docs/spec/v0.01-plus/governance/v0.01-plus-phase-9a-gene-promoted-subset-freeze-20260318.md)
5. [`v0.01-plus-phase-9a-gene-promoted-subset-freeze-20260318.md`](../../docs/spec/v0.01-plus/records/v0.01-plus-phase-9a-gene-promoted-subset-freeze-20260318.md)

### 7.2 Phase 9B

`single-variable Gene runtime validation`

This sub-phase must run isolated validation rounds such as:

1. `duration_percentile` as negative filter, alone
2. `wave_role` as negative filter, alone
3. `reversal_state` as exit-preparation signal, alone

Current opened round:

1. [`17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md`](./17.2-phase-9b-isolated-duration-percentile-validation-card-20260318.md)
2. completed first isolated win = `duration_percentile as negative filter, alone`
3. current isolated ruling = `promote_duration_percentile_negative_filter`

### 7.3 Phase 9C

`combination candidate only after isolated wins`

This sub-phase may open only after each component field has already passed isolated validation.
It must explicitly state which pre-validated fields are now being combined.

### 7.4 Phase 9D

`promotion ruling or retention ruling`

This sub-phase must produce one of only three outputs:

1. `promote narrow Gene subset`
2. `retain Gene as sidecar only`
3. `defer and open a smaller follow-up package`

## 8. Non-Goals

This package explicitly does not:

1. replace `BOF baseline` with a Gene-native entry engine
2. reactivate legacy `IRS-lite / MSS-lite`
3. promote all Gene labels into runtime switches
4. verbally declare that four-battlefield integration has already reached runtime cutover

## 9. Deliverables

This package is complete only when it leaves:

1. a formal promoted-subset freeze
2. isolated replay evidence per promoted field
3. combination replay evidence only where justified
4. a runtime ruling record
5. an updated operating runbook if promotion happens
6. an explicit rollback target

## 10. Acceptance Criteria

1. the promoted subset, if any, is smaller than the full Gene surface
2. replay proves the subset improves behavior without destroying traceability
3. no uncoded human interpretation leaks into runtime
4. rollback to `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only` remains possible
5. no promotion is considered real until a formal closeout record says so
