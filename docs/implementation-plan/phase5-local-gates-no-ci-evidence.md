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
  - `init` now supports `FH_ENABLE_TRAINING_CORPUS=0` with deterministic collections metadata stubs.
  - parser now accepts JSON-string payloads returned by runtime SDK responses.
  - `init` emits `phase_start` observability for first-run project bootstrap.
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

## Manual Live API Smoke Procedure

1. Ensure `.env` has both `XAI_API_KEY` and `XAI_MANAGEMENT_API_KEY`.
2. Run `FH_ENABLE_TRAINING_CORPUS=0 E2E_KEEP_PROJECT=1 E2E_PROJECT_NAME=\"e2e_live_<timestamp>\" bash tests/test_e2e_responses_api.sh`.
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
