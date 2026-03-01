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
