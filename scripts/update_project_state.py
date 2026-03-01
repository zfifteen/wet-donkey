import argparse
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Optional

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

_observability = importlib.import_module("harness.contracts.observability")
emit_phase_event = _observability.emit_phase_event
append_event = _observability.append_event
event_from_failure_context = _observability.event_from_failure_context
export_blocked_trace_bundle = _observability.export_blocked_trace_bundle

STATE_FILE_NAME = "project_state.json"

EVENT_TYPE_CHOICES = (
    "phase_start",
    "phase_success",
    "phase_failure",
    "phase_blocked",
    "phase_transition",
    "phase_unblocked",
    "diagnostic_bundle",
)


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


def _parse_metadata_json(raw: Optional[str]) -> dict[str, Any]:
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("metadata_json must decode to an object")
    return parsed


def _current_attempt_for_phase(state_payload: dict[str, Any], phase: str, *, next_attempt: bool) -> int:
    counters = state_payload.get("attempt_counters") or {}
    raw_count = counters.get(phase, 0)
    try:
        count = int(raw_count)
    except (TypeError, ValueError):
        count = 0

    if next_attempt:
        return max(1, count + 1)

    return max(1, count if count > 0 else 1)


def set_state(project_dir: Path, key: str, value: str, actor: str) -> int:
    """Set a key-value pair in project_state.json with contract validation."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        print(f"Error: state file not found at '{state_file}'", file=sys.stderr)
        return 1

    old_state = load_state(state_file)
    old_payload = old_state.model_dump(mode="json")
    parsed_value = _parse_cli_value(value)

    try:
        if key == "phase":
            state = transition_state(old_state, parsed_value, actor=actor)
        else:
            state = update_state_key(old_state, key, parsed_value)
    except PhaseTransitionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: failed to update state: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)

    if key == "phase":
        from_phase = old_state.phase
        to_phase = state.phase
        if from_phase != to_phase:
            try:
                emit_phase_event(
                    project_dir,
                    phase=from_phase,
                    event_type="phase_transition",
                    attempt=_current_attempt_for_phase(old_payload, from_phase, next_attempt=False),
                    actor=actor,
                    metadata={"to_phase": to_phase},
                )
            except Exception as exc:
                print(f"Error: state updated but failed to log phase_transition event: {exc}", file=sys.stderr)
                return 1

    return 0


def fail_phase(
    project_dir: Path,
    error_code: str,
    error_message: str,
    gate: str,
    owner_component: str,
    retryable: bool,
    error_signature: Optional[str],
    attempt_delta: Optional[str],
    evidence_token: Optional[str],
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
            gate=gate,
            owner_component=owner_component,
            retryable=retryable,
            error_signature=error_signature,
            attempt_delta=attempt_delta,
            evidence_token=evidence_token,
            actor=actor,
            force_block=force_block,
        )
    except Exception as exc:
        print(f"Error: failed to record phase failure: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)

    payload = state.model_dump(mode="json")
    failure_context = dict(payload.get("failure_context") or {})
    phase = str(payload.get("phase", "unknown"))

    try:
        failure_event = event_from_failure_context(
            project_dir,
            phase=phase,
            failure_context=failure_context,
            actor=actor,
        )
        append_event(project_dir, failure_event)

        if payload.get("phase_status") == "blocked":
            export_blocked_trace_bundle(
                project_dir,
                state_payload=payload,
                actor=actor,
            )
    except Exception as exc:
        print(f"Error: state updated but failed to write observability diagnostics: {exc}", file=sys.stderr)
        return 1

    return 0


def clear_failures(project_dir: Path, actor: str, reason: Optional[str]) -> int:
    """Clear retry/failure state for the current phase and unblock phase when applicable."""
    state_file = project_dir / STATE_FILE_NAME
    if not state_file.exists():
        print(f"Error: state file not found at '{state_file}'", file=sys.stderr)
        return 1

    previous_state = load_state(state_file)
    previous_payload = previous_state.model_dump(mode="json")

    try:
        state = clear_phase_failures(previous_state, actor=actor, reason=reason)
    except Exception as exc:
        print(f"Error: failed to clear failures: {exc}", file=sys.stderr)
        return 1

    save_state_atomic(state_file, state)

    if previous_payload.get("phase_status") == "blocked":
        try:
            phase = str(state.phase)
            attempt = _current_attempt_for_phase(previous_payload, phase, next_attempt=False)
            metadata: dict[str, Any] = {}
            if reason:
                metadata["reason"] = reason
            emit_phase_event(
                project_dir,
                phase=phase,
                event_type="phase_unblocked",
                attempt=attempt,
                actor=actor,
                metadata=metadata,
            )
        except Exception as exc:
            print(f"Error: failures cleared but failed to write unblocked observability event: {exc}", file=sys.stderr)
            return 1

    return 0


def log_event(
    project_dir: Path,
    event_type: str,
    phase: Optional[str],
    attempt: Optional[int],
    actor: str,
    message: Optional[str],
    next_action: Optional[str],
    metadata_json: Optional[str],
) -> int:
    state_file = project_dir / STATE_FILE_NAME
    if state_file.exists():
        state = load_state(state_file)
        state_payload = state.model_dump(mode="json")
        default_phase = state.phase
    else:
        state_payload = {}
        default_phase = "unknown"

    phase_value = phase or default_phase
    if attempt is None:
        attempt = _current_attempt_for_phase(
            state_payload,
            phase_value,
            next_attempt=(event_type == "phase_start"),
        )

    try:
        metadata = _parse_metadata_json(metadata_json)
    except ValueError as exc:
        print(f"Error: invalid metadata JSON: {exc}", file=sys.stderr)
        return 1

    if message:
        metadata["message"] = message

    try:
        event = emit_phase_event(
            project_dir,
            phase=phase_value,
            event_type=event_type,
            attempt=attempt,
            actor=actor,
            next_action=next_action,
            metadata=metadata,
        )
    except Exception as exc:
        print(f"Error: failed to log event: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(event.model_dump(mode="json")))
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
    set_parser.add_argument("--actor", default="manual", help="Actor making the state update.")

    fail_parser = subparsers.add_parser("fail", help="Record a phase failure.")
    fail_parser.add_argument("--project-dir", required=True, help="The project directory.")
    fail_parser.add_argument("--error-code", required=True, help="Machine-readable failure code.")
    fail_parser.add_argument("--error-message", required=True, help="Human-readable failure message.")
    fail_parser.add_argument("--gate", default="runtime", help="Validation gate that produced this failure.")
    fail_parser.add_argument(
        "--owner-component",
        default="orchestrator",
        help="Component that owns the failure (harness/parser/orchestrator/etc).",
    )
    fail_parser.add_argument(
        "--retryable",
        default="true",
        choices=("true", "false"),
        help="Whether this failure is retryable under policy.",
    )
    fail_parser.add_argument("--error-signature", help="Optional precomputed deterministic failure signature.")
    fail_parser.add_argument("--attempt-delta", help="Optional delta summary versus prior attempt.")
    fail_parser.add_argument("--evidence-token", help="Optional token proving new evidence on retry.")
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

    log_parser = subparsers.add_parser("log-event", help="Write an observability event.")
    log_parser.add_argument("--project-dir", required=True, help="The project directory.")
    log_parser.add_argument("--event-type", required=True, choices=EVENT_TYPE_CHOICES)
    log_parser.add_argument("--phase", help="Optional phase override. Defaults to current state phase.")
    log_parser.add_argument("--attempt", type=int, help="Optional attempt number.")
    log_parser.add_argument("--actor", default="orchestrator")
    log_parser.add_argument("--message", help="Optional message added to event metadata.")
    log_parser.add_argument("--next-action", help="Optional next-action recommendation.")
    log_parser.add_argument("--metadata-json", help="Optional JSON object metadata payload.")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Error: Project directory not found at '{project_dir}'", file=sys.stderr)
        sys.exit(1)

    if args.command == "get":
        get_state(project_dir, args.key)
        return

    if args.command == "set":
        exit_code = set_state(project_dir, args.key, args.value, args.actor)
        sys.exit(exit_code)

    if args.command == "fail":
        exit_code = fail_phase(
            project_dir=project_dir,
            error_code=args.error_code,
            error_message=args.error_message,
            gate=args.gate,
            owner_component=args.owner_component,
            retryable=args.retryable == "true",
            error_signature=args.error_signature,
            attempt_delta=args.attempt_delta,
            evidence_token=args.evidence_token,
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

    if args.command == "log-event":
        exit_code = log_event(
            project_dir=project_dir,
            event_type=args.event_type,
            phase=args.phase,
            attempt=args.attempt,
            actor=args.actor,
            message=args.message,
            next_action=args.next_action,
            metadata_json=args.metadata_json,
        )
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
