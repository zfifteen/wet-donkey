# harness_responses/schemas/narration.py
# Placeholder for narration schema
from pydantic import BaseModel, Field
from typing import List

class NarrationScene(BaseModel):
    scene_title: str = Field(description="Title of the scene")
    narration_text: str = Field(description="The narration script for this scene.")

class Narration(BaseModel):
    scenes: List[NarrationScene] = Field(description="List of narrations for each scene.")
