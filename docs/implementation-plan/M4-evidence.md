# M4 Evidence - Validation Hierarchy and Retry Control

Status: complete  
Date: 2026-03-01

## Scope Delivered

- Implemented validation hierarchy metadata and ownership in `src/harness/exit_codes.py`:
  - canonical gate order (`schema -> contract -> semantic -> runtime -> assembly`)
  - exit-code policy now includes gate, owner component, machine error code, and retryability
  - phase-aware schema retryability retained and enforced.
- Implemented machine-readable failure payload/signature + retry controls in `src/harness/contracts/state.py`:
  - deterministic normalized error signatures
  - structured failure context fields (`gate`, `owner_component`, `retryable`, `error_signature`, loop flags, block reasons)
  - no-blind-retry enforcement (retries without meaningful delta/evidence are blocked)
  - loop-risk detection based on repeated signature + attempt progression.
- Extended state CLI failure recording surface in `scripts/update_project_state.py`:
  - accepts gate/owner/retryability/signature/delta/evidence fields and persists structured failure context.
- Updated orchestrator failure policy in `scripts/build_video.sh`:
  - table-driven classification from exit codes to validation gate/owner/retryability
  - phase-specific schema retryability for code `3`
  - passes structured failure metadata to state recorder.

## Acceptance Criteria Check

- Validation failures identify owning component and retryability: PASS.
- Identical retry loops are detected and escalated to blocked: PASS.
- No blind retries without new context are allowed: PASS.

## Test Evidence

- `python3.13 -m pytest -q tests/contracts` -> `44 passed`.
- `python3.13 -m pytest -q tests/harness tests/test_training_corpus_upload.py` -> `11 passed`.
- `python3.13 -m pytest -q tests/contracts tests/harness tests/test_training_corpus_upload.py` -> `55 passed`.
- `bash -n scripts/build_video.sh` -> success.

Added/updated test coverage:
- `tests/contracts/test_harness_exit_codes.py`
  - gate/owner metadata assertions
  - validation gate ordering checks.
- `tests/contracts/test_retry_blocking.py`
  - loop-signature blocking regression
  - non-retryable immediate block
  - meaningful-delta retry allowance.

## IntelliJ Validation

- `get_file_problems` on edited production files: no errors.
- `build_project` -> success.

## Lessons Traceability

- L-003: retry loops are bounded and blind retries are blocked.
- L-005: validation ownership is machine-readable and phase-aware.
- L-009: layered validation hierarchy encoded as deterministic contract metadata.
