# harness/schemas/narration.py
# Placeholder for narration schema
from pydantic import BaseModel, ConfigDict, Field
from typing import List

class NarrationScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_title: str = Field(description="Title of the scene")
    narration_text: str = Field(description="The narration script for this scene.")

class Narration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenes: List[NarrationScene] = Field(description="List of narrations for each scene.")
