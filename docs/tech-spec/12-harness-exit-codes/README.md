# 12 Harness Exit Codes

Status: approved

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
| 0 | Success | Phase finished with valid structured output/artifacts | Advance phase |
| 1 | Infrastructure/Execution Error | API/network/runtime/system failure | Retry if budget remains; otherwise block |
| 2 | Semantic/Contract Validation Error | Output structurally valid but violates contract/semantic rules | Retry with failure context |
| 3 | Schema Violation | Output failed schema contract | Retry with schema diagnostics; escalate on repeated same signature |
| 4 | Non-Retryable Policy Violation | Disallowed behavior or forbidden mutation | Immediate block; require human action |
| 5 | Manual Gate Required | Execution halted pending explicit human decision | Set `phase_status=blocked` and wait for manual resume action |

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

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD will use a fixed, versioned harness exit-code contract.
- Orchestrator responses to exit codes are deterministic and table-driven.
- Non-retryable policy violations immediately transition to blocked state.
- Schema violation auto-retry is phase-specific: enabled for `plan`, `narration`, `build_scenes`, and `scene_qc`; disabled for `review`, `final_render`, and `assemble`.
- WD v1 reserves code `5` for explicit manual-gate/user-intervention required states.
- Exit-code taxonomy is shared across all harness backends in v1; backend-specific codes must map into this canonical table before orchestrator handling.
