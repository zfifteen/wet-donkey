# 13 Logging and Observability

Status: draft

## Purpose

Define observability standards that make WD failures diagnosable at the source and prevent blind retry/repair cycles.

## Scope

- Structured logging requirements by component.
- Correlation IDs and traceability across phases.
- Event and error payload standards.
- Operational artifacts and retention.

## Design

### Observability Principles

- Every phase execution must be traceable end-to-end.
- Logs must identify failure origin, not only failure symptom.
- Retry attempts must include delta-aware diagnostics.

### Required Log Streams

1. Orchestrator event log
- Phase start/end, transition decisions, retry/escalation actions.

2. Harness interaction log
- Model calls, tool invocations, schema outcomes, response IDs.

3. Validation log
- Gate-level pass/fail, failure codes, owner component, retryability.

4. Artifact lineage log
- Inputs/outputs and version hashes per phase artifact.

### Correlation and Identity

- Every run has a `run_id`.
- Every phase attempt has `phase_attempt_id`.
- Every error has `error_signature` used by loop detection.

### Logging Contract

- Logs are structured JSONL for machine processing.
- Human summary files are optional and derived from structured logs.
- Sensitive data is redacted at write-time.

### Minimum Diagnostic Payload

For failures, include:
- component owner,
- gate/phase context,
- normalized signature,
- prior-attempt comparison,
- next-action recommendation.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-003 | Retry/repair behavior is observable and signature-driven. |
| L-002 | Phase transitions are auditable with deterministic event records. |
| L-007 | Operational behavior documented and aligned with spec contracts. |
| L-009 | Validation ownership is visible in logs, reducing blind guardrail layering. |
| L-010 | Runtime artifact lineage is explicit and separated from core source evolution. |

## Open Questions

- What log retention windows should apply for local vs CI vs production runs?
- Should trace exports be generated automatically for blocked runs?
- Which observability checks should be required in CI gates?

## Decisions

- WD uses structured logging with mandatory correlation IDs.
- Failure diagnostics must support loop detection and owner-targeted remediation.
- Logging behavior is contract-bound and versioned with the spec.
