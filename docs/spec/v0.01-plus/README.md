# v0.01-plus Governance Archive

**Status**: `Active`  
**Last Updated**: `2026-03-18`

---

## Purpose

`docs/spec/v0.01-plus/` now carries governance, evidence, and records for the current mainline.

It is used for:

1. roadmap
2. governance
3. evidence
4. records

It is not the main design authority.  
Mainline design authority remains in `blueprint/`.

---

## Current Entry Points

| Type | Path | Use |
|---|---|---|
| Mainline design authority | `blueprint/README.md` | Mainline SoT |
| Current implementation spec | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` | Current implementation truth |
| Current execution breakdown | `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md` | Current phase and next-step breakdown |
| Phase 6 package card | `blueprint/03-execution/11-phase-6-unified-default-system-migration-package-card-20260317.md` | Unified default-system migration package |
| Current development status | `docs/spec/common/records/development-status.md` | State ledger and active progression |
| No-fake rules | `docs/spec/v0.01-plus/governance/v0.01-plus-mainline-no-fake-rules.md` | Mainline truth boundary |
| Promoted subset freeze | `docs/spec/v0.01-plus/governance/v0.01-plus-promoted-subset-freeze-20260317.md` | Promote-now / shadow-only / remain-research freeze |
| Phase 6A record | `docs/spec/v0.01-plus/records/v0.01-plus-phase-6a-promoted-subset-freeze-20260317.md` | Formal freeze record |
| Phase 6B record | `docs/spec/v0.01-plus/records/v0.01-plus-phase-6b-integrated-end-to-end-validation-20260317.md` | Formal integrated validation record |
| Phase 6C record | `docs/spec/v0.01-plus/records/v0.01-plus-phase-6c-unified-operating-runbook-refresh-20260317.md` | Formal runbook refresh record |
| Phase 6 closeout record | `docs/spec/v0.01-plus/records/v0.01-plus-phase-6-closeout-default-system-promotion-decision-20260317.md` | Final Phase 6 promotion decision |
| Phase 7 card | `blueprint/03-execution/15-phase-7-data-provider-refactor-card-20260317.md` | Data-provider refactor package |
| Phase 7B regression audit | `docs/spec/v0.01-plus/records/v0.01-plus-phase-7b-local-data-contract-regression-audit-20260318.md` | Local data-contract regression audit |
| Phase 7 closeout record | `docs/spec/v0.01-plus/records/v0.01-plus-phase-7-data-provider-refactor-closeout-20260318.md` | Final Phase 7 data-provider closeout |
| Current operating runbook | `docs/reference/operations/current-mainline-operating-runbook-20260317.md` | Truthful operating chain and rollback rules |

---

## Usage Rules

1. Use `blueprint/` for design and implementation authority.
2. Use this directory for governance, records, and evidence only.
3. If this directory conflicts with `blueprint/`, `blueprint/` wins.
4. If you need frozen historical baseline material, use `docs/design-v2/01-system/system-baseline.md`.
5. Retired or superseded proposals belong in `90-archive/`, not in shared live entry points.
