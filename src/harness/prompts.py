# harness/prompts.py
from pathlib import Path
import jinja2

PROMPTS_DIR = Path(__file__).parent / "prompts"

def compose_prompts(phase_name: str, **kwargs) -> dict:
    """
    Renders the system and user prompts for a given phase using Jinja2.

    Args:
        phase_name: The name of the phase (e.g., '00_plan').
        **kwargs: Key-value pairs to render into the templates.

    Returns:
        A dictionary with 'system' and 'user' prompt strings.
    """
    phase_dir = PROMPTS_DIR / phase_name
    if not phase_dir.is_dir():
        raise FileNotFoundError(f"Prompt directory not found for phase: {phase_name}")

    system_template_file = phase_dir / "system.md"
    user_template_file = phase_dir / "user.md"

    if not system_template_file.exists():
        raise FileNotFoundError(f"System prompt not found for phase: {phase_name}")
    if not user_template_file.exists():
        raise FileNotFoundError(f"User prompt not found for phase: {phase_name}")

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(phase_dir))
    
    system_prompt = environment.get_template("system.md").render(**kwargs)
    user_prompt = environment.get_template("user.md").render(**kwargs)

    return {
        "system": system_prompt,
        "user": user_prompt
    }
