# 10 Self-Healing and Retry Logic

Status: draft

## Purpose

Define bounded, evidence-driven retry behavior that supports recovery without turning repair loops into the default execution path.

## Scope

- Retry eligibility rules.
- Retry budget policy by phase.
- Repair prompt input requirements.
- Loop detection and escalation behavior.

## Design

### Retry Philosophy

- Retries are fallback recovery, never the normal path to success.
- First-pass quality is the primary objective.
- Retry logic exists to recover from transient or targeted fixable failures.

### Retry Eligibility

A retry is allowed only when all are true:
- Failure is classified as retryable (`schema`, `contract`, `semantic`, or fixable runtime).
- Failure payload includes actionable diagnostics.
- Next attempt includes new information (error context diff, constraint clarifications, or retrieved references).

### Retry Budgets

- Define `max_attempts` per phase (for example lower for `plan`, higher for `build_scenes`).
- Identical failure signature across consecutive attempts counts as loop-risk.
- On loop-risk threshold breach, phase enters `blocked` and requires human decision.

### Repair Inputs

Repair prompts must include:
- failing artifact snapshot,
- gate failure code and message,
- prior attempt delta summary,
- applicable contract constraints.

### Loop Detection

Loop detector compares:
- normalized error signature,
- key artifact diffs,
- tool usage/citation changes.

If no meaningful delta across attempts, stop retries.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-003 | Self-heal loops are bounded and require new evidence each retry. |
| L-002 | Retry outcomes feed explicit state transitions and blocked escalation. |
| L-005 | Retry prompts are generated from structured gate outputs. |
| L-009 | Retry policy is integrated with validation ownership, not ad hoc. |

## Open Questions

- What default `max_attempts` values should WD use per phase in v1?
- What exact criteria define a “meaningful delta” between attempts?
- Should blocked-state recovery require explicit human annotation before resume?

## Decisions

- WD will enforce bounded retries with per-phase budgets and loop detection.
- Retries without new evidence/context are disallowed.
- Repeated identical failures escalate to blocked state instead of continued repair cycling.
