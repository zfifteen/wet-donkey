# harness/parser.py
import json

def parse_response(response: str) -> dict:
    """
    Parses the JSON response from the legacy LLM.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print("Error parsing legacy response.")
        return {"error": "Invalid JSON response."}
