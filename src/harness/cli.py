import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .client import generate_plan, generate_scene, repair_scene
from .contracts.prompt_manifest import PromptContractError
from .exit_codes import HarnessExitCode
from .parser import SchemaContractError, SemanticValidationError
from .session import PipelineTrainingSession, SessionContractError
from .contracts.scaffold import ScaffoldContractError, inject_scene_body_file
from .contracts.state import load_state, save_state_atomic, update_state_key

LEGACY_HARNESS_ENV_VARS = ("FH_HARNESS", "USE_HARNESS")


def reject_legacy_fallback_toggles() -> None:
    configured = {
        name: os.getenv(name)
        for name in LEGACY_HARNESS_ENV_VARS
        if os.getenv(name, "").strip()
    }
    if configured:
        pairs = ", ".join(f"{name}={value}" for name, value in configured.items())
        raise PermissionError(f"legacy harness fallback toggles are disabled: {pairs}")


def write_plan(plan, project_dir):
    """Save plan into project_state.json using the canonical state contract."""
    project_dir = Path(project_dir)
    state_file = project_dir / "project_state.json"

    if not state_file.exists():
        raise FileNotFoundError(f"state file not found: {state_file}")

    state = load_state(state_file)
    updated_state = update_state_key(state, "plan", plan.model_dump(mode="json"))
    save_state_atomic(state_file, updated_state)
    print(f"Plan written to {state_file}")


def inject_scene_body(scene_body, scene_file):
    """Inject generated Python code into the scene file while preserving scaffold markers."""
    inject_scene_body_file(scene_file, scene_body)
    print(f"Scene body injected into {scene_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="xAI Responses API harness")
    parser.add_argument(
        "--phase",
        required=True,
        choices=["plan", "narration", "build_scenes", "scene_qc", "scene_repair"],
    )
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--topic", help="Topic for the video plan")
    parser.add_argument("--scene-file", help="For scene-specific phases")
    parser.add_argument("--scene-spec", help="JSON string of the scene specification for building")
    parser.add_argument("--retry-context", help="Error context from previous attempt")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        reject_legacy_fallback_toggles()
    except PermissionError as exc:
        print(f"Policy Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    try:
        session = PipelineTrainingSession.from_project(args.project_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.INFRASTRUCTURE_ERROR)
    except SessionContractError as exc:
        print(f"Schema Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.SCHEMA_VIOLATION)

    if args.dry_run:
        print("Dry run mode. No API calls will be made.")
        return int(HarnessExitCode.SUCCESS)

    try:
        if args.phase == "plan":
            if not args.topic:
                print("Error: --topic is required for the 'plan' phase.", file=sys.stderr)
                return int(HarnessExitCode.POLICY_VIOLATION)
            result = generate_plan(session, args.topic, args.retry_context)
            write_plan(result, args.project_dir)

        elif args.phase == "build_scenes":
            if not args.scene_spec or not args.scene_file:
                print("Error: --scene-spec and --scene-file are required for 'build_scenes'.", file=sys.stderr)
                return int(HarnessExitCode.POLICY_VIOLATION)
            scene_spec = json.loads(args.scene_spec)
            result = generate_scene(session, scene_spec, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)

        elif args.phase == "scene_repair":
            if not args.retry_context or not args.scene_file:
                print("Error: --retry-context and --scene-file are required for 'scene_repair'.", file=sys.stderr)
                return int(HarnessExitCode.POLICY_VIOLATION)
            result = repair_scene(session, args.scene_file, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)

        else:
            print(f"Phase '{args.phase}' is not yet implemented.", file=sys.stderr)
            return int(HarnessExitCode.INFRASTRUCTURE_ERROR)

        return int(HarnessExitCode.SUCCESS)

    except (SemanticValidationError, ScaffoldContractError) as exc:
        print(f"Validation Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.VALIDATION_ERROR)

    except (ValidationError, json.JSONDecodeError, SessionContractError, SchemaContractError, PromptContractError) as exc:
        print(f"Schema Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.SCHEMA_VIOLATION)

    except PermissionError as exc:
        print(f"Policy Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    except Exception as exc:
        print(f"Harness Error: {exc}", file=sys.stderr)
        return int(HarnessExitCode.INFRASTRUCTURE_ERROR)


if __name__ == "__main__":
    sys.exit(main())
