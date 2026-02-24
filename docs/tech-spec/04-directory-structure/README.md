# 04 Directory Structure

Status: draft

## Purpose

Define a repository layout that separates source of truth, generated artifacts, and diagnostics to preserve maintainability and review clarity.

## Scope

- Core source directories and ownership.
- Documentation and lessons directories.
- Runtime/project artifact boundaries.
- Test fixture boundaries.

## Design

### Canonical Layout Rules

- `src/`: production Python source root.
- `scripts/`: orchestrator and deterministic workflow scripts.
- `src/harness/`: LLM harness implementation and schemas/prompts.
- `src/wet_donkey/`: scene helpers and shared runtime logic.
- `src/wet_donkey_voice/`: voice adapter and caching implementation.
- `docs/tech-spec/`: canonical technical spec wiki.
- `docs/lessons-learned/`: FH lessons and guardrail evolution.
- `tests/`: contract, unit, integration, and e2e tests.
- `projects/`: runtime outputs (excluded from core source review).

### Boundary Policy

- Runtime artifacts must not be committed as core implementation changes unless explicitly fixture-scoped.
- Docs and lessons are first-class, versioned alongside code.
- Generated/debug outputs must be isolated from product source directories.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-010 | Runtime artifacts are separated from core system evolution. |
| L-007 | Documentation directories are canonical and maintained with implementation. |
| L-006 | Structure supports smaller concern-scoped changes. |

## Open Questions

- Should fixtures live under `tests/fixtures/` or phase-specific subtrees?
- Which generated artifacts, if any, are intentionally versioned?
- Do we need dedicated `ops/` or `tools/` directories in v1?

## Decisions

- WD repository layout separates core source, docs, and runtime artifacts by default.
- Core code review should not be polluted by generated operational outputs.
- Spec and lessons directories are permanent top-level architecture assets.
