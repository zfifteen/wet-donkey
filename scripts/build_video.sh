#!/bin/bash
set -Eeuo pipefail

# --- Main Build Orchestrator ---

# --- Config ---
PYTHON_CMD="python3.13"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

PHASE_HANDLER_TABLE=$(cat <<'EOF'
init:handle_init
plan:handle_plan
review:handle_review
narration:handle_unimplemented
build_scenes:handle_unimplemented
scene_qc:handle_unimplemented
precache_voiceovers:handle_unimplemented
final_render:handle_unimplemented
assemble:handle_unimplemented
complete:handle_complete
EOF
)

# --- Logging ---
log_info() { echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2; }

# --- State Management ---
get_state() {
  $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" get --project-dir "$PROJECT_DIR" --key "$1"
}

set_state() {
  $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" set --project-dir "$PROJECT_DIR" --key "$1" --value "$2"
}

advance_phase() {
  local next_phase="$1"
  log_info "Advancing phase to '$next_phase'"
  set_state "phase" "$next_phase"
}

clear_phase_failures() {
  $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" clear-failures --project-dir "$PROJECT_DIR" --actor orchestrator >/dev/null
}

record_phase_failure() {
  local error_code="$1"
  local error_message="$2"
  local force_block="${3:-false}"

  if [ "$force_block" = "true" ]; then
    $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" fail \
      --project-dir "$PROJECT_DIR" \
      --error-code "$error_code" \
      --error-message "$error_message" \
      --actor orchestrator \
      --force-block >/dev/null
  else
    $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" fail \
      --project-dir "$PROJECT_DIR" \
      --error-code "$error_code" \
      --error-message "$error_message" \
      --actor orchestrator >/dev/null
  fi

  local phase_status
  phase_status=$(get_state "phase_status" || echo "active")
  if [ "$phase_status" = "blocked" ]; then
    log_error "Phase '$CURRENT_PHASE' is blocked. Review failure_context and resolve manually."
    return 2
  fi
  return 1
}

is_retryable_exit_code() {
  case "$1" in
    1|2|3) return 0 ;;
    *) return 1 ;;
  esac
}

run_with_failure_policy() {
  local description="$1"
  shift

  set +e
  "$@"
  local rc=$?
  set -e

  if [ "$rc" -eq 0 ]; then
    clear_phase_failures
    return 0
  fi

  local error_code="INFRASTRUCTURE_ERROR"
  local force_block="false"
  case "$rc" in
    2) error_code="VALIDATION_ERROR" ;;
    3) error_code="SCHEMA_VIOLATION" ;;
    4) error_code="POLICY_VIOLATION"; force_block="true" ;;
    5) error_code="MANUAL_GATE_REQUIRED"; force_block="true" ;;
  esac

  local msg="$description failed with exit code $rc"
  if is_retryable_exit_code "$rc"; then
    record_phase_failure "$error_code" "$msg" "$force_block" || return $? 
    log_error "$msg"
    return "$rc"
  fi

  record_phase_failure "$error_code" "$msg" "true" || return $?
  log_error "$msg"
  return "$rc"
}

resolve_phase_handler() {
  local phase="$1"
  local line p h
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    p=${line%%:*}
    h=${line#*:}
    if [ "$p" = "$phase" ]; then
      echo "$h"
      return 0
    fi
  done <<EOF
$PHASE_HANDLER_TABLE
EOF
  return 1
}

# --- Phase Handlers ---

handle_init() {
  log_info "Initializing project and training corpus..."

  if [ ! -d "$PROJECT_DIR" ]; then
    run_with_failure_policy "project initialization" "$SCRIPT_DIR/new_project.sh" "$PROJECT_NAME" --topic "$TOPIC"
  fi

  if [[ -z "${XAI_MANAGEMENT_API_KEY:-}" ]]; then
    record_phase_failure "POLICY_VIOLATION" "XAI_MANAGEMENT_API_KEY is required for init phase" true
    return 1
  fi

  run_with_failure_policy "training corpus initialization" \
    "$PYTHON_CMD" "$SCRIPT_DIR/initialize_training_corpus.py" \
    --project-dir "$PROJECT_DIR" \
    --project-name "$PROJECT_NAME"

  advance_phase "plan"
}

handle_plan() {
  log_info "Generating video plan..."
  if [[ -z "${XAI_API_KEY:-}" ]]; then
    record_phase_failure "POLICY_VIOLATION" "XAI_API_KEY is required for plan phase" true
    return 1
  fi

  run_with_failure_policy "plan generation" \
    "$PYTHON_CMD" -m harness.cli \
    --phase "plan" \
    --project-dir "$PROJECT_DIR" \
    --topic "$TOPIC"

  log_info "Plan generated. Review and approve to continue."
  advance_phase "review"
}

handle_review() {
  log_info "Waiting for manual plan review and approval."
  log_info "To proceed, manually advance the phase to 'narration' by running:"
  echo
  echo "python3.13 scripts/update_project_state.py set --project-dir \"$PROJECT_DIR\" --key phase --value narration"
  echo
  return 0
}

handle_unimplemented() {
  record_phase_failure "INFRASTRUCTURE_ERROR" "Phase '$CURRENT_PHASE' handler is not yet implemented" false
  return 1
}

handle_complete() {
  log_info "Project already in complete phase. Nothing to do."
  return 0
}

run_current_phase() {
  local handler
  if ! handler=$(resolve_phase_handler "$CURRENT_PHASE"); then
    record_phase_failure "POLICY_VIOLATION" "Unknown phase: $CURRENT_PHASE" true
    return 1
  fi

  "$handler"
}

# --- Main Loop ---
main() {
  if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <project_name> [--topic \"Your video topic\"]"
    exit 1
  fi

  PROJECT_NAME=$1
  shift

  if [ "${1:-}" = "--topic" ]; then
    TOPIC=$2
  else
    if [ -f "projects/$PROJECT_NAME/project_state.json" ]; then
      TOPIC=$(jq -r .topic "projects/$PROJECT_NAME/project_state.json")
    else
      log_error "Topic not provided and project does not exist. Use --topic."
      exit 1
    fi
  fi

  export PROJECT_DIR="$ROOT_DIR/projects/$PROJECT_NAME"
  export PYTHONPATH="$ROOT_DIR/src"

  CURRENT_PHASE=$(get_state "phase" || echo "init")
  local phase_status
  phase_status=$(get_state "phase_status" || echo "active")

  log_info "Current project phase is: $CURRENT_PHASE (status=$phase_status)"

  if [ "$phase_status" = "blocked" ]; then
    log_error "Current phase is blocked. Resolve failure_context then clear failures before resuming."
    exit 2
  fi

  run_current_phase
  log_info "Phase '$CURRENT_PHASE' finished."
}

# --- Entrypoint ---
main "$@"
