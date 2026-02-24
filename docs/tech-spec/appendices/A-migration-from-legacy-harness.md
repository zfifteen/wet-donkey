# Appendix A: Migration from Legacy Harness

Status: draft

## Purpose

Document a controlled migration path from legacy harness patterns to WD’s contract-first responses harness model.

## Migration Steps

1. Establish baseline contracts
- Freeze phase/state, schema, scaffold, and exit-code contracts.
- Add contract tests before migrating behavior.

2. Isolate integration boundaries
- Route all LLM calls through the dedicated responses harness boundary.
- Remove direct orchestrator-to-model coupling.

3. Migrate phase by phase
- Enable one phase at a time under new contracts.
- Validate with contract + integration tests before advancing.

4. Remove legacy paths
- Decommission legacy harness logic after parity criteria are met.
- Remove dead config flags and stale docs references.

## Compatibility Notes

- No silent fallback to legacy mode.
- Migration milestones must be reversible until parity is verified.
- Contract versioning is mandatory during migration windows.

## Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Migration avoids parallel long-lived harness drift. |
| L-002 | Phase migration follows deterministic state contracts. |
| L-006 | Migration is sliced into small, verifiable milestones. |
| L-007 | Migration documentation is part of done criteria. |

## Exit Criteria

- Legacy harness paths removed from production execution path.
- All migrated phases pass contract-critical test suites.
- Spec, config, and operational docs reflect post-migration reality.
