# Flaming Horse Lessons Log

Status: active
Last updated: 2026-02-25

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
| L-003 | Self-heal loops became primary path instead of fallback | PR #55 explicitly audits parse failure loop; PRs #40 and #73 target loop convergence and repair behavior | First-pass generation quality/contracts were too weak; retries compensated for design gaps; oversized retry payloads hit model context ceilings, truncating critical diagnostics | In WD, optimize first-pass correctness, cap retries, and enforce structured, size-bounded retry payloads (error codes + minimal diffs) | WD Team | planned | Prevent infinite/near-infinite repair cycles |
| L-004 | Scaffold/slot contract drift in generated scenes | PRs #4, #51, #52, #58, #73 focus on scaffold generation fixes, duplicate helper removal, and stricter validation | Scaffold boundaries were mutable and not continuously verified | Introduce immutable scaffold markers plus automated contract tests that run before build/repair phases | WD Team | planned | Core generator integrity issue |
| L-005 | Prompt/schema drift caused parsing and serialization failures | PR #72 (JSON responses), #76 (timing validation), #77 (triple-quote corruption), #85/#89/#90 (prompt/schema alignment/layout validation) | Prompt contracts and parser expectations evolved independently | Single source of truth for phase schemas and prompt manifests; CI check that prompt outputs map exactly to parser/schema contracts | WD Team | planned | High frequency failure source |
| L-006 | Oversized multi-concern PRs increased regression risk | PRs #60, #92, #80, #42, #44 changed large surfaces (50-100 files) across docs/scripts/harness/examples at once | Changes were not scoped to single concern/milestone | Enforce smaller milestone PR slices in WD plan; one architectural concern per PR with explicit rollback boundary | WD Team | planned | Maintainability and review quality issue |
| L-007 | Documentation drift and stale policy references | PRs #2, #33, #36, #79, #93 repeatedly corrected contradictions/stale references | Docs were updated reactively after implementation changes | Treat WD tech spec wiki as authoritative and gate merges on docs alignment for affected phases | WD Team | planned | Source-of-truth ambiguity |
| L-008 | Voice/TTS policy and implementation churn | PRs #21, #23, #36, #60 repeatedly migrated TTS strategy/providers and references | Voice subsystem boundaries and policy were not stabilized early | Freeze WD voice policy early (service contract, fallback policy, cache behavior) and isolate provider adapters behind one interface | WD Team | planned | Affects determinism and runtime |
| L-009 | Validation layers accreted without simplifying upstream design | PRs #39, #40, #41, #76, #85, #90 add more semantic/layout/timing validation layers over time | Defensive checks grew faster than root-cause generator fixes | Define WD validation hierarchy with explicit ownership: schema -> semantic -> runtime; each added gate must remove a known failure class | WD Team | planned | Complexity growth risk |
| L-010 | Repository mixed runtime artifacts/examples with core system evolution | Multiple PRs (for example #14, #42, #58, #60, #82) include `projects/`/`examples/` artifacts alongside core logic updates | Diagnostics artifacts and core code were not cleanly separated | Separate WD operational artifacts from product code/docs; require clean boundaries for test fixtures vs runtime outputs | WD Team | planned | Signal-to-noise and review overhead |
| L-011 | MathTex/LaTeX strings caused runtime render failures | `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/build.log` shows repeated LaTeX compilation errors for `scene_03.py` | MathTex content is generated without strict syntax validation | Add a semantic gate for MathTex validity (balanced braces, allowed commands) or require validated templates | WD Team | planned | Frequent runtime breakage in math-heavy scenes |
| L-012 | Invalid Manim color types caused runtime failures | `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/build.log` shows ManimColor type errors (`float` used where color spec required) | Color parameters are not validated prior to runtime | Enforce color literal validation and helper APIs that constrain inputs | WD Team | planned | Preventable runtime errors in scene rendering |
| L-013 | Conversation context pointer invalidated during retries | `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/build.log` shows `previous_response_id invalid; retrying without conversation pointer` during repeated repairs | Response-id chaining is not validated/persisted robustly across retries | In WD, persist conversation chain in deterministic state; validate pointer before retry; if invalid, require explicit context restoration or fail closed | WD Team | planned | Likely contributes to drift and schema failures under repair pressure |
| L-014 | Retry context exceeded model limits, forcing truncation | `docs/analysis/fh-pr-audit/flaming-horse-generated/*/log/conversation.log` shows repeated `retry context truncated to 6000 chars`; xAI model limits indicate finite context budgets (see model list screenshot provided) | Repair payloads are not size-bounded against model context limits, so critical diagnostics are dropped | In WD, enforce deterministic retry payload budgets per model, using structured summaries (error codes + minimal diffs) and strict size checks before model calls | WD Team | planned | Truncation correlates with repair drift and prolonged retries |
| L-015 | Validation layers became the default fix instead of instruction clarity | Multiple FH PRs added successive validation gates (see L-009 and recurring repairs in `docs/analysis/fh-pr-audit/`), creating layered complexity and maintenance drag | Instructions and contracts were not made sufficiently precise; failures were patched by adding more validators | In WD, prioritize instruction-first design and deterministic helper abstractions; validation is a last-resort safety net with explicit justification and deprecation plan | WD Team | planned | Critical: validation spaghetti was a primary driver of FH becoming unmanageable and the need for WD rewrite |
| L-016 | Helper API misuse due to ambiguous output types (`harmonious_color`) | FH `harmonious_color` returns RGBA float lists while scene code expects Manim color objects; runtime failures show `ManimColor only accepts ... not <class 'float'>` in `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/error.log` | Helper API mixed input/output types and allowed LLM misuse (`set_color(harmonious_color(...))`) | In WD, helper APIs must return a single, safe type and accept only a constrained palette enum; disallow helper outputs being passed directly into color setters | WD Team | planned | Reduce LLM burden and eliminate color type mismatches |
| L-017 | Prompt/tooling conflicts forced guesswork in build phases | `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/conversation.log` shows system prompt requiring doc search + inline comment citations, while output rules ban comments and `tools_enabled: False` prevents any search | Prompt contracts were not validated against tool availability or output schema constraints | In WD, preflight prompt/tool compatibility: if tools are disabled, prompts must not require retrieval or citations; output schema must allow any mandated annotations | WD Team | planned | Unresolvable prompt constraints degrade first-pass quality |
| L-018 | LaTeX escaping ambiguity caused double-escaped MathTex | Generated `.tex` files contain `\\frac` and `\\sum` (see `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/media/Tex/f6670f2553652004.tex`), leading to `Missing } inserted` errors in build logs | Escaping rules between JSON prompt text and code strings were not defined; raw strings copied escaped content verbatim | In WD, use canonical LaTeX templates or a conversion layer that normalizes escaping; disallow raw MathTex literals unless validated | WD Team | planned | Prevents recurring LaTeX compile failures |
| L-019 | Unspecified API/ helper constraints led to invalid kwargs and misuse | Runtime errors include unsupported kwargs (`numbers_with_elaborate_zero`, `stroke_dash`, `max_tip_length`, `max_stroke_width`), `adaptive_title_position` missing `content_group`, and `self.camera.frame` on non-moving camera scenes (see `docs/analysis/fh-pr-audit/flaming-horse-generated/gibbs-phenomenon/log/error.log`) | LLMs guessed API surface and helper signatures without a version-locked contract | In WD, expose a strict, versioned API surface and helper signatures in prompts or via deterministic wrappers; add linting to reject unsupported kwargs before runtime | WD Team | planned | Reduces runtime failures from API drift and guesswork |

## Recurring Failure Themes (Rolling Summary)

- Contract drift between orchestrator, prompts, parser, and generated artifacts.
- Retry/self-heal behavior compensating for weak first-pass generation contracts.
- Large, mixed-scope changes that obscure causal regressions.
- Documentation and policy lagging behind implementation changes.
- Repeated subsystem migrations (API/harness/voice) before boundaries stabilized.
- Conversation context breaks under retry pressure (invalid response-id pointers), amplifying drift and schema failures.

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

### 2026-02-25

- Added L-017 through L-019 based on gibbs-phenomenon instruction-quality vs output analysis.
