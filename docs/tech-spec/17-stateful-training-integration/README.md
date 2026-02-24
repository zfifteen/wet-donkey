# 17 Stateful Training Integration

Status: draft

## Purpose

Define how WD uses stateful session context and training corpus retrieval without coupling core pipeline correctness to unstable retrieval behavior.

## Scope

- Session state persistence rules.
- Retrieval/training corpus integration boundaries.
- Cross-phase context continuity.
- Failure behavior when stateful dependencies are degraded.

## Design

### Integration Principles

- Stateful context improves quality but must not invalidate core deterministic contracts.
- Retrieval is an enhancement layer, not a replacement for phase contracts.
- Session metadata is explicit, versioned, and auditable.

### Session Contract

- Session state includes response/session identifiers, updated timestamp, and contract version.
- Session continuation is explicit per phase invocation.
- Missing or invalid session metadata is a controlled error path.

### Training Corpus Contract

- Corpus metadata tracks collection IDs and uploaded artifact lineage.
- Upload/read operations are idempotent where possible.
- Retrieval citations are captured for observability and auditability.

### Degradation Behavior

- If stateful retrieval is unavailable, WD follows explicit policy:
- either fail-fast for required phases,
- or run in degraded mode only when explicitly configured.
- Degraded mode must be marked in logs and output metadata.

### Cross-Project Reuse Policy

- Shared template corpus is allowed only through documented compatibility/version rules.
- Project-specific corpus remains isolated for artifact provenance.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stateful integration uses stable, versioned interfaces before expansion. |
| L-002 | Stateful metadata participates in deterministic phase/state contracts. |
| L-005 | Retrieval-enhanced outputs remain schema/contract constrained. |
| L-007 | Stateful policy is documented as authoritative behavior. |
| L-010 | Corpus/runtime artifacts are tracked separately from core codebase evolution. |

## Open Questions

- Which phases require retrieval/stateful context vs optional use in v1?
- What are strict failure policies for retrieval latency/timeouts?
- How should corpus growth be capped/governed over long-lived projects?

## Decisions

- WD treats stateful training integration as a constrained enhancement layer.
- Session and corpus metadata are versioned contracts with explicit error handling.
- Degraded operation is opt-in and fully observable.
