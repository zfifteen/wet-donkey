# Wet Donkey Revised Implementation Plan

Status: draft  
Last updated: 2026-02-24  
Current canonical phase: Phase 4 (revised implementation plan)  
Plan source of truth: `docs/tech-spec/` + `docs/lessons-learned/flaming-horse-lessons.md`

## 1) Session Start Alignment (Anti-Drift)

- Mission restatement: WD remains a clean re-implementation of FH, with deterministic contracts and no dual-harness regression.
- Current phase restatement: Phase 4 deliverable is this revised implementation plan, derived from completed Phase 3 tech spec draft and active lessons log.
- Canonical game-plan alignment: this document executes step 4 without reordering steps 1-3.
- Drift snapshot (as of 2026-02-24):
  - `docs/implementation-plan/README.md` did not exist; created in this session.
  - Tech spec and lessons exist and are populated; implementation plan now catches documentation structure up to current phase.

## 2) Planning Principles

- Contract-first before feature throughput.
- One harness path only: `src/harness/` (Responses API), no legacy fallback.
- Deterministic orchestration and explicit state transitions.
- Retries are bounded, evidence-driven, and never default control flow.
- Milestones are small, single-concern, and test-gated.
- Every milestone must map to lessons-learned IDs and spec sections.

## 3) Scope and Non-Scope

### In Scope (Phase 4 to execution handoff)

- Freeze implementable WD v1 contracts from current tech spec draft.
- Sequence WD implementation into testable milestones with acceptance criteria.
- Define CI/test gates per milestone.
- Track open risks/unknowns explicitly.

### Out of Scope (for this plan phase)

- Broad architecture pivots not represented in `docs/tech-spec/`.
- Reintroducing legacy/parallel harness flows.
- Large mixed-concern feature batches that skip contract tests.

## 4) Milestone Roadmap (Execution Sequence)

### M0 - Contract Freeze Baseline

Goal: lock minimum executable contracts before implementation expansion.

Checklist (pre-execution review): `docs/implementation-plan/M0-checklist.md`

Work items:
- Define and freeze v1 contract surfaces:
  - pipeline phase/state contract (`project_state`),
  - phase schema registry and `contract_version` policy,
  - scaffold slot immutability contract,
  - harness exit-code contract.
- Add contract ownership map (orchestrator/harness/parser/voice/render).
- Record unresolved fields as explicit TODOs, not implicit behavior.

Acceptance criteria:
- Contract documents exist and are internally consistent with spec sections 05, 08, 09, 12.
- No ambiguous phase transition ownership remains.
- Contract-change checklist exists for future PRs.

Required tests/gates:
- Contract schema validation tests passing.
- Exit-code mapping tests passing.
- State transition table tests for happy-path and fail-path basics.

Primary lessons covered: L-001, L-002, L-005, L-009.

### M1 - Orchestrator Deterministic Core

Goal: enforce deterministic phase execution and atomic state behavior in `scripts/`.

Work items:
- Implement/refine table-driven phase transition engine.
- Enforce orchestrator-only phase advancement.
- Implement atomic state write/read with append-only UTC history entries.
- Implement blocked escalation path when retry budget is exhausted.

Acceptance criteria:
- Canonical phase sequence executes deterministically.
- Transition preconditions/postconditions are enforced.
- Retry budget exhaustion yields blocked state consistently.

Required tests/gates:
- Phase transition acceptance suite (all phases and invalid transitions).
- Atomic write and recovery tests (interrupted write simulation).
- Retry exhaustion and blocked escalation tests.

Primary lessons covered: L-002, L-003, L-009.

### M2 - Harness and Structured Output Path

Goal: enforce one Responses-based harness path with schema-mandatory outputs.

Work items:
- Confirm single canonical harness boundary under `src/harness/`.
- Enforce phase-scoped schema outputs for every harness call.
- Implement explicit session metadata handling and persistence contract.
- Ensure no legacy fallback code path is callable in production flow.

Acceptance criteria:
- Every harness phase invocation returns schema-validated payload or explicit failure.
- Session continuation behavior is explicit and audited.
- No dual-harness runtime path remains.

Required tests/gates:
- Harness schema conformance tests per phase.
- Session metadata contract tests (present/missing/invalid).
- Negative tests proving legacy fallback is disabled.

Primary lessons covered: L-001, L-005, L-007.

### M3 - Prompt/Schema/Parser Contract Lock

Goal: prevent drift across prompt assets, schemas, and parser expectations.

Work items:
- Introduce prompt manifest contract per phase (declared variables + schema map).
- Enforce strict variable validation before model invocation.
- Align parser validators to canonical schema versions.
- Implement CI alignment checks (prompt fields <-> schema fields <-> parser).

Acceptance criteria:
- Undeclared/missing template variables fail fast.
- Prompt output fields map 1:1 to schema fields.
- Parser rejects out-of-contract fields deterministically.

Required tests/gates:
- Prompt manifest validation tests.
- Prompt-schema-parser alignment CI check.
- Regression tests for known FH drift cases.

Primary lessons covered: L-005, L-007, L-009.

### M4 - Validation Hierarchy and Retry Control

Goal: implement layered validation and bounded retry behavior with loop detection.

Work items:
- Implement layered gates: schema -> contract -> semantic -> runtime -> assembly.
- Standardize machine-readable error payloads and signatures.
- Enforce retry eligibility rules and per-phase max attempts.
- Add loop-risk detection based on signature and attempt delta.

Acceptance criteria:
- Validation failures identify owning component and retryability.
- Identical retry loops are detected and escalated to blocked.
- No blind retries without new context are allowed.

Required tests/gates:
- Gate-ordering and ownership tests.
- Retry eligibility and non-eligibility tests.
- Loop-detection regression suite.

Primary lessons covered: L-003, L-005, L-009.

### M5 - Voice, Render, and Assembly Contract Integration

Goal: make downstream media pipeline deterministic and contract-checked.

Work items:
- Stabilize voice adapter interface and deterministic cache policy.
- Enforce render preconditions from validated artifacts.
- Implement assembly manifest contract and final output verification.
- Ensure degraded/fallback behavior is explicit and configuration-gated.

Acceptance criteria:
- Voice outputs include required metadata and pass validation.
- Render/assembly only execute with validated prerequisites.
- Final output acceptance requires manifest and duration tolerance checks.

Required tests/gates:
- Voice cache and metadata contract tests.
- Render precondition tests.
- Assembly integrity and output verification tests.

Primary lessons covered: L-002, L-008, L-009, L-010.

### M6 - Observability, Risk Controls, and CI Enforcement

Goal: make failures diagnosable and enforce anti-drift governance.

Work items:
- Implement structured JSONL logging contracts with correlation IDs.
- Emit deterministic failure diagnostics and retry deltas.
- Add lessons-linked regression matrix in tests.
- Enforce docs-as-gate for architecture-affecting changes.

Acceptance criteria:
- Each phase attempt is traceable with run and attempt IDs.
- Blocked runs produce actionable diagnostics.
- CI enforces contract-critical suites and alignment checks.

Required tests/gates:
- Logging schema tests.
- End-to-end traceability tests for failed and successful runs.
- CI policy checks for docs/spec alignment on contract-touching changes.

Primary lessons covered: L-003, L-006, L-007, L-009, L-010.

### M7 - Execution Readiness Gate (Phase 5 Entry)

Goal: verify planning foundation completion and authorize implementation acceleration.

Work items:
- Confirm planning foundation definition-of-done conditions are satisfied.
- Reconcile open questions into decisions or bounded deferrals.
- Publish v1 implementation execution checklist per milestone.

Acceptance criteria:
- Lessons log, tech spec, and implementation plan are cross-consistent.
- High-severity open risks have named owners and mitigation path.
- Phase 5 kickoff checklist approved.

Required tests/gates:
- Documentation consistency check.
- Risk register completeness check.
- Final milestone readiness review.

Primary lessons covered: all lessons (L-001..L-010), with emphasis on governance consistency.

## 5) Deliverables by Milestone

For each milestone, produce:
- Contract/spec delta summary.
- Implementation PR(s) scoped to one concern.
- Test evidence summary (what ran, pass/fail, gaps).
- Lessons traceability update in `docs/lessons-learned/flaming-horse-lessons.md` status column.

## 6) PR and Change Control Rules

- One architectural concern per PR.
- PR must cite impacted:
  - tech spec section(s),
  - lesson ID(s),
  - contract/test updates.
- Architecture-affecting code changes without spec update are non-mergeable.
- Runtime artifacts under `projects/` are not included unless fixture-scoped and justified.

## 7) Risk Register (Current)

| Risk ID | Risk | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| R-001 | Contract freeze incomplete before implementation expansion | High regression/churn risk | Complete M0 before opening broader feature work | WD Team | open |
| R-002 | Retry budgets undefined by phase | Loop and blocked-state inconsistency | Define phase budgets in M1/M4 and codify tests | WD Team | open |
| R-003 | Prompt/schema/parser alignment automation incomplete | High parse/contract failure recurrence | Deliver M3 CI alignment gates before broad generator changes | WD Team | open |
| R-004 | Voice fallback policy ambiguity | Runtime nondeterminism in narration stages | Lock explicit fallback policy during M5 | WD Team | open |
| R-005 | Docs/code drift under execution pressure | Architectural divergence | Enforce docs-as-gate in M6 CI policy | WD Team | open |

## 8) Open Decisions to Resolve During Execution

- Exact per-phase `max_attempts` defaults (`plan`, `build_scenes`, `scene_qc`, `final_render`).
- Whether `blocked` is represented as phase vs phase-status flag.
- Prompt manifest format choice (machine-readable recommended).
- Voice fallback policy for v1 (disabled by default recommended).
- Duration tolerance threshold for final output validation.

## 9) Traceability Matrix (Lessons -> Spec -> Milestones)

| Lesson | Primary Spec Areas | Primary Milestones |
|---|---|---|
| L-001 | 01, 02, 03, 06, 08, 17 | M0, M2 |
| L-002 | 05, 08, 12, 16 | M0, M1, M5 |
| L-003 | 05, 10, 13 | M1, M4, M6 |
| L-004 | 06, 08, 15 | M0, M3 |
| L-005 | 02, 07, 08, 09, 12 | M0, M2, M3, M4 |
| L-006 | 01, 03, 15, 18 | M6 (process), all milestones (scope discipline) |
| L-007 | 01, 04, 11, 13, 15, 18 | M2, M3, M6, M7 |
| L-008 | 03, 06, 11, 14 | M5 |
| L-009 | 01, 05, 08, 09, 10, 13, 18 | M0, M1, M3, M4, M6 |
| L-010 | 04, 13, 16, 17 | M5, M6 |

## 10) Session End Log (Anti-Drift)

- Created: `docs/implementation-plan/README.md`.
- Phase progression: Phase 4 deliverable drafted and aligned to current spec + lessons.
- Next phase/action: begin milestone execution (Phase 5) only after reviewing and approving this plan and resolving highest-priority open decisions.
