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
- Risk of self-heal loops becoming the primary success path instead of recovery.

3. Scope-churn risk
- Multi-concern changes that hide regressions.

4. Documentation divergence risk
- Implementation changes without synchronized spec updates.

5. Scaffold boundary corruption risk
- Missing or mutated scaffold markers (for example `SLOT_START`) can invalidate downstream parsing and scene assembly.

6. Schema fragility under repair pressure
- Malformed JSON or partial outputs can cascade into repeated repair cycles and false “success” convergence.

7. Retry-context truncation risk
- Loss of prior attempt details reduces repair signal quality and increases loop churn.

### Risk Controls

- Contract alignment checks in CI.
- Loop detection and blocked escalation.
- Milestone slicing and review scope limits.
- Docs-as-gate policy for architecture-affecting changes.
 - Scaffold boundary validation at Contract Gate plus dedicated regression tests.
 - Strict schema parsing with explicit error localization (no auto-repair).
 - Required preservation of full retry context with diff summaries when size-limited.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Stabilize interfaces before feature expansion to reduce churn risk. |
| L-003 | Retry-loop risk is actively detected and escalated. |
| L-004 | Scaffold boundary corruption is treated as a first-class risk with explicit controls. |
| L-005 | Schema fragility is mitigated with strict parsing and alignment gates. |
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
