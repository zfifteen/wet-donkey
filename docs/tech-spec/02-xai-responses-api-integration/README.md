# 02 xAI Responses API Integration

Status: draft

## Purpose

Define how WD integrates with the xAI Responses API in a stateful, schema-enforced way while preserving deterministic pipeline contracts.

## Scope

- Session lifecycle and continuation semantics.
- Tool usage policy (retrieval, code execution, search).
- Structured outputs and schema enforcement.
- Failure and degradation behavior.

## Design

### Integration Model

- WD uses a dedicated responses harness as the only LLM integration path for v1.
- Harness interactions are phase-scoped and contract-constrained.
- Session continuation is explicit (no hidden implicit conversation state).

### Session Lifecycle

- Session initialized per project with versioned metadata.
- Each phase invocation may continue prior response context if contract checks pass.
- Session updates happen only on successful harness completion.

### Structured Output Contract

- Every phase invocation requests canonical phase schema output.
- Non-schema outputs are rejected before artifact mutation.
- Schema version is logged with response metadata.

### Tool Usage Policy

- Allowed tools are phase-specific and explicitly declared.
- Tool outputs are treated as evidence, not direct mutation authority.
- Tool usage/citations are logged for audit and retry diagnostics.

### Error/Degradation Behavior

- API/network failures map to explicit harness exit categories.
- Optional degraded mode is configuration-gated and observable.
- No silent fallback to legacy harness path.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Harness integration is stabilized before adding parallel paths. |
| L-002 | Session usage aligns with deterministic phase/state transitions. |
| L-005 | Structured outputs are schema-contract mandatory. |
| L-007 | Integration policy is spec-authoritative and versioned. |
| L-009 | Validation and tool evidence are first-class integration outputs. |

## Open Questions

- Which phases require stateful continuation versus isolated calls in v1?
- Should web/search tooling be allowed in all research-adjacent phases?
- What are hard timeout/backoff defaults for API stability?

## Decisions

- WD will use one primary responses harness integration path for v1.
- Structured schema output is mandatory for all phase calls.
- Session continuation and tool usage are explicit, auditable, and contract-bound.
