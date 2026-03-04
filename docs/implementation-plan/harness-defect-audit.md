# Harness Defect Audit

Date: 2026-03-02  
Scope: `src/harness/` and its runtime integration path through `scripts/build_video.sh`  
Status: Critical defects present; phase progression beyond early stages is currently inoperable.

## Findings (Ordered by Severity)

1. `P0` Retry budget is effectively bypassed during per-scene loops.
- Evidence: `run_with_failure_policy` always clears failures on *any* successful sub-step (`clear_phase_failures`), which resets the active phase counter during `build_scenes`/`scene_qc` loops.
- Impact: Repeated phase failures can continue indefinitely without hitting blocked escalation, so the retry contract is not enforced.
- References:
  - [build_video.sh](/Users/velocityworks/IdeaProjects/wet-donkey/scripts/build_video.sh#L197)
  - [build_video.sh](/Users/velocityworks/IdeaProjects/wet-donkey/scripts/build_video.sh#L450)
  - [build_video.sh](/Users/velocityworks/IdeaProjects/wet-donkey/scripts/build_video.sh#L543)
  - [state.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/state.py#L256)

2. `P0` Scene quality gate is not recoverable by design in current orchestration path.
- Evidence: `scene_qc` fails 16/17 reports in retained run and phase remains `scene_qc`; no deterministic built-in scene repair loop is wired in the phase handler.
- Impact: Pipeline stalls in `scene_qc` with manual intervention required; no reliable forward progression.
- References:
  - [runtime_pipeline.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/runtime_pipeline.py#L334)
  - [build_video.sh](/Users/velocityworks/IdeaProjects/wet-donkey/scripts/build_video.sh#L467)
  - [project_state.json](/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/project_state.json)

3. `P0` Generated scene code has high runtime-defect density and is not pre-screened before QC.
- Evidence: Scene files contain undefined symbols and unsupported methods; QC reports mostly fail (`passed=false` and low scores).
- Impact: Build output is frequently non-renderable or semantically invalid, overwhelming QC and preventing stable advancement.
- References:
  - [scene_09_proof_2__similar_triangles.py](/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/scenes/scene_09_proof_2__similar_triangles.py#L12)
  - [scene_09_proof_2__similar_triangles.py](/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/scenes/scene_09_proof_2__similar_triangles.py#L44)
  - [runtime_pipeline.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/runtime_pipeline.py#L287)

4. `P1` Tool-usage validation for build scenes is heuristic and can false-pass.
- Evidence: `validate_timing_execution` accepts string markers (`run_time=`, `.wait(`) in generated code as proxy for actual tool usage.
- Impact: Required `code_execution` behavior can be bypassed by text patterns; semantic gate can pass without actual deterministic verification.
- References:
  - [parser.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/parser.py#L99)
  - [client.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/client.py#L59)

5. `P1` Prompt tool policy and runtime tool wiring are not single-source-of-truth.
- Evidence: Tool policy exists in prompt manifests and injected text, while runtime tools are independently assembled in `session.py` from phase + env toggles.
- Impact: Policy drift risk remains; model instructions and actual available tools can diverge.
- References:
  - [prompts.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/prompts.py#L53)
  - [session.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/session.py#L73)
  - [04_build_scenes manifest](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/prompts/04_build_scenes/manifest.yaml#L15)

6. `P1` Session continuation behavior is phase-fragmented and still persisted globally.
- Evidence: `previous_response_id` is disabled for scene phases, but `update_response_id` still writes latest response id from all phases.
- Impact: State semantics are unclear; future refactors can accidentally reintroduce context-carry bugs.
- References:
  - [session.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/session.py#L83)
  - [session.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/session.py#L95)
  - [client.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/client.py#L63)

7. `P2` Manifest file format is mislabeled (`.yaml` files parsed as JSON).
- Evidence: Manifest loader uses `json.loads` on `manifest.yaml`.
- Impact: Confusing tooling and contributor errors; YAML-native edits can silently break loading.
- References:
  - [prompt_manifest.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/prompt_manifest.py#L113)
  - [04_build_scenes manifest](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/prompts/04_build_scenes/manifest.yaml#L1)

8. `P2` Scaffold validation is structural only; no compile/lint/renderability gate before QC.
- Evidence: `validate_built_scene_files` checks only marker presence and non-empty slot body.
- Impact: Syntactically broken or API-invalid scene code reaches QC phase, causing expensive late failures.
- References:
  - [runtime_pipeline.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/runtime_pipeline.py#L274)
  - [runtime_pipeline.py](/Users/velocityworks/IdeaProjects/wet-donkey/src/harness/contracts/runtime_pipeline.py#L287)

## Observed Runtime Evidence

- Retained project: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812`
- Latest QC aggregate:
  - reports generated: `17`
  - failed or below threshold: `16`
  - phase remains: `scene_qc`
- References:
  - [events.jsonl](/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/log/events.jsonl)
  - [scene_17 QC](/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/qc/scene_17_call_to_action_qc.json)

## Required Stabilization Actions

1. Fix retry accounting so phase attempt counters are only cleared when the phase succeeds, not per sub-step.
2. Add deterministic per-scene repair loop (bounded attempts) inside `scene_qc` phase execution flow.
3. Add pre-QC hard gates:
- Python compile pass for all scenes.
- Static banlist for known invalid API patterns.
- Minimum deterministic scene contract checks before QC invocation.
4. Unify tool policy:
- Derive runtime tool wiring from manifest policy directly (single source).
5. Make session continuity semantics explicit and testable per phase.
6. Rename prompt manifests to `.json` or switch loader to YAML parser.
