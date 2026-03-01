from __future__ import annotations

from pathlib import Path

import pytest

from wet_donkey_voice.contracts import build_voice_cache_key
from wet_donkey_voice.qwen_cached import QwenCachedTTS


def test_voice_cache_key_is_deterministic_after_text_normalization() -> None:
    key_one = build_voice_cache_key(
        text="Standing   waves   are cool",
        voice_id="qwen-default",
        synthesis_settings={"speed": 1.0, "pitch": 0.0},
    )
    key_two = build_voice_cache_key(
        text="Standing waves are cool",
        voice_id="qwen-default",
        synthesis_settings={"pitch": 0.0, "speed": 1.0},
    )

    assert key_one == key_two


def test_qwen_cached_service_writes_metadata_and_returns_cache_hit(tmp_path) -> None:
    cache_dir = tmp_path / "voice_cache"
    service = QwenCachedTTS(cache_dir=str(cache_dir), voice_id="qwen-default")

    first = service.synthesize("A deterministic narration line")
    second = service.synthesize("A   deterministic narration   line")

    assert first.metadata.generation_mode == "generated"
    assert second.metadata.generation_mode == "cache_hit"
    assert first.metadata.cache_key == second.metadata.cache_key

    assert Path(first.audio_path).exists()
    assert Path(first.metadata_path).exists()


def test_degraded_voice_generation_requires_explicit_fallback_enablement(tmp_path) -> None:
    strict_service = QwenCachedTTS(cache_dir=str(tmp_path / "strict"), fallback_enabled=False)

    with pytest.raises(ValueError, match="fallback/degraded generation is disabled"):
        strict_service.synthesize("Fallback should fail", degraded=True)

    allowed_service = QwenCachedTTS(cache_dir=str(tmp_path / "allowed"), fallback_enabled=True)
    degraded = allowed_service.synthesize("Fallback can proceed", degraded=True)

    assert degraded.metadata.generation_mode == "fallback_generated"
    assert degraded.metadata.degraded is True
