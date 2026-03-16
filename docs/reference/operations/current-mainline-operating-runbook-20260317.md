# Current Mainline Operating Runbook

**Status**: `Active`  
**Date**: `2026-03-17`  
**Scope**: `Current mainline operating chain, allowed switches, intervention boundary, and rollback rules`

---

## 1. Purpose

This runbook does one thing:
state the truthful operating path for the current mainline while `Phase 6` is still in migration.

It is not:

1. a research memo
2. an algorithm design spec
3. a verbal shortcut for unapproved promotion

---

## 2. Current Truth

The currently allowed operating path is still:

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL`

At the same time, the following are also fixed truths:

1. `v0.01-plus` is the current governance mainline
2. the production default runtime has **not** yet been switched away from `legacy_bof_baseline`
3. `Gene` may appear only as `context sidecar / dashboard / attribution`
4. legacy `IRS-lite / MSS-lite` runtime semantics remain retired
5. no retained or watch research object may be verbally promoted into default runtime behavior

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

1. `stock self-history tags`
2. `market / industry mirror ranks`
3. `gene conditioning readout`

These sidecars may inform observation, attribution, and post-trade review, but may not directly rewrite:

1. entry
2. sizing
3. exit
4. runtime filtering

---

## 4. Allowed Runtime Switches

The allowed runtime switches are fixed as:

1. `entry family = BOF baseline only`
2. `sizing baseline = FIXED_NOTIONAL_CONTROL`
3. `exit baseline = FULL_EXIT_CONTROL`
4. `SINGLE_LOT_CONTROL = floor sanity only`
5. `Gene = sidecar / shadow / attribution only`

---

## 5. Forbidden Runtime Switches

The following remain forbidden unless a new formal package and gate explicitly promote them:

1. turning legacy `IRS-lite / MSS-lite` back on as default runtime layers
2. translating any `Gene` label, mirror score, or conditioning bucket into a hard runtime filter
3. promoting `TRAIL_SCALE_OUT_25_75` or any retained partial-exit family into default exit behavior
4. promoting any `Normandy` watch or retained branch into default entry behavior
5. declaring that the unified default system has already been cut over

---

## 6. Pre-Run Checklist

Before any formal mainline run, the minimum checklist is:

1. run `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile hook`
2. confirm the main database is `G:\EmotionQuant_data\emotionquant.duckdb`
3. confirm the run target is still the baseline operating path, not a verbalized post-Phase-6 promotion
4. confirm no research-only switch was manually turned on
5. confirm `legacy_bof_baseline` remains replayable and recoverable

---

## 7. Human Intervention Boundary

Human intervention is allowed only for:

1. stopping a run because `preflight`, schema, trace, or core contracts failed
2. reviewing sidecar output for attribution and environment interpretation
3. executing already-defined `STOP_LOSS / FORCE_CLOSE` behavior under existing broker semantics
4. recording issues and explicitly rolling back to `legacy_bof_baseline`

Human intervention is forbidden for:

1. manually treating `Gene` sidecar tags as uncoded trading filters
2. temporarily adding retained or watch conclusions into default runtime behavior
3. rewriting sizing or exit semantics because of a small local win sample
4. announcing cutover completion without a formal closeout record

---

## 8. Reporting Requirements

Every formal run must remain able to answer:

1. was the run still on `legacy_bof_baseline`
2. did `FIXED_NOTIONAL_CONTROL` and `FULL_EXIT_CONTROL` execute as expected
3. was `Gene` clearly separated as sidecar rather than runtime logic
4. can any failure be traced back through `run_id / signal_id`

---

## 9. Rollback And Emergency Stop

The current rollback target is fixed as:

`legacy_bof_baseline`

Promotion talk must stop and rollback must be enforced if any of the following happens:

1. the end-to-end operating chain is broken
2. trace, report, or sidecar integrity becomes non-credible
3. any research-layer object leaks into runtime hard-gate behavior
4. default runtime semantics change without a formal package and formal gate

---

## 10. Relation To Phase 6

This runbook now serves two purposes:

1. it protects the truthful current operating baseline
2. it provides the single operational entry point for the `Phase 6` unified candidate boundary

This means:

`Phase 6B` has validated the candidate boundary, but the runtime default remains unchanged until `Phase 6 closeout` explicitly says otherwise.
