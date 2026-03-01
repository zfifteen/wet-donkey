# harness/schemas/plan.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List

class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Scene title")
    description: str = Field(description="Educational content description")
    estimated_duration_seconds: int = Field(ge=20, le=45)
    visual_ideas: List[str] = Field(description="Animation concepts")

class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Video title")
    description: str = Field(description="Video overview")
    target_duration_seconds: int = Field(ge=480, le=960)
    scenes: List[Scene] = Field(min_length=12, max_length=24)
