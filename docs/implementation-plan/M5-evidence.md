# M5 Evidence - Voice, Render, and Assembly Contract Integration

Status: complete  
Date: 2026-03-01

## Scope Delivered

- Implemented deterministic voice metadata/cache contracts in `src/wet_donkey_voice/contracts.py`:
  - stable cache key generation from normalized text + voice config
  - required voice metadata contract (`voice_id`, `cache_key`, generation mode, duration, format, sample rate, channels, text digest)
  - explicit fallback/degraded policy validation and sidecar metadata persistence.
- Refactored voice adapter in `src/wet_donkey_voice/qwen_cached.py`:
  - deterministic `synthesize()` API returning structured metadata
  - cache hit/miss behavior with sidecar metadata writes
  - fallback behavior blocked unless explicitly enabled.
- Added render/assembly contract layer in `src/harness/contracts/media_pipeline.py`:
  - render precondition contract with required gate coverage (`schema -> contract -> semantic -> runtime`)
  - voice manifest, render manifest, and assembly manifest schema contracts
  - assembly integrity checks and final output verification with tolerance policy `max(0.5s, 2% expected)`.
- Added orchestration-facing validator CLI `scripts/validate_media_pipeline.py`:
  - `validate-voice-manifest`
  - `validate-render-preconditions`
  - `validate-assembly`.
- Integrated M5 contract checks in `scripts/build_video.sh`:
  - implemented `precache_voiceovers`, `final_render`, and `assemble` handlers
  - handlers fail closed unless contract validation succeeds
  - phase advancement now occurs only after successful media contract validation.

## Acceptance Criteria Check

- Voice outputs include required metadata and pass validation: PASS.
- Render/assembly only execute with validated prerequisites: PASS.
- Final output acceptance requires manifest + duration tolerance checks: PASS.

## Test Evidence

- `python3.13 -m pytest -q tests/contracts/test_voice_contracts.py tests/contracts/test_media_pipeline_contracts.py tests/contracts/test_validate_media_pipeline_cli.py` -> `8 passed`.
- `python3.13 -m pytest -q tests/contracts` -> `52 passed`.
- `python3.13 -m pytest -q tests/harness tests/test_training_corpus_upload.py` -> `11 passed`.
- `python3.13 -m pytest -q tests/contracts tests/harness tests/test_training_corpus_upload.py` -> `63 passed`.
- `bash -n scripts/build_video.sh` -> success.
- `python3.13 -m py_compile scripts/validate_media_pipeline.py src/wet_donkey_voice/contracts.py src/wet_donkey_voice/qwen_cached.py src/harness/contracts/media_pipeline.py` -> success.

Added/updated test coverage:
- `tests/contracts/test_voice_contracts.py`
  - deterministic cache key normalization
  - metadata sidecar + cache-hit behavior
  - fallback policy gating.
- `tests/contracts/test_media_pipeline_contracts.py`
  - render precondition gate enforcement
  - voice/render/assembly integrity checks
  - final output duration tolerance verification.
- `tests/contracts/test_validate_media_pipeline_cli.py`
  - CLI happy-path contract validation across voice/render/assembly
  - schema-failure exit-code regression.

## IntelliJ Validation

- `get_file_problems` on edited production files: no errors.
- `build_project` -> success.

## Lessons Traceability

- L-002: downstream media phases now require deterministic, validated prerequisites before phase progression.
- L-008: voice subsystem is stabilized behind explicit adapter and metadata/fallback policy contracts.
- L-009: render/assembly validations are implemented as explicit contract gates, not ad hoc checks.
- L-010: output verification and manifests codify runtime artifact boundaries for downstream integrity checks.
