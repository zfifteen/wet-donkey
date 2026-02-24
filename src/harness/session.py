# harness/session.py
import os
import json
from pathlib import Path
from datetime import datetime
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
        project_dir = Path(project_dir)
        session_file = project_dir / ".xai_session.json"

        if session_file.exists():
            with open(session_file) as f:
                data = json.load(f)
            return cls(
                project_dir=project_dir,
                collection_ids=data["collection_ids"],
                response_id=data.get("response_id")
            )

        # Load collection IDs from metadata
        metadata_file = project_dir / ".collections_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"'{metadata_file}' not found. Please initialize the project first.")
        
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
