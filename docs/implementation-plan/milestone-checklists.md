# Milestone Checklists (M1-M7)

Status: approved (Phase 4 deliverable)  
Last updated: 2026-03-01

Purpose: publish execution-ready checklists for every implementation milestone after M0.

## M1 - Orchestrator Deterministic Core

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-002, L-003, L-009.
- [x] PR scope rule confirmed: one architectural concern per PR.

## M2 - Harness and Structured Output Path

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-001, L-005, L-007.
- [x] Single-harness constraint confirmed (`src/harness/` only).

## M3 - Prompt/Schema/Parser Contract Lock

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-005, L-007, L-009.
- [x] Alignment checks requirement confirmed (prompt <-> schema <-> parser).

## M4 - Validation Hierarchy and Retry Control

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-003, L-005, L-009.
- [x] Bounded-retry and loop-detection policies confirmed against tech spec.

## M5 - Voice, Render, and Assembly Contract Integration

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-002, L-008, L-009, L-010.
- [x] Voice fallback policy and render tolerance decisions confirmed in tech spec.

## M6 - Observability, Risk Controls, and CI Enforcement

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Required tests/gates are explicitly listed.
- [x] Lessons mapping validated: L-003, L-006, L-007, L-009, L-010.
- [x] Docs-as-gate policy confirmed as non-optional.

## M7 - Execution Readiness Gate (Phase 5 Entry)

- [x] Scope, work items, and acceptance criteria locked in `README.md`.
- [x] Documentation consistency check completed (see `phase4-completion-report.md`).
- [x] Risk register coverage check completed (owner + mitigation present for open/high risks).
- [x] Phase 5 kickoff approved in canonical docs.

## Release Gate Summary

- [x] Checklists are published for every milestone M1-M7.
- [x] M0 checklist is finalized and approved.
- [x] Phase 4 deliverables are complete and ready for execution under Phase 5.
