from __future__ import annotations

import pytest
from pydantic import ValidationError

from harness.parser import validate_parser_schema_alignment, validate_phase_payload
from harness.schemas.plan import Plan
from harness.schemas.scene_build import SceneBuild


def test_parser_schema_alignment_contract_is_valid() -> None:
    validate_parser_schema_alignment()


def test_validate_phase_payload_returns_typed_model() -> None:
    payload = {
        "scene_body": "title = Text('Hello')",
        "reasoning": "Simple intro scene",
    }
    result = validate_phase_payload("build_scenes", payload)
    assert isinstance(result, SceneBuild)


def test_validate_phase_payload_rejects_extra_fields() -> None:
    payload = {
        "scene_body": "title = Text('Hello')",
        "reasoning": "Simple intro scene",
        "extra": "should fail",
    }
    with pytest.raises(ValidationError):
        validate_phase_payload("build_scenes", payload)


def test_validate_plan_payload_rejects_invalid_visual_idea_shape() -> None:
    payload = {
        "title": "A topic",
        "description": "desc",
        "target_duration_seconds": 600,
        "scenes": [
            {
                "title": "Scene 1",
                "description": "desc",
                "estimated_duration_seconds": 30,
                "visual_ideas": ["x"],
                "extra_field": "forbidden",
            }
        ]
        * 12,
    }
    with pytest.raises(ValidationError):
        validate_phase_payload("plan", payload)


def test_validate_plan_payload_accepts_contract_shape() -> None:
    payload = {
        "title": "A topic",
        "description": "desc",
        "target_duration_seconds": 600,
        "scenes": [
            {
                "title": f"Scene {index}",
                "description": "desc",
                "estimated_duration_seconds": 30,
                "visual_ideas": ["idea"],
            }
            for index in range(1, 13)
        ],
    }
    result = validate_phase_payload("plan", payload)
    assert isinstance(result, Plan)
