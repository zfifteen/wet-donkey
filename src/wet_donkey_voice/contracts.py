from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

VOICE_CONTRACT_VERSION = "1.0.0"
SUPPORTED_AUDIO_FORMATS = {"mp3", "wav", "m4a", "aac", "ogg", "flac"}

GenerationMode = Literal["cache_hit", "generated", "fallback_generated"]


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_narration_text(text: str) -> str:
    normalized = _normalize_whitespace(text)
    if not normalized:
        raise ValueError("narration text must be non-empty")
    return normalized


def _stable_json(mapping: Mapping[str, Any]) -> str:
    return json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_voice_cache_key(
    *,
    text: str,
    voice_id: str,
    synthesis_settings: Mapping[str, Any] | None = None,
) -> str:
    normalized_voice_id = _normalize_whitespace(voice_id)
    if not normalized_voice_id:
        raise ValueError("voice_id must be non-empty")

    normalized_text = normalize_narration_text(text)
    settings_payload = synthesis_settings or {}

    raw_key = "|".join([
        normalized_voice_id,
        _stable_json(settings_payload),
        normalized_text,
    ])
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(normalize_narration_text(text).encode("utf-8")).hexdigest()


class VoiceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = VOICE_CONTRACT_VERSION
    voice_id: str
    cache_key: str
    generation_mode: GenerationMode
    degraded: bool = False
    duration_seconds: float = Field(gt=0)
    audio_format: str
    sample_rate_hz: int = Field(gt=0)
    channels: int = Field(gt=0)
    text_sha256: str

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise ValueError("contract_version must follow semver (x.y.z)")
        return value

    @field_validator("voice_id", "cache_key", "text_sha256")
    @classmethod
    def _require_non_empty_strings(cls, value: str) -> str:
        normalized = _normalize_whitespace(value)
        if not normalized:
            raise ValueError("value must be non-empty")
        return normalized

    @field_validator("audio_format")
    @classmethod
    def _validate_audio_format(cls, value: str) -> str:
        normalized = value.lower().lstrip(".")
        if normalized not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(f"unsupported audio format: {value}")
        return normalized


class VoiceSynthesisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_path: str
    metadata_path: str
    metadata: VoiceMetadata

    @field_validator("audio_path", "metadata_path")
    @classmethod
    def _require_path_strings(cls, value: str) -> str:
        if not _normalize_whitespace(value):
            raise ValueError("path must be non-empty")
        return value


def metadata_sidecar_path(audio_path: str | Path) -> Path:
    path = Path(audio_path)
    return path.with_suffix(f"{path.suffix}.json")


def write_metadata_sidecar(result: VoiceSynthesisResult) -> Path:
    sidecar = Path(result.metadata_path)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(result.metadata.model_dump(mode="json"), indent=2), encoding="utf-8")
    return sidecar


def validate_voice_result(
    result: VoiceSynthesisResult,
    *,
    fallback_enabled: bool,
) -> VoiceSynthesisResult:
    audio_path = Path(result.audio_path)
    metadata_path = Path(result.metadata_path)

    if not audio_path.exists():
        raise ValueError(f"audio file missing: {audio_path}")

    suffix = audio_path.suffix.lower().lstrip(".")
    if suffix != result.metadata.audio_format:
        raise ValueError(
            f"audio format mismatch: suffix '{suffix}' does not match metadata '{result.metadata.audio_format}'"
        )

    if result.metadata.duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    if result.metadata.degraded or result.metadata.generation_mode == "fallback_generated":
        if not fallback_enabled:
            raise ValueError("fallback/degraded generation is disabled by policy")

    if metadata_path.exists():
        metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        persisted = VoiceMetadata.model_validate(metadata_payload)
        if persisted.cache_key != result.metadata.cache_key:
            raise ValueError("metadata sidecar cache_key mismatch")

    return result
