# harness_responses/cli.py
import argparse
import sys
import json
from pathlib import Path

from .session import PipelineTrainingSession
from .client import generate_plan, generate_scene, repair_scene
from .parser import SemanticValidationError

def write_plan(plan, project_dir):
    """Saves the generated plan to project_state.json"""
    project_dir = Path(project_dir)
    state_file = project_dir / "project_state.json"
    
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        state = {}
        
    state['plan'] = plan.model_dump()
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Plan written to {state_file}")

def inject_scene_body(scene_body, scene_file):
    """Injects the generated Python code into the scene file."""
    scene_file = Path(scene_file)
    if not scene_file.exists():
        raise FileNotFoundError(f"Scene file not found: {scene_file}")

    content = scene_file.read_text()
    
    # Replace the placeholder with the generated code
    # Simple replacement for now, could be more robust
    start_marker = "# SLOT_START:scene_body"
    end_marker = "# SLOT_END:scene_body"
    
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    
    if start_index == -1 or end_index == -1:
        raise ValueError("Scene file does not contain scene_body SLOT markers.")

    new_content = (
        content[:start_index + len(start_marker)] +
        "
" +
        scene_body +
        "
    " +
        content[end_index:]
    )
    
    scene_file.write_text(new_content)
    print(f"Scene body injected into {scene_file}")


def main():
    parser = argparse.ArgumentParser(description="xAI Responses API harness")
    parser.add_argument("--phase", required=True, choices=[
        "plan", "narration", "build_scenes", "scene_qc", "scene_repair"
    ])
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--topic", help="Topic for the video plan")
    parser.add_argument("--scene-file", help="For scene-specific phases")
    parser.add_argument("--scene-spec", help="JSON string of the scene specification for building")
    parser.add_argument("--retry-context", help="Error context from previous attempt")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Load or create session
    try:
        session = PipelineTrainingSession.from_project(args.project_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("Dry run mode. No API calls will be made.")
        sys.exit(0)

    try:
        if args.phase == "plan":
            if not args.topic:
                print("Error: --topic is required for the 'plan' phase.", file=sys.stderr)
                sys.exit(1)
            result = generate_plan(session, args.topic, args.retry_context)
            write_plan(result, args.project_dir)
        
        elif args.phase == "build_scenes":
            if not args.scene_spec or not args.scene_file:
                print("Error: --scene-spec and --scene-file are required for 'build_scenes'.", file=sys.stderr)
                sys.exit(1)
            scene_spec = json.loads(args.scene_spec)
            result = generate_scene(session, scene_spec, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)

        elif args.phase == "scene_repair":
            if not args.retry_context or not args.scene_file:
                print("Error: --retry-context and --scene-file are required for 'scene_repair'.", file=sys.stderr)
                sys.exit(1)
            result = repair_scene(session, args.scene_file, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)
            
        else:
            print(f"Phase '{args.phase}' is not yet implemented.", file=sys.stderr)
            sys.exit(1)

        sys.exit(0)

    except SemanticValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(2)  # Exit code for retryable semantic error
    
    except Exception as e:
        print(f"Harness Error: {e}", file=sys.stderr)
        sys.exit(1)  # General error

if __name__ == "__main__":
    main()
