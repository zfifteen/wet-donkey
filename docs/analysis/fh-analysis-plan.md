# Flaming Horse Analysis Execution Plan

Status: draft (execution not started)  
Last updated: 2026-02-24  
Phase alignment: Canonical game plan step 1 (deep FH analysis)

## 1) Objective

Finish a structured, evidence-first Flaming Horse (FH) analysis pass that is sufficient to finalize the Wet Donkey (WD) tech spec without speculative gaps.

## 2) Scope

In scope:
- FH implementation behavior and failure modes across orchestrator, harness, prompts, validation, state, voice, and render pipeline.
- Process and change-management patterns visible in FH PR history.
- Runtime and contract drift indicators that impacted reliability/maintainability.

Out of scope:
- Implementing WD architecture changes directly during this analysis step.
- Rewriting FH as a solution path.
- Expanding WD implementation work before analysis outputs are complete.

## 3) Analysis Questions (Must Answer)

- Which FH failure classes recur and why?
- Which failures are contract/design failures vs execution/infrastructure failures?
- Which failure classes are blocked by spec-only controls vs code+test controls?
- Which WD spec sections still contain open decisions because FH evidence is incomplete?
- What is the minimum guardrail set required to prevent repeat FH failures in WD?

## 4) Evidence Sources

Primary:
- `docs/analysis/fh-pr-audit/merged_prs_detailed.json`
- `docs/analysis/fh-pr-audit/pr_comments.jsonl`
- `docs/analysis/fh-pr-audit/pr_files.jsonl`
- FH local repository at `/Users/velocityworks/IdeaProjects/flaming-horse`

Derived WD artifacts:
- `docs/lessons-learned/flaming-horse-lessons.md`
- `docs/tech-spec/` sections impacted by findings

## 5) Workstreams

### WS1 - PR/Change Pattern Analysis

Goal: identify high-frequency churn zones and regression-prone change shapes.

Outputs:
- churn heatmap by subsystem/path
- multi-concern PR risk list
- regression-linked PR clusters

### WS2 - Runtime Failure Class Analysis

Goal: classify FH runtime failures into deterministic categories.

Outputs:
- failure taxonomy (contract/schema/semantic/runtime/process)
- root-cause notes with evidence links
- recurrence counts and severity ranking

### WS3 - Contract Drift Analysis

Goal: map drift edges between orchestrator, prompt, schema, parser, scaffold, and state.

Outputs:
- drift matrix (producer/consumer mismatch map)
- top drift signatures and affected phases
- required WD contract controls

### WS4 - Retry/Self-Heal Behavior Analysis

Goal: quantify when repair loops were useful vs compensating for weak first pass.

Outputs:
- loop signature catalog
- bounded-retry policy recommendations (phase-specific)
- blocked-escalation trigger recommendations

### WS5 - Process/Documentation Drift Analysis

Goal: identify process and documentation failures that enabled technical drift.

Outputs:
- docs/code drift examples with dates/PR references
- governance control recommendations for WD
- PR scope discipline recommendations

## 6) Execution Method

1. Build evidence slices by workstream from existing PR audit data and targeted FH code reads.
2. Record findings in a normalized finding template (below).
3. Map each validated finding to:
   - lessons entry update (`planned` -> `in-progress`/`implemented`/`verified` as appropriate),
   - affected WD spec section(s),
   - required test/control type.
4. Rank findings by implementation impact on WD spec finalization.
5. Produce an analysis closeout summary with unresolved unknowns.

## 7) Finding Template (Required)

For each finding, capture:
- Finding ID: `FH-A-###`
- Workstream: `WS1`..`WS5`
- Failure pattern summary
- Evidence (PR/file/log/runtime symptom)
- Root cause
- WD prevention/control
- Spec impact (`docs/tech-spec/<section>`)
- Test impact (contract/unit/integration/e2e/process gate)
- Confidence (`high`/`medium`/`low`)
- Status (`open`/`validated`/`applied-to-spec`)

## 8) Deliverables

Required deliverables for this analysis cycle:
- Updated FH analysis evidence summary in `docs/analysis/` (new cycle report).
- Updated `docs/lessons-learned/flaming-horse-lessons.md` with concrete status movement and new IDs if needed.
- Spec gap/decision list identifying what blocks final WD tech spec signoff.
- Proposed WD guardrail updates traceable to evidence.

## 9) Exit Criteria (Analysis Complete)

Analysis plan execution is complete only when all are true:
- All five workstreams have at least one validated output artifact.
- Every high-severity finding has a mapped WD prevention strategy.
- Open WD tech spec decisions are reduced to a bounded list with explicit owners.
- Lessons log is updated and consistent with evidence artifacts.
- A “ready-to-finalize-spec” checkpoint is recorded.

## 10) Anti-Drift Session Workflow

At session start:
- Restate mission and current canonical step (step 1).
- State intended workstream(s) for the session.
- Confirm tasks do not skip ahead into implementation execution.

At session end:
- Record completed workstream progress.
- Update lessons status and spec impacts.
- Record next highest-priority unanswered analysis question.

## 11) Immediate Next Actions (Not Executed Yet)

- Review and approve this execution plan.
- Select first execution slice (recommended order: WS3 -> WS2 -> WS4 -> WS1 -> WS5).
- Open a cycle-1 analysis report file under `docs/analysis/` using the finding template.
