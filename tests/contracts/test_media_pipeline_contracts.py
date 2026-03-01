from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from harness.contracts.media_pipeline import (
    AssemblyManifest,
    RenderManifest,
    RenderPreconditions,
    VoiceManifest,
    validate_assembly_inputs,
    validate_render_manifest,
    validate_render_preconditions,
    validate_voice_manifest_files,
    verify_final_output,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _setup_voice_fixture(project_dir: Path) -> None:
    audio_path = project_dir / "voice" / "scene_01.mp3"
    metadata_path = project_dir / "voice" / "scene_01.mp3.json"

    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"VOICE")

    _write_json(
        metadata_path,
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


def test_render_preconditions_require_runtime_gate(tmp_path) -> None:
    _setup_voice_fixture(tmp_path)
    scene_path = tmp_path / "scenes" / "scene_01.py"
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text("# scene", encoding="utf-8")

    valid = RenderPreconditions.model_validate(
        {
            "contract_version": "1.0.0",
            "validated_gates": ["schema", "contract", "semantic", "runtime"],
            "voice_manifest_path": "artifacts/voice_manifest.json",
            "scene_sources": ["scenes/scene_01.py"],
            "tooling_preflight": True,
        }
    )
    voice_manifest = validate_render_preconditions(valid, project_dir=tmp_path)
    assert len(voice_manifest.assets) == 1

    with pytest.raises(ValidationError):
        RenderPreconditions.model_validate(
            {
                "contract_version": "1.0.0",
                "validated_gates": ["schema", "contract", "semantic"],
                "voice_manifest_path": "artifacts/voice_manifest.json",
                "scene_sources": ["scenes/scene_01.py"],
                "tooling_preflight": True,
            }
        )


def test_assembly_verification_accepts_in_tolerance_output(tmp_path) -> None:
    _setup_voice_fixture(tmp_path)

    voice_manifest = VoiceManifest.model_validate(
        json.loads((tmp_path / "artifacts" / "voice_manifest.json").read_text(encoding="utf-8"))
    )
    validate_voice_manifest_files(voice_manifest, project_dir=tmp_path)

    video_path = tmp_path / "render" / "scene_01.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"VIDEO")

    render_manifest = RenderManifest.model_validate(
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
        }
    )
    validate_render_manifest(render_manifest, voice_manifest=voice_manifest, project_dir=tmp_path)

    final_video = tmp_path / "final_video.mp4"
    final_video.write_bytes(b"FINAL")

    assembly_manifest = AssemblyManifest.model_validate(
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
        }
    )

    validate_assembly_inputs(assembly_manifest, render_manifest=render_manifest, project_dir=tmp_path)
    verify_final_output(assembly_manifest, project_dir=tmp_path)


def test_assembly_verification_rejects_duration_outside_tolerance(tmp_path) -> None:
    _setup_voice_fixture(tmp_path)

    render_video = tmp_path / "render" / "scene_01.mp4"
    render_video.parent.mkdir(parents=True, exist_ok=True)
    render_video.write_bytes(b"VIDEO")

    final_video = tmp_path / "final_video.mp4"
    final_video.write_bytes(b"FINAL")

    render_manifest = RenderManifest.model_validate(
        {
            "contract_version": "1.0.0",
            "run_id": "run-002",
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
        }
    )

    assembly_manifest = AssemblyManifest.model_validate(
        {
            "contract_version": "1.0.0",
            "run_id": "run-002",
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
            "actual_duration_seconds": 3.2,
            "duration_tolerance_seconds": 0.5,
            "degraded": False,
        }
    )

    validate_assembly_inputs(assembly_manifest, render_manifest=render_manifest, project_dir=tmp_path)

    with pytest.raises(ValueError, match="outside tolerance"):
        verify_final_output(assembly_manifest, project_dir=tmp_path)
