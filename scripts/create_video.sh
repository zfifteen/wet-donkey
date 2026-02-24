#!/bin/bash
set -Eeuo pipefail

# --- Usage ---
# ./scripts/create_video.sh <project_name> --topic "Standing waves explained visually"
# ----------------

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <project_name> --topic "Your video topic""
    exit 1
fi

PROJECT_NAME=$1
TOPIC=$3
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR_ABS=$(pwd)/projects/$PROJECT_NAME

echo "Starting video creation for project: ${PROJECT_NAME}"
echo "Topic: ${TOPIC}"

# Call the main build orchestrator
# It will handle project creation and the entire pipeline
bash "${SCRIPT_DIR}/build_video.sh" "$PROJECT_NAME" --topic "$TOPIC"

echo "Build process initiated."
echo "Final output will be in ${PROJECT_DIR_ABS}/final_video.mp4"
