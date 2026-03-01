from __future__ import annotations

import json
from pathlib import Path

from harness.contracts.observability import (
    append_event,
    emit_phase_event,
    event_from_failure_context,
    export_blocked_trace_bundle,
    read_events,
)
from harness.contracts.state import create_initial_state, record_phase_failure, save_state_atomic, transition_state


def _prepare_plan_state(project_dir: Path):
    state = create_initial_state("obs-test", "Observability")
    state = transition_state(state, "plan")
    save_state_atomic(project_dir / "project_state.json", state)
    return state


def test_phase_events_include_run_and_attempt_ids(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    _prepare_plan_state(project_dir)

    emit_phase_event(
        project_dir,
        phase="plan",
        event_type="phase_start",
        attempt=1,
        actor="orchestrator",
    )
    emit_phase_event(
        project_dir,
        phase="plan",
        event_type="phase_success",
        attempt=1,
        actor="orchestrator",
    )

    events = read_events(project_dir)
    assert len(events) == 2

    run_ids = {event["run_id"] for event in events}
    assert len(run_ids) == 1
    assert {event["phase_attempt_id"] for event in events} == {"plan:attempt:1"}


def test_blocked_failure_exports_trace_bundle(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    state = _prepare_plan_state(project_dir)
    state = record_phase_failure(
        state,
        error_code="POLICY_VIOLATION",
        error_message="forbidden action",
        gate="contract",
        owner_component="orchestrator",
        retryable=False,
        force_block=True,
    )
    save_state_atomic(project_dir / "project_state.json", state)

    payload = state.model_dump(mode="json")
    failure_context = payload["failure_context"]

    blocked_event = event_from_failure_context(
        project_dir,
        phase=state.phase,
        failure_context=failure_context,
        actor="orchestrator",
    )
    append_event(project_dir, blocked_event)

    bundle_path = export_blocked_trace_bundle(
        project_dir,
        state_payload=payload,
        actor="orchestrator",
    )

    assert bundle_path.exists()

    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle_payload["phase"] == "plan"
    assert bundle_payload["phase_status"] == "blocked"
    assert bundle_payload["failure_diagnostics"]["component_owner"] == "orchestrator"
    assert bundle_payload["failure_diagnostics"]["gate"] == "contract"
    assert bundle_payload["failure_diagnostics"]["next_action"]

    event_types = [event["event_type"] for event in read_events(project_dir)]
    assert "phase_blocked" in event_types
    assert "diagnostic_bundle" in event_types
