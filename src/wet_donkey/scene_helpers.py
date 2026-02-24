# wet_donkey/scene_helpers.py
from manim import *

# This file will contain helper functions for Manim scenes, 
# as referenced in the prompt architecture.

def harmonious_color():
    """ 
    Returns a color from a predefined harmonious palette.
    This is a placeholder. A real implementation would have a more
    sophisticated palette system.
    """
    colors = [BLUE, TEAL, GREEN, YELLOW, GOLD, RED, MAROON, PURPLE]
    return random.choice(colors)

def clamp_text_width(text_mobject: Text, max_width: float):
    """
    Scales a Text mobject down if its width exceeds the max_width.
    """
    if text_mobject.width > max_width:
        text_mobject.scale_to_fit_width(max_width)
    return text_mobject

def safe_layout(mobjects: list, buffer: float = 0.5):
    """
    Arranges mobjects to prevent overlaps.
    This is a placeholder for a more complex layout algorithm.
    For now, it just arranges them in a line.
    """
    for i, mobj in enumerate(mobjects):
        if i > 0:
            mobj.next_to(mobjects[i-1], DOWN, buff=buffer)
    return VGroup(*mobjects)

# The spec also implies the existence of a custom voiceover context manager.
# It would likely be part of a custom Scene class, but we can define
# a placeholder here to be imported.
from contextlib import contextmanager

@contextmanager
def voiceover(scene: Scene, text: str):
    """
    A context manager to handle voiceover synchronization.
    
    A real implementation would interact with the TTS service and Manim's
    tracker system to align animations with narration word by word.
    """
    class VoiceoverTracker:
        def duration_for_words(self, word_count):
            # Simple estimation: 0.5 seconds per word
            return word_count * 0.5
    
    print(f"VOICEOVER: {text}")
    
    # The total duration could be fetched from the TTS service
    # for the given text.
    estimated_duration = len(text.split()) * 0.4 
    scene.wait(estimated_duration) # Placeholder wait
    
    try:
        yield VoiceoverTracker()
    finally:
        pass

# We can patch the Scene class to include our custom method.
# This makes it available as `with self.voiceover(...)` inside a scene.
Scene.voiceover = voiceover
