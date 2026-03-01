# 16 Render and Assembly

Status: approved

## Purpose

Define deterministic render and assembly behavior so final output quality is reproducible and failures are diagnosable.

## Scope

- Scene render prerequisites.
- Render execution contract.
- Assembly input/output contracts.
- Failure handling and output verification.

## Design

### Render Preconditions

- Scene code has passed schema/contract/semantic/runtime gates.
- Narration and voice assets are ready with verified duration metadata.
- Required environment/tooling checks pass preflight.

### Render Contract

- Render executes per scene with stable config (resolution/fps/output naming).
- Render metadata includes scene ID, duration, and run identifier.
- Render failures are non-silent and attach reproducible diagnostics.

### Assembly Contract

- Assembly consumes validated per-scene video/audio pairs.
- Ordering is derived from canonical plan/scene sequence.
- Output includes final manifest describing inputs, durations, and assembly parameters.

### Output Verification

- Verify final file exists, duration is within expected tolerance, and manifest coverage requirements are satisfied.
- Assembly success is not declared without verification pass.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-002 | Render/assembly are deterministic phase outcomes with strict prerequisites. |
| L-003 | Final pipeline stages do not rely on repeated blind repair attempts. |
| L-009 | Runtime and assembly validations are explicit, layered gates. |
| L-010 | Output artifacts are tracked via lineage metadata and kept separate from core source. |

## Open Questions

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD render and assembly require validated prerequisites before execution.
- Final output is accepted only after deterministic verification checks.
- Render/assembly diagnostics must be sufficient for reproducible failure analysis.
- Final output duration tolerance is `max(0.5s, 2% of expected duration)` unless a phase-specific stricter bound is configured.
- v1 policy settings for render are fixed defaults (`resolution`, `fps`, codec/container profile) with validated config overrides allowed only within documented ranges.
- Assembly resume from partial scene success is supported in v1 when prior scene manifests and checksums are present and validated.
