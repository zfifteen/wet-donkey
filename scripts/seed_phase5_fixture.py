#!/usr/bin/env python3.13
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

_media_pipeline = importlib.import_module("harness.contracts.media_pipeline")
duration_tolerance_seconds = _media_pipeline.duration_tolerance_seconds

_runtime_pipeline = importlib.import_module("harness.contracts.runtime_pipeline")
build_scene_manifest = _runtime_pipeline.build_scene_manifest
ensure_scene_scaffolds = _runtime_pipeline.ensure_scene_scaffolds
write_narration_script = _runtime_pipeline.write_narration_script
write_scene_manifest = _runtime_pipeline.write_scene_manifest
write_scene_qc_report = _runtime_pipeline.write_scene_qc_report

inject_scene_body_file = importlib.import_module("harness.contracts.scaffold").inject_scene_body_file

_state_contract = importlib.import_module("harness.contracts.state")
create_initial_state = _state_contract.create_initial_state
save_state_atomic = _state_contract.save_state_atomic
transition_state = _state_contract.transition_state
update_state_key = _state_contract.update_state_key

_narration_schema = importlib.import_module("harness.schemas.narration")
Narration = _narration_schema.Narration
NarrationScene = _narration_schema.NarrationScene

_plan_schema = importlib.import_module("harness.schemas.plan")
Plan = _plan_schema.Plan
Scene = _plan_schema.Scene

SceneQC = importlib.import_module("harness.schemas.scene_qc").SceneQC

DEFAULT_SCENE_COUNT = 12
DEFAULT_TARGET_PHASE = "scene_qc"
PHASE_SEQUENCE = ["scene_qc", "precache_voiceovers", "final_render", "assemble", "complete"]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_plan(scene_count: int) -> Plan:
    scenes = []
    for index in range(scene_count):
        scene_number = index + 1
        scenes.append(
            Scene(
                title=f"Scene {scene_number:02d}",
                description=f"Deterministic fixture content for scene {scene_number:02d}.",
                estimated_duration_seconds=30,
                visual_ideas=["axes", "labels"],
            )
        )

    return Plan(
        title="Phase 5 Fixture Plan",
        description="Deterministic fixture plan for phase execution smoke tests.",
        target_duration_seconds=max(480, scene_count * 30),
        scenes=scenes,
    )


def _build_narration(scene_count: int) -> Narration:
    scenes = []
    for index in range(scene_count):
        scene_number = index + 1
        scenes.append(
            NarrationScene(
                scene_title=f"Scene {scene_number:02d}",
                narration_text=f"Narration for scene {scene_number:02d} in the deterministic fixture.",
            )
        )

    return Narration(scenes=scenes)


def _seed_state(project_dir: Path, *, plan: Plan, narration: Narration, target_phase: str) -> None:
    state = create_initial_state(project_name=project_dir.name, topic="Phase 5 fixture topic")
    state = transition_state(state, "plan", actor="fixture_seed")
    state = update_state_key(state, "plan", plan.model_dump(mode="json"))
    state = transition_state(state, "review", actor="fixture_seed")
    state = transition_state(state, "narration", actor="fixture_seed")
    state = update_state_key(state, "narration", narration.model_dump(mode="json"))
    state = transition_state(state, "build_scenes", actor="fixture_seed")
    state = transition_state(state, "scene_qc", actor="fixture_seed")

    for phase in PHASE_SEQUENCE[1:]:
        if phase == target_phase:
            state = transition_state(state, phase, actor="fixture_seed")
            break
        if PHASE_SEQUENCE.index(target_phase) > PHASE_SEQUENCE.index(phase):
            state = transition_state(state, phase, actor="fixture_seed")

    save_state_atomic(project_dir / "project_state.json", state)


def _seed_scene_artifacts(project_dir: Path, *, plan: Plan, narration: Narration) -> tuple[int, Path, Path]:
    manifest = build_scene_manifest(plan, narration)
    manifest_path = write_scene_manifest(project_dir, manifest)
    narration_script_path = write_narration_script(project_dir, manifest)

    ensure_scene_scaffolds(project_dir, manifest)
    for scene in manifest.scenes:
        scene_path = project_dir / scene.scene_file
        inject_scene_body_file(
            scene_path,
            "self.wait(0.1)\n" "self.add(Text(\"fixture\", font_size=24).to_edge(UP))",
        )

        qc_result = SceneQC(
            scene_title=scene.scene_title,
            passed=True,
            score=0.95,
            issues=[],
        )
        write_scene_qc_report(project_dir, scene, qc_result)

    return len(manifest.scenes), manifest_path, narration_script_path


def _seed_media_artifacts(project_dir: Path) -> dict[str, str]:
    manifest_payload = json.loads((project_dir / "artifacts" / "scene_manifest.json").read_text(encoding="utf-8"))
    scenes = manifest_payload["scenes"]

    voice_assets = []
    render_scenes = []
    assembly_inputs = []
    scene_order = []

    expected_duration = 0.0

    for scene in scenes:
        scene_id = scene["scene_id"]
        scene_order.append(scene_id)

        duration_seconds = float(scene["narration_duration_seconds"])
        expected_duration += duration_seconds

        audio_rel = f"voice/{scene_id}.mp3"
        metadata_rel = f"voice/{scene_id}.mp3.json"
        video_rel = f"render/{scene_id}.mp4"
        cache_key = f"cache-{scene_id}"

        audio_path = project_dir / audio_rel
        video_path = project_dir / video_rel
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"VOICE")
        video_path.write_bytes(b"VIDEO")

        metadata_payload = {
            "contract_version": "1.0.0",
            "voice_id": "qwen-default",
            "cache_key": cache_key,
            "generation_mode": "generated",
            "degraded": False,
            "duration_seconds": duration_seconds,
            "audio_format": "mp3",
            "sample_rate_hz": 24000,
            "channels": 1,
            "text_sha256": hashlib.sha256(scene["narration_text"].encode("utf-8")).hexdigest(),
        }
        _write_json(project_dir / metadata_rel, metadata_payload)

        voice_assets.append(
            {
                "scene_id": scene_id,
                "audio_path": audio_rel,
                "metadata_path": metadata_rel,
                "cache_key": cache_key,
                "duration_seconds": duration_seconds,
                "generation_mode": "generated",
                "degraded": False,
            }
        )
        render_scenes.append(
            {
                "scene_id": scene_id,
                "video_path": video_rel,
                "audio_path": audio_rel,
                "video_duration_seconds": duration_seconds,
                "audio_duration_seconds": duration_seconds,
            }
        )
        assembly_inputs.append(
            {
                "scene_id": scene_id,
                "video_path": video_rel,
                "audio_path": audio_rel,
                "duration_seconds": duration_seconds,
            }
        )

    voice_manifest = {
        "contract_version": "1.0.0",
        "voice_id": "qwen-default",
        "fallback_allowed": False,
        "assets": voice_assets,
    }
    _write_json(project_dir / "artifacts" / "voice_manifest.json", voice_manifest)

    render_preconditions = {
        "contract_version": "1.0.0",
        "validated_gates": ["schema", "contract", "semantic", "runtime"],
        "voice_manifest_path": "artifacts/voice_manifest.json",
        "scene_sources": [scene["scene_file"] for scene in scenes],
        "tooling_preflight": True,
    }
    _write_json(project_dir / "artifacts" / "render_preconditions.json", render_preconditions)

    render_manifest = {
        "contract_version": "1.0.0",
        "run_id": "fixture-run",
        "scene_order": scene_order,
        "scenes": render_scenes,
    }
    _write_json(project_dir / "artifacts" / "render_manifest.json", render_manifest)

    tolerance = duration_tolerance_seconds(expected_duration)
    assembly_manifest = {
        "contract_version": "1.0.0",
        "run_id": "fixture-run",
        "output_path": "final_video.mp4",
        "scene_order": scene_order,
        "inputs": assembly_inputs,
        "expected_duration_seconds": expected_duration,
        "actual_duration_seconds": expected_duration,
        "duration_tolerance_seconds": tolerance,
        "degraded": False,
    }
    _write_json(project_dir / "artifacts" / "assembly_manifest.json", assembly_manifest)

    (project_dir / "final_video.mp4").write_bytes(b"FINAL")

    return {
        "voice_manifest": str(project_dir / "artifacts" / "voice_manifest.json"),
        "render_preconditions": str(project_dir / "artifacts" / "render_preconditions.json"),
        "render_manifest": str(project_dir / "artifacts" / "render_manifest.json"),
        "assembly_manifest": str(project_dir / "artifacts" / "assembly_manifest.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic Phase 5 fixture artifacts.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--scene-count", type=int, default=DEFAULT_SCENE_COUNT)
    parser.add_argument("--phase", choices=PHASE_SEQUENCE, default=DEFAULT_TARGET_PHASE)
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    if args.scene_count < 12:
        print("Error: --scene-count must be >= 12 to satisfy Plan schema", file=sys.stderr)
        sys.exit(1)

    plan = _build_plan(args.scene_count)
    narration = _build_narration(args.scene_count)

    _seed_state(project_dir, plan=plan, narration=narration, target_phase=args.phase)
    scene_count, manifest_path, narration_script_path = _seed_scene_artifacts(
        project_dir, plan=plan, narration=narration
    )
    media_paths = _seed_media_artifacts(project_dir)

    payload = {
        "status": "ok",
        "project_dir": str(project_dir),
        "phase": args.phase,
        "scene_count": scene_count,
        "scene_manifest": str(manifest_path),
        "narration_script": str(narration_script_path),
        "media_artifacts": media_paths,
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
