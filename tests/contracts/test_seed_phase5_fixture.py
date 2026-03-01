from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

_media_pipeline = importlib.import_module("harness.contracts.media_pipeline")
load_assembly_manifest = _media_pipeline.load_assembly_manifest
load_render_manifest = _media_pipeline.load_render_manifest
load_render_preconditions = _media_pipeline.load_render_preconditions
load_voice_manifest = _media_pipeline.load_voice_manifest
validate_assembly_inputs = _media_pipeline.validate_assembly_inputs
validate_render_manifest = _media_pipeline.validate_render_manifest
validate_render_preconditions = _media_pipeline.validate_render_preconditions
validate_voice_manifest_files = _media_pipeline.validate_voice_manifest_files
verify_final_output = _media_pipeline.verify_final_output

_runtime_pipeline = importlib.import_module("harness.contracts.runtime_pipeline")
load_scene_manifest = _runtime_pipeline.load_scene_manifest
validate_built_scene_files = _runtime_pipeline.validate_built_scene_files
validate_scene_qc_reports = _runtime_pipeline.validate_scene_qc_reports

load_state = importlib.import_module("harness.contracts.state").load_state


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "seed_phase5_fixture.py"


def test_seed_phase5_fixture_produces_valid_contract_artifacts(tmp_path) -> None:
    project_dir = tmp_path / "fixture_project"

    result = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--project-dir",
            str(project_dir),
            "--scene-count",
            "12",
            "--phase",
            "scene_qc",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    state = load_state(project_dir / "project_state.json")
    assert state.phase == "scene_qc"

    manifest = load_scene_manifest(project_dir / "artifacts" / "scene_manifest.json")
    assert len(manifest.scenes) == 12

    build_errors = validate_built_scene_files(project_dir, manifest)
    assert build_errors == []

    qc_errors = validate_scene_qc_reports(project_dir, manifest)
    assert qc_errors == []

    voice_manifest = load_voice_manifest(project_dir / "artifacts" / "voice_manifest.json")
    validate_voice_manifest_files(voice_manifest, project_dir=project_dir)

    render_preconditions = load_render_preconditions(project_dir / "artifacts" / "render_preconditions.json")
    validated_voice_manifest = validate_render_preconditions(render_preconditions, project_dir=project_dir)

    render_manifest = load_render_manifest(project_dir / "artifacts" / "render_manifest.json")
    validate_render_manifest(render_manifest, voice_manifest=validated_voice_manifest, project_dir=project_dir)

    assembly_manifest = load_assembly_manifest(project_dir / "artifacts" / "assembly_manifest.json")
    validate_assembly_inputs(assembly_manifest, render_manifest=render_manifest, project_dir=project_dir)
    verify_final_output(assembly_manifest, project_dir=project_dir)
