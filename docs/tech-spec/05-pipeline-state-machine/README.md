# 05 Pipeline State Machine

Status: draft

## Purpose

Specify deterministic pipeline phase flow, transition rules, and failure handling so orchestration behavior is stable and testable.

## Scope

- Phase graph and ownership.
- Transition preconditions/postconditions.
- Retry and failure semantics per phase.
- Manual approval gates.
- State persistence requirements.

## Design

### Canonical Phase Sequence

`init -> plan -> review -> narration -> build_scenes -> scene_qc -> precache_voiceovers -> final_render -> assemble -> complete`

### Transition Contract

- Each phase has explicit entry criteria and exit artifacts.
- Orchestrator is the only authority that advances `phase`.
- A phase may advance only after required artifacts are validated.
- Any transition failure keeps phase unchanged and records failure metadata.

### Retry Model

- Retries are bounded per phase (`max_attempts` defined in config).
- Each retry must include new error context; identical retries are disallowed.
- Exceeding retry budget transitions to `blocked` state requiring human action.

### Manual Gates

- `review` is a hard manual gate.
- Gate actions are auditable and recorded with timestamp and actor.

### State File Contract (High Level)

- `project_state.json` persists current phase, history, failure metadata, and session references.
- State writes are atomic.
- History entries are append-only and timestamped in UTC.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-002 | State machine is an explicit tested contract with deterministic transitions. |
| L-003 | Retry loops are bounded and evidence-driven; no blind self-heal churn. |
| L-004 | Scaffold and artifact gates are checked before downstream phase advancement. |
| L-009 | Validation ownership is layered and phase-specific. |

## Open Questions

- Should `blocked` be a distinct phase or a flag on current phase?
- What are phase-specific retry budgets (for example `plan` vs `build_scenes`)?
- Which manual gates besides `review` are mandatory in v1?

## Decisions

- Orchestrator is the sole authority for phase advancement.
- Transition behavior must be acceptance-tested phase by phase.
- Retry behavior is explicitly bounded and cannot serve as normal execution flow.
