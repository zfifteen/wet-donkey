# 14 Voice Policy

Status: draft

## Purpose

Define a stable voice synthesis policy that guarantees deterministic behavior and avoids provider churn leaking into pipeline logic.

## Scope

- Voice service interface contract.
- Cache behavior and completeness requirements.
- Fallback/degraded behavior policy.
- Validation and observability expectations.

## Design

### Voice Interface Contract

- Single internal interface for text-to-audio generation and duration lookup.
- Provider-specific implementation details remain behind adapter boundary.
- Voice outputs include stable metadata (voice ID, cache key, duration, generation mode).

### Cache Policy

- Cache keys are deterministic from normalized text + voice config.
- Cache-hit/miss events are logged.
- Missing cache in required phases follows explicit policy (generate or block), never silent bypass.

### Fallback Policy

- Fallback behavior is explicit and configuration-gated.
- If fallback is disallowed, voice generation failures are hard-blocking.
- Degraded mode must be marked in logs and artifacts.

### Quality/Validation Policy

- Validate output file existence, format, and duration metadata before downstream assembly.
- Voice duration contract feeds timing validation and assembly checks.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-008 | Voice subsystem is stabilized behind one policy-driven interface. |
| L-002 | Voice readiness is part of deterministic phase progression. |
| L-007 | Voice policy remains documented and authoritative. |
| L-009 | Voice validations are explicit gates, not ad hoc checks. |

## Open Questions

- Is fallback ever allowed in v1, or strictly prohibited?
- What cache invalidation policy applies when voice config changes?
- Which minimum audio quality checks are mandatory before assembly?

## Decisions

- WD voice behavior is governed by a strict adapter contract and explicit policy flags.
- Cache and fallback behavior must be deterministic and observable.
- Voice generation failures cannot be silently bypassed.
