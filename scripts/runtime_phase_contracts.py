#!/usr/bin/env python3.13
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

_runtime = importlib.import_module("harness.contracts.runtime_pipeline")
HarnessExitCode = importlib.import_module("harness.exit_codes").HarnessExitCode

build_scene_manifest = _runtime.build_scene_manifest
build_scene_spec = _runtime.build_scene_spec
ensure_scene_scaffolds = _runtime.ensure_scene_scaffolds
load_plan_and_narration_from_state = _runtime.load_plan_and_narration_from_state
load_scene_manifest = _runtime.load_scene_manifest
scene_manifest_path = _runtime.scene_manifest_path
validate_built_scene_files = _runtime.validate_built_scene_files
validate_scene_qc_reports = _runtime.validate_scene_qc_reports
write_narration_script = _runtime.write_narration_script
write_scene_manifest = _runtime.write_scene_manifest


def _resolve_manifest_path(project_dir: Path, raw_manifest_path: str | None) -> Path:
    if not raw_manifest_path:
        return scene_manifest_path(project_dir)
    path = Path(raw_manifest_path)
    if path.is_absolute():
        return path
    return project_dir / path


def prepare_scene_manifest(project_dir: Path) -> int:
    plan, narration = load_plan_and_narration_from_state(project_dir)
    manifest = build_scene_manifest(plan, narration)

    manifest_file = write_scene_manifest(project_dir, manifest)
    narration_file = write_narration_script(project_dir, manifest)

    payload = {
        "status": "ok",
        "scene_count": len(manifest.scenes),
        "manifest_path": str(manifest_file),
        "narration_script": str(narration_file),
    }
    print(json.dumps(payload))
    return int(HarnessExitCode.SUCCESS)


def scaffold_scenes(project_dir: Path, manifest_path: Path) -> int:
    if not manifest_path.exists():
        print(f"Error: scene manifest not found at '{manifest_path}'", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    manifest = load_scene_manifest(manifest_path)
    created = ensure_scene_scaffolds(project_dir, manifest)

    payload = {
        "status": "ok",
        "scene_count": len(manifest.scenes),
        "created": [str(path.relative_to(project_dir)) for path in created],
    }
    print(json.dumps(payload))
    return int(HarnessExitCode.SUCCESS)


def validate_build_scenes(project_dir: Path, manifest_path: Path) -> int:
    if not manifest_path.exists():
        print(f"Error: scene manifest not found at '{manifest_path}'", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    manifest = load_scene_manifest(manifest_path)
    errors = validate_built_scene_files(project_dir, manifest)
    if errors:
        print("Build scene contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return int(HarnessExitCode.VALIDATION_ERROR)

    payload = {
        "status": "ok",
        "scene_count": len(manifest.scenes),
    }
    print(json.dumps(payload))
    return int(HarnessExitCode.SUCCESS)


def validate_scene_qc(project_dir: Path, manifest_path: Path, min_score: float) -> int:
    if not manifest_path.exists():
        print(f"Error: scene manifest not found at '{manifest_path}'", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    manifest = load_scene_manifest(manifest_path)
    errors = validate_scene_qc_reports(project_dir, manifest, min_score=min_score)
    if errors:
        print("Scene QC contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return int(HarnessExitCode.VALIDATION_ERROR)

    payload = {
        "status": "ok",
        "scene_count": len(manifest.scenes),
        "min_score": min_score,
    }
    print(json.dumps(payload))
    return int(HarnessExitCode.SUCCESS)


def print_scene_spec(project_dir: Path, manifest_path: Path, scene_id: str) -> int:
    if not manifest_path.exists():
        print(f"Error: scene manifest not found at '{manifest_path}'", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    manifest = load_scene_manifest(manifest_path)
    entry = next((scene for scene in manifest.scenes if scene.scene_id == scene_id), None)
    if entry is None:
        print(f"Error: scene_id '{scene_id}' not found in manifest", file=sys.stderr)
        return int(HarnessExitCode.POLICY_VIOLATION)

    payload = {
        "scene_id": scene_id,
        "scene_file": entry.scene_file,
        "scene_spec": build_scene_spec(entry),
    }
    print(json.dumps(payload))
    return int(HarnessExitCode.SUCCESS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Runtime phase contract helpers for narration/build_scenes/scene_qc.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare-scene-manifest")
    prepare_parser.add_argument("--project-dir", required=True)

    scaffold_parser = subparsers.add_parser("scaffold-scenes")
    scaffold_parser.add_argument("--project-dir", required=True)
    scaffold_parser.add_argument("--manifest-path")

    build_validate_parser = subparsers.add_parser("validate-build-scenes")
    build_validate_parser.add_argument("--project-dir", required=True)
    build_validate_parser.add_argument("--manifest-path")

    qc_validate_parser = subparsers.add_parser("validate-scene-qc")
    qc_validate_parser.add_argument("--project-dir", required=True)
    qc_validate_parser.add_argument("--manifest-path")
    qc_validate_parser.add_argument("--min-score", type=float, default=0.7)

    spec_parser = subparsers.add_parser("print-scene-spec")
    spec_parser.add_argument("--project-dir", required=True)
    spec_parser.add_argument("--manifest-path")
    spec_parser.add_argument("--scene-id", required=True)

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Error: project directory not found at '{project_dir}'", file=sys.stderr)
        sys.exit(int(HarnessExitCode.POLICY_VIOLATION))

    manifest_path = _resolve_manifest_path(project_dir, getattr(args, "manifest_path", None))

    try:
        if args.command == "prepare-scene-manifest":
            sys.exit(prepare_scene_manifest(project_dir))

        if args.command == "scaffold-scenes":
            sys.exit(scaffold_scenes(project_dir, manifest_path))

        if args.command == "validate-build-scenes":
            sys.exit(validate_build_scenes(project_dir, manifest_path))

        if args.command == "validate-scene-qc":
            sys.exit(validate_scene_qc(project_dir, manifest_path, args.min_score))

        if args.command == "print-scene-spec":
            sys.exit(print_scene_spec(project_dir, manifest_path, args.scene_id))

    except ValidationError as exc:
        print(f"Schema validation error: {exc}", file=sys.stderr)
        sys.exit(int(HarnessExitCode.SCHEMA_VIOLATION))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(int(HarnessExitCode.VALIDATION_ERROR))
    except Exception as exc:
        print(f"Runtime contract helper error: {exc}", file=sys.stderr)
        sys.exit(int(HarnessExitCode.INFRASTRUCTURE_ERROR))


if __name__ == "__main__":
    main()
