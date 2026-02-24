# harness/schemas/plan.py
from pydantic import BaseModel, Field
from typing import List

class Scene(BaseModel):
    title: str = Field(description="Scene title")
    description: str = Field(description="Educational content description")
    estimated_duration_seconds: int = Field(ge=20, le=45)
    visual_ideas: List[str] = Field(description="Animation concepts")

class Plan(BaseModel):
    title: str = Field(description="Video title")
    description: str = Field(description="Video overview")
    target_duration_seconds: int = Field(ge=480, le=960)
    scenes: List[Scene] = Field(min_items=12, max_items=24)
