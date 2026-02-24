# M0 Checklist - Contract Freeze Baseline

Status: draft (pre-execution)  
Execution state: not started  
Last updated: 2026-02-24

Purpose: review and approve the M0 scope before any implementation execution begins.

## Scope Confirmation

- [ ] M0 remains limited to contract-freeze work only (no M1+ implementation work).
- [ ] M0 scope maps to canonical game plan step 4 (implementation planning), not step 5 execution.
- [ ] No architecture pivots are introduced outside existing `docs/tech-spec/` direction.

## Work Items

- [ ] Freeze v1 pipeline state contract (`project_state`) and document required fields.
- [ ] Freeze phase schema registry strategy and `contract_version` policy.
- [ ] Freeze scaffold slot immutability contract and mutation boundaries.
- [ ] Freeze harness exit-code contract and orchestrator action mapping.
- [ ] Publish component ownership map:
  - orchestrator,
  - harness,
  - parser/validators,
  - voice,
  - render/assembly.
- [ ] Convert unresolved contract questions into explicit TODOs with owners.

## Acceptance Criteria

- [ ] Contract documents are consistent with spec sections:
  - `docs/tech-spec/05-pipeline-state-machine/README.md`,
  - `docs/tech-spec/08-data-contracts/README.md`,
  - `docs/tech-spec/09-validation-gates/README.md`,
  - `docs/tech-spec/12-harness-exit-codes/README.md`.
- [ ] No ambiguous phase transition ownership remains.
- [ ] Contract-change checklist exists for future PRs and is documented.

## Required Tests and Gates

- [ ] Contract schema validation tests pass.
- [ ] Exit-code mapping tests pass.
- [ ] State transition table tests pass for happy path and failure path basics.
- [ ] Test evidence is recorded with exact commands and outcomes.

## Lessons Traceability

- [ ] L-001 addressed (interface freeze before expansion).
- [ ] L-002 addressed (deterministic state/transition ownership).
- [ ] L-005 addressed (schema/contract alignment).
- [ ] L-009 addressed (validation ownership clarity).

## Review and Approval Gate (Before Execution)

- [ ] Reviewer confirms M0 checklist completeness.
- [ ] Reviewer approves moving from planning to M0 execution.
- [ ] Open risks impacting M0 are acknowledged and tracked.
- [ ] Any non-M0 requested work is deferred or explicitly re-scoped.
