from __future__ import annotations

from harness.contracts.state import (
    DEFAULT_MAX_ATTEMPTS,
    clear_phase_failures,
    create_initial_state,
    record_phase_failure,
    transition_state,
)


def _state_at_phase(phase: str):
    state = create_initial_state("demo-project", "Standing waves")
    order = [
        "plan",
        "review",
        "narration",
        "build_scenes",
        "scene_qc",
        "precache_voiceovers",
        "final_render",
        "assemble",
        "complete",
    ]
    for next_phase in order:
        state = transition_state(state, next_phase)
        if next_phase == phase:
            break
    return state


def test_retry_budget_exhaustion_blocks_phase() -> None:
    state = _state_at_phase("plan")
    limit = DEFAULT_MAX_ATTEMPTS["plan"]

    for _ in range(limit):
        state = record_phase_failure(
            state,
            error_code="INFRASTRUCTURE_ERROR",
            error_message="simulated",
        )

    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "blocked"
    assert payload["failure_context"]["blocked"] is True
    assert payload["failure_context"]["attempt"] == limit


def test_non_exhausted_retry_keeps_phase_active() -> None:
    state = _state_at_phase("build_scenes")
    limit = DEFAULT_MAX_ATTEMPTS["build_scenes"]

    for _ in range(limit - 1):
        state = record_phase_failure(
            state,
            error_code="VALIDATION_ERROR",
            error_message="retryable",
        )

    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "active"
    assert payload["failure_context"]["blocked"] is False


def test_force_block_marks_phase_blocked_immediately() -> None:
    state = _state_at_phase("plan")
    state = record_phase_failure(
        state,
        error_code="POLICY_VIOLATION",
        error_message="non-retryable",
        force_block=True,
    )

    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "blocked"
    assert payload["failure_context"]["blocked"] is True


def test_clear_failures_unblocks_phase() -> None:
    state = _state_at_phase("plan")
    state = record_phase_failure(
        state,
        error_code="POLICY_VIOLATION",
        error_message="non-retryable",
        force_block=True,
    )

    state = clear_phase_failures(state, reason="manual_resume")
    payload = state.model_dump(mode="json")

    assert payload["phase_status"] == "active"
    assert payload["failure_context"] == {}
    assert "plan" not in payload.get("attempt_counters", {})
