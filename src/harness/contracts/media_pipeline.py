from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_exit_codes = importlib.import_module("harness.exit_codes")
validate_gate_sequence = _exit_codes.validate_gate_sequence

_voice_contracts = importlib.import_module("wet_donkey_voice.contracts")
VoiceMetadata = _voice_contracts.VoiceMetadata

MEDIA_CONTRACT_VERSION = "1.0.0"
REQUIRED_RENDER_GATES: tuple[str, ...] = ("schema", "contract", "semantic", "runtime")

ValidationGate = Literal["schema", "contract", "semantic", "runtime", "assembly"]
GenerationMode = Literal["cache_hit", "generated", "fallback_generated"]


def _normalize_non_empty(value: str, *, field_name: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _resolve_path(raw_path: str, *, project_dir: Path | None) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or project_dir is None:
        return path
    return project_dir / path


def _require_semver(value: str) -> str:
    if not re.match(r"^\d+\.\d+\.\d+$", value):
        raise ValueError("contract_version must follow semver (x.y.z)")
    return value


def duration_tolerance_seconds(expected_duration_seconds: float) -> float:
    if expected_duration_seconds <= 0:
        raise ValueError("expected_duration_seconds must be > 0")
    return max(0.5, expected_duration_seconds * 0.02)


class VoiceAssetRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    audio_path: str
    metadata_path: str
    cache_key: str
    duration_seconds: float = Field(gt=0)
    generation_mode: GenerationMode
    degraded: bool = False

    @field_validator("scene_id", "audio_path", "metadata_path", "cache_key")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="voice_asset_field")


class VoiceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = MEDIA_CONTRACT_VERSION
    voice_id: str
    fallback_allowed: bool = False
    assets: list[VoiceAssetRef] = Field(min_length=1)

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        return _require_semver(value)

    @field_validator("voice_id")
    @classmethod
    def _validate_voice_id(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="voice_id")

    @model_validator(mode="after")
    def _validate_scene_uniqueness_and_fallback(self) -> "VoiceManifest":
        scene_ids = [asset.scene_id for asset in self.assets]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("voice manifest scene_id values must be unique")
        if not self.fallback_allowed:
            degraded_assets = [asset.scene_id for asset in self.assets if asset.degraded]
            if degraded_assets:
                raise ValueError(
                    "degraded/fallback voice assets are not allowed when fallback_allowed is false"
                )
        return self


class RenderPreconditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = MEDIA_CONTRACT_VERSION
    validated_gates: list[ValidationGate] = Field(min_length=4)
    voice_manifest_path: str
    scene_sources: list[str] = Field(min_length=1)
    tooling_preflight: bool = True

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        return _require_semver(value)

    @field_validator("voice_manifest_path")
    @classmethod
    def _validate_voice_manifest_path(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="voice_manifest_path")

    @field_validator("scene_sources")
    @classmethod
    def _validate_scene_sources(cls, value: list[str]) -> list[str]:
        return [_normalize_non_empty(path, field_name="scene_sources[]") for path in value]

    @model_validator(mode="after")
    def _validate_gates(self) -> "RenderPreconditions":
        gate_sequence = list(self.validated_gates)
        if not validate_gate_sequence(gate_sequence):
            raise ValueError("validated_gates must follow canonical gate ordering")
        missing = [gate for gate in REQUIRED_RENDER_GATES if gate not in gate_sequence]
        if missing:
            raise ValueError(f"missing required render gates: {', '.join(missing)}")
        return self


class RenderSceneAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    video_path: str
    audio_path: str
    video_duration_seconds: float = Field(gt=0)
    audio_duration_seconds: float = Field(gt=0)

    @field_validator("scene_id", "video_path", "audio_path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="render_scene_asset_field")


class RenderManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = MEDIA_CONTRACT_VERSION
    run_id: str
    scene_order: list[str] = Field(min_length=1)
    scenes: list[RenderSceneAsset] = Field(min_length=1)

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        return _require_semver(value)

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="run_id")

    @field_validator("scene_order")
    @classmethod
    def _validate_scene_order(cls, value: list[str]) -> list[str]:
        return [_normalize_non_empty(scene_id, field_name="scene_order[]") for scene_id in value]

    @model_validator(mode="after")
    def _validate_scene_alignment(self) -> "RenderManifest":
        scene_ids = [scene.scene_id for scene in self.scenes]
        if scene_ids != self.scene_order:
            raise ValueError("render manifest scenes must match scene_order exactly")
        return self


class AssemblyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    video_path: str
    audio_path: str
    duration_seconds: float = Field(gt=0)

    @field_validator("scene_id", "video_path", "audio_path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="assembly_input_field")


class AssemblyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = MEDIA_CONTRACT_VERSION
    run_id: str
    output_path: str
    scene_order: list[str] = Field(min_length=1)
    inputs: list[AssemblyInput] = Field(min_length=1)
    expected_duration_seconds: float = Field(gt=0)
    actual_duration_seconds: float = Field(gt=0)
    duration_tolerance_seconds: float = Field(gt=0)
    degraded: bool = False

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        return _require_semver(value)

    @field_validator("run_id", "output_path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="assembly_manifest_field")

    @field_validator("scene_order")
    @classmethod
    def _validate_scene_order(cls, value: list[str]) -> list[str]:
        return [_normalize_non_empty(scene_id, field_name="scene_order[]") for scene_id in value]

    @model_validator(mode="after")
    def _validate_scene_alignment(self) -> "AssemblyManifest":
        input_scene_ids = [scene.scene_id for scene in self.inputs]
        if input_scene_ids != self.scene_order:
            raise ValueError("assembly manifest inputs must match scene_order exactly")

        default_tolerance = duration_tolerance_seconds(self.expected_duration_seconds)
        if self.duration_tolerance_seconds > default_tolerance:
            raise ValueError(
                "duration_tolerance_seconds cannot exceed default policy max(0.5s, 2% of expected duration)"
            )
        return self


def load_manifest_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_voice_manifest(path: Path) -> VoiceManifest:
    return VoiceManifest.model_validate(load_manifest_file(path))


def load_render_preconditions(path: Path) -> RenderPreconditions:
    return RenderPreconditions.model_validate(load_manifest_file(path))


def load_render_manifest(path: Path) -> RenderManifest:
    return RenderManifest.model_validate(load_manifest_file(path))


def load_assembly_manifest(path: Path) -> AssemblyManifest:
    return AssemblyManifest.model_validate(load_manifest_file(path))


def validate_voice_manifest_files(
    manifest: VoiceManifest,
    *,
    project_dir: Path | None = None,
) -> None:
    for asset in manifest.assets:
        audio_path = _resolve_path(asset.audio_path, project_dir=project_dir)
        metadata_path = _resolve_path(asset.metadata_path, project_dir=project_dir)

        if not audio_path.exists():
            raise ValueError(f"voice audio file missing for scene '{asset.scene_id}': {audio_path}")
        if not metadata_path.exists():
            raise ValueError(f"voice metadata file missing for scene '{asset.scene_id}': {metadata_path}")

        metadata_payload = load_manifest_file(metadata_path)
        metadata = VoiceMetadata.model_validate(metadata_payload)
        if metadata.cache_key != asset.cache_key:
            raise ValueError(
                f"voice cache_key mismatch for scene '{asset.scene_id}': manifest={asset.cache_key} metadata={metadata.cache_key}"
            )
        if abs(metadata.duration_seconds - asset.duration_seconds) > 1e-6:
            raise ValueError(
                f"voice duration mismatch for scene '{asset.scene_id}': manifest={asset.duration_seconds} metadata={metadata.duration_seconds}"
            )


def validate_render_preconditions(
    preconditions: RenderPreconditions,
    *,
    project_dir: Path,
) -> VoiceManifest:
    if not preconditions.tooling_preflight:
        raise ValueError("render tooling preflight must pass before rendering")

    voice_manifest_path = _resolve_path(preconditions.voice_manifest_path, project_dir=project_dir)
    if not voice_manifest_path.exists():
        raise ValueError(f"voice manifest missing: {voice_manifest_path}")
    voice_manifest = load_voice_manifest(voice_manifest_path)
    validate_voice_manifest_files(voice_manifest, project_dir=project_dir)

    for scene_source in preconditions.scene_sources:
        scene_path = _resolve_path(scene_source, project_dir=project_dir)
        if not scene_path.exists():
            raise ValueError(f"scene source file missing: {scene_path}")

    return voice_manifest


def validate_render_manifest(
    render_manifest: RenderManifest,
    *,
    voice_manifest: VoiceManifest,
    project_dir: Path,
) -> None:
    voice_by_scene = {asset.scene_id: asset for asset in voice_manifest.assets}

    if list(voice_by_scene.keys()) != render_manifest.scene_order:
        raise ValueError("voice manifest scene order must match render manifest scene order")

    for scene in render_manifest.scenes:
        video_path = _resolve_path(scene.video_path, project_dir=project_dir)
        audio_path = _resolve_path(scene.audio_path, project_dir=project_dir)

        if not video_path.exists():
            raise ValueError(f"rendered video missing for scene '{scene.scene_id}': {video_path}")
        if not audio_path.exists():
            raise ValueError(f"render audio missing for scene '{scene.scene_id}': {audio_path}")

        voice_asset = voice_by_scene.get(scene.scene_id)
        if voice_asset is None:
            raise ValueError(f"scene '{scene.scene_id}' not found in voice manifest")

        voice_audio_path = _resolve_path(voice_asset.audio_path, project_dir=project_dir)
        if audio_path.resolve() != voice_audio_path.resolve():
            raise ValueError(f"render manifest audio path mismatch for scene '{scene.scene_id}'")

        if abs(scene.audio_duration_seconds - voice_asset.duration_seconds) > 1e-6:
            raise ValueError(f"render audio duration mismatch for scene '{scene.scene_id}'")


def validate_assembly_inputs(
    assembly_manifest: AssemblyManifest,
    *,
    render_manifest: RenderManifest,
    project_dir: Path,
) -> None:
    render_scene_ids = [scene.scene_id for scene in render_manifest.scenes]
    if assembly_manifest.scene_order != render_scene_ids:
        raise ValueError("assembly scene order must match render scene order")

    render_by_scene = {scene.scene_id: scene for scene in render_manifest.scenes}
    for assembly_input in assembly_manifest.inputs:
        source = render_by_scene.get(assembly_input.scene_id)
        if source is None:
            raise ValueError(f"assembly scene '{assembly_input.scene_id}' missing from render manifest")

        input_video_path = _resolve_path(assembly_input.video_path, project_dir=project_dir)
        input_audio_path = _resolve_path(assembly_input.audio_path, project_dir=project_dir)

        if not input_video_path.exists():
            raise ValueError(f"assembly video input missing for scene '{assembly_input.scene_id}': {input_video_path}")
        if not input_audio_path.exists():
            raise ValueError(f"assembly audio input missing for scene '{assembly_input.scene_id}': {input_audio_path}")

        source_video_path = _resolve_path(source.video_path, project_dir=project_dir)
        source_audio_path = _resolve_path(source.audio_path, project_dir=project_dir)
        if input_video_path.resolve() != source_video_path.resolve():
            raise ValueError(f"assembly video input mismatch for scene '{assembly_input.scene_id}'")
        if input_audio_path.resolve() != source_audio_path.resolve():
            raise ValueError(f"assembly audio input mismatch for scene '{assembly_input.scene_id}'")

        if abs(assembly_input.duration_seconds - source.video_duration_seconds) > 1e-6:
            raise ValueError(f"assembly duration mismatch for scene '{assembly_input.scene_id}'")


def verify_final_output(
    assembly_manifest: AssemblyManifest,
    *,
    project_dir: Path,
) -> None:
    output_path = _resolve_path(assembly_manifest.output_path, project_dir=project_dir)
    if not output_path.exists():
        raise ValueError(f"final output file missing: {output_path}")

    duration_delta = abs(assembly_manifest.actual_duration_seconds - assembly_manifest.expected_duration_seconds)
    if duration_delta > assembly_manifest.duration_tolerance_seconds:
        raise ValueError(
            "final output duration is outside tolerance "
            f"(delta={duration_delta:.3f}s, tolerance={assembly_manifest.duration_tolerance_seconds:.3f}s)"
        )
