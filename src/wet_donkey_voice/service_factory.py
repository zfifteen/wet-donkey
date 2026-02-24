# wet_donkey_voice/service_factory.py
from .qwen_cached import QwenCachedTTS

def get_tts_service(service_name: str = "qwen_cached"):
    """
    Factory function to get a TTS service instance.
    """
    if service_name == "qwen_cached":
        return QwenCachedTTS()
    # In the future, other services could be added here.
    # elif service_name == "another_tts":
    #     return AnotherTTS()
    else:
        raise ValueError(f"Unknown TTS service: {service_name}")
