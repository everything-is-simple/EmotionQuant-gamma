# Current Mainline Operating Runbook

**Status**: `Active`  
**Date**: `2026-03-19`  
**Scope**: `Current mainline operating chain, allowed switches, intervention boundary, and rollback rules`

---

## 1. Purpose

This runbook does one thing:
state the truthful operating path for the current mainline after the current-round `Phase 9D` ruling deferred package promotion.

It is not:

1. a research memo
2. an algorithm design spec
3. a verbal shortcut for unapproved Gene runtime use

---

## 2. Current Truth

The currently allowed operating path is:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

At the same time, the following are also fixed truths:

1. `v0.01-plus` is the current governance mainline
2. the entry backbone has **not** been switched away from `legacy_bof_baseline`
3. there is currently **no** package-promoted Gene runtime hook
4. `duration_percentile`, `reversal_state`, and `context_trend_direction_before` are validated isolated winners, but are not default runtime-promoted
5. `wave_role` remains `retain_sidecar_only`
6. all Gene outputs remain `sidecar / dashboard / attribution only` at package level
7. legacy `IRS-lite / MSS-lite` runtime semantics remain retired
8. no retained, isolated, or watch research object may be verbally promoted into default runtime behavior

---

## 3. Operating Chain

The current operating chain is:

```text
Selector prefilter
-> BOF baseline entry
-> FIXED_NOTIONAL_CONTROL
-> FULL_EXIT_CONTROL
-> Broker execution
-> Backtest / Report / Evidence
```

What may run alongside the chain as sidecar only:

1. `duration_percentile`
2. `reversal_state`
3. `current_context_trend_direction`
4. `wave_role`
5. `current_wave_age_band`
6. `market / industry mirror ranks`
7. `gene conditioning readout`

These sidecars may inform observation, attribution, and post-trade review, but may not directly rewrite:

1. entry
2. sizing
3. exit
4. runtime filtering

There is currently no Gene runtime exception.

---

## 4. Allowed Runtime Switches

The allowed runtime switches are fixed as:

1. `entry family = BOF baseline only`
2. `sizing baseline = FIXED_NOTIONAL_CONTROL`
3. `exit baseline = FULL_EXIT_CONTROL`
4. `Gene runtime exception = none`
5. `SINGLE_LOT_CONTROL = floor sanity only`
6. `duration_percentile = validated isolated winner, but not current default runtime switch`
7. `reversal_state = validated isolated winner, but not current default runtime switch`
8. `current_context_trend_direction_before = validated isolated winner, but not current default runtime switch`
9. `wave_role == COUNTERTREND = retain_sidecar_only`

---

## 5. Forbidden Runtime Switches

The following remain forbidden unless a new formal package and gate explicitly promote them:

1. turning legacy `IRS-lite / MSS-lite` back on as default runtime layers
2. promoting `duration_percentile`, `reversal_state`, or `context_trend_direction_before` into default runtime without the missing follow-up evidence now opened under `Phase 9`
3. translating `wave_role`, `current_wave_age_band`, any mirror score, any conditioning bucket, or any `gene_score` into a default runtime filter
4. declaring that a multi-field Gene combination has already been promoted without formal combination replay evidence
5. promoting `TRAIL_SCALE_OUT_25_75` or any retained partial-exit family into default exit behavior
6. promoting any `Normandy` watch or retained branch into default entry behavior

---

## 6. Pre-Run Checklist

Before any formal mainline run, the minimum checklist is:

1. run `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile hook`
2. confirm the main database is `G:\EmotionQuant_data\emotionquant.duckdb`
3. confirm the run target is still:
   `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
4. confirm no Gene sidecar object was manually turned into a runtime switch
5. confirm `duration_percentile`, `reversal_state`, and `current_context_trend_direction_before` remain off as default runtime switches
6. confirm rollback remains identical to the current truthful path

---

## 7. Human Intervention Boundary

Human intervention is allowed only for:

1. stopping a run because `preflight`, schema, trace, or core contracts failed
2. reviewing sidecar output for attribution and environment interpretation
3. executing already-defined `STOP_LOSS / FORCE_CLOSE` behavior under existing broker semantics
4. recording issues and explicitly preserving `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

Human intervention is forbidden for:

1. manually treating `duration_percentile` as an uncoded runtime filter
2. manually treating `reversal_state` as an uncoded runtime exit hook
3. manually treating `current_context_trend_direction_before` as an uncoded runtime filter
4. temporarily adding retained or watch conclusions into default runtime behavior
5. rewriting sizing or exit semantics because of a small local win sample
6. announcing Gene package promotion before the opened `Phase 9` follow-up cards finish

---

## 8. Reporting Requirements

Every formal run must remain able to answer:

1. was the run still on the BOF baseline entry backbone
2. did `FIXED_NOTIONAL_CONTROL` and `FULL_EXIT_CONTROL` execute as expected
3. did every Gene field remain clearly separated as sidecar rather than runtime logic
4. can any failure be traced back through `run_id / signal_id`

---

## 9. Rollback And Emergency Stop

The current rollback target is fixed as:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

Promotion talk must stop and rollback must be enforced if any of the following happens:

1. the end-to-end operating chain is broken
2. trace, report, or sidecar integrity becomes non-credible
3. any Gene object leaks into runtime filtering, sizing, or hard-gate behavior
4. default runtime semantics change without a formal package and formal gate

---

## 10. Relation To Phase 9

This runbook now serves two purposes:

1. it preserves the truthful BOF baseline entry backbone
2. it records that `Phase 9` is still active and has **not** yet earned package-level Gene runtime promotion

This means:

`Phase 9` currently leaves Gene as sidecar only at package level, while `17.8` and `17.9` are opened to refine the duration axis and the frozen combination surface before any later promotion claim is allowed.`
