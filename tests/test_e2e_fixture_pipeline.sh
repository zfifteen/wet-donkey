#!/bin/bash
set -Eeuo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")
PROJECT_NAME="e2e_fixture_$(date +%s)"
PROJECT_DIR="$ROOT_DIR/projects/$PROJECT_NAME"
TOPIC="Phase 5 deterministic fixture topic"

log_info() { echo "[E2E_FIXTURE] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

cleanup() {
  rm -rf "$PROJECT_DIR"
}
trap cleanup EXIT

log_info "Bootstrapping .env from Flaming Horse source"
python3.13 "$ROOT_DIR/scripts/bootstrap_env_from_fh.py" \
  --target-env "$ROOT_DIR/.env" \
  --template-env "$ROOT_DIR/.env.example" \
  --source-env "/Users/velocityworks/IdeaProjects/flaming-horse/.env"

log_info "Seeding deterministic Phase 5 fixture project"
python3.13 "$ROOT_DIR/scripts/seed_phase5_fixture.py" \
  --project-dir "$PROJECT_DIR" \
  --scene-count 12 \
  --phase scene_qc

log_info "Validating runtime contracts before post-QC phase execution"
python3.13 "$ROOT_DIR/scripts/runtime_phase_contracts.py" validate-build-scenes --project-dir "$PROJECT_DIR"
python3.13 "$ROOT_DIR/scripts/runtime_phase_contracts.py" validate-scene-qc --project-dir "$PROJECT_DIR"

log_info "Advancing deterministic handoff from scene_qc to precache_voiceovers"
python3.13 "$ROOT_DIR/scripts/update_project_state.py" set \
  --project-dir "$PROJECT_DIR" \
  --key phase \
  --value precache_voiceovers \
  --actor orchestrator-fixture

log_info "Running orchestrator for precache_voiceovers"
bash "$ROOT_DIR/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"
phase_after_precache=$(python3.13 "$ROOT_DIR/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase)
if [[ "$phase_after_precache" != "final_render" ]]; then
  echo "[ERROR] Expected phase final_render after precache_voiceovers, got '$phase_after_precache'"
  exit 1
fi

log_info "Running orchestrator for final_render"
bash "$ROOT_DIR/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"
phase_after_render=$(python3.13 "$ROOT_DIR/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase)
if [[ "$phase_after_render" != "assemble" ]]; then
  echo "[ERROR] Expected phase assemble after final_render, got '$phase_after_render'"
  exit 1
fi

log_info "Running orchestrator for assemble"
bash "$ROOT_DIR/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"
final_phase=$(python3.13 "$ROOT_DIR/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase)
if [[ "$final_phase" != "complete" ]]; then
  echo "[ERROR] Expected phase complete, got '$final_phase'"
  exit 1
fi

phase_status=$(python3.13 "$ROOT_DIR/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase_status)
if [[ "$phase_status" != "complete" ]]; then
  echo "[ERROR] Expected phase_status complete, got '$phase_status'"
  exit 1
fi

log_info "Validating observability event stream"
python3.13 - "$PROJECT_DIR" <<'PY'
import json
import sys
from pathlib import Path

project_dir = Path(sys.argv[1])
log_path = project_dir / "log" / "events.jsonl"
if not log_path.exists():
    raise SystemExit("events.jsonl not found")

entries = []
for line in log_path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        entries.append(json.loads(line))

required_phases = ("precache_voiceovers", "final_render", "assemble")
required_types = ("phase_start", "phase_success")

for phase in required_phases:
    for event_type in required_types:
        if not any(e.get("phase") == phase and e.get("event_type") == event_type for e in entries):
            raise SystemExit(f"missing required event {event_type} for phase {phase}")

if any(e.get("event_type") == "phase_failure" for e in entries):
    raise SystemExit("unexpected phase_failure event in deterministic fixture run")
PY

log_info "Deterministic fixture e2e smoke test passed"
