# 11 Configuration and Environment Variables

Status: approved

## Purpose

Define deterministic runtime configuration rules so WD behavior is explicit, reproducible, and safe across environments.

## Scope

- Environment variable taxonomy (required/optional).
- Defaulting and override behavior.
- Validation and startup checks.
- Configuration drift prevention.

## Design

### Configuration Classes

1. Required secrets
- API credentials and sensitive tokens.
- Must be present before invoking dependent components.

2. Required runtime controls
- Harness selection, phase limits, retry budgets, feature gates.
- Must have explicit defaults in code and docs.

3. Optional tuning values
- Logging verbosity, timeout tuning, non-breaking performance knobs.

### Startup Validation

- WD performs a preflight configuration validation before phase execution.
- Missing required config for a selected path is a hard fail.
- Invalid enum/range values are rejected before runtime side effects.

### Deterministic Defaults

- Defaults are centralized and versioned.
- Environment overrides are explicit and logged at startup (with secret redaction).
- No hidden fallback to legacy behavior unless explicitly configured.

### Configuration Change Policy

- New variables require spec update and tests.
- Renames/removals require migration notes and backward-compat handling for active milestones.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-001 | Config boundaries prevent ad hoc harness behavior drift. |
| L-002 | Phase execution depends on validated config preconditions. |
| L-007 | Configuration semantics are spec-authoritative and versioned. |
| L-008 | Voice/TTS policy is controlled by explicit configuration, not implicit fallback. |

## Open Questions

- None for WD v1. Previously listed questions were resolved on 2026-03-01 and codified in `Decisions`.

## Decisions

- WD uses strict startup preflight validation for configuration.
- Required vs optional variables are explicitly documented and tested.
- Runtime defaults are centralized; hidden implicit fallbacks are disallowed.
- WD uses layered environment files with precedence: `.env` < `.env.local` < `.env.ci`; missing files are allowed but required keys must still validate.
- Temporary feature flags must include an expiry milestone and removal owner; permanent flags require explicit stability rationale in spec.
- Startup validation emits both human-readable output and machine-readable JSON diagnostics for CI consumption.
