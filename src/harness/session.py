# harness/session.py
import os
from pathlib import Path

from pydantic import BaseModel
from xai_sdk import Client
from xai_sdk.tools import code_execution, collections_search, web_search

from .contracts.session import (
    SessionContractError,
    SessionMetadata,
    load_collections_metadata,
    load_session_metadata,
    save_session_metadata,
)
from .schemas import get_schema_for_phase

class PipelineTrainingSession:
    """Stateful session manager for xAI Responses API"""

    def __init__(self, project_dir, collection_ids, response_id=None):
        self.project_dir = Path(project_dir)
        self.collection_ids = list(collection_ids)
        self.response_id = response_id
        self.client = Client(api_key=os.getenv("XAI_API_KEY"))
        self.session_file = self.project_dir / ".xai_session.json"

    @classmethod
    def from_project(cls, project_dir):
        """Load existing session or create new"""
        project_dir = Path(project_dir)
        session_file = project_dir / ".xai_session.json"

        if session_file.exists():
            data = load_session_metadata(session_file)
            return cls(
                project_dir=project_dir,
                collection_ids=data.collection_ids,
                response_id=data.response_id,
            )

        # Load collection IDs from metadata
        metadata_file = project_dir / ".collections_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"'{metadata_file}' not found. Please initialize the project first.")

        metadata = load_collections_metadata(metadata_file)

        return cls(
            project_dir=project_dir,
            collection_ids=[
                metadata.template_collection_id,
                metadata.project_collection_id,
            ],
        )

    def create_chat(self, phase: str, response_format: type[BaseModel] | None = None):
        """Create stateful chat for phase"""
        try:
            canonical_schema = get_schema_for_phase(phase)
        except ValueError as exc:
            raise SessionContractError(str(exc)) from exc

        if response_format is None:
            resolved_schema = canonical_schema
        elif response_format is not canonical_schema:
            raise SessionContractError(
                f"phase '{phase}' must use canonical schema '{canonical_schema.__name__}'"
            )
        else:
            resolved_schema = response_format

        training_corpus_enabled = os.getenv("FH_ENABLE_TRAINING_CORPUS", "1") == "1"
        tools = [code_execution()]

        if training_corpus_enabled:
            tools.insert(0, collections_search(collection_ids=self.collection_ids))

        # Add web search for research phases
        if phase in ["plan", "narration"]:
            tools.append(web_search())

        # Keep stateful context for narrative phases only; scene-level phases are
        # intentionally stateless to avoid runaway context growth across many scenes.
        previous_response_id = self.response_id if phase in {"plan", "narration"} else None

        return self.client.chat.create(
            model="grok-4-1-fast-reasoning",
            tools=tools,
            store_messages=True,
            previous_response_id=previous_response_id,
            response_format=resolved_schema,
        )

    def update_response_id(self, response_id):
        """Update session state after successful call"""
        self.response_id = response_id
        self._save_session()

    def _save_session(self):
        """Persist session state"""
        save_session_metadata(
            self.session_file,
            SessionMetadata(
                response_id=self.response_id,
                collection_ids=self.collection_ids,
            ),
        )
