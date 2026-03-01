#!/bin/bash
set -Eeuo pipefail

# --- End-to-End Test for Responses API Pipeline ---
# This test runs a minimal live API flow through init and plan.
#
# Pre-requisites:
# - XAI_API_KEY must be set.
# - XAI_MANAGEMENT_API_KEY must be set.
# - Python 3.13 must be available as `python3.13`.
# - `jq` must be installed.
# ----------------------------------------------------

# --- Config ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")
PROJECT_NAME="${E2E_PROJECT_NAME:-e2e_test_$(date +%s)}"
PROJECT_DIR="${ROOT_DIR}/projects/${PROJECT_NAME}"
TOPIC="${E2E_TOPIC:-The first 30 seconds of a video explaining the Pythagorean theorem}"
KEEP_PROJECT="${E2E_KEEP_PROJECT:-0}"

# --- Functions ---
log_info() { echo "[E2E_TEST] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
cleanup() {
    if [[ "$KEEP_PROJECT" == "1" ]]; then
        log_info "Keeping test project directory: ${PROJECT_DIR}"
        return
    fi
    log_info "Cleaning up test project directory: ${PROJECT_DIR}"
    rm -rf "${PROJECT_DIR}"
}
trap cleanup EXIT

# --- Test Steps ---
log_info "Starting E2E test for project '${PROJECT_NAME}'"

# 1. Check for API keys
if [[ -z "${XAI_API_KEY:-}" ]] || [[ -z "${XAI_MANAGEMENT_API_KEY:-}" ]]; then
    echo "[ERROR] XAI_API_KEY and XAI_MANAGEMENT_API_KEY must be set for this test."
    exit 1
fi

# 2. Run the orchestrator through 'init' then 'plan'
log_info "Running build_video.sh for init..."
bash "${ROOT_DIR}/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"

phase_after_init=$(python3.13 "${ROOT_DIR}/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase)
if [[ "$phase_after_init" != "plan" ]]; then
    echo "[ERROR] Expected phase to be 'plan' after init, but got '$phase_after_init'."
    exit 1
fi

log_info "Running build_video.sh for plan..."
bash "${ROOT_DIR}/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"

# 3. Verify that the 'plan' phase finished
CURRENT_PHASE=$(python3.13 "${ROOT_DIR}/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key phase)
if [[ "$CURRENT_PHASE" != "review" ]]; then
    echo "[ERROR] Expected phase to be 'review', but got '$CURRENT_PHASE'."
    exit 1
fi
log_info "Phase correctly advanced to 'review'."

# 4. Verify the plan was created
PLAN_TITLE=$(python3.13 "${ROOT_DIR}/scripts/update_project_state.py" get --project-dir "$PROJECT_DIR" --key "plan" | jq -r .title)
if [[ -z "$PLAN_TITLE" ]]; then
    echo "[ERROR] Plan title is empty in project_state.json."
    exit 1
fi
log_info "Plan was successfully generated with title: '$PLAN_TITLE'"

# 5. Verify observability events for init and plan
python3.13 - "$PROJECT_DIR" <<'PY'
import json
import sys
from pathlib import Path

project_dir = Path(sys.argv[1])
events_path = project_dir / "log" / "events.jsonl"
if not events_path.exists():
    raise SystemExit("events.jsonl not found")

events = []
for line in events_path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        events.append(json.loads(line))

required_phases = ("init", "plan")
required_types = ("phase_start", "phase_success")

for phase in required_phases:
    for event_type in required_types:
        if not any(
            event.get("phase") == phase and event.get("event_type") == event_type
            for event in events
        ):
            raise SystemExit(f"missing required event {event_type} for phase {phase}")

if any(event.get("event_type") == "phase_failure" for event in events):
    raise SystemExit("unexpected phase_failure event found in events.jsonl")
PY
log_info "Observability assertions passed for init and plan."

# --- Success ---
log_info "E2E test finished successfully!"
exit 0
