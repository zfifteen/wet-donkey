from __future__ import annotations

import pytest

from harness.contracts.prompt_manifest import (
    PHASE_ALLOWED_TOOLS,
    PromptContractError,
    discover_template_variables,
    load_prompt_manifest,
    validate_manifest_schema_alignment,
    validate_manifest_template_alignment,
    validate_manifest_tool_policy,
)
from harness.prompts import compose_prompts, validate_prompt_contracts


def test_all_prompt_contracts_validate() -> None:
    validate_prompt_contracts()


def test_compose_prompts_rejects_missing_required_variables() -> None:
    with pytest.raises(PromptContractError, match="missing required prompt variables"):
        compose_prompts("00_plan")


def test_compose_prompts_rejects_undeclared_variables() -> None:
    with pytest.raises(PromptContractError, match="undeclared prompt variables"):
        compose_prompts("00_plan", topic="Signal processing", unexpected="x")


def test_build_scene_prompt_accepts_optional_retry_context() -> None:
    payload = compose_prompts(
        "04_build_scenes",
        scene_title="Scene A",
        scene_description="Description",
        narration_duration=30,
        visual_ideas="bar chart",
        retry_context="timing overflow",
    )

    assert "Retry Context" in payload["user"]


def test_manifest_template_alignment_and_tool_policy_per_phase() -> None:
    from harness.prompts import PROMPTS_DIR

    phase_map = {
        "00_plan": "plan",
        "02_narration": "narration",
        "04_build_scenes": "build_scenes",
        "05_scene_qc": "scene_qc",
        "06_scene_repair": "scene_repair",
    }

    for folder, phase in phase_map.items():
        phase_dir = PROMPTS_DIR / folder
        manifest = load_prompt_manifest(phase_dir)
        discovered = discover_template_variables(phase_dir)
        validate_manifest_template_alignment(manifest, discovered)
        validate_manifest_schema_alignment(manifest)
        validate_manifest_tool_policy(manifest)
        assert set(manifest.allowed_tools).issubset(PHASE_ALLOWED_TOOLS[phase])


def test_compose_prompts_includes_manifest_tool_contract_block() -> None:
    payload = compose_prompts(
        "04_build_scenes",
        scene_title="Scene A",
        scene_description="Description",
        narration_duration=30,
        visual_ideas="bar chart",
        retry_context=None,
    )

    system = payload["system"]
    assert "Tool Contract (manifest-derived):" in system
    assert "Allowed tools: collections_search, code_execution" in system
    assert "Required tools: collections_search, code_execution" in system
    assert "`collections_search`:" in system
    assert "`code_execution`:" in system
