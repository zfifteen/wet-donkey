# Wet Donkey Revised Implementation Plan

Status: complete (Phase 4 delivered; Phase 5 execution baseline)  
Last updated: 2026-03-01  
Current canonical phase: Phase 5 (implementation execution against approved plan)  
Plan source of truth: `docs/tech-spec/` + `docs/lessons-learned/flaming-horse-lessons.md`

## 1) Session Start Alignment (Anti-Drift)

- Mission restatement: WD remains a clean re-implementation of FH, with deterministic contracts and no dual-harness regression.
- Current phase restatement: Phase 4 deliverables are complete; this document is now the approved baseline for active Phase 5 execution.
- Canonical game-plan alignment: this document executes step 4 without reordering steps 1-3.
- Drift snapshot (as of 2026-03-01):
  - Tech spec sections are approved and Phase 3 is explicitly approved in canonical control docs.
  - Implementation plan is approved and synchronized to finalized Phase 3 defaults.

## 1.1) Phase Gate

Phase 5 activation condition:

- [x] Phase 4 milestones and acceptance criteria are completed and evidence-backed.
- [x] Phase 5 kickoff checklist is explicitly approved in canonical control docs.

## 2) Planning Principles

- Contract-first before feature throughput.
- One harness path only: `src/harness/` (Responses API), no legacy fallback.
- Deterministic orchestration and explicit state transitions.
- Retries are bounded, evidence-driven, and never default control flow.
- Milestones are small, single-concern, and test-gated.
- Every milestone must map to lessons-learned IDs and spec sections.

## 3) Scope and Non-Scope

### In Scope (Phase 4 to execution handoff)

- Freeze implementable WD v1 contracts from current approved tech-spec baseline.
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

Goal: verify planning foundation readiness and authorize implementation acceleration.

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
- Risk register coverage check.
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
| R-001 | Contract freeze unresolved before implementation expansion | High regression/churn risk | Phase 3 approved; M0 contract freeze planning deliverables completed; execute M0 implementation gates first in Phase 5 | WD Team | mitigated |
| R-002 | Retry budgets undefined by phase | Loop and blocked-state inconsistency | Defaults locked in tech spec; codify and test in M1/M4 | WD Team | mitigated |
| R-003 | Prompt/schema/parser alignment automation unresolved | High parse/contract failure recurrence | M3 alignment gates are active and enforced in CI baseline (`check_prompt_schema_alignment.py`) | WD Team | mitigated |
| R-004 | Voice fallback policy ambiguity | Runtime nondeterminism in narration stages | Policy locked in tech spec; enforced in M5 implementation and contract tests | WD Team | mitigated |
| R-005 | Docs/code drift under execution pressure | Architectural divergence | Docs-as-gate policy enforced via `scripts/check_docs_as_gate.py` and CI workflow | WD Team | mitigated |

## 8) Locked Decisions from Phase 3 Finalization

- Per-phase retry defaults are fixed (`plan=2`, `build_scenes=4`, `scene_qc=3`, `final_render=2`, others bounded <= 2 where applicable).
- `blocked` is represented as `phase_status` on the active phase, not a standalone phase.
- Prompt manifests are machine-readable YAML with strict undeclared-variable rejection.
- Voice fallback is disabled by default in v1 and allowed only via explicit non-release configuration.
- Final output duration tolerance is `max(0.5s, 2% of expected duration)`.

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

## 10) Session State Snapshot (Anti-Drift)

- Created: `docs/implementation-plan/README.md`.
- Phase state: Phase 4 complete; plan approved as the active execution baseline for Phase 5.
- Next action: implement remaining Phase 5 runtime handlers (`narration`, `build_scenes`, `scene_qc`) under the enforced contract/observability gates.

## 11) Phase 4 Completion Record

- Completion report: `docs/implementation-plan/phase4-completion-report.md`
- M0 checklist: `docs/implementation-plan/M0-checklist.md`
- M1 evidence: `docs/implementation-plan/M1-evidence.md`
- M2 evidence: `docs/implementation-plan/M2-evidence.md`
- M3 evidence: `docs/implementation-plan/M3-evidence.md`
- M4 evidence: `docs/implementation-plan/M4-evidence.md`
- M5 evidence: `docs/implementation-plan/M5-evidence.md`
- M6 evidence: `docs/implementation-plan/M6-evidence.md`
- M1-M7 checklists: `docs/implementation-plan/milestone-checklists.md`
- Phase 5 kickoff checklist: `docs/implementation-plan/phase5-kickoff-checklist.md`
- Readiness decision: Phase 5 kickoff approved on 2026-03-01.
