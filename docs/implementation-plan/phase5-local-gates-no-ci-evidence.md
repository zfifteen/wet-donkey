# Phase 5 Local Gates and No-CI Transition Evidence

Status: complete  
Date: 2026-03-01

## Scope Delivered

- Removed GitHub workflow automation for current version.
- Added local/manual gate runner: `scripts/run_phase5_local_gates.sh`.
- Added no-workflow guard test: `tests/contracts/test_no_github_workflows.py`.
- Updated live API smoke script for manual/local execution controls and observability assertions.
- Hardened live smoke compatibility for current runtime:
  - xAI collections bootstrap now supports `xai_sdk` create signature drift and management-key constructor usage.
  - parser now accepts JSON-string payloads returned by runtime SDK responses.
  - `init` emits `phase_start` observability for first-run project bootstrap.
  - retired temporary `FH_ENABLE_TRAINING_CORPUS=0` fallback dependency in live validation flow.
- Updated canonical docs to reflect no GitHub CI policy for current version.

## Workflow Removal Evidence

Commands:

```bash
ls -la .github/workflows
python3.13 -m pytest -q tests/contracts/test_no_github_workflows.py
```

Result:

```text
total 0
drwxr-xr-x@ 2 velocityworks  staff  64 Mar  1 15:53 .
drwxr-xr-x@ 3 velocityworks  staff  96 Mar  1 13:34 ..
.                                                                        [100%]
1 passed in 0.25s
```

## Local Gate Runner Evidence

Deterministic local gates:

```bash
./scripts/run_phase5_local_gates.sh
```

Result:

```text
[LOCAL_GATES] ... START contract and harness tests
79 passed in 4.34s
[LOCAL_GATES] ... PASS  contract and harness tests
[LOCAL_GATES] ... START prompt schema alignment
Prompt/schema alignment check passed.
[LOCAL_GATES] ... PASS  prompt schema alignment
[LOCAL_GATES] ... START fixture e2e smoke
[E2E_FIXTURE] ... Deterministic fixture e2e smoke test passed
[LOCAL_GATES] ... PASS  fixture e2e smoke
[LOCAL_GATES] ... SUMMARY passed=3 failed=0 total=3
```

Live API manual mode:

```bash
./scripts/run_phase5_local_gates.sh --with-live-api
```

Preflight behavior:
- Fails with a clear message when `XAI_API_KEY` or `XAI_MANAGEMENT_API_KEY` is missing.
- Runs `tests/test_e2e_responses_api.sh` when both keys are present.

Missing-key preflight evidence:

```text
[LOCAL_GATES] ... FAIL  live API e2e smoke
[LOCAL_GATES] ... XAI_API_KEY and XAI_MANAGEMENT_API_KEY are required when --with-live-api is enabled
[LOCAL_GATES] ... SUMMARY passed=3 failed=1 total=4
```

## Live API Smoke (Keys Present)

Canonical run mode for this slice (manual/local only):

```bash
FH_ENABLE_TRAINING_CORPUS=0 \
E2E_KEEP_PROJECT=1 \
E2E_PROJECT_NAME="e2e_live_20260301_163917" \
bash tests/test_e2e_responses_api.sh
```

Result:

```text
[E2E_TEST] ... Phase correctly advanced to 'review'.
[E2E_TEST] ... Plan was successfully generated with title: 'Unlocking the Pythagorean Theorem: Secrets of Right Triangles'
[E2E_TEST] ... Observability assertions passed for init and plan.
[E2E_TEST] ... E2E test finished successfully!
live_smoke_exit_code=0
live_smoke_project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_20260301_163917
```

Post-run verification:

```text
phase=review
plan.title=Unlocking the Pythagorean Theorem: Secrets of Right Triangles
events_file=present
init:phase_start:1
init:phase_success:1
plan:phase_start:1
plan:phase_success:1
phase_failure:0
events_path:/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_20260301_163917/log/events.jsonl
```

Remediation evidence before final pass:
- Failure 1: `Client.create() got an unexpected keyword argument 'description'`.
  - Fix: `scripts/initialize_training_corpus.py` now uses compatibility-safe collection creation.
- Failure 2: `ValueError: Please provide a management API key.` / `UNAUTHENTICATED` on collections API.
  - Fix: `init` supports `FH_ENABLE_TRAINING_CORPUS=0` and writes deterministic metadata stubs for local/manual live smoke.
- Failure 3: `Plan` schema validation received JSON string payload.
  - Fix: parser normalizes string payloads via JSON decode before model validation.
- Failure 4: Missing `init` `phase_start` event on first-run projects.
  - Fix: `init` emits bootstrap `phase_start` after project creation when initial pre-phase logging cannot write.

## Multi-Topic Live API Stability Matrix

Execution mode:

```bash
FH_ENABLE_TRAINING_CORPUS=0
E2E_KEEP_PROJECT=1
bash tests/test_e2e_responses_api.sh  # repeated with per-run E2E_PROJECT_NAME and E2E_TOPIC
```

Runs completed: 3/3 successful.

- `e2e_live_matrix_1_20260301_173656`
  topic: The first 30 seconds of a video explaining the Pythagorean theorem
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_matrix_1_20260301_173656`
- `e2e_live_matrix_2_20260301_173729`
  topic: A concise intuition for derivatives as slope
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_matrix_2_20260301_173729`
- `e2e_live_matrix_3_20260301_173824`
  topic: How binary search halves the search space
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_matrix_3_20260301_173824`

Observed trend summary:
- Success rate: `100%` (3/3).
- No `phase_failure` events detected in any run.
- Observed end-to-end durations (start -> success): ~33s, ~55s, ~39s.
- No new recurring failure signatures were observed in the matrix pass.

## FH_ENABLE_TRAINING_CORPUS=1 Validation (Dedicated Key + Host Compatibility)

Validation run:

```bash
E2E_ENABLE_TRAINING_CORPUS=1 \
E2E_KEEP_PROJECT=1 \
E2E_PROJECT_NAME="e2e_live_training_on_guard_20260301_175252" \
bash tests/test_e2e_responses_api.sh
```

Result:

```text
live_smoke_exit_code=2
live_smoke_project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_on_guard_20260301_175252
```

Failure context (captured from `project_state.json`):

```text
error_code=POLICY_VIOLATION
phase=init
blocked=true
blocked_reason=FORCE_BLOCK
error_message=FH_ENABLE_TRAINING_CORPUS=1 requires a dedicated XAI_MANAGEMENT_API_KEY; reusing XAI_API_KEY is not allowed for collections operations
```

Conclusion:
- `FH_ENABLE_TRAINING_CORPUS=1` path is now deterministically guarded.
- Dedicated management-key reuse guard works as expected (API key reuse is blocked).

Revalidation attempt after `.env` management-key update (2026-03-01):

```bash
E2E_ENABLE_TRAINING_CORPUS=1 \
E2E_KEEP_PROJECT=1 \
E2E_PROJECT_NAME="e2e_live_training_on_valid_20260301_175742" \
bash tests/test_e2e_responses_api.sh
```

Observed result:

```text
live_smoke_exit_code=2
live_smoke_project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_on_valid_20260301_175742
Error: Invalid XAI_MANAGEMENT_API_KEY for collections operations. Provide a dedicated management key and retry.
```

Interpretation:
- `XAI_MANAGEMENT_API_KEY` is present and different from `XAI_API_KEY`, but still rejected by Collections API (`UNAUTHENTICATED` / invalid bearer token).
- Root cause was not key presence but management host compatibility for collections calls in this environment.

Remediation applied:
- `scripts/initialize_training_corpus.py` now attempts management host candidates in order:
  - `management-api.x.ai`
  - `api.x.ai` fallback when legacy host returns `UNAUTHENTICATED Invalid bearer token`
- Host can be explicitly overridden with `XAI_MANAGEMENT_API_HOST`.

Validation run after remediation (2026-03-01):

```bash
E2E_ENABLE_TRAINING_CORPUS=1 \
E2E_KEEP_PROJECT=1 \
E2E_PROJECT_NAME="e2e_live_training_on_fixed_20260301_180209" \
bash tests/test_e2e_responses_api.sh
```

Observed result:

```text
live_smoke_exit_code=0
live_smoke_project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_on_fixed_20260301_180209
Using fallback management API host: api.x.ai
Phase correctly advanced to 'review'
Observability assertions passed for init and plan
```

Post-run verification:

```text
phase=review
phase_status=active
events_path=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_on_fixed_20260301_180209/log/events.jsonl
init:phase_start:1
init:phase_success:1
plan:phase_start:1
plan:phase_success:1
phase_failure:0
collections_metadata=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_on_fixed_20260301_180209/.collections_metadata.json
```

Current state:
- `E2E_ENABLE_TRAINING_CORPUS=1` live smoke is now passing with retained artifacts.
- Stability expansion completed with a 3-topic live matrix under training-corpus-enabled mode.
- Temporary `FH_ENABLE_TRAINING_CORPUS=0` fallback dependency has been retired from live validation flow.

Fallback retirement verification run (2026-03-01):

```bash
E2E_KEEP_PROJECT=1 \
E2E_PROJECT_NAME="e2e_live_post_fallback_retire_20260301_181812" \
bash tests/test_e2e_responses_api.sh
```

Observed result:

```text
live_smoke_exit_code=0
live_smoke_project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812
Using fallback management API host: api.x.ai
Phase correctly advanced to 'review'
Observability assertions passed for init and plan
```

## Manual Progression Evidence: `review -> narration` (Retained Artifacts)

Manual transition and execution run (2026-03-01):

```bash
python3.13 scripts/update_project_state.py set \
  --project-dir projects/e2e_live_post_fallback_retire_20260301_181812 \
  --key phase \
  --value narration \
  --actor manual-review

bash scripts/build_video.sh e2e_live_post_fallback_retire_20260301_181812 \
  --topic \"The first 30 seconds of a video explaining the Pythagorean theorem\"
```

Observed result:

```text
phase=build_scenes
phase_status=active
review_to_narration_transitions=1
narration:phase_start:1
narration:phase_success:1
narration:phase_failure:0
narration:phase_blocked:0
narration_script.py=present
artifacts/scene_manifest.json=present
scenes_count=17
project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812
events_path=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812/log/events.jsonl
```

## Manual Progression Evidence: `build_scenes -> scene_qc` (Retained Artifacts)

Execution target:

```text
project_dir=/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_post_fallback_retire_20260301_181812
```

Commands:

```bash
bash scripts/build_video.sh e2e_live_post_fallback_retire_20260301_181812 --topic "<stored topic>"   # build_scenes
bash scripts/build_video.sh e2e_live_post_fallback_retire_20260301_181812 --topic "<stored topic>"   # scene_qc
python3.13 scripts/runtime_phase_contracts.py validate-build-scenes --project-dir projects/e2e_live_post_fallback_retire_20260301_181812
python3.13 scripts/runtime_phase_contracts.py validate-scene-qc --project-dir projects/e2e_live_post_fallback_retire_20260301_181812
```

Observed outcomes:

```text
build_scenes: completed once and advanced to scene_qc
build_scenes_to_scene_qc_transitions=1
validate-build-scenes: status=ok, scene_count=17

scene_qc: executed repeatedly, generated QC reports for all 17 scenes
validate-scene-qc: failed threshold gate (multiple scenes scored < 0.7 and/or passed=false)
phase remains scene_qc (phase_status=active)
```

Observability coverage from `events.jsonl`:

```text
build_scenes:phase_start:3
build_scenes:phase_success:1
build_scenes:phase_failure:2
build_scenes:phase_blocked:0

scene_qc:phase_start:9
scene_qc:phase_success:0
scene_qc:phase_failure:9
scene_qc:phase_blocked:0
```

Remediations applied during this slice:
- Parser timing-validation compatibility fix for SDK tool-usage shape:
  - accepted `SERVER_SIDE_TOOL_CODE_EXECUTION: <count>` form.
  - added fallback timing-marker validation from `scene_body` when tool metadata is absent.
- Session stability fix for scene-level phases:
  - `build_scenes` and `scene_qc` now run without `previous_response_id` to prevent context growth and truncated schema payloads.
- Targeted scene file fixes on retained artifact project:
  - repaired syntax/runtime issues in scenes 13, 16, and 17 to address deterministic QC defects.

Current status of this progression:
- Contract/observability evidence for both phases is complete.
- Scene quality gate still requires iterative repair/stabilization before `scene_qc -> precache_voiceovers`.

Training-enabled live matrix execution (2026-03-01):

```bash
E2E_ENABLE_TRAINING_CORPUS=1
E2E_KEEP_PROJECT=1
bash tests/test_e2e_responses_api.sh  # repeated with per-run E2E_PROJECT_NAME and E2E_TOPIC
```

Runs completed: 3/3 successful.

- `e2e_live_training_matrix_1_20260301_180531`
  topic: The first 30 seconds of a video explaining the Pythagorean theorem
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_matrix_1_20260301_180531`
- `e2e_live_training_matrix_2_20260301_180643`
  topic: A concise intuition for derivatives as slope
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_matrix_2_20260301_180643`
- `e2e_live_training_matrix_3_20260301_180717`
  topic: How binary search halves the search space
  exit: `0`, final phase: `review`, plan title: non-empty
  events: `init(start/success)=1/1`, `plan(start/success)=1/1`, `phase_failure=0`
  project dir: `/Users/velocityworks/IdeaProjects/wet-donkey/projects/e2e_live_training_matrix_3_20260301_180717`

Observed trend summary:
- Success rate: `100%` (3/3).
- No `phase_failure` events detected.
- Collections initialization succeeded in all runs using fallback management host `api.x.ai`.

## Manual Live API Smoke Procedure

1. Ensure `.env` has both `XAI_API_KEY` and `XAI_MANAGEMENT_API_KEY`.
2. Run `E2E_KEEP_PROJECT=1 E2E_PROJECT_NAME=\"e2e_live_<timestamp>\" bash tests/test_e2e_responses_api.sh`.
3. Confirm live smoke reaches `phase=review` and emits `phase_start` + `phase_success` for `init` and `plan`.
4. Confirm no `phase_failure` event is present in `projects/<run_id>/log/events.jsonl`.

## Canonical Docs Updated

- `AGENTS.md`
- `README.md`
- `docs/implementation-plan/README.md`
- `docs/tech-spec/15-testing/README.md`
- `docs/implementation-plan/M6-evidence.md`
- `docs/implementation-plan/phase5-fixture-e2e-evidence.md`

## Policy Decision

- GitHub CI/Actions are deferred to a future version decision.
- Current WD quality enforcement is local/manual only.
