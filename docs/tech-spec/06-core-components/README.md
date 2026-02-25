# 06 Core Components

Status: draft

## Purpose

Define WD’s core modules, boundaries, and ownership so implementation stays modular and does not repeat FH coupling/drift patterns.

## Scope

- Orchestrator component responsibilities.
- Harness component responsibilities.
- Prompt/schema/parser boundary ownership.
- Scene scaffold and helpers boundary.
- Voice and render subsystems.

## Design

### Component Map

1. Orchestrator (`scripts/`)
- Owns phase execution order, transition rules, retry budget enforcement, and state writes.
- Must not contain phase-specific parsing/business logic.

2. Harness (`harness/`)
- Owns model invocation, tool wiring, and structured output requests.
- Must not directly mutate orchestrator state.
- Must not act as phase authority; it returns contract-scoped payloads only.

3. Context Manager (`harness/` or `src/context/`)
- Owns context budgeting, compaction, and retry-payload assembly.
- Validates `previous_response_id` chain and persists it in deterministic state.
- Enforces per-model token budgets and hard caps before any model call.
- Emits structured metrics (truncation count, compaction events, dropped fields).
- Exposes a deterministic API: `build_payload(phase, artifacts, errors, model_id) -> payload`.
 - Emits logging per `docs/tech-spec/13-logging-and-observability/README.md`.

4. Prompt + Schema + Parser Layer
- Prompts define task intent constrained to schema.
- Schemas define canonical phase outputs.
- Parser/validators enforce semantic/runtime policy before artifacts are accepted.

5. Scaffold and Scene Contract Layer
- Scaffold generator owns immutable scene structure and slot markers.
- Generated content may only populate allowed slots.

6. Voice Subsystem
- Exposes one stable service interface (generate/cache/query duration).
- Provider-specific adapters are isolated behind this interface.

7. Render + Assembly Subsystem
- Consumes validated scene + narration + audio artifacts.
- No silent repair logic in final render stage.

### Boundary Rules

- Cross-component communication occurs only through versioned contracts.
- A component cannot “reach across” and fix another component’s invariants.
- Temporary containment changes must include explicit removal conditions.
- Deterministic orchestration code is the control plane; LLM output is data input to that control plane, never orchestration authority.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stable component interfaces are defined before feature expansion. |
| L-004 | Scaffold ownership is isolated and immutable outside slot boundaries. |
| L-005 | Prompt/schema/parser are treated as one contract surface. |
| L-008 | Voice policy is frozen behind one adapter interface. |
| L-010 | Runtime artifacts are decoupled from core component evolution. |
| L-013 | Conversation chain is validated and persisted deterministically. |
| L-014 | Retry payloads are size-bounded and compacted deterministically. |

## Open Questions

- Which components need strict package-level isolation immediately (v1)?
- Which cross-component APIs require explicit versioning from day one?
- Should render assembly be in orchestrator or a separate execution component?

## Decisions

- WD will enforce explicit component boundaries with contract-only integration points.
- Orchestrator, harness, and validation layers remain separate ownership domains.
- Voice provider details are adapter-internal and must not leak into phase logic.
- Infrastructure operations (state updates, phase transitions, artifact lifecycle mutations) remain deterministic-code responsibilities.
