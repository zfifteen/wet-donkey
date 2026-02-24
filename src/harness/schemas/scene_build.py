# harness/schemas/scene_build.py
from pydantic import BaseModel, Field

class SceneBuild(BaseModel):
    scene_body: str = Field(
        description="Python code for scene body (no imports, no class wrapper)"
    )
    reasoning: str = Field(
        description="Explanation of visual choices and animation strategy"
    )
