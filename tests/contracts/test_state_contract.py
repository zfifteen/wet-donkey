from __future__ import annotations

import json

import pytest

from harness.contracts.state import (
    CONTRACT_VERSION,
    PhaseTransitionError,
    create_initial_state,
    load_state,
    save_state_atomic,
    transition_state,
)


def test_initial_state_has_required_contract_fields() -> None:
    state = create_initial_state("demo-project", "Standing waves")
    payload = state.model_dump(mode="json")

    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["project_name"] == "demo-project"
    assert payload["topic"] == "Standing waves"
    assert payload["phase"] == "init"
    assert payload["phase_status"] == "active"
    assert len(payload["history"]) == 1
    assert payload["history"][0]["phase"] == "init"


def test_atomic_save_and_load_round_trip(tmp_path) -> None:
    state_file = tmp_path / "project_state.json"
    state = create_initial_state("demo-project", "Standing waves")

    save_state_atomic(state_file, state)
    loaded = load_state(state_file)

    assert loaded.project_name == "demo-project"
    assert loaded.phase == "init"
    assert loaded.contract_version == CONTRACT_VERSION


def test_valid_transition_updates_phase_and_history() -> None:
    state = create_initial_state("demo-project", "Standing waves")

    next_state = transition_state(state, "plan", actor="orchestrator")

    assert next_state.phase == "plan"
    assert next_state.phase_status == "active"
    assert len(next_state.history) == 2
    assert next_state.history[-1].phase == "plan"


def test_invalid_transition_raises() -> None:
    state = create_initial_state("demo-project", "Standing waves")

    with pytest.raises(PhaseTransitionError):
        transition_state(state, "build_scenes", actor="orchestrator")


def test_legacy_state_payload_is_normalized(tmp_path) -> None:
    state_file = tmp_path / "project_state.json"
    legacy_payload = {
        "project_name": "legacy-project",
        "topic": "Legacy topic",
        "phase": "plan",
        "history": [{"phase": "plan", "timestamp": "2026-03-01T12:00:00Z"}],
    }
    state_file.write_text(json.dumps(legacy_payload), encoding="utf-8")

    loaded = load_state(state_file)

    assert loaded.contract_version == CONTRACT_VERSION
    assert loaded.phase_status == "active"
