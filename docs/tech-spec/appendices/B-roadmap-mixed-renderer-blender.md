# Appendix B: Roadmap - Mixed Renderer Capability (Manim + Blender)

Status: roadmap (deferred from WD v1)

## Purpose

Capture the post-v1 intent to support mixed-renderer videos where a single project may include both:
- Manim scenes (diagram/math-native animation), and
- Blender scenes (cinematic/non-math 3D visuals).

## Intent

WD should eventually support composing one final video from a renderer-aware scene sequence, with each scene explicitly declaring its renderer contract.

Example intent:
- Scene 1-4 rendered by Manim,
- Scene 5 rendered by Blender,
- Scene 6-10 rendered by Manim,
- final assembly merges all validated scene outputs in canonical order.

## Non-Goals for WD v1

- No Blender runtime dependency in WD v1 baseline.
- No parallel harness architecture introduced for this roadmap item.
- No expansion of v1 acceptance criteria to include mixed-renderer execution.

## Constraints and Guardrails

- Must preserve WD contract-first architecture and deterministic state handling.
- Must not reintroduce dual-harness or parallel long-lived orchestration paths.
- Must define renderer boundaries through explicit schemas/contracts before implementation.
- Must keep validation ownership explicit per renderer while preserving one orchestrator authority.

## Candidate Future Design Direction

- Add optional `renderer` field to scene contracts (default `manim`).
- Keep one orchestrator state machine; dispatch render stage by scene renderer.
- Define renderer adapter interface so renderer-specific details stay isolated.
- Keep assembly contract renderer-agnostic (validated scene video/audio manifest inputs only).

## Entry Criteria to Start Implementation (Post-v1)

- WD v1 contracts and milestones are complete and stable.
- No unresolved high-severity contract-drift risks in current WD stack.
- Renderer extension contracts are spec-reviewed and test strategy is defined.
- Dependency and CI implications (for example Blender install/runtime) are approved.

## Exit Criteria for Roadmap Graduation

- Mixed-renderer contract sections are promoted from roadmap appendix into main tech-spec sections.
- Milestone plan is added to implementation plan with explicit acceptance tests.
- Lessons traceability and risk controls are updated before coding starts.
