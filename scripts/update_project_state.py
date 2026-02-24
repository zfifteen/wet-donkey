# scripts/update_project_state.py
import argparse
import json
from pathlib import Path
import sys

STATE_FILE_NAME = "project_state.json"

def get_state(project_dir: Path, key: str = None):
    """Prints the value of a key from the project state."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        sys.exit(0) # No state yet, not an error
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    if key:
        # Using .get() to avoid errors if the key doesn't exist
        value = state.get(key)
        if value is not None:
            # If value is a dict or list, print as JSON
            if isinstance(value, (dict, list)):
                print(json.dumps(value))
            else:
                print(value)
    else:
        # Print the whole state if no key is specified
        print(json.dumps(state))

def set_state(project_dir: Path, key: str, value: str):
    """Sets a key-value pair in the project state."""
    state_file = project_dir / STATE_FILE_NAME
    state = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                # File is corrupt or empty, start fresh
                pass
    
    # Try to parse the value as JSON, otherwise treat as a string
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
        
    state[key] = parsed_value
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Manages the project_state.json file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'get' command
    get_parser = subparsers.add_parser("get", help="Get a value from the state.")
    get_parser.add_argument("--project-dir", required=True, help="The project directory.")
    get_parser.add_argument("--key", help="The key to retrieve. If omitted, returns the whole state.")
    
    # 'set' command
    set_parser = subparsers.add_parser("set", help="Set a value in the state.")
    set_parser.add_argument("--project-dir", required=True, help="The project directory.")
    set_parser.add_argument("--key", required=True, help="The key to set.")
    set_parser.add_argument("--value", required=True, help="The value to set (can be a JSON string).")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Error: Project directory not found at '{project_dir}'", file=sys.stderr)
        sys.exit(1)

    if args.command == "get":
        get_state(project_dir, args.key)
    elif args.command == "set":
        set_state(project_dir, args.key, args.value)

if __name__ == "__main__":
    main()
