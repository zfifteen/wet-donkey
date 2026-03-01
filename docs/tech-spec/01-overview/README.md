# 01 Overview

Status: approved

## Purpose

Define Wet Donkey (WD) as a clean re-implementation of Flaming Horse (FH) with explicit contracts, deterministic orchestration, and bounded recovery behavior.

## Scope

- Mission and architectural intent for WD.
- Non-goals and anti-patterns WD must avoid.
- Canonical design principles that all deeper spec sections must follow.
- Traceability from FH lessons to WD rules.

## Design

### Product Objective

WD converts a topic into a narrated Manim video through a deterministic multi-phase pipeline. The primary objective is maintainability and reliability first, with quality improvements layered on top.

### Core Principles

- Contract-first design across orchestrator, harness, prompts, schemas, and generated artifacts.
- Deterministic phase ownership and state transitions.
- Orchestration and infrastructure concerns are deterministic-code responsibilities, not LLM responsibilities.
- LLM scope is constrained to bounded creative/content outputs inside contract-defined schemas.
- First-pass correctness prioritized over retry volume.
- Stable subsystem interfaces (LLM harness, TTS, retrieval, render assembly).
- Documentation is authoritative and versioned with implementation.

### Non-Goals

- WD is not a partial patch of FH.
- WD does not rely on self-heal loops as normal control flow.
- WD does not permit undocumented architecture pivots during implementation.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Freeze major interface boundaries before expanding features. |
| L-003 | Retry is fallback behavior, not a primary pipeline path. |
| L-006 | Implementation milestones must remain small and single-concern. |
| L-007 | Spec wiki is authoritative; code and docs must ship together. |
| L-009 | Validation exists to enforce contracts, not mask upstream instability. |

## Open Questions

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD will be developed contract-first with explicit traceability to lessons learned.
- WD spec wiki (`docs/tech-spec/`) is canonical and must lead implementation updates.
- WD architecture will optimize for deterministic operation and maintainability over rapid feature expansion.
- WD explicitly separates concerns: deterministic code is the orchestrator/control plane; the LLM is a constrained content generator.
- The first frozen interfaces for WD v1 are: `project_state.json`, phase output schemas, scaffold slot markers, harness exit-code mapping, and helper API registry.
- Global retry policy baseline is fixed at "first pass preferred, bounded retries only"; numeric defaults are defined in section 10 and enforced by orchestrator state policy in section 05.
- WD execution PR scope is constrained to one architectural concern per change and a target of <= 600 net LOC for code (excluding generated artifacts and snapshots) unless a spec-approved exception is recorded.
