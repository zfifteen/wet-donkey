# tests/harness_responses/test_session_state.py
import unittest
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from harness_responses.session import PipelineTrainingSession

class TestSessionState(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    def test_session_creation_from_metadata(self):
        """
        Test that a new session is correctly created when only metadata exists.
        """
        # Arrange
        metadata_path = self.project_dir / ".collections_metadata.json"
        metadata_content = {
            "template_collection_id": "coll_templates_123",
            "project_collection_id": "coll_proj_456",
            "documents": []
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata_content, f)

        # Act
        with patch('harness_responses.session.Client') as MockClient:
            session = PipelineTrainingSession.from_project(self.project_dir)

            # Assert
            self.assertIsNotNone(session)
            self.assertEqual(session.collection_ids, ["coll_templates_123", "coll_proj_456"])
            self.assertIsNone(session.response_id)
            MockClient.assert_called_once()

    def test_session_loading_from_existing_file(self):
        """
        Test that an existing session state is loaded correctly.
        """
        # Arrange
        session_path = self.project_dir / ".xai_session.json"
        session_data = {
            "response_id": "resp_abc_123",
            "collection_ids": ["coll_a", "coll_b"],
            "updated_at": "2026-02-24T10:00:00Z"
        }
        with open(session_path, 'w') as f:
            json.dump(session_data, f)
        
        # Act
        with patch('harness_responses.session.Client'):
            session = PipelineTrainingSession.from_project(self.project_dir)

            # Assert
            self.assertEqual(session.response_id, "resp_abc_123")
            self.assertEqual(session.collection_ids, ["coll_a", "coll_b"])

    def test_update_and_save_session(self):
        """
        Test that updating the response_id persists the session to a file.
        """
        # Arrange
        metadata_path = self.project_dir / ".collections_metadata.json"
        metadata_content = {"template_collection_id": "t_id", "project_collection_id": "p_id"}
        with open(metadata_path, 'w') as f:
            json.dump(metadata_content, f)

        with patch('harness_responses.session.Client'):
            session = PipelineTrainingSession.from_project(self.project_dir)
        
        # Act
        session.update_response_id("resp_new_id_456")

        # Assert
        session_file = self.project_dir / ".xai_session.json"
        self.assertTrue(session_file.exists())
        with open(session_file, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["response_id"], "resp_new_id_456")
        self.assertEqual(saved_data["collection_ids"], ["t_id", "p_id"])

if __name__ == '__main__':
    unittest.main()
