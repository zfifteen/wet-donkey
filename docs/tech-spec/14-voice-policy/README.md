# 14 Voice Policy

Status: approved

## Purpose

Define a stable voice synthesis policy that guarantees deterministic behavior and avoids provider churn leaking into pipeline logic.

## Scope

- Voice service interface contract.
- Cache behavior and coverage requirements.
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

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD voice behavior is governed by a strict adapter contract and explicit policy flags.
- Cache and fallback behavior must be deterministic and observable.
- Voice generation failures cannot be silently bypassed.
- v1 fallback policy is disabled by default; fallback may only be enabled for non-release runs through explicit configuration and must be labeled in output metadata.
- Cache invalidation is deterministic through a cache key composed of normalized narration text + voice profile + synthesis settings hash; changed voice configuration always produces a new key.
- Minimum audio acceptance checks in v1 are: file exists, decodable format, non-zero duration, duration metadata present, and sample-rate/channel metadata captured for downstream timing validation.
