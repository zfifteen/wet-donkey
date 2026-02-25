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
 - Evidence of “eventual convergence after heavy retry churn” is treated as a design smell that must trigger upstream fixes, not higher retry budgets.

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
 - If the full prior context is too large, the orchestrator must include a deterministic diff summary plus a pointer to the preserved full payload in logs/artifacts.
 - Repair prompts must not introduce new tool requirements or annotations that are incompatible with the phase tool policy or output schema.

### Retry Payload Budgeting

Retry payloads must be size-bounded against model context limits before any model call.

Policy:
- Define `retry_payload_max_tokens` per model as `min(8192, floor(context_limit_tokens * 0.05))`.
- If the retry payload exceeds the budget, replace verbose fields with:
  - error code + short message,
  - minimal artifact diff (line ranges only),
  - deterministic pointer to full artifacts in logs.
- If the payload still exceeds the budget after compaction, the retry is ineligible and the phase must fail closed with `needs_human_review`.
 - Retry payload assembly and compaction are owned by the Context Manager component.

Model context limits (from xAI model list screenshot, 2026-02-25):
- `grok-4-1-fast-reasoning`: 2,000,000
- `grok-4-1-fast-non-reasoning`: 2,000,000
- `grok-code-fast-1`: 256,000
- `grok-4-fast-reasoning`: 2,000,000
- `grok-4-fast-non-reasoning`: 2,000,000
- `grok-4-0709`: 256,000
- `grok-3-mini`: 131,072
- `grok-3`: 131,072
- `grok-2-vision-1212`: 32,768

### Loop Detection

Loop detector compares:
- normalized error signature,
- key artifact diffs,
- tool usage/citation changes.

If no meaningful delta across attempts, stop retries.
Context truncation that removes required diagnostics is a retry-ineligible failure.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-003 | Self-heal loops are bounded and require new evidence each retry. |
| L-002 | Retry outcomes feed explicit state transitions and blocked escalation. |
| L-005 | Retry prompts are generated from structured gate outputs. |
| L-009 | Retry policy is integrated with validation ownership, not ad hoc. |
| L-014 | Retry payloads are size-bounded against model context limits. |
| L-017 | Retry prompts are rejected if they require unavailable tools or disallowed annotations. |

## Open Questions

- What default `max_attempts` values should WD use per phase in v1?
- What exact criteria define a “meaningful delta” between attempts?
- Should blocked-state recovery require explicit human annotation before resume?

## Decisions

- WD will enforce bounded retries with per-phase budgets and loop detection.
- Retries without new evidence/context are disallowed.
- Repeated identical failures escalate to blocked state instead of continued repair cycling.
