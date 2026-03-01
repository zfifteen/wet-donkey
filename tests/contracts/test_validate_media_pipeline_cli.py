from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "validate_media_pipeline.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _prepare_media_contract_fixture(project_dir: Path) -> None:
    (project_dir / "scenes").mkdir(parents=True, exist_ok=True)
    (project_dir / "scenes" / "scene_01.py").write_text("# scene", encoding="utf-8")

    (project_dir / "voice").mkdir(parents=True, exist_ok=True)
    (project_dir / "voice" / "scene_01.mp3").write_bytes(b"VOICE")
    _write_json(
        project_dir / "voice" / "scene_01.mp3.json",
        {
            "contract_version": "1.0.0",
            "voice_id": "qwen-default",
            "cache_key": "cache-key-01",
            "generation_mode": "generated",
            "degraded": False,
            "duration_seconds": 2.4,
            "audio_format": "mp3",
            "sample_rate_hz": 24000,
            "channels": 1,
            "text_sha256": "abc123",
        },
    )

    _write_json(
        project_dir / "artifacts" / "voice_manifest.json",
        {
            "contract_version": "1.0.0",
            "voice_id": "qwen-default",
            "fallback_allowed": False,
            "assets": [
                {
                    "scene_id": "scene_01",
                    "audio_path": "voice/scene_01.mp3",
                    "metadata_path": "voice/scene_01.mp3.json",
                    "cache_key": "cache-key-01",
                    "duration_seconds": 2.4,
                    "generation_mode": "generated",
                    "degraded": False,
                }
            ],
        },
    )

    _write_json(
        project_dir / "artifacts" / "render_preconditions.json",
        {
            "contract_version": "1.0.0",
            "validated_gates": ["schema", "contract", "semantic", "runtime"],
            "voice_manifest_path": "artifacts/voice_manifest.json",
            "scene_sources": ["scenes/scene_01.py"],
            "tooling_preflight": True,
        },
    )

    (project_dir / "render").mkdir(parents=True, exist_ok=True)
    (project_dir / "render" / "scene_01.mp4").write_bytes(b"VIDEO")

    _write_json(
        project_dir / "artifacts" / "render_manifest.json",
        {
            "contract_version": "1.0.0",
            "run_id": "run-001",
            "scene_order": ["scene_01"],
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "video_path": "render/scene_01.mp4",
                    "audio_path": "voice/scene_01.mp3",
                    "video_duration_seconds": 2.4,
                    "audio_duration_seconds": 2.4,
                }
            ],
        },
    )

    (project_dir / "final_video.mp4").write_bytes(b"FINAL")
    _write_json(
        project_dir / "artifacts" / "assembly_manifest.json",
        {
            "contract_version": "1.0.0",
            "run_id": "run-001",
            "output_path": "final_video.mp4",
            "scene_order": ["scene_01"],
            "inputs": [
                {
                    "scene_id": "scene_01",
                    "video_path": "render/scene_01.mp4",
                    "audio_path": "voice/scene_01.mp3",
                    "duration_seconds": 2.4,
                }
            ],
            "expected_duration_seconds": 2.4,
            "actual_duration_seconds": 2.45,
            "duration_tolerance_seconds": 0.5,
            "degraded": False,
        },
    )


def test_media_pipeline_cli_happy_path(tmp_path) -> None:
    _prepare_media_contract_fixture(tmp_path)
    script = _script_path()

    voice = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate-voice-manifest",
            "--project-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert voice.returncode == 0

    render = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate-render-preconditions",
            "--project-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert render.returncode == 0

    assembly = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate-assembly",
            "--project-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert assembly.returncode == 0


def test_media_pipeline_cli_reports_schema_errors(tmp_path) -> None:
    _prepare_media_contract_fixture(tmp_path)
    script = _script_path()

    # Break schema by removing required field from render preconditions.
    _write_json(
        tmp_path / "artifacts" / "render_preconditions.json",
        {
            "contract_version": "1.0.0",
            "validated_gates": ["schema", "contract", "semantic", "runtime"],
            "voice_manifest_path": "artifacts/voice_manifest.json",
            "tooling_preflight": True,
        },
    )

    render = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate-render-preconditions",
            "--project-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert render.returncode == 3
