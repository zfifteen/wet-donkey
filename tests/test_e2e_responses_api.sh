#!/bin/bash
set -Eeuo pipefail

# --- End-to-End Test for Responses API Pipeline ---
# This test runs a minimal version of the pipeline.
# It requires live API keys to be set in the environment.
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
PROJECT_NAME="e2e_test_$(date +%s)"
PROJECT_DIR="${ROOT_DIR}/projects/${PROJECT_NAME}"
TOPIC="The first 30 seconds of a video explaining the Pythagorean theorem"

# --- Functions ---
log_info() { echo "[E2E_TEST] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
cleanup() {
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

# 2. Run the main build script for the 'init' and 'plan' phases
log_info "Running build_video.sh to initialize project and generate plan..."
bash "${ROOT_DIR}/scripts/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"

# 3. Verify that the 'plan' phase completed
# The script will exit at the 'review' phase, so we check if the state was advanced to 'review'
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

# --- Success ---
log_info "E2E test completed successfully!"
exit 0
