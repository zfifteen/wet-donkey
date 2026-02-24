# harness/prompts.py

def get_prompt(phase: str, context: dict) -> str:
    """
    Returns a prompt for the legacy system.
    """
    prompt = f"Phase: {phase}
"
    prompt += "Context:
"
    for key, value in context.items():
        prompt += f"- {key}: {value}
"
    
    return prompt
