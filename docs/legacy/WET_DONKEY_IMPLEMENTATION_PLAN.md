# Wet Donkey Implementation Plan

**Version:** 2.0  
**Date:** 2026-02-24  
**Repository:** `zfifteen/wet-donkey`

***

## Table of Contents

1. [Overview](#1-overview)
2. [xAI Responses API Integration](#2-xai-responses-api-integration)
3. [Technology Stack](#3-technology-stack)
4. [Directory Structure](#4-directory-structure)
5. [Pipeline State Machine](#5-pipeline-state-machine)
6. [Core Components](#6-core-components)
7. [Prompt Architecture](#7-prompt-architecture)
8. [Data Contracts](#8-data-contracts)
9. [Validation Gates](#9-validation-gates)
10. [Self-Healing and Retry Logic](#10-self-healing-and-retry-logic)
11. [Configuration and Environment Variables](#11-configuration-and-environment-variables)
12. [Harness Exit Codes](#12-harness-exit-codes)
13. [Logging and Observability](#13-logging-and-observability)
14. [Voice Policy](#14-voice-policy)
15. [Testing](#15-testing)
16. [Render and Assembly](#16-render-and-assembly)
17. [Stateful Training Integration](#17-stateful-training-integration)
18. [Known Constraints and Risk Areas](#18-known-constraints-and-risk-areas)

***

## 1. Overview

Flaming Horse is a **deterministic, script-orchestrated pipeline** that converts a topic string into a fully narrated Manim video (`final_video.mp4`) with minimal human intervention. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)

**New in v2.0:** Deep integration with xAI Responses API for stateful multi-turn conversations, Collections-based RAG for training data, and API-enforced structured outputs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/0d357dfd-fd14-473f-8302-cc93b3f39c8b/TECH_SPEC.md)

The pipeline integrates:

- **Bash orchestration** with stateful phase machine [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)
- **xAI Responses API** via `xai_sdk` for structured LLM interactions with 30-day conversation storage [arxiv](http://arxiv.org/pdf/2209.02552.pdf)
- **Collections-based training corpus** with semantic search and document retrieval [arxiv](https://arxiv.org/pdf/2305.09770.pdf)
- **Manim CE** for 1440p60 animation rendering [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)
- **Qwen TTS** cached voice clone [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)
- **FFmpeg** video assembly [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)

**Canonical user entrypoint:**

```bash
./scripts/create_video.sh <project_name> --topic "Standing waves explained visually"
```

**Output:** `projects/<project_name>/final_video.mp4`

***

## 2. xAI Responses API Integration

### 2.1 Core Architecture

The `harness_responses/` harness uses the xAI Responses API (`/v1/responses`) for stateful LLM interactions with guaranteed structured outputs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/0d357dfd-fd14-473f-8302-cc93b3f39c8b/TECH_SPEC.md)

**Key features leveraged:**

| Feature | Implementation | Benefit |
|---|---|---|
| Stateful conversations | `previous_response_id` parameter | 30-day server-side storage; no message resending [docs.x](https://docs.x.ai/developers/model-capabilities/text/comparison) |
| Structured outputs | `chat.parse()` + Pydantic schemas | API-enforced JSON schema compliance [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/0d357dfd-fd14-473f-8302-cc93b3f39c8b/TECH_SPEC.md) |
| Collections RAG | `collections_search()` tool | Semantic retrieval from training corpus [aihola](https://aihola.com/article/xai-grok-collections-api-launch) |
| Multi-turn agentic state | Server-side tool call preservation | Full context across repair loops [arxiv](http://arxiv.org/pdf/2209.02552.pdf) |
| Code execution | `code_execution()` tool | Runtime validation and data analysis |

### 2.2 Session Management

**Per-project training session** (extends stateful conversation across pipeline phases):

```python
class PipelineTrainingSession:
    """Manages stateful xAI Responses API interaction across pipeline phases"""
    
    def __init__(self, project_dir, collection_id):
        self.project_dir = Path(project_dir)
        self.collection_id = collection_id
        self.response_id = None  # Current response ID for continuation
        self.client = Client(api_key=os.getenv("XAI_API_KEY"))
        
        # Load or initialize session state
        self.session_file = self.project_dir / ".xai_session.json"
        self._load_session()
    
    def invoke_phase(self, phase_name, prompts, tools=None):
        """Invoke LLM for a pipeline phase with full state preservation"""
        
        # Create chat with tools
        chat = self.client.chat.create(
            model="grok-4-1-fast-reasoning",
            tools=tools or [
                collections_search(collection_ids=[self.collection_id]),
                code_execution()
            ],
            store_messages=True,  # 30-day retention
            previous_response_id=self.response_id  # Resume from last state
        )
        
        # Add phase-specific prompt
        chat.append(user(prompts["system"], prompts["user"]))
        
        # Stream response
        response = self._stream_with_monitoring(chat)
        
        # Update session state
        self.response_id = response.id
        self._save_session()
        
        return response
```

### 2.3 Training Corpus Management

**Collection setup for template library and generated artifacts:**

```python
def initialize_training_corpus(project_name):
    """Create Collections for template library and scene examples"""
    
    client = Client(api_key=os.getenv("XAI_API_KEY"))
    
    # Template library collection (reusable across projects)
    template_collection = client.collections.create(
        name="flaming-horse-templates",
        description="Kitchen sink patterns, scene helpers, visual reference docs"
    )
    
    # Upload template files with metadata
    for template_path in Path("harness/templates").glob("*.py"):
        with open(template_path, 'rb') as f:
            client.collections.upload_document(
                collection_id=template_collection.collection_id,
                name=template_path.name,
                data=f.read(),
                fields={
                    "type": "template",
                    "category": extract_category(template_path),
                    "patterns": extract_patterns(template_path)
                }
            )
    
    # Project-specific collection for generated scenes (learning corpus)
    project_collection = client.collections.create(
        name=f"{project_name}-scenes",
        description=f"Generated scene files and QC reports for {project_name}"
    )
    
    return template_collection, project_collection
```

### 2.4 Structured Output Schemas

**Phase-specific Pydantic models** (`harness_responses/schemas/`):

```python
# harness_responses/schemas/plan.py
from pydantic import BaseModel, Field
from typing import List

class Scene(BaseModel):
    title: str = Field(description="Scene title")
    description: str = Field(description="Educational content description")
    estimated_duration_seconds: int = Field(ge=20, le=45)
    visual_ideas: List[str] = Field(description="Animation concepts")

class Plan(BaseModel):
    title: str = Field(description="Video title")
    description: str = Field(description="Video overview")
    target_duration_seconds: int = Field(ge=480, le=960)
    scenes: List[Scene] = Field(min_items=12, max_items=24)

# harness_responses/schemas/scene_build.py
class SceneBuild(BaseModel):
    scene_body: str = Field(
        description="Python code for scene body (no imports, no class wrapper)"
    )
    reasoning: str = Field(
        description="Explanation of visual choices and animation strategy"
    )
```

**Usage in harness:**

```python
# harness_responses/client.py
from xai_sdk.chat import user
from .schemas.plan import Plan

def generate_plan(session, topic, retry_context=None):
    """Generate structured plan with API-enforced schema"""
    
    prompts = compose_prompts("plan", topic=topic, retry_context=retry_context)
    
    chat = session.client.chat.create(
        model="grok-4-fast",
        response_format=Plan,  # Pydantic model for structured output
        tools=[
            collections_search(collection_ids=[session.collection_id]),
            web_search()  # For topic research
        ],
        previous_response_id=session.response_id
    )
    
    chat.append(user(prompts["system"], prompts["user"]))
    response = chat.sample()
    
    # Parse structured output (guaranteed valid by API)
    plan = Plan.model_validate_json(response.content)
    
    # Update session state
    session.response_id = response.id
    session._save_session()
    
    return plan
```

***

## 3. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Orchestration | Bash (`set -Eeuo pipefail`) | Python 3.13 enforced [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| LLM Integration (primary) | `xai_sdk` via `/v1/responses` | `harness_responses/`, stateful API [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/0d357dfd-fd14-473f-8302-cc93b3f39c8b/TECH_SPEC.md) |
| LLM Integration (legacy) | HTTP to OpenAI-compatible `/chat/completions` | `harness/` fallback [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| Training corpus | xAI Collections API | Semantic search, 100MB per doc [arxiv](https://arxiv.org/pdf/2305.09770.pdf) |
| Animation engine | Manim Community Edition | 2560×1440, 60fps [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| Voice synthesis | Qwen/Qwen3-TTS-12Hz-1.7B-Base (local) | Cached, no fallback [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| Video assembly | FFmpeg | concat + `aresample=async=1` [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| State management | JSON + Python | `project_state.json` [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| Python version | 3.13 (enforced) |  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |
| Testing | pytest + bash smoke tests | No live API calls in standard suite [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md) |

***

## 4. Directory Structure

```text
flaming-horse/
├── scripts/                         # Orchestration and utilities
│   ├── build_video.sh               # Main orchestrator
│   ├── create_video.sh              # User entrypoint
│   ├── update_project_state.py      # State authority
│   ├── scaffold_scene.py            # Scene template generator
│   ├── initialize_training_corpus.py # NEW: Collections setup
│   ├── upload_scene_to_collection.py # NEW: Post-build artifact upload
│   └── ...
│
├── harness/                         # Legacy Chat Completions harness
│   ├── cli.py
│   ├── client.py
│   ├── prompts.py
│   ├── parser.py
│   └── prompts/                     # Phase-specific prompts
│
├── harness_responses/               # NEW: xAI Responses API harness
│   ├── cli.py                       # Argparse entry point
│   ├── client.py                    # Uses xai_sdk.chat
│   ├── session.py                   # PipelineTrainingSession class
│   ├── prompts.py                   # Prompt composition
│   ├── parser.py                    # Structured output validation
│   ├── schemas/                     # Pydantic models per phase
│   │   ├── plan.py
│   │   ├── narration.py
│   │   ├── scene_build.py
│   │   └── scene_qc.py
│   └── prompts/                     # Phase-specific prompt assets
│       ├── 00_plan/
│       ├── 02_narration/
│       ├── 04_build_scenes/
│       ├── 05_scene_qc/
│       └── 06_scene_repair/
│
├── flaming_horse/
│   └── scene_helpers.py             # Animation utilities
│
├── flaming_horse_voice/             # TTS services
│   ├── service_factory.py
│   └── qwen_cached.py
│
├── projects/                        # Runtime artifacts (gitignored)
│   └── <project_name>/
│       ├── .xai_session.json        # NEW: Session state
│       ├── .collections_metadata.json # NEW: Collection IDs
│       └── ...
│
└── tests/
```

***

## 5. Pipeline State Machine

```
init → plan → review → narration → build_scenes → scene_qc
     → precache_voiceovers → final_render → assemble → complete
```

**Enhanced phase tracking** in `project_state.json`:

```json
{
  "phase": "build_scenes",
  "xai_session": {
    "response_id": "resp_abc123",
    "template_collection_id": "coll_templates",
    "project_collection_id": "coll_proj_xyz",
    "conversation_turns": 14,
    "last_phase": "build_scenes"
  }
}
```

***

## 6. Core Components

### 6.1 Orchestrator Enhancements

**NEW: Collection initialization** (added to `handle_init`):

```bash
handle_init() {
    log_info "Initializing project and training corpus..."
    
    # Create project directory and state
    "$SCRIPT_DIR/new_project.sh" "$PROJECT_NAME" --topic "$TOPIC"
    
    # Initialize Collections
    if [[ "$FH_HARNESS" == "responses" ]]; then
        python3 "$SCRIPT_DIR/initialize_training_corpus.py" \
            --project-dir "$PROJECT_DIR" \
            --project-name "$PROJECT_NAME"
    fi
    
    advance_phase "plan"
}
```

**NEW: Post-build artifact upload** (added to `handle_build_scenes` after successful scene build):

```bash
# After scene validation succeeds
if [[ "$FH_HARNESS" == "responses" ]]; then
    python3 "$SCRIPT_DIR/upload_scene_to_collection.py" \
        --project-dir "$PROJECT_DIR" \
        --scene-file "$scene_file" \
        --qc-report "$PROJECT_DIR/scene_qc_report.md"
fi
```

### 6.2 Responses API Harness Architecture

**Entry point** (`harness_responses/cli.py`):

```python
def main():
    parser = argparse.ArgumentParser(description="xAI Responses API harness")
    parser.add_argument("--phase", required=True, choices=[
        "plan", "narration", "build_scenes", "scene_qc", "scene_repair"
    ])
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--scene-file", help="For scene-specific phases")
    parser.add_argument("--retry-context", help="Error context from previous attempt")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    # Load or create session
    session = PipelineTrainingSession.from_project(args.project_dir)
    
    # Execute phase
    try:
        if args.phase == "plan":
            result = generate_plan(session, state["topic"], args.retry_context)
            write_plan(result, args.project_dir)
        
        elif args.phase == "build_scenes":
            result = generate_scene(session, scene_spec, args.retry_context)
            inject_scene_body(result.scene_body, args.scene_file)
        
        # ... other phases
        
        sys.exit(0)
    
    except SemanticValidationError as e:
        log_error(f"Validation: {e}")
        sys.exit(2)  # Retryable
    
    except Exception as e:
        log_error(f"Harness error: {e}")
        sys.exit(1)  # General error
```

**Session class** (`harness_responses/session.py`):

```python
from xai_sdk import Client
from xai_sdk.tools import collections_search, code_execution, web_search

class PipelineTrainingSession:
    """Stateful session manager for xAI Responses API"""
    
    def __init__(self, project_dir, collection_ids, response_id=None):
        self.project_dir = Path(project_dir)
        self.collection_ids = collection_ids
        self.response_id = response_id
        self.client = Client(api_key=os.getenv("XAI_API_KEY"))
        self.session_file = self.project_dir / ".xai_session.json"
    
    @classmethod
    def from_project(cls, project_dir):
        """Load existing session or create new"""
        session_file = Path(project_dir) / ".xai_session.json"
        
        if session_file.exists():
            with open(session_file) as f:
                data = json.load(f)
            return cls(
                project_dir=project_dir,
                collection_ids=data["collection_ids"],
                response_id=data.get("response_id")
            )
        
        # Load collection IDs from metadata
        metadata_file = Path(project_dir) / ".collections_metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        return cls(
            project_dir=project_dir,
            collection_ids=[
                metadata["template_collection_id"],
                metadata["project_collection_id"]
            ]
        )
    
    def create_chat(self, phase, response_format=None):
        """Create stateful chat for phase"""
        tools = [
            collections_search(collection_ids=self.collection_ids),
            code_execution()
        ]
        
        # Add web search for research phases
        if phase in ["plan", "narration"]:
            tools.append(web_search())
        
        return self.client.chat.create(
            model="grok-4-1-fast-reasoning",
            tools=tools,
            store_messages=True,
            previous_response_id=self.response_id,
            response_format=response_format
        )
    
    def update_response_id(self, response_id):
        """Update session state after successful call"""
        self.response_id = response_id
        self._save_session()
    
    def _save_session(self):
        """Persist session state"""
        with open(self.session_file, 'w') as f:
            json.dump({
                "response_id": self.response_id,
                "collection_ids": self.collection_ids,
                "updated_at": datetime.utcnow().isoformat()
            }, f, indent=2)
```

***

## 7. Prompt Architecture

### 7.1 Responses Harness Prompts

**Directory:** `harness_responses/prompts/<phase>/`

Each phase directory contains:
- `system.md` with training instructions
- `user.md` with task-specific prompt
- `examples.json` (optional) with few-shot examples
- `constraints.yaml` with phase-specific rules

**Example: `harness_responses/prompts/04_build_scenes/system.md`:**

```markdown
# Scene Generation Agent

You are a Manim scene code generator with access to:

1. **Template Library** (via Collections search): Kitchen sink patterns, proven animation techniques
2. **Previous Scenes** (via Collections): Successfully validated scenes from this project
3. **Scene Helpers** (via code execution): Test layout and timing constraints

## Search Strategy

Before generating code:
1. Search Collections for similar visual patterns
2. Review validated scenes for working code structures
3. Use code execution to validate timing budgets

## Output Requirements

Generate ONLY the scene body (Python statements). NO imports, NO class wrapper, NO config.

Your output will be injected between:
```python
with self.voiceover(text=SCRIPT["scene_XX"]) as tracker:
    # SLOT_START:scene_body
    <YOUR CODE HERE>
    # SLOT_END:scene_body
```

## Constraints

- Use ONLY `harmonious_color()` for colors (no hardcoded RGB)
- All text must use `clamp_text_width(obj, max_width=6.0)`
- Animation run_time must fit narration duration ±10%
- NO layout overlaps (use `safe_layout()`)
```

### 7.2 Collections-Enhanced Prompts

**User prompt with RAG context** (`harness_responses/prompts/04_build_scenes/user.md`):

```markdown
## Task

Generate scene body for:
- Title: {{scene_title}}
- Description: {{scene_description}}
- Narration duration: {{narration_duration}}s
- Visual ideas: {{visual_ideas}}

## Available Tools

1. **Search template library**: Find proven patterns
   - Query example: "animated line graph with voiceover tracking"

2. **Search previous scenes**: Review validated code
   - Query example: "safe_layout with multiple equations"

3. **Execute validation code**: Test timing/layout
   ```python
   # Check if animations fit duration budget
   total_runtime = sum([anim1.run_time, anim2.run_time, ...])
   assert total_runtime <= {{narration_duration}} * 1.1
   ```

## Process

1. Search Collections for 2-3 relevant examples
2. Draft scene body using proven patterns
3. Validate timing with code execution
4. Output final scene body as JSON:

```json
{
  "scene_body": "title = Text(...)\nself.play(Write(title))\n...",
  "reasoning": "Chose pattern X because Y..."
}
```
```

***

## 8. Data Contracts

### 8.1 Enhanced `project_state.json`

**NEW fields:**

```json
{
  "xai_session": {
    "response_id": "resp_abc123",
    "template_collection_id": "coll_xyz",
    "project_collection_id": "coll_proj_abc",
    "conversation_turns": 14,
    "last_updated": "2026-02-24T07:44:00Z"
  },
  "training_corpus": {
    "scenes_uploaded": 8,
    "total_examples": 42,
    "last_upload": "2026-02-24T07:42:00Z"
  }
}
```

### 8.2 Collections Metadata

**`.collections_metadata.json`** (per project):

```json
{
  "template_collection_id": "coll_flaming_horse_templates",
  "project_collection_id": "coll_standing_waves_scenes",
  "documents": [
    {
      "file_id": "file_abc123",
      "name": "scene_01_intro.py",
      "uploaded_at": "2026-02-24T07:30:00Z",
      "fields": {
        "scene_id": "scene_01",
        "status": "validated",
        "qc_score": 0.95
      }
    }
  ]
}
```

### 8.3 Session State

**`.xai_session.json`** (per project):

```json
{
  "response_id": "resp_current_state",
  "collection_ids": ["coll_templates", "coll_project"],
  "phase_history": [
    {"phase": "plan", "response_id": "resp_plan_001", "timestamp": "..."},
    {"phase": "build_scenes", "response_id": "resp_scene_01", "timestamp": "..."}
  ],
  "updated_at": "2026-02-24T07:44:00Z"
}
```

***

## 9. Validation Gates

All existing validation layers remain, with **NEW additions:** [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)

### Layer 10: Collections Citation Tracking

After scene generation, verify that Collections citations are present in reasoning:

```python
def validate_collections_usage(response, scene_id):
    """Ensure agent used template library"""
    if not response.citations:
        log_warning(f"{scene_id}: No Collections citations found")
        return False
    
    collections_refs = [c for c in response.citations 
                        if c.startswith("collections://")]
    
    if len(collections_refs) < 2:
        log_warning(f"{scene_id}: Insufficient template references")
        return False
    
    return True
```

### Layer 11: Code Execution Validation

For build_scenes phase, require that timing validation was executed:

```python
def validate_timing_execution(response):
    """Ensure agent used code_execution for timing check"""
    tool_calls = response.server_side_tool_usage.get("code_execution", [])
    
    if not tool_calls:
        raise SemanticValidationError(
            "Scene build must include code_execution timing validation"
        )
    
    # Check that timing logic was present
    for call in tool_calls:
        if "run_time" in call.get("code", ""):
            return True
    
    raise SemanticValidationError("No timing validation detected in code execution")
```

***

## 10. Self-Healing and Retry Logic

### 10.1 Stateful Repair Loops

**Enhanced scene repair** with full conversation context:

```python
def repair_scene_with_state(session, scene_file, failure_reason, max_attempts=3):
    """Repair scene using stateful Responses API"""
    
    for attempt in range(1, max_attempts + 1):
        log_info(f"Repair attempt {attempt}/{max_attempts}")
        
        # Create chat resuming from last successful state
        chat = session.create_chat("scene_repair")
        
        # Add repair prompt with full context
        chat.append(user(
            f"Previous scene generation failed. Error:\n{failure_reason}\n\n"
            f"Review the Collections for working examples and regenerate."
        ))
        
        # Stream response
        response = None
        for resp, chunk in chat.stream():
            response = resp
            if chunk.content:
                print(chunk.content, end="", flush=True)
        
        # Update session state
        session.update_response_id(response.id)
        
        # Parse and validate
        try:
            repair = SceneBuild.model_validate_json(response.content)
            inject_scene_body(repair.scene_body, scene_file)
            
            # Run full validation chain
            if validate_scene_all_gates(scene_file):
                log_success("Scene repaired successfully")
                return True
        
        except Exception as e:
            log_error(f"Repair validation failed: {e}")
            failure_reason = str(e)
            continue
    
    return False
```

***

## 11. Configuration and Environment Variables

**NEW variables:**

| Variable | Default | Purpose |
|---|---|---|
| `XAI_API_KEY` | — | xAI API key (required for `harness_responses/`) |
| `XAI_MANAGEMENT_API_KEY` | — | xAI management API key for Collections |
| `FH_HARNESS` | `responses` | **Changed default** to use Responses API |
| `FH_ENABLE_TRAINING_CORPUS` | `1` | Enable Collections-based training corpus |
| `FH_TEMPLATE_COLLECTION_ID` | — | Reuse existing template collection |

**Updated defaults:**
- `FH_HARNESS` now defaults to `responses` (was `legacy`)
- `AGENT_MODEL` ignored when `FH_HARNESS=responses` (always uses `grok-4-1-fast-reasoning`)

***

## 12. Harness Exit Codes

**Responses harness** (`harness_responses/`):

| Code | Meaning | Orchestrator action |
|---|---|---|
| `0` | Success with valid structured output | Advance phase |
| `1` | General error (API, network, timeout) | Retry up to `PHASE_RETRY_LIMIT` |
| `2` | `SemanticValidationError` (business logic) | Retry with error context |
| `3` | Schema validation error (should never occur with `chat.parse()`) | Fatal, needs human review |

***

## 13. Logging and Observability

**NEW log files:**

| File | Content |
|---|---|---|
| `log/xai_session.log` | Response IDs, collection queries, tool calls per phase |
| `log/collections_citations.log` | Full citation provenance per scene |
| `log/responses_api_calls.jsonl` | One JSON object per API call with request/response/timing |

**Enhanced conversation log** includes Collections citations:

```
----- ASSISTANT RESPONSE -----
<response content>

----- CITATIONS -----
collections://coll_abc/files/file_xyz (Kitchen Sink: Line Graphs)
collections://coll_abc/files/file_123 (Scene 02 validated example)
web:5 (Manim documentation reference)

----- TOOL CALLS -----
collections_search(query="animated line graph", collection_ids=[...])
code_execution(code="total_runtime = ...")
```

***

## 14. Voice Policy

**No changes from v1.0**. Voice policy remains: Qwen cached service only, no fallback. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)

***

## 15. Testing

**NEW tests:**

| Test file | Coverage |
|---|---|
| `tests/harness_responses/test_session_state.py` | Session persistence, response_id chaining |
| `tests/harness_responses/test_collections_search.py` | RAG integration, citation tracking |
| `tests/harness_responses/test_structured_outputs.py` | Pydantic schema validation |
| `tests/harness_responses/test_stateful_repair.py` | Multi-turn repair with context preservation |
| `tests/test_training_corpus_upload.py` | Collection document upload and metadata |

**Integration test** (live API):

```bash
# Full pipeline with Responses API
FH_HARNESS=responses bash tests/test_e2e_responses_api.sh
```

***

## 16. Render and Assembly

**No changes from v1.0**. Render configuration and FFmpeg assembly remain unchanged. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)

***

## 17. Stateful Training Integration

### 17.1 Learning Corpus Growth

As scenes are built and validated, they are uploaded to the project collection:

```python
def upload_validated_scene(project_dir, scene_file, qc_report):
    """Upload scene to collection after successful validation"""
    
    session = PipelineTrainingSession.from_project(project_dir)
    metadata_file = Path(project_dir) / ".collections_metadata.json"
    
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    project_collection_id = metadata["project_collection_id"]
    
    # Upload scene file
    with open(scene_file, 'rb') as f:
        scene_doc = session.client.collections.upload_document(
            collection_id=project_collection_id,
            name=Path(scene_file).name,
            data=f.read(),
            fields={
                "scene_id": extract_scene_id(scene_file),
                "status": "validated",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # Upload QC report
    with open(qc_report, 'rb') as f:
        qc_doc = session.client.collections.upload_document(
            collection_id=project_collection_id,
            name=f"qc_{Path(scene_file).stem}.md",
            data=f.read(),
            fields={
                "type": "qc_report",
                "scene_id": extract_scene_id(scene_file)
            }
        )
    
    # Update metadata
    metadata["documents"].extend([
        {"file_id": scene_doc.file_metadata.file_id, "name": scene_doc.name},
        {"file_id": qc_doc.file_metadata.file_id, "name": qc_doc.name}
    ])
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
```

### 17.2 Context Preservation Across Phases

The stateful Responses API maintains full conversation context:

```
Turn 1 (plan):     Create video plan → response_id_1
Turn 2 (build_01): Generate scene 1 → response_id_2 (references response_id_1)
Turn 3 (repair_01): Fix scene 1 → response_id_3 (references response_id_2)
Turn 4 (build_02): Generate scene 2 → response_id_4 (references response_id_3)
...
```

Each turn has access to:
- All previous prompts and responses (30 days)
- Collection citations from earlier phases
- Tool execution results (code validation, searches)

### 17.3 Cross-Project Template Reuse

The template collection is **shared across all projects**:

```python
# First project initializes shared template collection
project_a_session = initialize_training_corpus("project_a")

# Second project reuses templates
project_b_session = initialize_training_corpus(
    "project_b",
    template_collection_id=project_a_session.template_collection_id
)
```

This enables:
- Cumulative learning across video projects
- Proven patterns propagate to new videos
- Template library grows over time

***

## 18. Known Constraints and Risk Areas

**NEW constraints:**

| Area | Description |
|---|---|
| **xAI API rate limits** | Grok-4 models have rate limits (requests/min, tokens/min). Pipeline may need backoff for high-scene-count videos. |
| **Collections processing latency** | Documents require processing before search. `wait_for_processing()` adds latency to init phase. |
| **30-day conversation retention** | Responses older than 30 days are purged. Long-paused projects lose context. |
| **Collection size limits** | 100MB per document. Large scene files may need chunking. |
| **Network dependency** | Unlike legacy harness, Responses API requires persistent network for stateful calls. |

**Existing constraints** (unchanged from v1.0): [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/85312621/8072162c-068b-4db7-8a01-4c723fa1ed03/TECH_SPEC.md)
- Python 3.13 requirement
- Voice cache completeness
- Single-machine rendering
- Manim version pinning

***

## Appendix A: Migration from Legacy Harness

**Backward compatibility:** `FH_HARNESS=legacy` still works. Projects created before v2.0 can complete without Collections.

**Migration path:**

1. Set `FH_HARNESS=responses` in `.env`
2. Run `scripts/initialize_training_corpus.py --project-dir <path>` to retrofit existing project
3. Rebuild from `build_scenes` phase to leverage RAG

**Automatic fallback:** If `XAI_API_KEY` is not set, orchestrator falls back to legacy harness with warning.
