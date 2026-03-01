# harness/schemas/scene_build.py
from pydantic import BaseModel, ConfigDict, Field

class SceneBuild(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_body: str = Field(
        description="Python code for scene body (no imports, no class wrapper)"
    )
    reasoning: str = Field(
        description="Explanation of visual choices and animation strategy"
    )
