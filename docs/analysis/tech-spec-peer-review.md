# Tech Spec Peer Review

Status: complete  
Last updated: 2026-02-25  
Reviewer: Copilot Agent  
Scope: all `docs/tech-spec/` sections (01–18 + appendices)  
Source commit: `docs/tech-spec/` as of 2026-02-24

---

## 1. Executive Summary

The Wet Donkey tech spec is architecturally sound and reflects disciplined learning from the Flaming Horse failure analysis. The contract-first philosophy, the deterministic-code-owns-orchestration principle, the validation hierarchy, and the harness exit-code contract are all strong design anchors.

However, the spec is uniformly in **draft** state, and a substantial number of **Open Questions remain unresolved across every section**. Several of these are critical-path design decisions that must be locked before implementation can begin without churn risk. The review below identifies those blockers, documents consistency gaps across sections, and flags ambiguities that could become integration problems during execution.

**Overall rating: solid foundation with critical gaps to close before M0 execution.**

---

## 2. Review Methodology

For each section, I evaluated:

1. **Internal consistency** — does the section contradict itself?
2. **Cross-section consistency** — does the section align with related sections?
3. **Lessons traceability** — are the relevant lessons addressed and correctly mapped?
4. **Completeness** — are design decisions made, or deferred in ways that block execution?
5. **Actionability** — can an implementer build from this section, or are too many details missing?

I also cross-referenced the spec against:
- `docs/lessons-learned/flaming-horse-lessons.md`
- `docs/implementation-plan/README.md` and `M0-checklist.md`
- Existing source code at `src/harness/`, `src/wet_donkey/`, `src/wet_donkey_voice/`, and `scripts/`

---

## 3. Section-by-Section Findings

### 3.1 Section 01 — Overview

**Strengths:**
- Clear mission statement and non-goals.
- Design principles are crisp and non-negotiable.
- Lessons traceability table is accurate and well-chosen.

**Gaps:**
- Open questions (which interfaces to lock first, retry budget, PR scope thresholds) are restated verbatim in the implementation plan without being resolved in the spec. These questions should either be answered here or explicitly deferred with a named owner and target milestone.
- The principle "first-pass correctness prioritized over retry volume" is stated but no metric or threshold defines what "first-pass correctness" means in practice.

**Verdict:** Acceptable as a principles section. Does not need blocking changes before M0, but open questions must be closed before M1 execution.

---

### 3.2 Section 02 — xAI Responses API Integration

**Strengths:**
- Integration model is clear: one harness, phase-scoped, contract-constrained, untrusted LLM outputs.
- Tool usage and degradation behavior policies are sound.

**Gaps:**
- No API timeout, backoff, or rate-limit defaults are specified. This is a critical operational gap: without these, retry behavior cannot be deterministic. The open question acknowledges this but leaves it entirely unresolved.
- No specific model name or version is locked. The legacy implementation plan referenced `grok-4-1-fast-reasoning`. The spec should either name the model or define a versioning policy for model selection.
- "Session continuation is explicit (no hidden implicit conversation state)" is stated but the concrete mechanism (the `previous_response_id` field) is not documented in the spec. An implementer reading only the spec cannot derive the implementation.
- The 30-day server-side conversation storage window (a known xAI API constraint) is not mentioned here or in section 18 (Known Constraints). This is a real operational risk for long-paused projects.

**Verdict:** Needs these gaps closed before M2 execution. The timeout/backoff and model version decisions are M0-level locks.

---

### 3.3 Section 03 — Technology Stack

**Strengths:**
- Stack is appropriately minimal and deterministic-oriented.
- Versioning policy and deprecation intent are stated.

**Gaps:**
- The spec says "Runtime-critical tools/libraries are pinned by policy" but does not list a single version number anywhere. This is an internal contradiction. The stack section must either carry a version table or reference a `requirements.txt` / `pyproject.toml` as the authoritative pin source.
- "Orchestration: Bash + Python scripts" is listed as the orchestration layer, but the component map in section 06 says scripts own phase execution order. The Bash vs Python split is not defined: which parts of orchestration are Bash and which are Python? This ambiguity can lead to architectural drift (FH lesson L-001).
- There is no mention of CI tooling (for example GitHub Actions), despite CI enforcement being a recurring requirement across sections 09, 13, and 15.
- "Deprecated paths are removed by explicit milestone, not linger indefinitely" is a policy statement without a supporting process (no deprecation tracking mechanism or milestone ownership defined).

**Verdict:** Needs a version table or external version-source reference, and a Bash/Python boundary definition, before M0 is complete.

---

### 3.4 Section 04 — Directory Structure

**Strengths:**
- Clean separation of source, docs, runtime artifacts, and tests.
- Boundary policy is clear and addresses L-010 directly.

**Gaps:**
- The prompt template directory is not mapped. Section 07 specifies `prompts/<phase>/` as the layout, but section 04 does not show where this lives in the repository tree. The existing code has `src/harness/prompts.py` (a single file), which conflicts with the phase-directory structure implied in section 07. This inconsistency needs resolution.
- `scripts/` is listed in the directory structure but no subdirectory breakdown is provided for it. The existing scripts directory contains `build_video.sh`, `create_video.sh`, `new_project.sh`, `scaffold_scene.py`, and several Python utilities. How these scripts relate to the orchestrator component (section 06) is not defined.
- No mention of CI configuration directory (`.github/`), documentation build artifacts, or tooling configuration files (`.env.example`, `requirements.txt`). These exist in the repo and belong in the canonical layout.
- The open question about fixture location (`tests/fixtures/` vs phase-specific subtrees) is unresolved and affects test structure for every milestone.

**Verdict:** Needs prompt directory disambiguation and fixture location decision before M3/M4 test work begins.

---

### 3.5 Section 05 — Pipeline State Machine

**Strengths:**
- Canonical phase sequence is explicit and well-ordered.
- Orchestrator-as-sole-authority rule is clear.
- Retry model philosophy aligns with L-003 correctly.

**Gaps (critical):**
- **The `blocked` state is still an open question.** Whether `blocked` is a distinct phase or a status flag on the current phase affects the state schema, the orchestrator logic, the exit code mapping in section 12, and the logging contract in section 13. This must be decided at M0. It cannot remain open through M1 execution without causing exactly the kind of architecture churn the spec was designed to prevent.
- **`max_attempts` per phase is an unresolved open question.** Without concrete defaults, the retry model is not implementable deterministically. At minimum, v1 defaults should be specified here (they can be overridden by config), with a comment that per-phase tuning is tracked in section 11.
- The `review` phase appears in the canonical sequence but is described as a "hard manual gate" without specifying how manual gate actions are recorded in `project_state.json`. The state contract (section 08) must reflect the gating mechanism.
- No explicit "failure" or "error" state is shown in the phase sequence. Implied recovery paths (retry → blocked) are described in prose but not shown in a state transition diagram or table.
- The History entry format for state transitions is described as "append-only and timestamped in UTC" but the actual schema of a history entry is not specified.

**Verdict:** The `blocked` state decision and `max_attempts` defaults are **M0 blockers**. They must be resolved before any implementation work on the orchestrator begins.

---

### 3.6 Section 06 — Core Components

**Strengths:**
- Component responsibility boundaries are well-drawn.
- The LLM-as-data-input rule is explicit and actionable.
- Cross-component boundary rules are good guardrails.

**Gaps:**
- The component map refers to `harness/` (relative path), while section 04 specifies `src/harness/`. Every component reference should use canonical paths from section 04 to prevent ambiguity.
- Component 4 (Scaffold and Scene Contract Layer) is listed but has no corresponding directory in section 04's layout. Where does the scaffold generator and slot contract logic live?
- "Temporary containment changes must include explicit removal conditions" is a sound policy but has no tracking mechanism. How and where are these tracked?
- The render + assembly subsystem (component 6) is described as consuming "validated scene + narration + audio artifacts" but section 16 has not resolved whether assembly can resume from partial scene success. This open question affects the render component boundary.
- Open question about render assembly ownership (in orchestrator vs separate component) is unresolved and is consequential for M5 milestone scope.

**Verdict:** Needs canonical path alignment and scaffold generator directory placement. Render assembly ownership must be decided before M5 scoping.

---

### 3.7 Section 07 — Prompt Architecture

**Strengths:**
- Phase-scoped prompt organization is clean and aligns with the single-source-of-truth principle.
- Variable contract and schema alignment rules are precise.
- Repair/retry prompt requirements directly address L-003 and L-005.

**Gaps (critical):**
- **Prompt manifest format (markdown table vs machine-readable YAML/JSON) is an unresolved open question that directly blocks M3.** A machine-readable manifest is strongly preferable (it enables CI checks), but the decision is explicitly deferred. This must be made at M0.
- `prompts/<phase>/` is the specified layout, but this conflicts with the existing `src/harness/prompts.py` module. The path is not anchored to any root in the repository. Does `prompts/` live under `src/harness/prompts/<phase>/`, or as a top-level `prompts/` directory? Section 04 must be updated to match whichever is chosen.
- "Prompts cannot introduce unofficial fields" is a good rule, but the enforcement mechanism (at what layer, by what component, at what time) is not specified. Is this a CI check, a parser gate, or a harness pre-validation step?
- The section says "Orchestrator injects runtime context; prompts do not infer hidden state" — this is architecturally sound but the mechanism for context injection is not described. How does the orchestrator pass variables to prompt templates at runtime?

**Verdict:** Prompt manifest format and prompt directory path are **M0 blockers**. Must be resolved to build the prompt/schema/parser alignment CI check in M3.

---

### 3.8 Section 08 — Data Contracts

**Strengths:**
- Clear ownership mapping across components.
- Versioning rules are principled and explicit.
- The LLM-output-as-untrusted-content rule is well-placed here.

**Gaps:**
- **`project_state.json` required fields are listed without types or format constraints.** `project_name` (string), `topic` (string), `phase` (enum?), `history` (array of what?) should each have type and cardinality specified. Without this, contract tests cannot be written deterministically.
- **`contract_version` is required in the versioning rules but is NOT listed as a required field in the `project_state.json` contract definition.** This is a direct internal inconsistency in this section.
- The `.xai_session.json` contract mentions "response/session identifiers" but doesn't list required fields, types, or schema. This should be at least a minimal field table.
- The "contract_version" format is not defined. Is it semver (1.0.0), a date string (2026-02-24), or a monotonic integer (v1, v2)? This needs to be decided before M0 contract documents can be written.
- The phase schema registry is referenced but not localized to a directory or module. Where does the registry live?

**Verdict:** `project_state.json` field types and `contract_version` format are **M0 blockers**. The `contract_version` inconsistency must be corrected before contract tests can be written.

---

### 3.9 Section 09 — Validation Gates

**Strengths:**
- Layered hierarchy (schema → contract → semantic → runtime → assembly) is logical and maps cleanly to existing validation patterns.
- Gate failure output requirements are concrete (machine-readable error codes, owner component, retryability).
- Scaffold boundary violation as contract failure (not semantic fix) is exactly the right classification.
- New-gate admission criteria are excellent and will prevent validation sprawl.

**Gaps:**
- The "layout tag allowlist" and "helper usage" rules mentioned under the Semantic Gate are not defined anywhere in the spec. If these are real constraints, they need a reference or a definition.
- The Contract Gate rule references `SLOT_START` as an example boundary marker, but this is the only place in the spec this marker is named. The scaffold slot contract (section 08) should formally define the marker names and syntax.
- "CI Alignment Checks" are described but neither the CI mechanism (GitHub Actions, pre-commit hooks, etc.) nor the specific check commands are referenced. An implementer cannot build this from the spec alone.
- The relationship between validation gate failures and harness exit codes (section 12) is implied but not explicitly mapped. For example: Schema Gate failure → exit code 3; Contract Gate failure → exit code 2. This mapping table should exist in either section 09 or section 12.

**Verdict:** Needs gate-to-exit-code mapping table and `SLOT_START` marker formal definition. CI mechanism must be named before M3 gates can be implemented.

---

### 3.10 Section 10 — Self-Healing and Retry Logic

**Strengths:**
- "Evidence of eventual convergence after heavy retry churn is a design smell" is exactly the right framing.
- Repair input requirements are specific and actionable.
- Loop detection criteria are well-described conceptually.

**Gaps:**
- **`max_attempts` defaults are still an open question.** This is also flagged in section 05. Since both sections reference it, the canonical answer should live in section 05 (state machine) or section 11 (configuration), with a cross-reference here. It must be resolved at M0.
- "Normalized error signature" is mentioned in both loop detection and logging but is never defined. What is the normalization algorithm? What fields are included? How is the signature computed? This needs at minimum a brief specification or a reference to where it will be defined.
- "Key artifact diffs" as a loop detection criterion is described without specifying which artifacts are diffed, which fields are compared, or what threshold constitutes "no meaningful delta." This level of vagueness will cause inconsistent loop detection behavior.
- Context truncation that "removes required diagnostics is a retry-ineligible failure" is an important rule, but it creates an ambiguity: who determines if truncation has occurred, and what is the handling path when it does?

**Verdict:** `max_attempts` defaults and "normalized error signature" specification are **M0/M1 blockers**.

---

### 3.11 Section 11 — Configuration and Environment Variables

**Strengths:**
- Configuration class taxonomy (required secrets, required runtime controls, optional tuning) is clean and practical.
- Startup validation concept is sound.
- Centralized defaults principle addresses L-001 and L-008 well.

**Gaps (significant):**
- **No actual environment variable names are listed.** The spec says these must be "explicitly documented and tested" but does not document a single variable. The repository's `.env.example` file exists but is not referenced here. At minimum, this section should list the v1 required variables and their expected values/types.
- The layered environment file question (`.env` vs `.env.local` vs `.env.ci`) is unresolved. This affects developer onboarding, CI setup, and secret management strategy.
- "Logging verbosity" is listed as an optional tuning value but section 13 defines structured JSONL logging as mandatory — there's a tension here. If logging format is required, verbosity tuning must be constrained to level-filtering only, not format changes.
- Feature flags are mentioned as part of configuration but there is no inventory of what feature flags exist or are planned for v1.

**Verdict:** Variable inventory and layered env policy must be documented before any CI/CD or harness implementation work begins.

---

### 3.12 Section 12 — Harness Exit Codes

**Strengths:**
- The five-code taxonomy is the most concrete, implementation-ready content in the entire spec.
- Exit code 4 (non-retryable policy violation → immediate block) is a critical guardrail against catastrophic runaway behavior.
- Error payload requirements (machine-readable code, human summary, retryability, signature token) are specific and actionable.

**Gaps:**
- Exit code 1 covers "API/network/runtime/system failure" — this is too broad. An API rate-limit 429 response has different retry semantics than an OS-level crash. Consider splitting into `1` (transient infrastructure, auto-retry eligible) and a sub-category or a `5` (non-transient system failure, human investigation required). At minimum, the orchestrator action should differentiate retry-eligible infrastructure errors from fatal system errors.
- No exit code for manual gate state. The open question acknowledges this but doesn't resolve it. If the `review` phase triggers a pause-for-human action, the harness or orchestrator needs a signal for this state that is distinct from a failure.
- The exit code contract says it is "versioned; changes require orchestrator/spec/test updates" but the current contract has no version field. `contract_version` should be added to this exit code schema consistent with section 08 policy.
- The exit code table applies to the harness but is this the same exit code surface used by Python orchestrator scripts? The section doesn't clarify whether the code taxonomy applies to all processes in the pipeline or only the harness module.

**Verdict:** Exit code 1 disambiguation is a **design decision needed before M1**. Manual gate exit code must be resolved before M0 acceptance criteria (state machine definition) can be complete.

---

### 3.13 Section 13 — Logging and Observability

**Strengths:**
- Four distinct log streams (orchestrator event, harness interaction, validation, artifact lineage) map cleanly to component ownership.
- Correlation ID requirement (run_id, phase_attempt_id, error_signature) is well-designed for loop detection.
- Minimum diagnostic payload for failures is specific enough to implement.

**Gaps:**
- **No example log record or schema is provided.** The spec says "Logs are structured JSONL" but gives no field inventory for any of the four log streams. Without at least one example record per stream, the logging contract is aspirational rather than implementable.
- The generation strategy for `run_id` and `phase_attempt_id` is unspecified. Should these be UUIDs, timestamps, or monotonic counters? Inconsistent generation will break log correlation.
- "Sensitive data is redacted at write-time" is stated but no redaction policy is defined — which fields are sensitive, and what redaction format is used (e.g., `[REDACTED]` vs hash vs omission)?
- "Human summary files are optional and derived from structured logs" — by what tooling? Is there a planned log viewer/summary tool, or is this purely aspirational for v1?
- Log retention windows are an open question with no recommended defaults even for local dev use.

**Verdict:** At minimum, one example JSONL record per log stream and `run_id` generation strategy should be specified before M6 logging implementation begins.

---

### 3.14 Section 14 — Voice Policy

**Strengths:**
- Adapter isolation principle is sound and directly addresses L-008.
- Cache policy and quality validation requirements are concrete.
- "Silent bypass" is explicitly prohibited — this is the right call.

**Gaps:**
- **Fallback policy for v1 is still an open question.** Given that L-008 is about voice churn and the implementation plan recommends "disabled by default," this should be decided in this section, not left open. The recommendation is: fallback is disabled in v1; enable-path exists behind a named config flag.
- Cache key derivation mentions "normalized text + voice config" but "normalized" is undefined. Text normalization (whitespace, punctuation, case?) must be specified to ensure cache hit/miss determinism.
- Cache invalidation policy when voice config changes is unresolved. In a pipeline that may re-run phases, this is an operational risk.
- "Which minimum audio quality checks are mandatory before assembly" is open. At minimum, file existence, non-zero duration, and expected format (e.g., `.wav` or `.mp3`) should be defined as baseline requirements.

**Verdict:** v1 fallback policy decision and baseline audio quality checks are **M5 execution gates**. Fallback policy should ideally be decided at M0 to prevent ambiguity in earlier phases.

---

### 3.15 Section 15 — Testing

**Strengths:**
- Four-layer test pyramid is well-defined and practically ordered.
- Lessons-linked regression suite concept is strong and traceable.
- CI merge policy is explicit and non-negotiable.
- Specific coverage areas (scaffold immutability, retry-loop detection, config preflight) are concrete and right.

**Gaps:**
- **No minimum coverage threshold is specified**, despite noting it as an open question. "Adequate coverage" without a number will lead to inconsistent gate enforcement. Even a rough milestone-specific threshold (e.g., 80% for M0-M2 contract tests) would be better than none.
- The nightly vs every-change test split is unresolved. This affects CI pipeline design.
- The "lessons-linked regression matrix" is described but not actually built out. It should be a table showing lesson ID → test file/function, not just a prose description of the concept.
- Live API test isolation strategy is open. This is a significant gap because the harness tests cannot run without API access, yet CI should be deterministic. The mock strategy for harness tests must be defined before M2 test gates can be written.

**Verdict:** Coverage threshold and live API isolation strategy must be defined before any milestone CI gates can be enforced.

---

### 3.16 Section 16 — Render and Assembly

**Strengths:**
- Render preconditions are explicit and correctly gate-ordered.
- Assembly manifest requirement is concrete.
- Output verification requirement is sound.

**Gaps:**
- **Duration tolerance threshold for final output is still open.** This is a simple threshold (e.g., ±2 seconds or ±5%) that should be a configurable default. Without it, output verification is not implementable.
- No specific ffmpeg settings or flags are mentioned. Even a reference to a separate configuration or script (e.g., `scripts/build_video.sh`) would anchor the render contract.
- Assembly resumability from partial scene success is unresolved. This affects whether a failed `assemble` phase can be retried without re-rendering all scenes, which has significant operational cost implications.
- Render metadata fields (scene ID, duration, run identifier) are stated but not typed or formatted. These must align with the artifact lineage log in section 13.

**Verdict:** Duration tolerance and ffmpeg settings need defaults. Assembly resumability must be decided before M5 scoping.

---

### 3.17 Section 17 — Stateful Training Integration

**Strengths:**
- Retrieval-as-enhancement-layer principle correctly prevents core correctness dependency on LLM retrieval quality.
- Degraded operation being opt-in and fully observable is the right policy.
- Cross-project corpus reuse governance is explicitly bounded.

**Gaps:**
- **Which phases require retrieval vs use it optionally is still open.** This decision affects the phase contract definitions (section 08) and the harness schema per phase (section 02). It cannot remain open through M2 execution.
- Corpus growth cap and governance policy are open. For a system intended for repeated use, uncontrolled corpus growth is an operational risk with no mitigation defined.
- "Upload/read operations are idempotent where possible" — "where possible" is a weak constraint. Which operations are not idempotent, and what is the expected behavior when they are not?
- The 30-day conversation storage window constraint (an xAI API fact) is not mentioned here or in the constraints section (18), despite being operationally relevant for long-paused projects.

**Verdict:** Phase-level retrieval requirement/optional decision is needed before M2 harness schema work. The 30-day storage constraint should be documented in section 18.

---

### 3.18 Section 18 — Known Constraints and Risk Areas

**Strengths:**
- The risk areas enumerated (contract drift, retry-loop, scope churn, docs divergence, scaffold boundary corruption, schema fragility, retry-context truncation) are well-identified and lesson-traceable.
- Risk controls are concrete and multi-layered.
- Section 18 was clearly updated to reflect risks discovered during spec drafting (items 5-7 are more specific and detailed than the earlier items).

**Gaps:**
- The risk register does not assign **severity levels** (high/medium/low) or **probability estimates**. Without these, risk prioritization is subjective.
- The 30-day xAI conversation storage window is a real external constraint that is not listed here. Long-paused projects that exceed the window will lose session continuity silently unless this is called out.
- xAI API rate limits and quotas are mentioned in passing ("API availability and rate/latency behavior") but no specific constraints are documented. If known, these should be listed here; if unknown, they should be flagged as an open risk requiring investigation.
- "Risk controls" are described per-risk but there is no ownership assigned per risk at the individual level. "WD Team" as a generic owner provides no accountability.
- Open question about "which risks are acceptable for v1 launch versus deferred mitigation" is unanswered and consequential for the M7 readiness gate.

**Verdict:** Severity levels and the 30-day storage constraint must be added before M7 risk review can be completed.

---

### 3.19 Appendix A — Migration from Legacy Harness

**Strengths:**
- Phase-by-phase migration approach is the right strategy.
- No-silent-fallback rule is correctly non-negotiable.
- Exit criteria are specific enough to enforce.

**Gaps:**
- The appendix references "legacy harness patterns" but the current `src/harness/` is already the Responses API harness. It is unclear whether there is an actual legacy harness to migrate from in the WD codebase, or whether this appendix describes a historical concern that has already been resolved. If the latter, the appendix status should reflect this.
- "Migration milestones must be reversible until parity is verified" — no rollback mechanism is described. This is important for M2 acceptance criteria.

---

### 3.20 Appendix B — Roadmap: Mixed Renderer (Manim + Blender)

**Strengths:**
- Correctly deferred from v1 scope.
- Entry and exit criteria are well-defined.
- Guardrails against dual-harness reintroduction are explicit.

**Gaps:**
- The renderer adapter interface is described conceptually but not even sketched at a field/method level. A minimal interface definition would make the entry criteria more actionable.

---

## 4. Cross-Cutting Issues

### 4.1 Open Questions Are Systematically Unresolved

Every section has an "Open Questions" block, and the majority of these questions remain open in the implementation plan as well. The following open questions are **M0 blockers** — they must be resolved before any implementation work begins:

| Open Question | Blocking Section(s) | Recommended Action |
|---|---|---|
| Is `blocked` a phase or a status flag? | 05, 10, 12 | Decide: recommend status flag on current phase to avoid phase-sequence coupling |
| What are per-phase `max_attempts` defaults? | 05, 10, 11 | Define: suggest `plan=3`, `build_scenes=5`, `scene_qc=3`, `final_render=2` as v1 defaults |
| What is the prompt manifest format? | 07 | Decide: machine-readable YAML/JSON is required for CI alignment checks |
| What is the `contract_version` format? | 08 | Decide: recommend semver string (`1.0.0`) |
| Where does the prompt directory live? | 04, 07 | Resolve conflict with existing `src/harness/prompts.py` module |
| What model version is used for v1? | 02 | Name the model; define update policy |
| What are API timeout/backoff defaults? | 02 | Specify numeric defaults |
| Is voice fallback allowed in v1? | 14 | Decide: recommend disabled by default |

### 4.2 The `blocked` State Is Undefined Across Three Sections

Sections 05, 10, and 12 all reference `blocked` state but describe it differently:
- Section 05: "transitions to `blocked` state requiring human action"
- Section 10: "phase enters `blocked`"
- Section 12: "immediate block; require human action"

Whether `blocked` is a distinct phase value in the `phase` field, a separate `status` field (e.g., `phase: build_scenes, status: blocked`), or a special history entry has cascading implications on the state schema, the state machine, the exit codes, and the logging contract. This is a single design decision that must be made and propagated to all affected sections.

### 4.3 Schema Version Contract Is Internally Inconsistent

Section 08 says "Every contract includes a `contract_version` field" but the `project_state.json` required fields list (`project_name`, `topic`, `phase`, `history`) does not include `contract_version`. This is a direct contradiction within one section and must be corrected.

### 4.4 Prompt Directory vs Existing Code Conflict

Section 07 specifies `prompts/<phase>/` as the prompt organization structure, but the existing codebase has `src/harness/prompts.py` as a flat Python module. The spec does not anchor the `prompts/` path to a repository root or parent directory. This will cause an implementation-spec conflict at M3. The resolution must be documented in section 04.

### 4.5 No Environment Variable Inventory

Section 11 asserts that required vs optional variables are "explicitly documented and tested" but the spec itself documents zero variables. The `.env.example` in the repository root is the closest existing artifact, but it is not referenced in the spec. For the spec to serve as an authoritative reference, at minimum the required variables and their semantics must be listed in section 11.

### 4.6 Gate-to-Exit-Code Mapping Gap

Sections 09 (Validation Gates) and 12 (Harness Exit Codes) describe overlapping concerns but do not cross-reference each other. An implementer needs to know: when the Schema Gate fails, which exit code does the harness emit? This mapping table should exist in one place and be referenced from both sections.

Suggested mapping:
| Validation Gate | Harness Exit Code |
|---|---|
| Schema Gate failure | 3 (Schema Violation) |
| Contract Gate failure | 2 (Semantic/Contract Validation Error) |
| Semantic Gate failure | 2 (Semantic/Contract Validation Error) |
| Runtime Gate failure | 1 (Infrastructure/Execution Error) |
| Assembly Gate failure | 4 (Non-Retryable Policy Violation) or 2 depending on recoverability |

### 4.7 Lessons Log Status Is Inconsistent with Spec Coverage

All 10 lessons in `docs/lessons-learned/flaming-horse-lessons.md` have status `planned`, even though the tech spec has coverage for every one of them (every section has a Lessons Traceability table). The lessons log status column should be updated to `in-progress` for all lessons that have spec-level coverage, reserving `implemented` for when corresponding code and tests exist.

### 4.8 FH PR Audit Evidence Files Are Referenced but Missing

`docs/analysis/fh-analysis-plan.md` references three evidence files:
- `docs/analysis/fh-pr-audit/merged_prs_detailed.json`
- `docs/analysis/fh-pr-audit/pr_comments.jsonl`
- `docs/analysis/fh-pr-audit/pr_files.jsonl`

None of these files exist in the repository. If the analysis was completed using these files, either the findings should be summarized in a committed artifact, or the analysis plan should be updated to reflect that this workstream was completed and evidence is available only in the local FH repository.

### 4.9 Missing Spec Sections for v1 Scope

The following topics appear in implementation discussion but have no corresponding spec section:
- **Developer environment setup** — how to install dependencies, configure `.env`, and run tests locally. This is operational but is referenced as a milestone acceptance criterion.
- **CI/CD pipeline definition** — multiple sections require CI gates but the CI pipeline itself is not described in the spec. A stub section or reference to `.github/workflows/` would close this gap.
- **Deprecation and migration tracking** — section 03 mentions a deprecation policy but there is no mechanism described for tracking deprecated paths. A lightweight decision log or ADR process would address this.

---

## 5. Positive Observations

The following elements represent genuine design strength and should be preserved through implementation:

1. **LLM scope is aggressively bounded.** The principle that LLM outputs are untrusted data inputs to deterministic control logic (not orchestration participants) is consistently applied across every section. This is the single most important FH lesson and it is well-embedded.

2. **The validation hierarchy is correctly layered.** Schema → Contract → Semantic → Runtime → Assembly matches real failure modes in ascending cost-of-detection order. This is a mature design.

3. **The exit code taxonomy is implementable today.** Section 12 is the most implementation-ready section in the spec. The five-code structure is simple enough to build against immediately.

4. **Retry philosophy is architecturally sound.** "Evidence of eventual convergence after heavy retry churn is a design smell" is a disciplined and correct principle that will prevent the FH L-003 failure pattern from recurring.

5. **The lessons traceability tables are well-populated.** Every section connects to the relevant lessons, making it easy to verify that prevention strategies have spec coverage.

6. **The implementation plan milestone sequence is correct.** M0 (contract freeze) → M1 (orchestrator) → M2 (harness) → M3 (prompt/schema/parser alignment) → M4 (validation/retry) → M5 (voice/render/assembly) is the right build order.

7. **Appendix B (mixed renderer roadmap) is correctly bounded.** Deferring Blender until after v1 contract stability is the right discipline.

---

## 6. Recommended Actions (Prioritized)

### Priority 1 — M0 Blockers (must resolve before any implementation)

| ID | Action | Section(s) |
|---|---|---|
| A-01 | Decide `blocked` state representation (phase value vs status flag) and propagate to sections 05, 08, 10, 12 | 05, 08, 10, 12 |
| A-02 | Specify v1 `max_attempts` defaults per phase in section 05 or 11; cross-reference from 10 | 05, 10, 11 |
| A-03 | Add `contract_version` to `project_state.json` required fields; define version format | 08 |
| A-04 | Decide and document prompt manifest format (YAML/JSON recommended) | 07 |
| A-05 | Resolve prompt directory path conflict with existing code; update section 04 accordingly | 04, 07 |
| A-06 | Name the v1 model version and define the model-update policy | 02 |
| A-07 | Specify API timeout and backoff defaults in section 02 or 11 | 02, 11 |
| A-08 | Add `contract_version` field to exit code payload; align with section 08 versioning policy | 12 |

### Priority 2 — Before Milestone Implementation (needed before respective milestone executes)

| ID | Action | Target Milestone | Section(s) |
|---|---|---|---|
| A-09 | Add gate-to-exit-code mapping table in section 09 or 12 | M0/M1 | 09, 12 |
| A-10 | Document at minimum the required environment variables and their semantics in section 11 | M0 | 11 |
| A-11 | Update lessons log status from `planned` to `in-progress` for all spec-covered lessons | M0 | lessons log |
| A-12 | Define normalized error signature algorithm and loop detection delta criteria | M1/M4 | 10 |
| A-13 | Specify minimum audio quality validation rules (format, duration, existence) | M5 | 14 |
| A-14 | Specify duration tolerance threshold and ffmpeg config defaults for render/assembly | M5 | 16 |
| A-15 | Decide assembly resumability from partial scene success | M5 | 16 |
| A-16 | Decide which phases require retrieval vs optional | M2 | 17 |
| A-17 | Decide v1 voice fallback policy (recommend: disabled by default) and name the config flag | M5 | 14 |

### Priority 3 — Spec Quality Improvements (non-blocking but important)

| ID | Action | Section(s) |
|---|---|---|
| A-18 | Add severity levels and probability to section 18 risk register | 18 |
| A-19 | Document 30-day xAI conversation storage window as a known constraint | 02, 18 |
| A-20 | Add minimum JSONL log record example per stream to section 13 | 13 |
| A-21 | Specify `run_id` and `phase_attempt_id` generation strategy | 13 |
| A-22 | Document Bash/Python orchestration split in section 03 or 06 | 03, 06 |
| A-23 | Add scaffold slot marker (`SLOT_START`, `SLOT_END`) names and syntax to section 08 | 08 |
| A-24 | Verify Appendix A status (is there an actual legacy harness to migrate from in WD?) | Appendix A |
| A-25 | Clarify fh-pr-audit evidence availability; update analysis plan if completed | analysis |
| A-26 | Add CI/CD pipeline section stub or reference | new section / 15 |
| A-27 | Add version table to section 03 or reference `requirements.txt` as authoritative pin source | 03 |

---

## 7. Conclusion

The Wet Donkey tech spec represents a well-reasoned architectural response to the Flaming Horse failure analysis. The foundational principles — contract-first, deterministic orchestration, bounded retries, adapter isolation — are correctly derived from the lessons learned and consistently applied across all 18 sections.

The primary risk before implementation is the accumulation of unresolved open questions that span multiple sections. Left open, these will create exactly the ad hoc architectural divergence the spec was designed to prevent. The highest-priority action is to schedule a focused decision session to resolve the eight M0 blockers listed in Priority 1 above, update the relevant spec sections, and then authorize M0 execution.

The spec is ready for that decision session. It is not yet ready for implementation execution without it.
