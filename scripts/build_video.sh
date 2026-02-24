#!/bin/bash
set -Eeuo pipefail

# --- Main Build Orchestrator ---

# --- Config ---
# Using python3.13 as per spec
PYTHON_CMD="python3.13"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

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
    log_info "Advancing phase to '$1'"
    set_state "phase" "$1"
    # Append to history
    local history
    history=$(get_state "history")
    history=${history:-[]}
    history=$(echo "$history" | jq --arg phase "$1" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '. + [{"phase": $phase, "timestamp": $ts}]')
    set_state "history" "$history"
}

# --- Phase Handlers ---

handle_init() {
    log_info "Initializing project and training corpus..."
    
    # Create project directory and state if it doesn't exist
    if [ ! -d "$PROJECT_DIR" ]; then
        "$SCRIPT_DIR/new_project.sh" "$PROJECT_NAME" --topic "$TOPIC"
    fi
    
    # Check for XAI_MANAGEMENT_API_KEY
    if [[ -z "${XAI_MANAGEMENT_API_KEY:-}" ]]; then
        log_error "XAI_MANAGEMENT_API_KEY is not set. Cannot initialize collections."
        exit 1
    fi

    $PYTHON_CMD "$SCRIPT_DIR/initialize_training_corpus.py" \
        --project-dir "$PROJECT_DIR" \
        --project-name "$PROJECT_NAME"
    
    advance_phase "plan"
}

handle_plan() {
    log_info "Generating video plan..."
    # Check for XAI_API_KEY
    if [[ -z "${XAI_API_KEY:-}" ]]; then
        log_error "XAI_API_KEY is not set. Cannot generate plan."
        exit 1
    fi

    # Invoke the harness
    $PYTHON_CMD -m harness.cli \
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
    echo "python3.13 scripts/update_project_state.py set --project-dir "$PROJECT_DIR" --key phase --value narration"
    echo
    # This phase is a manual gate. The script will stop here.
    exit 0
}

# --- Main Loop ---
main() {
    if [ "$#" -lt 2 ]; then
        echo "Usage: $0 <project_name> [--topic "Your video topic"]"
        exit 1
    fi
    
    PROJECT_NAME=$1
    shift
    # Parse --topic argument
    if [ "${1:-}" == "--topic" ]; then
        TOPIC=$2
    else
        # If topic is not provided, try to get it from state
        if [ -f "projects/$PROJECT_NAME/project_state.json" ]; then
            TOPIC=$(jq -r .topic "projects/$PROJECT_NAME/project_state.json")
        else
            log_error "Topic not provided and project does not exist. Use --topic."
            exit 1
        fi
    fi

    export PROJECT_DIR="$ROOT_DIR/projects/$PROJECT_NAME"
    export PYTHONPATH="$ROOT_DIR/src"
    
    # Get current phase or default to 'init'
    local phase
    phase=$(get_state "phase" || echo "init")
    log_info "Current project phase is: $phase"

    case "$phase" in
        "init")
            handle_init
            ;;
        "plan")
            handle_plan
            ;;
        "review")
            handle_review
            ;;
        "narration" | "build_scenes" | "scene_qc" | "precache_voiceovers" | "final_render" | "assemble" | "complete")
            log_error "Phase '$phase' handler not implemented yet."
            exit 1
            ;;
        *)
            log_error "Unknown phase: $phase"
            exit 1
            ;;
    esac
    
    # If a phase handler succeeded, we might want to automatically run the next one
    # This can be added later to make the pipeline more automated.
    log_info "Phase '$phase' completed."
}

# --- Entrypoint ---
main "$@"
