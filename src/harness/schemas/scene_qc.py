# harness/schemas/scene_qc.py
# Placeholder for scene QC schema
from pydantic import BaseModel, Field
from typing import List

class QCIssue(BaseModel):
    time_code: str = Field(description="Time code of the issue, e.g., 00:15-00:18")
    description: str = Field(description="Description of the issue found.")
    severity: str = Field(description="Severity of the issue (e.g., critical, major, minor)")

class SceneQC(BaseModel):
    scene_title: str = Field(description="Title of the scene being reviewed.")
    passed: bool = Field(description="Whether the scene passed the quality check.")
    score: float = Field(ge=0.0, le=1.0, description="Quality score from 0.0 to 1.0")
    issues: List[QCIssue] = Field(description="List of issues found during QC.")
