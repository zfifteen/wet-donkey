from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from harness.contracts.scaffold import inject_scene_body_file


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "runtime_phase_contracts.py"


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
                "description": f"Description for scene {scene_number:02d}",
                "estimated_duration_seconds": 30,
                "visual_ideas": ["axes", "labels"],
            }
        )

    return {
        "title": "Runtime Contract Fixture",
        "description": "Fixture plan",
        "target_duration_seconds": 600,
        "scenes": scenes,
    }


def _build_narration_payload(scene_count: int = 12) -> dict:
    scenes = []
    for index in range(scene_count):
        scene_number = index + 1
        scenes.append(
            {
                "scene_title": f"Scene {scene_number:02d}",
                "narration_text": f"Narration text for scene {scene_number:02d}.",
            }
        )
    return {"scenes": scenes}


def _write_project_state(project_dir: Path, scene_count: int = 12) -> None:
    state = {
        "contract_version": "1.0.0",
        "project_name": "runtime-contracts",
        "topic": "Runtime phase contracts",
        "phase": "narration",
        "phase_status": "active",
        "history": [{"phase": "narration", "timestamp": "2026-03-01T00:00:00Z"}],
        "plan": _build_plan_payload(scene_count=scene_count),
        "narration": _build_narration_payload(scene_count=scene_count),
    }
    _write_json(project_dir / "project_state.json", state)


def _run_script(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_script_path()), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_runtime_phase_contract_flow(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    _write_project_state(project_dir)

    prepare = _run_script("prepare-scene-manifest", "--project-dir", str(project_dir))
    assert prepare.returncode == 0

    manifest_path = project_dir / "artifacts" / "scene_manifest.json"
    assert manifest_path.exists()
    assert (project_dir / "narration_script.py").exists()

    scaffold = _run_script("scaffold-scenes", "--project-dir", str(project_dir))
    assert scaffold.returncode == 0

    validate_build_initial = _run_script("validate-build-scenes", "--project-dir", str(project_dir))
    assert validate_build_initial.returncode == 2

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for scene in manifest_payload["scenes"]:
        scene_path = project_dir / scene["scene_file"]
        inject_scene_body_file(scene_path, "self.wait(0.1)")

    validate_build = _run_script("validate-build-scenes", "--project-dir", str(project_dir))
    assert validate_build.returncode == 0

    validate_qc_initial = _run_script("validate-scene-qc", "--project-dir", str(project_dir))
    assert validate_qc_initial.returncode == 2

    for scene in manifest_payload["scenes"]:
        scene_stem = Path(scene["scene_file"]).stem
        qc_path = project_dir / "qc" / f"{scene_stem}_qc.json"
        _write_json(
            qc_path,
            {
                "contract_version": "1.0.0",
                "scene_id": scene["scene_id"],
                "scene_file": scene["scene_file"],
                "scene_title": scene["scene_title"],
                "passed": True,
                "score": 0.95,
                "issues": [],
            },
        )

    validate_qc = _run_script("validate-scene-qc", "--project-dir", str(project_dir))
    assert validate_qc.returncode == 0
