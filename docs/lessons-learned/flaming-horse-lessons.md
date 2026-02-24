# Flaming Horse Lessons Log

Status: active
Last updated: 2026-02-24

## Purpose

Capture concrete design and implementation failures observed in Flaming Horse and map each one to a specific Wet Donkey prevention strategy.

## How To Use This Log

1. Add one row per distinct FH failure pattern.
2. Keep findings evidence-based (file paths, behavior, logs, reproducible symptoms).
3. Define WD prevention as a clear architectural/process rule.
4. Keep status current: `planned`, `in-progress`, `implemented`, or `verified`.

## Lesson Table

| ID | FH Failure Pattern | Evidence (FH path/log/runtime symptom) | Root Cause | WD Prevention Strategy | Owner | Status | Notes |
|---|---|---|---|---|---|---|---|
| L-001 | Rapid architecture churn in LLM harness layer | PRs #34, #60, #72, #80, #92 repeatedly reworked harness/API strategy across `harness/` and `harness_responses/` | Core interfaces and migration boundaries were not frozen before feature expansion | Define a versioned harness contract and migration plan in WD spec before implementation; no parallel harness expansion without explicit deprecation plan | WD Team | planned | High-maintenance churn driver |
| L-002 | Phase/state contract instability in orchestrator flow | PRs #24, #40, #52, #73, #82, #85, #90 repeatedly modified phase behavior, validation gates, and scene flow | Pipeline state machine was not treated as a strict contract with acceptance tests per phase | Make phase transitions deterministic and schema-validated (`project_state` contract + phase-specific acceptance tests) | WD Team | planned | Direct reliability risk |
| L-003 | Self-heal loops became primary path instead of fallback | PR #55 explicitly audits parse failure loop; PRs #40 and #73 target loop convergence and repair behavior | First-pass generation quality/contracts were too weak; retries compensated for design gaps | In WD, optimize first-pass correctness and cap retries; retry policy must require new evidence/context each attempt | WD Team | planned | Prevent infinite/near-infinite repair cycles |
| L-004 | Scaffold/slot contract drift in generated scenes | PRs #4, #51, #52, #58, #73 focus on scaffold generation fixes, duplicate helper removal, and stricter validation | Scaffold boundaries were mutable and not continuously verified | Introduce immutable scaffold markers plus automated contract tests that run before build/repair phases | WD Team | planned | Core generator integrity issue |
| L-005 | Prompt/schema drift caused parsing and serialization failures | PR #72 (JSON responses), #76 (timing validation), #77 (triple-quote corruption), #85/#89/#90 (prompt/schema alignment/layout validation) | Prompt contracts and parser expectations evolved independently | Single source of truth for phase schemas and prompt manifests; CI check that prompt outputs map exactly to parser/schema contracts | WD Team | planned | High frequency failure source |
| L-006 | Oversized multi-concern PRs increased regression risk | PRs #60, #92, #80, #42, #44 changed large surfaces (50-100 files) across docs/scripts/harness/examples at once | Changes were not scoped to single concern/milestone | Enforce smaller milestone PR slices in WD plan; one architectural concern per PR with explicit rollback boundary | WD Team | planned | Maintainability and review quality issue |
| L-007 | Documentation drift and stale policy references | PRs #2, #33, #36, #79, #93 repeatedly corrected contradictions/stale references | Docs were updated reactively after implementation changes | Treat WD tech spec wiki as authoritative and gate merges on docs alignment for affected phases | WD Team | planned | Source-of-truth ambiguity |
| L-008 | Voice/TTS policy and implementation churn | PRs #21, #23, #36, #60 repeatedly migrated TTS strategy/providers and references | Voice subsystem boundaries and policy were not stabilized early | Freeze WD voice policy early (service contract, fallback policy, cache behavior) and isolate provider adapters behind one interface | WD Team | planned | Affects determinism and runtime |
| L-009 | Validation layers accreted without simplifying upstream design | PRs #39, #40, #41, #76, #85, #90 add more semantic/layout/timing validation layers over time | Defensive checks grew faster than root-cause generator fixes | Define WD validation hierarchy with explicit ownership: schema -> semantic -> runtime; each added gate must remove a known failure class | WD Team | planned | Complexity growth risk |
| L-010 | Repository mixed runtime artifacts/examples with core system evolution | Multiple PRs (for example #14, #42, #58, #60, #82) include `projects/`/`examples/` artifacts alongside core logic updates | Diagnostics artifacts and core code were not cleanly separated | Separate WD operational artifacts from product code/docs; require clean boundaries for test fixtures vs runtime outputs | WD Team | planned | Signal-to-noise and review overhead |

## Recurring Failure Themes (Rolling Summary)

- Contract drift between orchestrator, prompts, parser, and generated artifacts.
- Retry/self-heal behavior compensating for weak first-pass generation contracts.
- Large, mixed-scope changes that obscure causal regressions.
- Documentation and policy lagging behind implementation changes.
- Repeated subsystem migrations (API/harness/voice) before boundaries stabilized.

## WD Guardrails Derived From Lessons

- Freeze core contracts first: phase state machine, harness API, scaffold markers, and phase schemas.
- Require evidence-linked design decisions: each major WD design choice maps to one lesson ID.
- Enforce first-pass quality: retries are bounded fallback, not normal control flow.
- Keep PR scope narrow: one architectural concern per milestone slice.
- Keep spec and implementation synchronized; docs update is part of done criteria.
- Isolate adapters (LLM, TTS, retrieval) behind stable internal interfaces.
- Add CI checks for contract alignment: prompts <-> schemas <-> parser <-> orchestrator.
- Keep generated/runtime artifacts out of core code review paths unless explicitly auditing them.

## Open Questions

- Which lessons are highest priority blockers before WD implementation resumes?
- What exact PR size/scope limits should WD enforce to reduce regression risk?
- Which retry budget is acceptable per phase before mandatory human intervention?
- Which WD phase contracts must be locked first to prevent architecture churn?

## Change Log

### 2026-02-24

- Initialized lessons log structure.
- Added first lessons extraction from merged FH PR audit (48 merged PRs reviewed, comments + files analyzed).
