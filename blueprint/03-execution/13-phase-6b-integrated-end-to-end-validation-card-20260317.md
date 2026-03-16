# Phase 6B Integrated End-to-End Validation Card

**Status**: `Completed`  
**Date**: `2026-03-17`  
**Scope**: `First battlefield / Phase 6B / integrated end-to-end validation`

---

## 1. Goal

`Phase 6B` does one thing:
run a formal integrated replay and gate decision for the frozen unified default-system candidate defined in `Phase 6A`.

---

## 2. Validation Window

1. `2026-01-05` to `2026-02-24`
2. full window plus `front_half_window` and `back_half_window`
3. source DB: `G:\EmotionQuant_data\emotionquant.duckdb`

---

## 3. Formal Evidence

1. `docs/spec/v0.01-plus/evidence/phase6_integrated_validation_legacy_phase6_unified_default_candidate_w20260105_20260224_t181741__integrated_validation.json`
2. `docs/spec/v0.01-plus/records/v0.01-plus-phase-6b-integrated-end-to-end-validation-20260317.md`

---

## 4. Formal Outcome

1. `decision = go_to_phase_6c`
2. `diagnosis = candidate_boundary_and_runtime_validated`
3. `boundary_audit_passed = true`
4. `gene_sidecar_ready = true`
5. `retired_runtime_boundary_held = true`
6. `trace_complete = true`
7. `window_slice_complete = true`

Full-window comparison:

1. raw legacy control: `trade_count=7`, `EV=-0.019861`, `PF=0.289672`, `MDD=0.011477`
2. unified candidate: `trade_count=13`, `EV=-0.018301`, `PF=0.652769`, `MDD=0.024216`
3. candidate vs raw legacy: `trade_count_ratio=1.8571`, `profit_factor_delta=+0.3631`, `expected_value_delta=+0.001559`

---

## 5. Boundary Notes

1. `Gene` remains shadow-only; no runtime hard gate was promoted.
2. legacy `IRS-lite / MSS-lite` runtime semantics remain retired inside the unified candidate.
3. `Phase 6B` validates the candidate boundary and runtime behavior, but does not itself declare final default-runtime promotion.

---

## 6. Next Step

The next fixed sub-card is:

`Phase 6C / unified operating runbook refresh`
