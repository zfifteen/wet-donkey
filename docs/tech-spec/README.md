# Wet Donkey Tech Spec Wiki

This wiki is the canonical technical specification for Wet Donkey.

## Phase 3 Exit Criteria

Phase 3 is approved only when all are true:

1. Every section under `docs/tech-spec/*/README.md` is marked `Status: approved` (not `draft`/`stub`).
2. Section `Open Questions` are either:
   - resolved into `Decisions`, or
   - explicitly deferred with owner and milestone in `docs/implementation-plan/README.md`.
3. Required Phase 3 scope is covered with implementable specificity:
   - explicit boundaries,
   - data/state contracts,
   - validation gates,
   - error/retry policy,
   - observability strategy,
   - test strategy.
4. Lessons traceability is present for major design decisions.
5. `AGENTS.md` State Snapshot is updated to indicate Phase 3 approved and Phase 4 active.

## Navigation

1. [01 Overview](./01-overview/README.md)
2. [02 xAI Responses API Integration](./02-xai-responses-api-integration/README.md)
3. [03 Technology Stack](./03-technology-stack/README.md)
4. [04 Directory Structure](./04-directory-structure/README.md)
5. [05 Pipeline State Machine](./05-pipeline-state-machine/README.md)
6. [06 Core Components](./06-core-components/README.md)
7. [07 Prompt Architecture](./07-prompt-architecture/README.md)
8. [08 Data Contracts](./08-data-contracts/README.md)
9. [09 Validation Gates](./09-validation-gates/README.md)
10. [10 Self-Healing and Retry Logic](./10-self-healing-and-retry-logic/README.md)
11. [11 Configuration and Environment Variables](./11-configuration-and-environment-variables/README.md)
12. [12 Harness Exit Codes](./12-harness-exit-codes/README.md)
13. [13 Logging and Observability](./13-logging-and-observability/README.md)
14. [14 Voice Policy](./14-voice-policy/README.md)
15. [15 Testing](./15-testing/README.md)
16. [16 Render and Assembly](./16-render-and-assembly/README.md)
17. [17 Stateful Training Integration](./17-stateful-training-integration/README.md)
18. [18 Known Constraints and Risk Areas](./18-known-constraints-and-risk-areas/README.md)
19. [Appendices](./appendices/README.md)

## Source

Legacy reference only: `docs/legacy/WET_DONKEY_IMPLEMENTATION_PLAN.md`
