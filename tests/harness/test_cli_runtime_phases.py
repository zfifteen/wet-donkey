from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from harness import cli
from harness.schemas.narration import Narration, NarrationScene
from harness.schemas.scene_qc import SceneQC


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_plan_payload(scene_count: int = 12) -> dict:
    scenes = []
    for index in range(scene_count):
        scene_number = index + 1
        scenes.append(
            {
                "title": f"Scene {scene_number:02d}",
                "description": f"Description {scene_number:02d}",
                "estimated_duration_seconds": 30,
                "visual_ideas": ["idea-a", "idea-b"],
            }
        )

    return {
        "title": "CLI Runtime Fixture",
        "description": "fixture",
        "target_duration_seconds": 600,
        "scenes": scenes,
    }


@patch("harness.cli.PipelineTrainingSession.from_project")
@patch("harness.cli.generate_narration")
def test_cli_narration_phase_writes_state(mock_generate_narration, mock_from_project, monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    _write_json(
        project_dir / "project_state.json",
        {
            "contract_version": "1.0.0",
            "project_name": "cli-runtime",
            "topic": "topic",
            "phase": "narration",
            "history": [{"phase": "narration", "timestamp": "2026-03-01T00:00:00Z"}],
            "plan": _build_plan_payload(),
        },
    )

    mock_from_project.return_value = MagicMock()
    mock_generate_narration.return_value = Narration(
        scenes=[NarrationScene(scene_title="Scene 01", narration_text="Narration")]
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "harness.cli",
            "--phase",
            "narration",
            "--project-dir",
            str(project_dir),
        ],
    )

    rc = cli.main()
    assert rc == 0

    payload = json.loads((project_dir / "project_state.json").read_text(encoding="utf-8"))
    assert payload["narration"]["scenes"][0]["scene_title"] == "Scene 01"


@patch("harness.cli.PipelineTrainingSession.from_project")
@patch("harness.cli.run_scene_qc")
def test_cli_scene_qc_phase_writes_report(mock_run_scene_qc, mock_from_project, monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    scene_rel = "scenes/scene_01_intro.py"
    scene_path = project_dir / scene_rel
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text("from manim import *\n", encoding="utf-8")

    _write_json(
        project_dir / "artifacts" / "scene_manifest.json",
        {
            "contract_version": "1.0.0",
            "generated_at": "2026-03-01T00:00:00Z",
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "scene_index": 1,
                    "scene_title": "Scene 01",
                    "scene_description": "desc",
                    "scene_file": scene_rel,
                    "narration_text": "Narration",
                    "narration_duration_seconds": 1.2,
                    "visual_ideas": ["idea"],
                }
            ],
        },
    )

    mock_from_project.return_value = MagicMock()
    mock_run_scene_qc.return_value = SceneQC(
        scene_title="Scene 01",
        passed=True,
        score=0.9,
        issues=[],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "harness.cli",
            "--phase",
            "scene_qc",
            "--project-dir",
            str(project_dir),
            "--scene-id",
            "scene_01",
            "--scene-file",
            str(scene_path),
        ],
    )

    rc = cli.main()
    assert rc == 0

    qc_path = project_dir / "qc" / "scene_01_intro_qc.json"
    assert qc_path.exists()
    qc_payload = json.loads(qc_path.read_text(encoding="utf-8"))
    assert qc_payload["scene_id"] == "scene_01"
    assert qc_payload["passed"] is True
