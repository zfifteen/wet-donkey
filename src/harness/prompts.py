# harness/prompts.py
from pathlib import Path
import jinja2

from .contracts.prompt_manifest import (
    discover_template_variables,
    load_prompt_manifest,
    validate_manifest_schema_alignment,
    validate_manifest_template_alignment,
    validate_manifest_tool_policy,
    validate_runtime_variables,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _resolve_phase_dir(phase_name: str) -> Path:
    phase_dir = PROMPTS_DIR / phase_name
    if not phase_dir.is_dir():
        raise FileNotFoundError(f"Prompt directory not found for phase: {phase_name}")
    return phase_dir


def _validate_phase_contracts(phase_dir: Path) -> None:
    manifest = load_prompt_manifest(phase_dir)
    discovered = discover_template_variables(phase_dir)
    validate_manifest_template_alignment(manifest, discovered)
    validate_manifest_schema_alignment(manifest)
    validate_manifest_tool_policy(manifest)


def validate_prompt_contracts() -> None:
    for phase_dir in sorted(PROMPTS_DIR.iterdir()):
        if phase_dir.is_dir():
            _validate_phase_contracts(phase_dir)


def compose_prompts(phase_name: str, **kwargs) -> dict:
    """
    Renders the system and user prompts for a given phase using Jinja2.

    Args:
        phase_name: The name of the phase (e.g., '00_plan').
        **kwargs: Key-value pairs to render into the templates.

    Returns:
        A dictionary with 'system' and 'user' prompt strings.
    """
    phase_dir = _resolve_phase_dir(phase_name)

    system_template_file = phase_dir / "system.md"
    user_template_file = phase_dir / "user.md"

    if not system_template_file.exists():
        raise FileNotFoundError(f"System prompt not found for phase: {phase_name}")
    if not user_template_file.exists():
        raise FileNotFoundError(f"User prompt not found for phase: {phase_name}")

    manifest = load_prompt_manifest(phase_dir)
    discovered = discover_template_variables(phase_dir)
    validate_manifest_template_alignment(manifest, discovered)
    validate_manifest_schema_alignment(manifest)
    validate_manifest_tool_policy(manifest)
    validate_runtime_variables(manifest, kwargs.keys())

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(phase_dir),
        undefined=jinja2.StrictUndefined,
    )
    
    system_prompt = environment.get_template("system.md").render(**kwargs)
    user_prompt = environment.get_template("user.md").render(**kwargs)

    return {
        "system": system_prompt,
        "user": user_prompt
    }
