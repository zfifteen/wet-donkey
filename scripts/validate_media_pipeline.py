from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys

from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

media_contracts = importlib.import_module("harness.contracts.media_pipeline")
load_voice_manifest = media_contracts.load_voice_manifest
load_render_preconditions = media_contracts.load_render_preconditions
load_render_manifest = media_contracts.load_render_manifest
load_assembly_manifest = media_contracts.load_assembly_manifest
validate_voice_manifest_files = media_contracts.validate_voice_manifest_files
validate_render_preconditions = media_contracts.validate_render_preconditions
validate_render_manifest = media_contracts.validate_render_manifest
validate_assembly_inputs = media_contracts.validate_assembly_inputs
verify_final_output = media_contracts.verify_final_output


def _resolve_with_project(project_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_dir / path


def validate_voice_manifest(project_dir: Path, manifest_path: str) -> int:
    manifest_file = _resolve_with_project(project_dir, manifest_path)
    if not manifest_file.exists():
        print(f"Error: voice manifest not found at '{manifest_file}'", file=sys.stderr)
        return 2

    manifest = load_voice_manifest(manifest_file)
    validate_voice_manifest_files(manifest, project_dir=project_dir)
    print(json.dumps({"status": "ok", "type": "voice_manifest", "path": str(manifest_file)}))
    return 0


def validate_render(project_dir: Path, preconditions_path: str) -> int:
    preconditions_file = _resolve_with_project(project_dir, preconditions_path)
    if not preconditions_file.exists():
        print(f"Error: render preconditions not found at '{preconditions_file}'", file=sys.stderr)
        return 2

    preconditions = load_render_preconditions(preconditions_file)
    voice_manifest = validate_render_preconditions(preconditions, project_dir=project_dir)
    print(
        json.dumps(
            {
                "status": "ok",
                "type": "render_preconditions",
                "path": str(preconditions_file),
                "voice_assets": len(voice_manifest.assets),
            }
        )
    )
    return 0


def validate_assembly(
    project_dir: Path,
    voice_manifest_path: str,
    render_manifest_path: str,
    assembly_manifest_path: str,
) -> int:
    voice_manifest_file = _resolve_with_project(project_dir, voice_manifest_path)
    render_manifest_file = _resolve_with_project(project_dir, render_manifest_path)
    assembly_manifest_file = _resolve_with_project(project_dir, assembly_manifest_path)

    missing = [
        str(path)
        for path in (voice_manifest_file, render_manifest_file, assembly_manifest_file)
        if not path.exists()
    ]
    if missing:
        print(f"Error: required manifest file(s) missing: {', '.join(missing)}", file=sys.stderr)
        return 2

    voice_manifest = load_voice_manifest(voice_manifest_file)
    validate_voice_manifest_files(voice_manifest, project_dir=project_dir)

    render_manifest = load_render_manifest(render_manifest_file)
    validate_render_manifest(render_manifest, voice_manifest=voice_manifest, project_dir=project_dir)

    assembly_manifest = load_assembly_manifest(assembly_manifest_file)
    validate_assembly_inputs(assembly_manifest, render_manifest=render_manifest, project_dir=project_dir)
    verify_final_output(assembly_manifest, project_dir=project_dir)

    print(
        json.dumps(
            {
                "status": "ok",
                "type": "assembly",
                "render_manifest": str(render_manifest_file),
                "assembly_manifest": str(assembly_manifest_file),
            }
        )
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate WD voice/render/assembly media contracts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    voice_parser = subparsers.add_parser("validate-voice-manifest")
    voice_parser.add_argument("--project-dir", required=True)
    voice_parser.add_argument(
        "--manifest-path",
        default="artifacts/voice_manifest.json",
        help="Path to voice manifest, relative to project-dir unless absolute",
    )

    render_parser = subparsers.add_parser("validate-render-preconditions")
    render_parser.add_argument("--project-dir", required=True)
    render_parser.add_argument(
        "--preconditions-path",
        default="artifacts/render_preconditions.json",
        help="Path to render preconditions manifest, relative to project-dir unless absolute",
    )

    assembly_parser = subparsers.add_parser("validate-assembly")
    assembly_parser.add_argument("--project-dir", required=True)
    assembly_parser.add_argument("--voice-manifest-path", default="artifacts/voice_manifest.json")
    assembly_parser.add_argument("--render-manifest-path", default="artifacts/render_manifest.json")
    assembly_parser.add_argument("--assembly-manifest-path", default="artifacts/assembly_manifest.json")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        print(f"Error: project directory not found at '{project_dir}'", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "validate-voice-manifest":
            sys.exit(validate_voice_manifest(project_dir, args.manifest_path))

        if args.command == "validate-render-preconditions":
            sys.exit(validate_render(project_dir, args.preconditions_path))

        if args.command == "validate-assembly":
            sys.exit(
                validate_assembly(
                    project_dir,
                    voice_manifest_path=args.voice_manifest_path,
                    render_manifest_path=args.render_manifest_path,
                    assembly_manifest_path=args.assembly_manifest_path,
                )
            )
    except ValidationError as exc:
        print(f"Schema validation error: {exc}", file=sys.stderr)
        sys.exit(3)
    except ValueError as exc:
        print(f"Contract validation error: {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"Unexpected media validation error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
