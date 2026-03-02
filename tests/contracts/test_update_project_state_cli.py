from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "update_project_state.py"


def _write_state(state_file: Path) -> None:
    payload = {
        "project_name": "cli-test",
        "topic": "CLI state contract test",
        "phase": "init",
        "history": [{"phase": "init", "timestamp": "2026-03-01T00:00:00Z"}],
    }
    state_file.write_text(json.dumps(payload), encoding="utf-8")


def test_cli_phase_transition_validation_and_blocking(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    state_file = project_dir / "project_state.json"
    _write_state(state_file)

    script = _script_path()

    # Valid transition init -> plan
    ok = subprocess.run(
        [
            sys.executable,
            str(script),
            "set",
            "--project-dir",
            str(project_dir),
            "--key",
            "phase",
            "--value",
            "plan",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0

    start_event = subprocess.run(
        [
            sys.executable,
            str(script),
            "log-event",
            "--project-dir",
            str(project_dir),
            "--event-type",
            "phase_start",
            "--phase",
            "plan",
            "--attempt",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert start_event.returncode == 0

    success_event = subprocess.run(
        [
            sys.executable,
            str(script),
            "log-event",
            "--project-dir",
            str(project_dir),
            "--event-type",
            "phase_success",
            "--phase",
            "plan",
            "--attempt",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert success_event.returncode == 0

    # Invalid transition plan -> build_scenes
    bad = subprocess.run(
        [
            sys.executable,
            str(script),
            "set",
            "--project-dir",
            str(project_dir),
            "--key",
            "phase",
            "--value",
            "build_scenes",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 2

    # Plan phase default max attempts is 2; two failures should block.
    fail1 = subprocess.run(
        [
            sys.executable,
            str(script),
            "fail",
            "--project-dir",
            str(project_dir),
            "--error-code",
            "INFRASTRUCTURE_ERROR",
            "--error-message",
            "attempt-1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail1.returncode == 0

    fail2 = subprocess.run(
        [
            sys.executable,
            str(script),
            "fail",
            "--project-dir",
            str(project_dir),
            "--error-code",
            "INFRASTRUCTURE_ERROR",
            "--error-message",
            "attempt-2",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail2.returncode == 0

    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["phase_status"] == "blocked"

    events_path = project_dir / "log" / "events.jsonl"
    assert events_path.exists()
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    event_types = [event["event_type"] for event in events]
    assert "phase_failure" in event_types
    assert "phase_blocked" in event_types

    trace_bundle_dir = project_dir / "log" / "trace-bundles"
    trace_bundles = list(trace_bundle_dir.glob("blocked-*.json"))
    assert trace_bundles

    clear = subprocess.run(
        [
            sys.executable,
            str(script),
            "clear-failures",
            "--project-dir",
            str(project_dir),
            "--reason",
            "manual_resume",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert clear.returncode == 0

    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["phase_status"] == "active"
    assert payload["failure_context"] == {}

    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(event["event_type"] == "phase_unblocked" for event in events)


def test_cli_logs_phase_transition_event_for_review_to_narration(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    state_file = project_dir / "project_state.json"
    payload = {
        "project_name": "cli-transition-test",
        "topic": "Transition observability test",
        "phase": "review",
        "history": [{"phase": "review", "timestamp": "2026-03-01T00:00:00Z"}],
    }
    state_file.write_text(json.dumps(payload), encoding="utf-8")

    script = _script_path()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "set",
            "--project-dir",
            str(project_dir),
            "--key",
            "phase",
            "--value",
            "narration",
            "--actor",
            "manual-review",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0

    events_path = project_dir / "log" / "events.jsonl"
    assert events_path.exists()
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    transition_events = [
        event
        for event in events
        if event.get("event_type") == "phase_transition"
        and event.get("phase") == "review"
        and (event.get("metadata") or {}).get("to_phase") == "narration"
    ]
    assert transition_events


def test_cli_logs_build_scenes_and_scene_qc_observability_events(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    state_file = project_dir / "project_state.json"
    payload = {
        "project_name": "cli-observability-test",
        "topic": "Build scenes and scene_qc observability",
        "phase": "build_scenes",
        "history": [{"phase": "build_scenes", "timestamp": "2026-03-01T00:00:00Z"}],
    }
    state_file.write_text(json.dumps(payload), encoding="utf-8")

    script = _script_path()
    for phase in ("build_scenes", "scene_qc"):
        for event_type in ("phase_start", "phase_success"):
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "log-event",
                    "--project-dir",
                    str(project_dir),
                    "--event-type",
                    event_type,
                    "--phase",
                    phase,
                    "--attempt",
                    "1",
                    "--actor",
                    "orchestrator",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0

    events_path = project_dir / "log" / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for phase in ("build_scenes", "scene_qc"):
        for event_type in ("phase_start", "phase_success"):
            assert any(
                event.get("phase") == phase and event.get("event_type") == event_type
                for event in events
            )
