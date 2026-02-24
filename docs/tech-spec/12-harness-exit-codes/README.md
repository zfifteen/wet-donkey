# 12 Harness Exit Codes

Status: draft

## Purpose

Define a stable harness exit-code contract so orchestrator behavior is deterministic and retry/escalation logic is machine-driven.

## Scope

- Exit code taxonomy.
- Mapping from exit codes to orchestrator actions.
- Retry vs block semantics.
- Logging and observability requirements.

## Design

### Exit Code Contract

| Code | Category | Meaning | Orchestrator Action |
|---|---|---|---|
| 0 | Success | Phase completed with valid structured output/artifacts | Advance phase |
| 1 | Infrastructure/Execution Error | API/network/runtime/system failure | Retry if budget remains; otherwise block |
| 2 | Semantic/Contract Validation Error | Output structurally valid but violates contract/semantic rules | Retry with failure context |
| 3 | Schema Violation | Output failed schema contract | Retry with schema diagnostics; escalate on repeated same signature |
| 4 | Non-Retryable Policy Violation | Disallowed behavior or forbidden mutation | Immediate block; require human action |

### Rules

- Harness must emit one and only one canonical exit code per run.
- Exit code meaning is versioned; changes require orchestrator/spec/test updates.
- Orchestrator actions are table-driven and not inferred ad hoc.

### Error Payload Requirements

On non-zero exits, harness must provide:
- machine-readable error code/category,
- concise human-readable summary,
- recommended retryability (`retryable: true/false`),
- signature token for loop detection.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-002 | Deterministic phase transitions require stable machine-actionable harness outcomes. |
| L-003 | Retry behavior depends on explicit retryable vs non-retryable signaling. |
| L-005 | Schema/semantic failures are separated for targeted correction. |
| L-009 | Validation ownership is reflected in distinct exit categories. |

## Open Questions

- Should schema violations (`3`) be retried automatically in all phases or phase-specific?
- Is a dedicated code needed for user-intervention/manual-gate required state?
- Should exit-code taxonomy be shared across all harness backends from day one?

## Decisions

- WD will use a fixed, versioned harness exit-code contract.
- Orchestrator responses to exit codes are deterministic and table-driven.
- Non-retryable policy violations immediately transition to blocked state.
