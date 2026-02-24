# AGENTS.md

This document defines the operating game plan for AI agents working in Wet Donkey (WD).

## Mission

Wet Donkey is a clean, fresh re-implementation of Flaming Horse (FH), not a continuation of FH's evolving/spaghetti architecture.

Primary goal: extract lessons from FH failures and use them to build WD correctly from first principles.

## Repositories and Roles

- Wet Donkey (implementation target): `/Users/velocityworks/IdeaProjects/wet-donkey`
- Flaming Horse (analysis source): `/Users/velocityworks/IdeaProjects/flaming-horse`

FH is studied for lessons only. WD is where new architecture/spec/implementation are authored.

## Canonical Game Plan (Do Not Reorder)

1. Continue deep analysis of FH implementation.
2. Produce a formal lessons-learned document in WD.
3. Revise WD technical specification using those lessons.
4. Revise WD implementation plan using the revised spec.
5. Execute WD implementation against the revised plan.

If work requests conflict with this sequence, pause and explicitly call out the conflict.

## Current Documentation Baseline

- Existing (legacy draft): `docs/legacy/WET_DONKEY_IMPLEMENTATION_PLAN.md`
- New wiki-style spec scaffold: `docs/tech-spec/`
- Lessons learned index: `docs/lessons-learned/README.md`
- FH analysis log: `docs/lessons-learned/flaming-horse-lessons.md`

The wiki under `docs/tech-spec/` is the destination for the revised tech spec. Do not treat the old implementation plan as final truth.

## Non-Negotiable Operating Rules

- WD must remain a clean re-implementation; avoid copying FH architecture blindly.
- Every major WD design choice should trace to either:
  - an FH lesson learned, or
  - an explicit WD-first rationale documented in spec.
- Avoid hidden complexity and "self-heal loop" dependence as a design crutch.
- No architecture pivots without updating spec docs first.
- Prefer deterministic state handling and explicit contracts over implicit behavior.
- Keep docs and implementation in sync; flag drift immediately.

## Required Deliverables by Phase

### Phase 1: FH Analysis

Produce concrete findings (not impressions):
- Failure patterns
- Root causes
- Architectural anti-patterns
- Process/tooling gaps

### Phase 2: Lessons Learned Document

Create and maintain a WD-local lessons artifact that includes:
- What failed in FH
- Why it failed
- How WD will prevent recurrence
- Status of whether the prevention is implemented, planned, or pending

### Phase 3: Revised WD Tech Spec

Populate `docs/tech-spec/` section-by-section with:
- explicit boundaries
- data/state contracts
- validation gates
- error/retry policy
- observability and test strategy

### Phase 4: Revised WD Implementation Plan

Update/replace implementation planning so it is:
- derived from the revised tech spec
- sequenced by milestones
- testable at each milestone
- clear on acceptance criteria

## Daily Anti-Drift Workflow

At start of each work session:
1. Re-state mission and current phase.
2. Confirm today's tasks map to canonical game plan.
3. Identify any drift between code and docs.
4. Execute scoped work.
5. Record what changed and what phase is next.

At end of each session:
- Update this AGENTS.md if goals/constraints changed.
- Update relevant spec/lessons docs to keep alignment current.

## Definition of Done for "Planning Foundation"

The planning foundation is complete only when all are true:
- FH lessons are documented clearly in WD.
- Revised tech spec in `docs/tech-spec/` is complete enough to implement from.
- Revised implementation plan is aligned to that spec.
- Open risks and unknowns are explicitly tracked.

## Instructions to Future Agents

If you start with no prior context:
1. Read this file first.
2. Read `docs/lessons-learned/README.md` and `docs/lessons-learned/flaming-horse-lessons.md`.
3. Read `docs/tech-spec/README.md` and section stubs/status.
4. Read the current implementation plan.
5. Propose work only within the current phase of the canonical game plan.

When uncertain, optimize for architectural clarity, maintainability, and documented rationale over speed.
