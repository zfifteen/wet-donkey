# 15 Testing

Status: approved

## Purpose

Define a test strategy that validates WD contracts early, prevents regressions during iteration, and keeps implementation aligned with spec.

## Scope

- Test pyramid by layer (unit/integration/e2e/contract).
- Required tests per phase and component.
- Local/manual gating and failure policy.
- Regression strategy for lessons-derived risks.

## Design

### Test Layers

1. Contract tests
- Validate schema, state, scaffold, and exit-code contracts.
 - Include negative fixtures for missing or mutated scaffold boundary markers (for example `SLOT_START`).

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
- Schema parse strictness under malformed/repair-pressure outputs.
- Retry-context preservation and truncation handling.
- MathTex/LaTeX validity checks for generated formulas.
- Manim color literal validation (reject non-color types).
- Prompt/tool capability compatibility checks (required tools/annotations vs phase policy).
- LaTeX escaping normalization (reject double-escaped sequences).
- Helper signature validation and API kwargs allowlist enforcement.
- Plot callback scalar-compatibility checks for `Axes.plot`.
- Dashed-line rendering tests to ensure `stroke_dash` is rejected and `DashedVMobject` is accepted.
- Camera capability tests to ensure moving-camera APIs are rejected unless explicitly enabled.
- Axis config allowlist tests to reject unsupported keys.
- Plan lint tests to reject raw Manim API tokens inside `visual_ideas`.
- MathTex subobject access tests to reject numeric indexing and require `get_part_by_tex`.

### Local Gate Policy (v1)

- Contract tests are mandatory on every change touching prompts/schemas/parser/orchestrator.
- Failing local gates block progression for this version; no bypass for architecture-affecting changes.
- New lessons-derived guardrails require accompanying tests.
- GitHub CI/Actions are intentionally deferred to a future version decision.

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
| L-017 | Prompt/tool compatibility is tested before model calls. |
| L-018 | LaTeX escaping normalization has dedicated regression tests. |
| L-019 | Helper signature and API kwargs validation are regression-tested. |
| L-021 | Plot callbacks are validated for scalar safety. |
| L-022 | Plan lint prevents invalid Manim API leakage into build. |
| L-023 | MathTex subobject access is validated for safe selectors. |

## Open Questions

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD will prioritize contract and integration tests before expanding e2e scope.
- Lessons-derived failure classes are tracked with explicit regression tests.
- Local gate policy requires passing contract-critical suites before proceeding.
- Minimum v1 coverage targets are `>=85%` for contract-critical modules and explicit scenario coverage for each phase transition and retry/escalation branch.
- Default local gate execution runs deterministic contract/unit/integration suites plus one fixture-based e2e smoke path.
- Live API smoke remains an explicit manual run with secrets gating and cannot replace deterministic local gate baselines.
