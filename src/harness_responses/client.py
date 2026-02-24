# harness_responses/client.py
import os
from .session import PipelineTrainingSession
from .prompts import compose_prompts
from .schemas.plan import Plan
from .schemas.scene_build import SceneBuild
from .parser import SemanticValidationError, validate_timing_execution

def generate_plan(session: PipelineTrainingSession, topic: str, retry_context: str = None):
    """Generate structured plan with API-enforced schema"""
    
    prompts = compose_prompts("00_plan", topic=topic, retry_context=retry_context)
    
    chat = session.create_chat(
        phase="plan",
        response_format=Plan,  # Pydantic model for structured output
    )
    
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()
    
    # The SDK handles the validation against the Pydantic model.
    # We can directly access the parsed object.
    plan = response.content
    
    session.update_response_id(response.id)
    
    return plan

def generate_scene(session: PipelineTrainingSession, scene_spec: dict, retry_context: str = None):
    """Generates the Manim code for a single scene."""

    prompts = compose_prompts(
        "04_build_scenes",
        scene_title=scene_spec['title'],
        scene_description=scene_spec['description'],
        narration_duration=scene_spec['narration_duration'],
        visual_ideas=", ".join(scene_spec['visual_ideas']),
        retry_context=retry_context
    )

    chat = session.create_chat(
        phase="build_scenes",
        response_format=SceneBuild
    )
    
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    # Validate that the model actually used the code execution tool for timing
    validate_timing_execution(response)

    scene_build = response.content
    session.update_response_id(response.id)

    return scene_build

def repair_scene(session: PipelineTrainingSession, scene_file: str, failure_reason: str):
    """Attempts to repair a scene that failed validation."""
    
    prompts = compose_prompts(
        "06_scene_repair",
        scene_file_content=Path(scene_file).read_text(),
        failure_reason=failure_reason
    )

    chat = session.create_chat(
        phase="scene_repair",
        response_format=SceneBuild
    )

    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    scene_repair = response.content
    session.update_response_id(response.id)

    return scene_repair

# Placeholder for other phases mentioned in the spec
def generate_narration(session: PipelineTrainingSession, plan: Plan):
    """Placeholder function to generate narration script."""
    print("Generating narration...")
    # In a real implementation, this would call the xAI API
    # with prompts from '02_narration'
    pass

def run_scene_qc(session: PipelineTrainingSession, scene_file: str):
    """Placeholder function to run Quality Control on a scene."""
    print(f"Running QC on {scene_file}...")
    # In a real implementation, this would call the xAI API
    # with prompts from '05_scene_qc'
    pass
