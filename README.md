![Wet Donkey Banner](assests/wet_donkey_readme_banner.jpeg)

# Wet Donkey

Wet Donkey is a deterministic, script-orchestrated pipeline that converts a topic string into a fully narrated [Manim](https://www.manim.community/) video with minimal human intervention.

This project uses the xAI Responses API for stateful, multi-turn conversations, a Collections-based RAG for training data, and API-enforced structured outputs to automate the creation of educational animations.

## Features

- **Bash Orchestration**: A stateful pipeline managed by shell scripts.
- **xAI Responses API**: Deep integration with `xai_sdk` for structured, stateful LLM interactions.
- **Collections-based RAG**: Utilizes a training corpus for in-context learning and pattern reuse.
- **Manim Animation**: Renders 1440p60 animations using Manim Community Edition.
- **TTS Integration**: Caches text-to-speech voiceovers.
- **Automated Workflow**: From a single topic string to a final `.mp4` video.

## Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | Bash (`set -Eeuo pipefail`) |
| Python Version | 3.13 (enforced) |
| LLM Integration | `xai_sdk` (Responses API) |
| Training Corpus | xAI Collections API |
| Animation Engine | Manim Community Edition |
| Voice Synthesis | Qwen TTS (or similar) |
| Video Assembly | FFmpeg |

## Getting Started

### Prerequisites

- Python 3.13
- `pip` for installing Python packages
- `ffmpeg`
- `jq` (for a few scripts)
- An account with [xAI](https.x.ai) to obtain API keys.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/zfifteen/wet-donkey.git
    cd wet-donkey
    ```

2.  **Set up the environment:**
    Create a `.env` file by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and add your xAI API keys:
    ```
    XAI_API_KEY="YOUR_XAI_API_KEY"
    XAI_MANAGEMENT_API_KEY="YOUR_XAI_MANAGEMENT_API_KEY"
    ```

3.  **Install dependencies:**
    A `requirements.txt` file should be created. Install it using pip:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

The main entrypoint to the pipeline is the `create_video.sh` script.

```bash
./scripts/create_video.sh <project_name> --topic "A short explanation of black holes"
```

-   `<project_name>`: A unique name for your video project. All artifacts will be stored in `projects/<project_name>/`.
-   `--topic`: The topic string that will be used to generate the video plan.

The script will initialize the project, create the necessary training collections via the API, and generate a video plan.

The pipeline has a manual approval gate after the planning phase. To continue the process, you must manually advance the state as instructed by the script output.

## Directory Structure

```text
wet-donkey/
├── src/                  # Production Python packages
│   ├── harness/          # xAI Responses API harness package
│   ├── wet_donkey/       # Manim scene helpers package
│   └── wet_donkey_voice/ # TTS services package
├── scripts/              # Orchestration and utility scripts
├── projects/             # Runtime artifacts (gitignored)
└── tests/                # Tests
```

## How It Works

The pipeline is a state machine orchestrated by `scripts/build_video.sh`. The current phase of a project is stored in `projects/<project_name>/project_state.json`.

The main phases are:
1.  **init**: Creates the project and initializes the xAI Collections for the training corpus.
2.  **plan**: Calls the xAI API to generate a structured video plan from the topic.
3.  **review**: A manual gate where the user can review and approve the plan.
4.  **narration**: Generates the voiceover script for each scene.
5.  **build_scenes**: Generates the Manim code for each scene, using the training corpus for context.
6.  **scene_qc**: A quality control phase.
7.  **final_render**: Renders all scenes with Manim.
8.  **assemble**: Stitches the rendered video clips and voiceovers together using FFmpeg.
9.  **complete**: The final video is ready.
