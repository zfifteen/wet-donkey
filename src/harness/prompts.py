# harness/prompts.py
from pathlib import Path
import jinja2

from .contracts.prompt_manifest import (
    PromptManifest,
    discover_template_variables,
    load_prompt_manifest,
    validate_manifest_schema_alignment,
    validate_manifest_template_alignment,
    validate_manifest_tool_policy,
    validate_runtime_variables,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"

TOOL_DEFINITIONS: dict[str, str] = {
    "collections_search": (
        "Query project/template collections for reference patterns and prior context. "
        "Use this to ground outputs in known examples."
    ),
    "code_execution": (
        "Run deterministic calculations/checks (timing, counts, numeric validation). "
        "Use this to verify concrete claims before finalizing output."
    ),
    "web_search": (
        "Research externally-sourced facts when the phase requires current or factual grounding."
    ),
}


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


def _tool_contract_block(manifest: PromptManifest) -> str:
    allowed = ", ".join(manifest.allowed_tools) if manifest.allowed_tools else "none"
    required = ", ".join(manifest.required_tools) if manifest.required_tools else "none"
    tool_lines: list[str] = []
    for tool_name in manifest.allowed_tools:
        definition = TOOL_DEFINITIONS.get(tool_name, "No definition available.")
        tool_lines.append(f"- `{tool_name}`: {definition}")
    if not tool_lines:
        tool_lines.append("- none")

    return (
        "Tool Contract (manifest-derived):\n"
        f"- Allowed tools: {allowed}\n"
        f"- Required tools: {required}\n"
        "- Tool definitions:\n"
        + "\n".join(tool_lines)
        + "\n"
        "- Use required tools when listed.\n"
        "- Do not claim tool usage unless the call was actually made."
    )


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
    system_prompt = f"{system_prompt.rstrip()}\n\n{_tool_contract_block(manifest)}\n"
    user_prompt = environment.get_template("user.md").render(**kwargs)

    return {
        "system": system_prompt,
        "user": user_prompt
    }
