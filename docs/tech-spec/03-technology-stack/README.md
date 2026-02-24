# 03 Technology Stack

Status: draft

## Purpose

Define WD’s approved technology stack and boundary rationale to reduce architecture churn and hidden dependency risk.

## Scope

- Orchestration/runtime languages and tooling.
- LLM integration stack.
- Animation, audio, and assembly stack.
- Testing and validation tooling.

## Design

### Stack Overview

- Orchestration: Bash + Python scripts with strict state contracts.
- LLM integration: xAI Responses API via dedicated harness.
- Schema/validation: Pydantic + custom semantic/runtime validators.
- Animation: Manim CE.
- Voice: local cached TTS through a stable adapter interface.
- Assembly: ffmpeg.
- Tests: pytest + shell integration checks.

### Selection Principles

- Favor deterministic and scriptable tools over opaque orchestration.
- Prefer single integration path per subsystem in v1.
- New dependencies require explicit ownership and migration strategy.

### Versioning Policy

- Runtime-critical tools/libraries are pinned by policy.
- Stack changes must include compatibility notes and rollout plan.
- Deprecated paths are removed by explicit milestone, not linger indefinitely.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stack boundaries are stabilized before expansion/migration churn. |
| L-006 | Large multi-stack shifts are split into controlled milestones. |
| L-007 | Stack policy and implementation stay synchronized in spec. |
| L-008 | Voice stack is adapter-isolated with clear policy controls. |

## Open Questions

- Which versions should be hard-pinned in v1 baseline?
- Which stack components can be optional for local development?
- What formal deprecation window should WD require for stack changes?

## Decisions

- WD adopts a single, documented stack per subsystem for v1.
- Stack changes require spec update, migration notes, and tests.
- Runtime-critical dependency behavior must be deterministic and observable.
