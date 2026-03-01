# 13 Logging and Observability

Status: approved

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

3. Context Manager log
- Payload budget decisions, compaction events, dropped fields.
- `previous_response_id` validation results and retry eligibility.
- Per-model budget usage (tokens estimated vs budget).

4. Validation log
- Gate-level pass/fail, failure codes, owner component, retryability.

5. Artifact lineage log
- Inputs/outputs and version hashes per phase artifact.
 - Prompt capability manifest snapshot per phase attempt (required tools/annotations vs allowed).

### Correlation and Identity

- Every run has a `run_id`.
- Every phase attempt has `phase_attempt_id`.
- Every error has `error_signature` used by loop detection.

### Logging Contract

- Logs are structured JSONL for machine processing.
- Human summary files are optional and derived from structured logs.
- Sensitive data is redacted at write-time.
 - When payloads exceed size limits, logs must preserve a complete raw artifact in deterministic storage and include a diff/summary pointer in the structured log event.

### Minimum Diagnostic Payload

For failures, include:
- component owner,
- gate/phase context,
- normalized signature,
- prior-attempt comparison,
- next-action recommendation.
 - retry-context integrity marker (indicates whether full prior payload was preserved).
 - context budget marker (estimated tokens, budget, compaction applied).

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-003 | Retry/repair behavior is observable and signature-driven. |
| L-002 | Phase transitions are auditable with deterministic event records. |
| L-007 | Operational behavior documented and aligned with spec contracts. |
| L-009 | Validation ownership is visible in logs, reducing blind guardrail layering. |
| L-010 | Runtime artifact lineage is explicit and separated from core source evolution. |
| L-014 | Context budget enforcement is logged and auditable. |

## Open Questions

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD uses structured logging with mandatory correlation IDs.
- Failure diagnostics must support loop detection and owner-targeted remediation.
- Logging behavior is contract-bound and versioned with the spec.
- Retention defaults are: local runs `14 days`, CI artifacts `30 days`, and persistent production-like runs `90 days` (or stricter organizational policy, whichever is greater).
- Blocked runs must automatically emit a deterministic trace export bundle (state snapshot, gate failures, artifact pointers, retry history summary).
- CI observability gates require: valid JSONL schema, presence of `run_id`/`phase_attempt_id`, and complete blocked-run diagnostic payloads.
