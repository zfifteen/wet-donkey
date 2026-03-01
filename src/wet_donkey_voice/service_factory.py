from __future__ import annotations

from typing import Any

from .qwen_cached import QwenCachedTTS


def get_tts_service(service_name: str = "qwen_cached", **kwargs: Any):
    """Factory function to get a deterministic TTS service instance."""
    if service_name == "qwen_cached":
        return QwenCachedTTS(**kwargs)
    raise ValueError(f"Unknown TTS service: {service_name}")
