# 15 Testing

Status: draft

## Purpose

Define a test strategy that validates WD contracts early, prevents regressions during iteration, and keeps implementation aligned with spec.

## Scope

- Test pyramid by layer (unit/integration/e2e/contract).
- Required tests per phase and component.
- CI gating and failure policy.
- Regression strategy for lessons-derived risks.

## Design

### Test Layers

1. Contract tests
- Validate schema, state, scaffold, and exit-code contracts.

2. Unit tests
- Component-local logic (parser, config validation, retry policy, helpers).

3. Integration tests
- Orchestrator + harness + validation chain with mocked external dependencies.

4. End-to-end tests
- Full phase flow with controlled fixtures; optional live API smoke path.

### Required Coverage Areas

- State machine transition correctness.
- Prompt/schema/parser alignment checks.
- Retry-loop detection and blocked escalation behavior.
- Scaffold immutability enforcement.
- Config preflight validation and deterministic defaults.

### CI Policy

- Contract tests are mandatory on every change touching prompts/schemas/parser/orchestrator.
- Failing tests block merge; no bypass for architecture-affecting changes.
- New lessons-derived guardrails require accompanying tests.

### Regression Strategy

- Maintain a lessons-linked regression suite where each lesson ID maps to one or more tests.
- Add a test before/with each fix for known recurring failure class.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-002 | State transition behavior is acceptance-tested phase by phase. |
| L-003 | Retry-loop behavior has explicit regression tests. |
| L-004 | Scaffold/slot integrity is tested as an immutable contract. |
| L-005 | Prompt/schema/parser alignment is tested automatically. |
| L-006 | Small milestone slices are validated with focused test gates. |
| L-007 | Spec updates require matching test updates for affected contracts. |

## Open Questions

- What minimum coverage threshold is acceptable for WD v1 milestones?
- Which end-to-end tests must run by default vs nightly-only?
- How should live API tests be isolated from deterministic CI baselines?

## Decisions

- WD will prioritize contract and integration tests before expanding e2e scope.
- Lessons-derived failure classes are tracked with explicit regression tests.
- CI merge policy requires passing contract-critical suites.
