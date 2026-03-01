# 05 Pipeline State Machine

Status: approved

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

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- Orchestrator is the sole authority for phase advancement.
- Transition behavior must be acceptance-tested phase by phase.
- Retry behavior is explicitly bounded and cannot serve as normal execution flow.
- `blocked` is represented as a `phase_status` flag on the active phase (not a separate phase name) to preserve deterministic phase identity.
- WD v1 default `max_attempts` by phase: `init=1`, `plan=2`, `review=1` (manual gate), `narration=2`, `build_scenes=4`, `scene_qc=3`, `precache_voiceovers=2`, `final_render=2`, `assemble=2`.
- Mandatory manual gates in v1 are `review` approval and blocked-state resume approval; no other manual gates may be introduced without a spec update.
