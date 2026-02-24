# 16 Render and Assembly

Status: draft

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

- Verify final file exists, duration is within expected tolerance, and manifest completeness is satisfied.
- Assembly success is not declared without verification pass.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-002 | Render/assembly are deterministic phase outcomes with strict prerequisites. |
| L-003 | Final pipeline stages do not rely on repeated blind repair attempts. |
| L-009 | Runtime and assembly validations are explicit, layered gates. |
| L-010 | Output artifacts are tracked via lineage metadata and kept separate from core source. |

## Open Questions

- What duration tolerance should be enforced for final output validation?
- Which ffmpeg/manim settings are hard policy vs configurable defaults?
- Should assembly run be resumable from partial scene success states in v1?

## Decisions

- WD render and assembly require validated prerequisites before execution.
- Final output is accepted only after deterministic verification checks.
- Render/assembly diagnostics must be sufficient for reproducible failure analysis.
