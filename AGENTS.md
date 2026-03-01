# AGENTS.md

Wet Donkey (WD) agent control spec.
This file is a compact, durable coordination contract, not a historical log.

## 1) Mission

Wet Donkey is a clean re-implementation of Flaming Horse (FH), built from first principles.
WD must apply FH lessons without inheriting FH architecture/sprawl.

## 2) State Snapshot (Overwrite-Only)

As of: 2026-03-01

- Current phase: Phase 5 (implementation execution)
- Next phase: N/A (Phase 5 is the terminal execution phase in the canonical game plan)
- Phase status flags:
  - P1 FH analysis: complete for current audited FH run set
  - P2 lessons learned: complete for current scope (L-013 through L-023 captured)
  - P3 revised tech spec: approved
  - P4 revised implementation plan: complete and approved
  - P5 implementation: active
- Current blockers:
  - None for Phase 5 activation; implementation execution pending milestone-by-milestone delivery
- Next concrete action:
  - Implement remaining Phase 5 runtime handlers (`narration`, `build_scenes`, `scene_qc`) under enforced contract, retry, and observability gates

Rule: this snapshot is updated in place. Never append timeline entries here.

## 3) Canonical Game Plan (Do Not Reorder)

1. Continue deep analysis of FH implementation.
2. Produce a formal lessons-learned document in WD.
3. Revise WD technical specification using those lessons.
4. Revise WD implementation plan using the revised spec.
5. Execute WD implementation against the revised plan.

If requested work conflicts with this order, call out the conflict explicitly.

## 4) State Authority and Drift Rules

Precedence for phase/state truth:

1. `AGENTS.md` State Snapshot (Section 2)
2. `docs/implementation-plan/README.md` current canonical phase
3. `docs/lessons-learned/flaming-horse-lessons.md` lesson/status evidence
4. `docs/tech-spec/` section status and contracts

If any contradiction is found:

1. Stop and identify the mismatch.
2. Update `AGENTS.md` snapshot in the same session.
3. Update the conflicting canonical doc if needed.
4. Do not end session with unresolved state contradictions.

## 5) WD Non-Negotiables

- WD remains a clean re-implementation; do not copy FH architecture blindly.
- Every major WD design choice must map to:
  - an FH lesson learned, or
  - a WD-first rationale documented in spec.
- The LLM is not the orchestrator.
- Deterministic code owns:
  - file writes/mutations
  - phase advancement
  - retries/escalation
  - validation/policy enforcement
  - state persistence
- Avoid hidden complexity and self-heal loops as a design crutch.
- No architecture pivots without spec updates first.
- Prefer explicit contracts and deterministic state handling.
- Keep docs and implementation synchronized; flag and fix drift immediately.
- WD has one harness module only: `src/harness/`.

## 6) Phase Deliverables (Definition-Level)

Phase 1: FH Analysis
- Produce concrete findings: failure patterns, root causes, anti-patterns, tooling/process gaps.

Phase 2: Lessons Learned
- Maintain WD-local lessons with what failed, why, WD prevention, and status.

Phase 3: Revised Tech Spec
- Populate `docs/tech-spec/` with boundaries, data/state contracts, validation gates, retry/error policy, observability, and tests.

Phase 4: Revised Implementation Plan
- Maintain `docs/implementation-plan/README.md` with spec-derived milestones, acceptance criteria, and testability at each milestone.

Phase 5: Implementation
- Execute milestones with contract/tests/docs alignment and lessons traceability.

## 7) Session Control Loop

At session start:

1. Read this file first.
2. Confirm Section 2 snapshot still matches canonical docs.
3. Restate mission + current phase.
4. Map proposed work to canonical game plan.

During session:

1. Keep work within current phase scope unless explicitly reprioritized.
2. Tie major design decisions to lesson IDs or WD-first rationale.
3. Fix state/document drift immediately when detected.

At session end:

1. Update Section 2 snapshot (overwrite only).
2. Update affected canonical docs.
3. Record unresolved risks/unknowns in canonical docs (not here).

## 8) Documentation and Tooling Baseline

- Lessons index: `docs/lessons-learned/README.md`
- Lessons log: `docs/lessons-learned/flaming-horse-lessons.md`
- FH audit evidence: `docs/analysis/fh-pr-audit/`
- Revised tech spec: `docs/tech-spec/`
- Revised implementation plan: `docs/implementation-plan/README.md`
- Legacy plan (non-canonical): `docs/legacy/WET_DONKEY_IMPLEMENTATION_PLAN.md`
- Python runtime requirement: WD scripts/tests/tooling must run on `python3.13`; using `python3` or earlier runtimes is non-compliant.
- IntelliJ MCP is the default execution surface when available.
  - Prefer IntelliJ-native operations for project analysis, code search, inspections, semantic symbol lookups, refactors, formatting, builds, and run configurations.
  - Prefer IntelliJ inspection/build outputs over ad-hoc manual reasoning whenever equivalent IDE functionality exists.
  - After material edits, run IntelliJ validation first (`get_file_problems`, then `build_project` when relevant).
- GitHub CLI assumption: `gh` is always available and authenticated in this workspace; use `gh` for GitHub operations.
- Shell/CLI fallback is allowed only when IntelliJ MCP lacks the needed capability or is unavailable; document fallback rationale in the session response.

## 9) File Size and Structure Guardrail

- Target max length: 200 lines.
- This file must stay declarative and compact.
- Additions must replace/consolidate existing content, not append historical narrative.
- Historical evidence belongs in canonical docs, not `AGENTS.md`.

## 10) Glossary (Execution and Control)

- Active phase: the only phase that may receive execution work in the current session.
- Approved: explicit sign-off state for a phase or spec section; required before phase advancement.
- Blocker: a condition that prevents phase advancement until resolved.
- Canonical docs: authoritative project-control documents (`AGENTS.md`, tech spec, lessons log, implementation plan).
- Drift: contradiction between control docs, spec, and/or implementation state.
- Exit criteria: required conditions that must be satisfied before a phase can be approved.
- Finalization: converting draft coverage into approved, implementable guidance.
- Gate: mandatory decision/validation checkpoint that controls progression.
- In scope: work allowed under the current active phase.
- Next phase: the immediate phase that follows the active phase once exit criteria are approved.
- Phase advancement: explicit change of active phase after gate/approval conditions are met.
- Prepared: drafted and available, but not yet active for execution.
- State snapshot: overwrite-only control block in this file defining current phase truth.
- Status flags: per-phase state markers used for quick control-plane interpretation.
