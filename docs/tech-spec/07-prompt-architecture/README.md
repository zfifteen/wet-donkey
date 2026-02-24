# 07 Prompt Architecture

Status: draft

## Purpose

Define a prompt system that is schema-aligned, phase-specific, and resistant to drift across harness, parser, and orchestration layers.

## Scope

- Prompt asset organization by phase.
- System/user prompt responsibilities.
- Prompt variable contracts and rendering rules.
- Prompt-to-schema alignment policy.
- Retry/repair prompt behavior.

## Design

### Prompt Structure

- Prompts are organized per phase in `prompts/<phase>/`.
- Each phase includes at minimum:
- `system.md` (global behavior/policy for that phase),
- `user.md` (task instance + runtime variables),
- optional constraints/examples assets.

### Role Separation

- `system.md` defines invariant rules and non-negotiable constraints.
- `user.md` defines specific task payload for the current phase execution.
- Orchestrator injects runtime context; prompts do not infer hidden state.

### Variable Contract

- Every template variable must be declared in a phase manifest/spec table.
- Missing required variables are a hard failure before model invocation.
- Extra undeclared variables are rejected in strict mode.

### Schema Alignment Rules

- Prompt outputs must map 1:1 to canonical phase schemas.
- Prompts cannot introduce unofficial fields.
- Schema changes require synchronized updates to:
- phase prompt assets,
- schema definitions,
- parser validations,
- phase tests.

### Retry/Repair Prompting

- Repair prompts must include structured failure payloads from validation gates.
- Retry prompts must include attempt delta context to prevent repeated identical output.
- No free-form "try again" retries without new evidence.

### Lessons Traceability

| Lesson ID | WD Rule in This Section |
|---|---|
| L-005 | Prompt/schema/parser alignment is contract-enforced, not best-effort. |
| L-003 | Retry prompts require new evidence/context each attempt. |
| L-007 | Prompt policy is documentation-first and versioned. |
| L-009 | Prompt behavior integrates directly with validation ownership. |

## Open Questions

- Should prompt manifests be markdown tables or machine-readable YAML/JSON?
- How strict should undeclared-variable rejection be in early WD milestones?
- Should prompt assets support per-model variants or one canonical form?

## Decisions

- WD prompt architecture is phase-scoped and contract-driven.
- Prompt templates must remain synchronized with schema and parser contracts.
- Retry/repair prompting always uses structured failure context from validation gates.
