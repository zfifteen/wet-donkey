#!/bin/bash
set -Eeuo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")
WITH_LIVE_API=0
FAILURES=0
TOTAL_STEPS=3

usage() {
  echo "Usage: $0 [--with-live-api]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-live-api)
      WITH_LIVE_API=1
      TOTAL_STEPS=4
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[LOCAL_GATES] Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

log_info() { echo "[LOCAL_GATES] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

run_step() {
  local step_name="$1"
  shift

  log_info "START ${step_name}"
  if "$@"; then
    log_info "PASS  ${step_name}"
    return 0
  fi

  log_info "FAIL  ${step_name}"
  return 1
}

run_step "contract and harness tests" \
  python3.13 -m pytest -q tests/contracts tests/harness tests/test_training_corpus_upload.py || FAILURES=$((FAILURES + 1))

run_step "prompt schema alignment" \
  python3.13 "$ROOT_DIR/scripts/check_prompt_schema_alignment.py" || FAILURES=$((FAILURES + 1))

run_step "fixture e2e smoke" \
  bash "$ROOT_DIR/tests/test_e2e_fixture_pipeline.sh" || FAILURES=$((FAILURES + 1))

if [[ "$WITH_LIVE_API" -eq 1 ]]; then
  if [[ -z "${XAI_API_KEY:-}" ]] || [[ -z "${XAI_MANAGEMENT_API_KEY:-}" ]]; then
    log_info "FAIL  live API e2e smoke"
    log_info "XAI_API_KEY and XAI_MANAGEMENT_API_KEY are required when --with-live-api is enabled"
    FAILURES=$((FAILURES + 1))
  else
    run_step "live API e2e smoke" \
      bash "$ROOT_DIR/tests/test_e2e_responses_api.sh" || FAILURES=$((FAILURES + 1))
  fi
fi

PASSED=$((TOTAL_STEPS - FAILURES))
log_info "SUMMARY passed=${PASSED} failed=${FAILURES} total=${TOTAL_STEPS}"

if [[ "$FAILURES" -gt 0 ]]; then
  exit 1
fi

exit 0
