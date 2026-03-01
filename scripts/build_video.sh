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
precache_voiceovers:handle_precache_voiceovers
final_render:handle_final_render
assemble:handle_assemble
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
  $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" set --project-dir "$PROJECT_DIR" --key "$1" --value "$2" --actor orchestrator
}

advance_phase() {
  local next_phase="$1"
  log_info "Advancing phase to '$next_phase'"
  set_state "phase" "$next_phase"
}

clear_phase_failures() {
  $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" clear-failures --project-dir "$PROJECT_DIR" --actor orchestrator >/dev/null
}

emit_phase_event() {
  local event_type="$1"
  local attempt="$2"
  local message="${3:-}"
  local next_action="${4:-}"

  if [ ! -d "$PROJECT_DIR" ]; then
    return 0
  fi

  local args=(
    "$PYTHON_CMD" "$SCRIPT_DIR/update_project_state.py" log-event
    --project-dir "$PROJECT_DIR"
    --event-type "$event_type"
    --phase "$CURRENT_PHASE"
    --attempt "$attempt"
    --actor orchestrator
  )

  if [ -n "$message" ]; then
    args+=(--message "$message")
  fi
  if [ -n "$next_action" ]; then
    args+=(--next-action "$next_action")
  fi

  "${args[@]}" >/dev/null
}

record_phase_failure() {
  local error_code="$1"
  local error_message="$2"
  local gate="${3:-runtime}"
  local owner_component="${4:-orchestrator}"
  local retryable="${5:-true}"
  local force_block="${6:-false}"
  local error_signature="${7:-}"
  local attempt_delta="${8:-}"
  local evidence_token="${9:-}"

  if [ "$force_block" = "true" ]; then
    $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" fail \
      --project-dir "$PROJECT_DIR" \
      --error-code "$error_code" \
      --error-message "$error_message" \
      --gate "$gate" \
      --owner-component "$owner_component" \
      --retryable "$retryable" \
      --error-signature "$error_signature" \
      --attempt-delta "$attempt_delta" \
      --evidence-token "$evidence_token" \
      --actor orchestrator \
      --force-block >/dev/null
  else
    $PYTHON_CMD "$SCRIPT_DIR/update_project_state.py" fail \
      --project-dir "$PROJECT_DIR" \
      --error-code "$error_code" \
      --error-message "$error_message" \
      --gate "$gate" \
      --owner-component "$owner_component" \
      --retryable "$retryable" \
      --error-signature "$error_signature" \
      --attempt-delta "$attempt_delta" \
      --evidence-token "$evidence_token" \
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

schema_violation_retryable_for_phase() {
  case "$1" in
    plan|narration|build_scenes|scene_qc) return 0 ;;
    *) return 1 ;;
  esac
}

classify_exit_code() {
  local rc="$1"
  local phase="$2"

  FAILURE_ERROR_CODE="INFRASTRUCTURE_ERROR"
  FAILURE_GATE="runtime"
  FAILURE_OWNER="harness"
  FAILURE_RETRYABLE="true"
  FAILURE_FORCE_BLOCK="false"

  case "$rc" in
    1)
      FAILURE_ERROR_CODE="INFRASTRUCTURE_ERROR"
      FAILURE_GATE="runtime"
      FAILURE_OWNER="harness"
      FAILURE_RETRYABLE="true"
      ;;
    2)
      FAILURE_ERROR_CODE="VALIDATION_ERROR"
      FAILURE_GATE="semantic"
      FAILURE_OWNER="parser"
      FAILURE_RETRYABLE="true"
      ;;
    3)
      FAILURE_ERROR_CODE="SCHEMA_VIOLATION"
      FAILURE_GATE="schema"
      FAILURE_OWNER="harness"
      if schema_violation_retryable_for_phase "$phase"; then
        FAILURE_RETRYABLE="true"
      else
        FAILURE_RETRYABLE="false"
      fi
      ;;
    4)
      FAILURE_ERROR_CODE="POLICY_VIOLATION"
      FAILURE_GATE="contract"
      FAILURE_OWNER="orchestrator"
      FAILURE_RETRYABLE="false"
      FAILURE_FORCE_BLOCK="true"
      ;;
    5)
      FAILURE_ERROR_CODE="MANUAL_GATE_REQUIRED"
      FAILURE_GATE="assembly"
      FAILURE_OWNER="orchestrator"
      FAILURE_RETRYABLE="false"
      FAILURE_FORCE_BLOCK="true"
      ;;
    *)
      FAILURE_ERROR_CODE="INFRASTRUCTURE_ERROR"
      FAILURE_GATE="runtime"
      FAILURE_OWNER="harness"
      FAILURE_RETRYABLE="false"
      FAILURE_FORCE_BLOCK="true"
      ;;
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

  classify_exit_code "$rc" "$CURRENT_PHASE"

  local msg="$description failed with exit code $rc"
  local signature="${CURRENT_PHASE}:${FAILURE_ERROR_CODE}:${description}"
  local retry_delta="${WD_RETRY_DELTA:-}"
  local evidence_token="${WD_RETRY_EVIDENCE_TOKEN:-}"

  if [ "$FAILURE_RETRYABLE" = "true" ] && [ "$FAILURE_FORCE_BLOCK" != "true" ]; then
    record_phase_failure \
      "$FAILURE_ERROR_CODE" \
      "$msg" \
      "$FAILURE_GATE" \
      "$FAILURE_OWNER" \
      "$FAILURE_RETRYABLE" \
      "$FAILURE_FORCE_BLOCK" \
      "$signature" \
      "$retry_delta" \
      "$evidence_token" || return $?
    log_error "$msg"
    return "$rc"
  fi

  record_phase_failure \
    "$FAILURE_ERROR_CODE" \
    "$msg" \
    "$FAILURE_GATE" \
    "$FAILURE_OWNER" \
    "$FAILURE_RETRYABLE" \
    "true" \
    "$signature" \
    "$retry_delta" \
    "$evidence_token" || return $?
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
    record_phase_failure \
      "POLICY_VIOLATION" \
      "XAI_MANAGEMENT_API_KEY is required for init phase" \
      "contract" \
      "orchestrator" \
      "false" \
      "true"
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
    record_phase_failure \
      "POLICY_VIOLATION" \
      "XAI_API_KEY is required for plan phase" \
      "contract" \
      "orchestrator" \
      "false" \
      "true"
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

handle_precache_voiceovers() {
  log_info "Validating voice manifest and cached voiceover assets..."

  run_with_failure_policy "voice manifest validation" \
    "$PYTHON_CMD" "$SCRIPT_DIR/validate_media_pipeline.py" \
    validate-voice-manifest \
    --project-dir "$PROJECT_DIR"

  advance_phase "final_render"
}

handle_final_render() {
  log_info "Validating render preconditions..."

  run_with_failure_policy "render preconditions validation" \
    "$PYTHON_CMD" "$SCRIPT_DIR/validate_media_pipeline.py" \
    validate-render-preconditions \
    --project-dir "$PROJECT_DIR"

  log_info "Render preconditions validated."
  advance_phase "assemble"
}

handle_assemble() {
  log_info "Validating assembly manifest and final output..."

  run_with_failure_policy "assembly contract verification" \
    "$PYTHON_CMD" "$SCRIPT_DIR/validate_media_pipeline.py" \
    validate-assembly \
    --project-dir "$PROJECT_DIR"

  log_info "Assembly contracts validated."
  advance_phase "complete"
}

handle_unimplemented() {
  record_phase_failure \
    "INFRASTRUCTURE_ERROR" \
    "Phase '$CURRENT_PHASE' handler is not yet implemented" \
    "runtime" \
    "orchestrator" \
    "true" \
    "false"
  return 1
}

handle_complete() {
  log_info "Project already in complete phase. Nothing to do."
  return 0
}

run_current_phase() {
  local handler
  if ! handler=$(resolve_phase_handler "$CURRENT_PHASE"); then
    record_phase_failure \
      "POLICY_VIOLATION" \
      "Unknown phase: $CURRENT_PHASE" \
      "contract" \
      "orchestrator" \
      "false" \
      "true"
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

  local attempt_counters_json
  attempt_counters_json=$(get_state "attempt_counters" || echo "{}")
  local prior_attempt_count
  prior_attempt_count=$(echo "$attempt_counters_json" | jq -r --arg phase "$CURRENT_PHASE" '.[$phase] // 0' 2>/dev/null || echo "0")
  local phase_attempt
  phase_attempt=$((prior_attempt_count + 1))

  log_info "Current project phase is: $CURRENT_PHASE (status=$phase_status)"

  if [ "$phase_status" = "blocked" ]; then
    emit_phase_event "phase_blocked" "$phase_attempt" "phase already blocked at entry" "resolve failure_context before resume"
    log_error "Current phase is blocked. Resolve failure_context then clear failures before resuming."
    exit 2
  fi

  emit_phase_event "phase_start" "$phase_attempt"
  run_current_phase
  emit_phase_event "phase_success" "$phase_attempt"
  log_info "Phase '$CURRENT_PHASE' finished."
}

# --- Entrypoint ---
main "$@"
