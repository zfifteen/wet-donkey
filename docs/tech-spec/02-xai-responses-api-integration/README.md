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
- The harness mediates all LLM IO; LLM outputs are treated as untrusted content payloads until deterministic validators accept them.
- LLM calls do not directly perform infrastructure actions (for example state advancement, file lifecycle control, or policy overrides).

### Session Lifecycle

- Session initialized per project with versioned metadata.
- Each phase invocation may continue prior response context if contract checks pass.
- Session updates happen only on successful harness completion.
 - Context Manager enforces per-model payload budgets and validates `previous_response_id` before any continuation.

### Structured Output Contract

- Every phase invocation requests canonical phase schema output.
- Non-schema outputs are rejected before artifact mutation.
- Schema version is logged with response metadata.

### Tool Usage Policy

- Allowed tools are phase-specific and explicitly declared.
- Tool outputs are treated as evidence, not direct mutation authority.
- Tool usage/citations are logged for audit and retry diagnostics.
 - Prompt templates must declare required tools/capabilities; orchestration preflight must reject any prompt that requires tools not enabled for the phase.

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
| L-013 | Session continuation requires validated conversation pointers. |
| L-014 | Per-model context limits are enforced before model calls. |
| L-017 | Prompt/tool capability mismatches are blocked before model calls. |

## Open Questions

- Which phases require stateful continuation versus isolated calls in v1?
- Should web/search tooling be allowed in all research-adjacent phases?
- What are hard timeout/backoff defaults for API stability?

## Decisions

- WD will use one primary responses harness integration path for v1.
- Structured schema output is mandatory for all phase calls.
- Session continuation and tool usage are explicit, auditable, and contract-bound.
- Orchestration authority remains deterministic and script-owned; LLM participation is bounded to schema-constrained content generation.
