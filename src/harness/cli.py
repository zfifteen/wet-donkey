import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .client import generate_narration, generate_plan, generate_scene, repair_scene, run_scene_qc
from .contracts.prompt_manifest import PromptContractError
from .contracts.runtime_pipeline import load_scene_manifest, scene_manifest_path, write_scene_qc_report
from .contracts.scaffold import ScaffoldContractError, inject_scene_body_file
from .contracts.state import load_state, save_state_atomic, update_state_key
from .exit_codes import HarnessExitCode
from .parser import SchemaContractError, SemanticValidationError
from .schemas.plan import Plan
from .session import PipelineTrainingSession, SessionContractError

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


def write_state_payload(key: str, payload, project_dir: str | Path) -> None:
    """Save a phase payload into project_state.json using the canonical state contract."""
    project_dir = Path(project_dir)
    state_file = project_dir / "project_state.json"

    if not state_file.exists():
        raise FileNotFoundError(f"state file not found: {state_file}")

    state = load_state(state_file)
    updated_state = update_state_key(state, key, payload)
    save_state_atomic(state_file, updated_state)
    print(f"{key} written to {state_file}")


def write_plan(plan, project_dir) -> None:
    write_state_payload("plan", plan.model_dump(mode="json"), project_dir)


def write_narration(narration, project_dir) -> None:
    write_state_payload("narration", narration.model_dump(mode="json"), project_dir)


def load_plan_from_state(project_dir: str | Path) -> Plan:
    project_dir = Path(project_dir)
    state_file = project_dir / "project_state.json"

    if not state_file.exists():
        raise SemanticValidationError(f"state file not found: {state_file}")

    state = load_state(state_file)
    payload = state.model_dump(mode="json")

    if "plan" not in payload:
        raise SemanticValidationError("project_state.json is missing required 'plan' payload")

    try:
        return Plan.model_validate(payload["plan"])
    except ValidationError as exc:
        raise SemanticValidationError(f"invalid plan payload in state: {exc}") from exc


def inject_scene_body(scene_body, scene_file) -> None:
    """Inject generated Python code into the scene file while preserving scaffold markers."""
    inject_scene_body_file(scene_file, scene_body)
    print(f"Scene body injected into {scene_file}")


def resolve_scene_file_relative(scene_file: str, project_dir: Path) -> str:
    path = Path(scene_file)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(project_dir.resolve())
        except ValueError as exc:
            raise PermissionError(
                f"--scene-file must be under project directory '{project_dir}': {scene_file}"
            ) from exc
    return path.as_posix()


def find_manifest_scene_entry(project_dir: Path, scene_file: str, scene_id: str | None):
    manifest_file = scene_manifest_path(project_dir)
    if not manifest_file.exists():
        raise PermissionError(
            f"scene manifest not found: {manifest_file} (required before scene_qc phase)"
        )

    manifest = load_scene_manifest(manifest_file)
    scene_file_rel = resolve_scene_file_relative(scene_file, project_dir)

    for scene in manifest.scenes:
        if scene_id and scene.scene_id != scene_id:
            continue
        if scene.scene_file == scene_file_rel:
            return scene

    raise PermissionError(
        f"scene file '{scene_file_rel}' not found in scene manifest"
        + (f" for scene_id '{scene_id}'" if scene_id else "")
    )


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
    parser.add_argument("--scene-id", help="Optional scene identifier for scene-specific phases")
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

        elif args.phase == "narration":
            plan = load_plan_from_state(args.project_dir)
            result = generate_narration(session, plan)
            write_narration(result, args.project_dir)

        elif args.phase == "build_scenes":
            if not args.scene_spec or not args.scene_file:
                print("Error: --scene-spec and --scene-file are required for 'build_scenes'.", file=sys.stderr)
                return int(HarnessExitCode.POLICY_VIOLATION)
            scene_spec = json.loads(args.scene_spec)
            result = generate_scene(session, scene_spec, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)

        elif args.phase == "scene_qc":
            if not args.scene_file:
                print("Error: --scene-file is required for 'scene_qc'.", file=sys.stderr)
                return int(HarnessExitCode.POLICY_VIOLATION)
            scene_file_path = Path(args.scene_file)
            if not scene_file_path.is_absolute():
                scene_file_path = Path(args.project_dir) / scene_file_path
            scene_result = run_scene_qc(session, str(scene_file_path))
            scene_entry = find_manifest_scene_entry(Path(args.project_dir), str(scene_file_path), args.scene_id)
            report_path = write_scene_qc_report(Path(args.project_dir), scene_entry, scene_result)
            print(f"Scene QC report written to {report_path}")

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
