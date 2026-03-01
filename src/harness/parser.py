from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .schemas import SCHEMA_REGISTRY_CONTRACT_VERSION, get_schema_for_phase

PARSER_SCHEMA_CONTRACT_VERSION = "1.0.0"


class SemanticValidationError(Exception):
    """
    Raised when the LLM output is structurally valid but fails
    business logic or semantic checks.
    """
    pass


class SchemaContractError(ValueError):
    """Raised when parser schema contract metadata drifts from the registry."""


def validate_parser_schema_alignment() -> None:
    if PARSER_SCHEMA_CONTRACT_VERSION != SCHEMA_REGISTRY_CONTRACT_VERSION:
        raise SchemaContractError(
            "parser/schema contract version mismatch: "
            f"parser={PARSER_SCHEMA_CONTRACT_VERSION}, "
            f"registry={SCHEMA_REGISTRY_CONTRACT_VERSION}"
        )


def validate_phase_payload(phase: str, payload: Any):
    """
    Validate payload against the canonical schema for a phase.
    """
    validate_parser_schema_alignment()
    schema = get_schema_for_phase(phase)
    try:
        return schema.model_validate(payload)
    except ValidationError:
        raise

# The xAI SDK's `response_format` feature with Pydantic models handles
# the primary JSON parsing and type validation. This file can be
# used to add more complex, application-specific validation logic
# that runs after the initial parsing.

def validate_collections_usage(response, scene_id):
    """Ensure agent used template library.
    This is an example of a semantic validation check.
    """
    if not hasattr(response, 'citations') or not response.citations:
        print(f"Warning: {scene_id}: No Collections citations found in response.")
        return False
    
    collections_refs = [c for c in response.citations 
                        if c.startswith("collections://")]
    
    if len(collections_refs) < 1:
        print(f"Warning: {scene_id}: Insufficient template references.")
        return False
    
    return True


def validate_timing_execution(response):
    """Ensure agent used code_execution for timing check"""
    if not hasattr(response, 'server_side_tool_usage'):
        raise SemanticValidationError(
            "Scene build response must include server_side_tool_usage attribute."
        )

    tool_calls = response.server_side_tool_usage.get("code_execution", [])
    
    if not tool_calls:
        raise SemanticValidationError(
            "Scene build must include code_execution timing validation."
        )
    
    # Check that timing logic was present
    for call in tool_calls:
        if "run_time" in call.get("code", ""):
            return True
    
    raise SemanticValidationError("No timing validation detected in code execution.")
