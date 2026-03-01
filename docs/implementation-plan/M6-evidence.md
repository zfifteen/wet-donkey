# M6 Evidence - Observability, Risk Controls, and CI Enforcement

Status: complete  
Date: 2026-03-01

## Scope Delivered

- Implemented structured observability contract in `src/harness/contracts/observability.py`:
  - versioned JSONL event schema with required correlation fields (`run_id`, `phase_attempt_id`)
  - event stream support for phase lifecycle, failure, blocked escalation, transitions, and trace bundles
  - deterministic blocked trace bundle export with failure diagnostics, retry summary, artifact pointers, and events tail.
- Integrated observability into state control path in `scripts/update_project_state.py`:
  - `fail` now emits structured failure/blocked events and auto-exports blocked trace bundles
  - `set` phase transitions emit transition events
  - `clear-failures` emits `phase_unblocked` events
  - new `log-event` command allows orchestrator phase start/success lifecycle logging.
- Integrated phase lifecycle logging in `scripts/build_video.sh`:
  - emits `phase_start` and `phase_success` for each phase attempt
  - emits `phase_blocked` entry event when phase is already blocked at orchestrator entry.
- Implemented docs-as-gate CI policy in `scripts/check_docs_as_gate.py`:
  - fails when contract-touching changes are missing canonical docs updates.
- Added CI workflow baseline in `.github/workflows/ci.yml`:
  - runs contract/harness tests, prompt/schema alignment check, and docs-as-gate policy.
- Added lessons-linked regression matrix:
  - `tests/contracts/lessons_regression_matrix.json`
  - validator test `tests/contracts/test_lessons_regression_matrix.py`.

## Acceptance Criteria Check

- Each phase attempt is traceable with run and attempt IDs: PASS.
- Blocked runs produce actionable diagnostics: PASS.
- CI enforces contract-critical suites and alignment checks: PASS.

## Test Evidence

- `python3.13 -m pytest -q tests/contracts/test_observability_contract.py tests/contracts/test_docs_as_gate_cli.py tests/contracts/test_lessons_regression_matrix.py tests/contracts/test_update_project_state_cli.py` -> `8 passed`.
- `python3.13 -m pytest -q tests/contracts tests/harness tests/test_training_corpus_upload.py` -> `70 passed`.
- `python3.13 -m pytest -q tests/contracts/test_docs_as_gate_cli.py tests/contracts/test_observability_contract.py tests/contracts/test_update_project_state_cli.py` -> `6 passed`.
- `python3.13 scripts/check_prompt_schema_alignment.py` -> passed.
- `python3.13 scripts/check_docs_as_gate.py --changed-file src/harness/contracts/observability.py --changed-file docs/implementation-plan/README.md` -> passed.
- `python3.13 -m py_compile src/harness/contracts/observability.py scripts/update_project_state.py scripts/check_docs_as_gate.py` -> success.
- `bash -n scripts/build_video.sh` -> success.

## IntelliJ Validation

- `get_file_problems` on edited production files: no errors.
- `build_project` -> success.

## Lessons Traceability

- L-003: failure diagnostics now include signature/delta context in structured events and blocked trace exports.
- L-006: CI/docs policy and regression matrix enforce scoped, reviewable contract changes.
- L-007: canonical docs are now an explicit gate for contract-touching changes.
- L-009: validation ownership/gate context is emitted as structured observability metadata.
- L-010: blocked trace bundles and artifact pointers make runtime lineage explicit and auditable.

## Policy Revision Note (2026-03-01)

- GitHub CI is intentionally retired for the current WD version.
- `.github/workflows/ci.yml` was removed as part of the Phase 5 local-gates transition.
- Contract/docs enforcement continues through local/manual gates, primarily `scripts/run_phase5_local_gates.sh`.
