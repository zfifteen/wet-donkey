# 09 Validation Gates

Status: draft

## Purpose

Define a strict validation hierarchy that blocks invalid artifacts early and prevents “validation sprawl” from replacing root-cause fixes.

## Scope

- Validation layers and ownership.
- Gate entry/exit behavior.
- Failure reporting requirements.
- CI validation alignment checks.

## Design

### Validation Hierarchy

1. Schema Gate (Harness output)
- Validates phase output against canonical schema.
- Failure outcome: reject output, retry eligible.
 - No schema auto-repair; failures are surfaced with exact parse locations and field paths.

2. Contract Gate (Parser + scaffold/state contracts)
- Validates required fields, slot boundaries, and artifact contracts.
- Failure outcome: reject output, retry eligible with explicit contract error.

3. Semantic Gate (Domain rules)
- Validates policy/business constraints (timing bounds, layout tag allowlist, helper usage).
- Failure outcome: reject output, retry eligible with semantic diff guidance.

4. Runtime Gate (Execution checks)
- Validates executable correctness (syntax/import/runtime/ffmpeg/render preconditions).
- Failure outcome: reject output, retry eligible if upstream-fixable.

5. Assembly Gate (Final package integrity)
- Validates expected final outputs and metadata completeness.
- Failure outcome: block completion and mark phase `blocked` if non-recoverable.

### Gate Rules

- Each gate emits machine-readable error codes and human-readable context.
- A failed gate must identify owner component and likely fix location.
- Contract Gate must hard-fail if scaffold boundary markers are missing, reordered, or mutated (for example missing `SLOT_START`).
- New gate additions require:
- documented failure class addressed,
- expected false-positive rate,
- retirement criteria if superseded.

### CI Alignment Checks

- Prompt-template fields must map to schema fields.
- Parser expectations must align with schema version.
- Orchestrator phase artifact checks must reference contract definitions.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-005 | Prevent prompt/schema/parser drift with enforced alignment checks. |
| L-007 | Validation policy is spec-driven and versioned with implementation. |
| L-009 | Validation hierarchy has explicit ownership and measurable purpose. |
| L-003 | Failed validations cannot trigger unbounded blind retries. |
| L-004 | Scaffold boundary integrity is enforced at the Contract Gate. |

## Open Questions

- Which semantic checks are mandatory before first runtime render attempt?
- What threshold justifies adding a new gate vs fixing upstream generation?
- Should runtime-gate failures always include minimal repro artifacts?

## Decisions

- WD uses a layered validation hierarchy: schema -> contract -> semantic -> runtime -> assembly.
- Every gate must be tied to a defined failure class and owner component.
- Validation failures produce structured error payloads suitable for targeted retry prompts.
- Scaffold boundary violations are treated as contract failures, not semantic fixes.
