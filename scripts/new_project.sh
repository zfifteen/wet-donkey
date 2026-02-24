#!/bin/bash
set -Eeuo pipefail

# --- Usage ---
# ./scripts/new_project.sh <project_name> --topic "Your video topic"
# ----------------

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <project_name> --topic "Your video topic""
    exit 1
fi

PROJECT_NAME=$1
TOPIC=$3
PROJECTS_ROOT="projects"
PROJECT_DIR="${PROJECTS_ROOT}/${PROJECT_NAME}"

if [ -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory '${PROJECT_DIR}' already exists."
    exit 1
fi

echo "Creating new project: ${PROJECT_NAME}"
mkdir -p "$PROJECT_DIR"
echo "Project directory created at '${PROJECT_DIR}'"

# Initial project state
cat > "${PROJECT_DIR}/project_state.json" << EOL
{
  "project_name": "${PROJECT_NAME}",
  "topic": "${TOPIC}",
  "phase": "init",
  "history": [
    {
      "phase": "init",
      "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    }
  ]
}
EOL

echo "Initial project_state.json created."
echo "Project '${PROJECT_NAME}' initialized successfully."
