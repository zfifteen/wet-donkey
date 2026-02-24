# 08 Data Contracts

Status: draft

## Purpose

Define canonical data contracts across pipeline state, phase payloads, and generated artifacts so components interoperate without drift.

## Scope

- `project_state.json` contract.
- Session metadata contracts (LLM/session/retrieval IDs).
- Phase input/output schemas.
- Scaffold insertion contract for generated scene bodies.
- Contract versioning and compatibility rules.

## Design

### Contract Ownership

- Orchestrator owns phase/state contracts.
- Harness owns structured phase outputs.
- Parser/validators enforce semantic and runtime constraints.
- Scaffold generator owns immutable scene file boundaries.

### Core Contracts

1. `project_state.json`
- Required: `project_name`, `topic`, `phase`, `history`.
- Optional: `xai_session`, `training_corpus`, `failure_context`.
- Must be schema-validated on every read/write.

2. Phase Output Schemas
- Each phase has one canonical schema definition.
- Prompts must target schema fields exactly (no parallel informal fields).
- Schema changes require coordinated updates to prompt templates, parser logic, and tests.

3. Scene Scaffold Contract
- Immutable slot markers define insertion boundaries.
- Generator outputs only slot body content.
- Parser rejects outputs that modify scaffold outside approved regions.

4. Session/Corpus Metadata
- `.xai_session.json` and collection metadata must be versioned and backward-compatible within major WD spec version.
- Missing required metadata is a hard failure, not silently repaired.

### Versioning Rules

- Every contract includes a `contract_version` field.
- Breaking changes require explicit migration notes and test updates.
- No implicit upgrades during runtime.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stable versioned interfaces prevent unbounded harness churn. |
| L-004 | Scaffold boundaries are immutable and validator-enforced. |
| L-005 | One source of truth for schema/prompt/parser alignment. |
| L-007 | Contract docs are authoritative and must update with code. |
| L-009 | Validation layers map to explicit contract ownership. |
| L-010 | Runtime artifacts are separated from core contract definitions. |

## Open Questions

- Which contract fields are mandatory in v1 vs deferred?
- How strict should backward compatibility be for session metadata in pre-release WD milestones?
- Should schema registries be centralized under one module or kept per phase package?

## Decisions

- WD will use explicit versioned contracts for state, phase outputs, and session metadata.
- Prompt, schema, parser, and orchestrator contracts must remain synchronized or CI fails.
- Scaffold mutation outside slot boundaries is a hard contract violation.
