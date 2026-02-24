# 18 Known Constraints and Risk Areas

Status: draft

## Purpose

Track known WD constraints and risk areas explicitly so design and implementation choices are made with visible tradeoffs.

## Scope

- External dependency constraints.
- Performance/latency risks.
- Contract and migration risks.
- Operational/process risks.

## Design

### Known Constraints

- External API availability and rate/latency behavior can affect phase throughput.
- Stateful context retention windows may limit long-paused project continuity.
- Manim/ffmpeg runtime variability introduces platform-specific risk.
- Voice generation dependencies can become throughput bottlenecks.

### Primary Risk Areas

1. Contract drift risk
- Prompt/schema/parser/orchestrator divergence.

2. Retry-loop risk
- Repeated failure signatures without meaningful attempt delta.

3. Scope-churn risk
- Multi-concern changes that hide regressions.

4. Documentation divergence risk
- Implementation changes without synchronized spec updates.

### Risk Controls

- Contract alignment checks in CI.
- Loop detection and blocked escalation.
- Milestone slicing and review scope limits.
- Docs-as-gate policy for architecture-affecting changes.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stabilize interfaces before feature expansion to reduce churn risk. |
| L-003 | Retry-loop risk is actively detected and escalated. |
| L-006 | Scope discipline is a core risk mitigation control. |
| L-007 | Spec drift is treated as a first-class risk. |
| L-009 | Validation sprawl risk is controlled by explicit gate ownership. |

## Open Questions

- Which risks are acceptable for WD v1 launch versus deferred mitigation?
- What quantitative risk thresholds should trigger design review?
- How should risk status be reported per milestone?

## Decisions

- WD will maintain explicit risk tracking as part of core technical governance.
- Risk controls are implemented as enforceable process + technical gates.
- Lessons-derived risks are prioritized in planning and test strategy.
