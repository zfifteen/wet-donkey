from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping

from .contracts import (
    VoiceMetadata,
    VoiceSynthesisResult,
    build_voice_cache_key,
    metadata_sidecar_path,
    normalize_narration_text,
    text_digest,
    validate_voice_result,
    write_metadata_sidecar,
)


class QwenCachedTTS:
    """Deterministic cached TTS adapter with explicit metadata contracts."""

    def __init__(
        self,
        cache_dir: str = "projects/voice_cache",
        *,
        voice_id: str = "qwen-default",
        synthesis_settings: Mapping[str, Any] | None = None,
        fallback_enabled: bool = False,
        audio_format: str = "mp3",
        sample_rate_hz: int = 24000,
        channels: int = 1,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.voice_id = voice_id
        self.synthesis_settings = dict(synthesis_settings or {})
        self.fallback_enabled = fallback_enabled
        self.audio_format = audio_format.lower().lstrip(".")
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels

    def synthesize(self, text: str, *, degraded: bool = False) -> VoiceSynthesisResult:
        normalized_text = normalize_narration_text(text)
        cache_key = build_voice_cache_key(
            text=normalized_text,
            voice_id=self.voice_id,
            synthesis_settings=self.synthesis_settings,
        )
        audio_path = self.cache_dir / f"{cache_key}.{self.audio_format}"

        generation_mode: Literal["cache_hit", "generated", "fallback_generated"]
        if audio_path.exists() and not degraded:
            generation_mode = "cache_hit"
        else:
            generation_mode = "fallback_generated" if degraded else "generated"
            self._write_mock_audio(audio_path)

        metadata = VoiceMetadata(
            voice_id=self.voice_id,
            cache_key=cache_key,
            generation_mode=generation_mode,
            degraded=degraded,
            duration_seconds=self._estimate_duration_seconds(normalized_text),
            audio_format=self.audio_format,
            sample_rate_hz=self.sample_rate_hz,
            channels=self.channels,
            text_sha256=text_digest(normalized_text),
        )

        result = VoiceSynthesisResult(
            audio_path=str(audio_path),
            metadata_path=str(metadata_sidecar_path(audio_path)),
            metadata=metadata,
        )
        write_metadata_sidecar(result)
        return validate_voice_result(result, fallback_enabled=self.fallback_enabled)

    def generate_audio(self, text: str) -> tuple[str, float]:
        """Backwards-compatible tuple return used by older call sites."""
        result = self.synthesize(text)
        return result.audio_path, result.metadata.duration_seconds

    @staticmethod
    def _estimate_duration_seconds(text: str) -> float:
        word_count = len(text.split())
        return max(0.2, word_count * 0.4)

    @staticmethod
    def _write_mock_audio(audio_path: Path) -> None:
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"MOCKAUDIO")
