import argparse
import importlib
import json
from pathlib import Path
import sys
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

_state_contract = importlib.import_module("harness.contracts.state")
PhaseTransitionError = _state_contract.PhaseTransitionError
load_state = _state_contract.load_state
save_state_atomic = _state_contract.save_state_atomic
transition_state = _state_contract.transition_state
update_state_key = _state_contract.update_state_key
record_phase_failure = _state_contract.record_phase_failure
clear_phase_failures = _state_contract.clear_phase_failures

STATE_FILE_NAME = "project_state.json"


def get_state(project_dir: Path, key: Optional[str] = None) -> None:
    """Print the state payload, or a specific state key if requested."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        sys.exit(0)

    state = load_state(state_file)
    state_payload = state.model_dump(mode="json")

    if key:
        value = state_payload.get(key)
        if value is not None:
            if isinstance(value, (dict, list)):
                print(json.dumps(value))
            else:
                print(value)
        return

    print(json.dumps(state_payload))


def _parse_cli_value(value: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def set_state(project_dir: Path, key: str, value: str) -> int:
    """Set a key-value pair in project_state.json with contract validation."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        print(f"Error: state file not found at '{state_file}'", file=sys.stderr)
        return 1

    state = load_state(state_file)
    parsed_value = _parse_cli_value(value)

    try:
        if key == "phase":
            state = transition_state(state, parsed_value, actor="manual")
        else:
            state = update_state_key(state, key, parsed_value)
    except PhaseTransitionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: failed to update state: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)
    return 0


def fail_phase(
    project_dir: Path,
    error_code: str,
    error_message: str,
    actor: str,
    force_block: bool,
) -> int:
    """Record a phase failure and apply blocked escalation when retry budget is exhausted."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        print(f"Error: state file not found at '{state_file}'", file=sys.stderr)
        return 1

    state = load_state(state_file)
    try:
        state = record_phase_failure(
            state,
            error_code=error_code,
            error_message=error_message,
            actor=actor,
            force_block=force_block,
        )
    except Exception as exc:
        print(f"Error: failed to record phase failure: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)
    return 0


def clear_failures(project_dir: Path, actor: str, reason: Optional[str]) -> int:
    """Clear retry/failure state for the current phase and unblock phase when applicable."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        print(f"Error: state file not found at '{state_file}'", file=sys.stderr)
        return 1

    state = load_state(state_file)
    try:
        state = clear_phase_failures(state, actor=actor, reason=reason)
    except Exception as exc:
        print(f"Error: failed to clear failures: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manages the project_state.json file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get", help="Get a value from the state.")
    get_parser.add_argument("--project-dir", required=True, help="The project directory.")
    get_parser.add_argument("--key", help="The key to retrieve. If omitted, returns the whole state.")

    set_parser = subparsers.add_parser("set", help="Set a value in the state.")
    set_parser.add_argument("--project-dir", required=True, help="The project directory.")
    set_parser.add_argument("--key", required=True, help="The key to set.")
    set_parser.add_argument("--value", required=True, help="The value to set (can be a JSON string).")

    fail_parser = subparsers.add_parser("fail", help="Record a phase failure.")
    fail_parser.add_argument("--project-dir", required=True, help="The project directory.")
    fail_parser.add_argument("--error-code", required=True, help="Machine-readable failure code.")
    fail_parser.add_argument("--error-message", required=True, help="Human-readable failure message.")
    fail_parser.add_argument("--actor", default="orchestrator", help="Actor recording the failure.")
    fail_parser.add_argument(
        "--force-block",
        action="store_true",
        help="Mark the phase as blocked regardless of retry attempt count.",
    )

    clear_parser = subparsers.add_parser("clear-failures", help="Clear failure and retry context.")
    clear_parser.add_argument("--project-dir", required=True, help="The project directory.")
    clear_parser.add_argument("--actor", default="orchestrator", help="Actor clearing failure state.")
    clear_parser.add_argument("--reason", help="Optional history reason for the clear action.")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Error: Project directory not found at '{project_dir}'", file=sys.stderr)
        sys.exit(1)

    if args.command == "get":
        get_state(project_dir, args.key)
        return

    if args.command == "set":
        exit_code = set_state(project_dir, args.key, args.value)
        sys.exit(exit_code)

    if args.command == "fail":
        exit_code = fail_phase(
            project_dir=project_dir,
            error_code=args.error_code,
            error_message=args.error_message,
            actor=args.actor,
            force_block=args.force_block,
        )
        sys.exit(exit_code)

    if args.command == "clear-failures":
        exit_code = clear_failures(
            project_dir=project_dir,
            actor=args.actor,
            reason=args.reason,
        )
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
