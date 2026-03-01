from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from harness import cli
from harness.exit_codes import HarnessExitCode


@patch("harness.cli.PipelineTrainingSession.from_project")
def test_cli_rejects_fh_harness_env_toggle(mock_from_project, monkeypatch) -> None:
    monkeypatch.setenv("FH_HARNESS", "legacy")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "harness.cli",
            "--phase",
            "plan",
            "--project-dir",
            "/tmp/demo",
            "--topic",
            "test topic",
            "--dry-run",
        ],
    )

    rc = cli.main()
    assert rc == int(HarnessExitCode.POLICY_VIOLATION)
    mock_from_project.assert_not_called()


@patch("harness.cli.PipelineTrainingSession.from_project")
def test_cli_rejects_use_harness_env_toggle(mock_from_project, monkeypatch) -> None:
    monkeypatch.setenv("USE_HARNESS", "0")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "harness.cli",
            "--phase",
            "plan",
            "--project-dir",
            "/tmp/demo",
            "--topic",
            "test topic",
            "--dry-run",
        ],
    )

    rc = cli.main()
    assert rc == int(HarnessExitCode.POLICY_VIOLATION)
    mock_from_project.assert_not_called()


def test_orchestrator_contains_no_legacy_harness_selector() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts" / "build_video.sh").read_text(encoding="utf-8")

    assert "FH_HARNESS" not in script
    assert "USE_HARNESS" not in script
