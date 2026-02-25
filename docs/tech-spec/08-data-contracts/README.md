# 08 Data Contracts

Status: draft

## Purpose

Define canonical data contracts across pipeline state, phase payloads, and generated artifacts so components interoperate without drift.

## Scope

- `project_state.json` contract.
- Session metadata contracts (LLM/session/retrieval IDs).
- Phase input/output schemas.
- Scaffold insertion contract for generated scene bodies.
- Contract versioning and compatibility rules.

## Design

### Contract Ownership

- Orchestrator owns phase/state contracts.
- Harness owns structured phase outputs.
- Parser/validators enforce semantic and runtime constraints.
- Scaffold generator owns immutable scene file boundaries.
- LLM output ownership is limited to schema-constrained content fields; deterministic code owns all infrastructure/state mutation contracts.

### Core Contracts

1. `project_state.json`
- Required: `project_name`, `topic`, `phase`, `history`.
- Optional: `xai_session`, `training_corpus`, `failure_context`.
- Must be schema-validated on every read/write.

2. Phase Output Schemas
- Each phase has one canonical schema definition.
- Prompts must target schema fields exactly (no parallel informal fields).
- Schema changes require coordinated updates to prompt templates, parser logic, and tests.

2.1 Prompt Capability Manifest (Draft)
- Each prompt template includes a machine-readable capability manifest:
  - `required_tools` (array)
  - `allowed_tools` (array)
  - `required_annotations` (array; for example citations)
  - `output_restrictions` (array; for example "no comments")
- Orchestrator must validate that required tools and annotations are compatible with phase tool policy and output schema.
- If incompatible, phase fails closed before any model call.

Example (Draft):
```
{
  "prompt_id": "build_scenes_v1",
  "required_tools": [],
  "allowed_tools": [],
  "required_annotations": [],
  "output_restrictions": ["json_only", "no_comments", "no_code_fences"]
}
```

3. Scene Scaffold Contract
- Immutable slot markers define insertion boundaries.
- Generator outputs only slot body content.
- Parser rejects outputs that modify scaffold outside approved regions.

4. Session/Corpus Metadata
- `.xai_session.json` and collection metadata must be versioned and backward-compatible within major WD spec version.
- Missing required metadata is a hard failure, not silently repaired.

5. Context Manager Contract (Draft)

Status: draft (subject to refinement during tech spec iteration)

Purpose: define the deterministic interface between orchestrator/harness and the Context Manager for payload assembly and context continuity enforcement.
Logging: see `docs/tech-spec/13-logging-and-observability/README.md` for required Context Manager log fields.

Required fields (input):
- `model_id` (string)
- `phase` (string)
- `previous_response_id` (string | null)
- `error_code` (string)
- `error_message` (string)
- `artifact_refs` (array of stable artifact pointers)
- `artifact_diff` (string | null) — compact diff summary only
- `retry_attempt` (int)
- `context_budget_tokens` (int)
- `timestamp_utc` (string)

Required fields (output):
- `payload` (string | structured object) — ready for model call
- `payload_tokens_est` (int)
- `payload_compacted` (bool)
- `dropped_fields` (array of string)
- `previous_response_id_valid` (bool)
- `retry_eligible` (bool)

Required invariants:
- `payload_tokens_est <= context_budget_tokens`
- If `previous_response_id_valid` is false, `retry_eligible` must be false unless `context_restored` is true.
- If `retry_eligible` is false, orchestrator must fail closed with `needs_human_review`.

Optional fields:
- `context_restored` (bool)
- `full_payload_pointer` (string) — deterministic pointer to full artifacts/logs
- `compaction_reason` (string)

Example (Draft)

Input:
```
{
  "model_id": "grok-4-1-fast-reasoning",
  "phase": "build_scenes",
  "previous_response_id": "ba857ddd-7be3-bfe8-c058-c0a9a37046aa",
  "error_code": "RUNTIME_VALIDATION_FAILED",
  "error_message": "MathTex compilation error in scene_03.py",
  "artifact_refs": [
    "logs/build.log#L770",
    "logs/error.log#L119"
  ],
  "artifact_diff": "scene_03.py:34 MathTex string adjusted; removed \\left...\\right",
  "retry_attempt": 2,
  "context_budget_tokens": 8192,
  "timestamp_utc": "2026-02-25T01:17:58Z"
}
```

Output:
```
{
  "payload": {
    "phase": "build_scenes",
    "error": {
      "code": "RUNTIME_VALIDATION_FAILED",
      "message": "MathTex compilation error in scene_03.py"
    },
    "diff": "scene_03.py:34 MathTex string adjusted; removed \\left...\\right",
    "artifact_pointers": [
      "logs/build.log#L770",
      "logs/error.log#L119"
    ]
  },
  "payload_tokens_est": 412,
  "payload_compacted": true,
  "dropped_fields": ["full_build_log", "full_error_log"],
  "previous_response_id_valid": true,
  "retry_eligible": true,
  "full_payload_pointer": "logs/context_payloads/scene_03_retry_2.json",
  "compaction_reason": "payload exceeded budget"
}
```

Validation Checklist (Draft)
- `model_id` is recognized and maps to a known context limit.
- `context_budget_tokens` equals the derived budget for the model.
- `payload_tokens_est` does not exceed `context_budget_tokens`.
- `previous_response_id_valid` is true before allowing continuation.
- `artifact_diff` is present if retry is permitted.
- `dropped_fields` is non-empty when `payload_compacted` is true.

### Versioning Rules

- Every contract includes a `contract_version` field.
- Breaking changes require explicit migration notes and test updates.
- No implicit upgrades during runtime.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stable versioned interfaces prevent unbounded harness churn. |
| L-004 | Scaffold boundaries are immutable and validator-enforced. |
| L-005 | One source of truth for schema/prompt/parser alignment. |
| L-007 | Contract docs are authoritative and must update with code. |
| L-009 | Validation layers map to explicit contract ownership. |
| L-010 | Runtime artifacts are separated from core contract definitions. |
| L-017 | Prompt capability manifests are validated against tool policy and output restrictions. |

## Open Questions

- Which contract fields are mandatory in v1 vs deferred?
- How strict should backward compatibility be for session metadata in pre-release WD milestones?
- Should schema registries be centralized under one module or kept per phase package?

## Decisions

- WD will use explicit versioned contracts for state, phase outputs, and session metadata.
- Prompt, schema, parser, and orchestrator contracts must remain synchronized or CI fails.
- Scaffold mutation outside slot boundaries is a hard contract violation.
- LLM-generated payloads are untrusted until they pass deterministic contract and validation gates.
