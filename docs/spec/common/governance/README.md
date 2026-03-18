# Common Governance

## Position

`docs/spec/common/governance/` stores long-lived formal definitions that must remain stable across versions, battlefields, and implementation cycles.

This directory answers:

1. which shared terms are authoritative
2. which things are objects, states, events, indicators, or signals
3. which foundational concepts are formally frozen inside the system
4. which promotion and validation disciplines later packages must obey

This directory does not answer:

1. how a specific execution card advances
2. what a single experiment window concluded
3. one-off evidence, patch notes, or temporary run results

## Boundary With Nearby Directories

- `docs/spec/common/records/`: historical governance facts, state logs, switching records, and status ledgers
- `docs/spec/common/governance/`: formal definitions, frozen terminology, and cross-battlefield discipline
- `blueprint/`: active first-battlefield mainline design and execution packages
- `normandy/`, `positioning/`, `gene/`: battlefield-specific design, execution, evidence, and records

One line:

`records` answer `what happened`; `governance` answers `what the system means`.

## Current Entry Files

- `four-battlefields-unified-terminology-glossary-20260317.md`
- `four-battlefields-object-indicator-signal-boundary-20260317.md`
- `gene-foundational-definition-freeze-20260317.md`
- `normandy-foundational-definition-freeze-20260317.md`
- `positioning-foundational-definition-freeze-20260317.md`
- `gene-definition-gap-remediation-checklist-20260317.md`
- `research-line-promotion-discipline-freeze-20260318.md`
- `single-variable-validation-discipline-freeze-20260318.md`

## Authority Links

- [`system-baseline.md`](../../../design-v2/01-system/system-baseline.md)
- [`development-status.md`](../records/development-status.md)

## Maintenance Rules

1. Only cross-battlefield rules that require long-term stability belong here.
2. Files here should prefer stable terminology over temporary experimental wording.
3. If a foundational definition changes, the change must be traceable to formal design, implementation, and downstream impact.
