from __future__ import annotations

from harness.contracts.state import (
    DEFAULT_MAX_ATTEMPTS,
    LOOP_SIGNATURE_REPEAT_BLOCK_THRESHOLD,
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

    for attempt in range(limit - 1):
        state = record_phase_failure(
            state,
            error_code="VALIDATION_ERROR",
            error_message="retryable",
            attempt_delta=f"attempt-delta-{attempt}",
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


def test_identical_signature_without_delta_blocks_retry_loop() -> None:
    state = _state_at_phase("build_scenes")
    state = record_phase_failure(
        state,
        error_code="SCHEMA_VIOLATION",
        error_message="same-failure",
    )
    state = record_phase_failure(
        state,
        error_code="SCHEMA_VIOLATION",
        error_message="same-failure",
    )

    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "blocked"
    assert payload["failure_context"]["loop_risk"] is True
    assert payload["failure_context"]["blocked_reason"] == "NO_NEW_EVIDENCE"
    assert payload["failure_context"]["loop_signature_repeat_threshold"] == LOOP_SIGNATURE_REPEAT_BLOCK_THRESHOLD


def test_identical_signature_with_new_delta_remains_retryable() -> None:
    state = _state_at_phase("build_scenes")
    state = record_phase_failure(
        state,
        error_code="SCHEMA_VIOLATION",
        error_message="same-failure",
    )
    state = record_phase_failure(
        state,
        error_code="SCHEMA_VIOLATION",
        error_message="same-failure",
        attempt_delta="updated remediation directive",
    )

    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "active"
    assert payload["failure_context"]["retryable"] is True
    assert payload["failure_context"]["has_meaningful_delta"] is True
    assert payload["failure_context"]["blocked"] is False


def test_non_retryable_failure_blocks_immediately() -> None:
    state = _state_at_phase("plan")
    state = record_phase_failure(
        state,
        error_code="POLICY_VIOLATION",
        error_message="forbidden operation",
        gate="contract",
        owner_component="orchestrator",
        retryable=False,
    )
    payload = state.model_dump(mode="json")
    assert payload["phase_status"] == "blocked"
    assert payload["failure_context"]["retryable"] is False
    assert payload["failure_context"]["blocked_reason"] == "NON_RETRYABLE_FAILURE"
