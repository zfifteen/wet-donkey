# M3 Evidence - Prompt/Schema/Parser Contract Lock

Status: complete  
Date: 2026-03-01

## Scope Delivered

- Introduced machine-readable per-phase prompt manifests (`manifest.yaml`) co-located with prompt templates:
  - `src/harness/prompts/00_plan/manifest.yaml`
  - `src/harness/prompts/02_narration/manifest.yaml`
  - `src/harness/prompts/04_build_scenes/manifest.yaml`
  - `src/harness/prompts/05_scene_qc/manifest.yaml`
  - `src/harness/prompts/06_scene_repair/manifest.yaml`
- Implemented prompt manifest contract enforcement in `src/harness/contracts/prompt_manifest.py`:
  - strict declared variable contract (required + optional)
  - schema map validation (`phase` -> canonical schema)
  - tool/annotation policy compatibility validation
  - output field parity with canonical schema fields.
- Enforced strict prompt rendering and runtime variable validation in `src/harness/prompts.py`:
  - strict undeclared-variable rejection
  - missing required variable rejection
  - contract validation before every render.
- Added parser/schema alignment lock in `src/harness/parser.py`:
  - parser-schema contract version alignment guard
  - canonical schema validation function for phase payloads.
- Enforced parser-side schema validation in harness client:
  - `src/harness/client.py` now validates phase payloads via parser contract before mutation/state updates.
- Added CI-style alignment check script:
  - `scripts/check_prompt_schema_alignment.py`.

## Acceptance Criteria Check

- Undeclared/missing template variables fail fast: PASS.
- Prompt output fields map 1:1 to schema fields: PASS.
- Parser rejects out-of-contract fields deterministically: PASS.

## Test Evidence

- `python3.13 -m pytest -q tests/contracts` -> `39 passed`.
- `python3.13 -m pytest -q tests/harness tests/test_training_corpus_upload.py` -> `11 passed`.
- `python3.13 scripts/check_prompt_schema_alignment.py` -> `Prompt/schema alignment check passed.`

Added/updated test coverage:
- `tests/contracts/test_prompt_manifest_contract.py`
- `tests/contracts/test_parser_schema_contract.py`
- `tests/contracts/test_prompt_schema_alignment_cli.py`

## IntelliJ Validation

- `get_file_problems` for edited M3 production files: no errors.
- `build_project` -> success.

## Lessons Traceability

- L-005: prompt/schema/parser alignment is contract-enforced with CI-checkable validation.
- L-007: prompt policy now encoded as versioned manifests and validated in code.
- L-009: schema/contract validation ownership explicitly split between prompt preflight and parser payload validation.
