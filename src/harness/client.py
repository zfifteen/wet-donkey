# harness/client.py
from pathlib import Path

from xai_sdk.chat import user

from .parser import (
    validate_phase_payload,
    validate_timing_execution,
)
from .prompts import compose_prompts
from .schemas import get_schema_for_phase
from .schemas.narration import Narration
from .schemas.plan import Plan
from .schemas.scene_qc import SceneQC
from .session import PipelineTrainingSession

def generate_plan(session: PipelineTrainingSession, topic: str, retry_context: str | None = None) -> Plan:
    """Generate structured plan with API-enforced schema"""
    
    prompts = compose_prompts("00_plan", topic=topic, retry_context=retry_context)
    
    chat = session.create_chat(
        phase="plan",
        response_format=get_schema_for_phase("plan"),
    )
    
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()
    
    plan = validate_phase_payload("plan", response.content)
    
    session.update_response_id(response.id)
    
    return plan

def generate_scene(session: PipelineTrainingSession, scene_spec: dict, retry_context: str | None = None):
    """Generates the Manim code for a single scene."""

    prompts = compose_prompts(
        "04_build_scenes",
        scene_title=scene_spec['title'],
        scene_description=scene_spec['description'],
        narration_duration=scene_spec.get(
            'narration_duration',
            scene_spec.get('estimated_duration_seconds')
        ),
        visual_ideas=", ".join(scene_spec['visual_ideas']),
        retry_context=retry_context
    )

    chat = session.create_chat(
        phase="build_scenes",
        response_format=get_schema_for_phase("build_scenes"),
    )
    
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    # Validate that the model actually used the code execution tool for timing
    validate_timing_execution(response)

    scene_build = validate_phase_payload("build_scenes", response.content)
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
        response_format=get_schema_for_phase("scene_repair"),
    )

    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    scene_repair = validate_phase_payload("scene_repair", response.content)
    session.update_response_id(response.id)

    return scene_repair


def generate_narration(
    session: PipelineTrainingSession,
    plan: Plan,
) -> Narration:
    """Generate narration script for all plan scenes."""
    prompts = compose_prompts(
        "02_narration",
        plan=plan.model_dump(mode="json"),
    )

    chat = session.create_chat(
        phase="narration",
        response_format=get_schema_for_phase("narration"),
    )
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    narration = validate_phase_payload("narration", response.content)
    session.update_response_id(response.id)
    return narration


def run_scene_qc(
    session: PipelineTrainingSession,
    scene_file: str,
) -> SceneQC:
    """Run scene quality checks and return structured QC result."""
    prompts = compose_prompts(
        "05_scene_qc",
        scene_code=Path(scene_file).read_text(encoding="utf-8"),
    )

    chat = session.create_chat(
        phase="scene_qc",
        response_format=get_schema_for_phase("scene_qc"),
    )
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()

    scene_qc = validate_phase_payload("scene_qc", response.content)
    session.update_response_id(response.id)
    return scene_qc
