# tests/harness/test_collections_search.py
import unittest
from unittest.mock import MagicMock, patch
from harness.session import PipelineTrainingSession
from harness.parser import validate_collections_usage

class TestCollectionsSearch(unittest.TestCase):

    def setUp(self):
        # Mock a session object
        self.session = MagicMock(spec=PipelineTrainingSession)
        self.session.collection_ids = ["coll_test_1", "coll_test_2"]

    @patch('harness.session.Client')
    def test_chat_creation_with_collections_tool(self, MockClient):
        """
        Test that the created chat object includes the collections_search tool.
        """
        # Arrange
        mock_chat = MagicMock()
        mock_client_instance = MockClient.return_value
        mock_client_instance.chat.create.return_value = mock_chat
        
        session = PipelineTrainingSession(
            project_dir="/tmp", 
            collection_ids=["coll_abc"], 
            response_id=None
        )
        
        # Act
        session.create_chat(phase="plan")

        # Assert
        # Check that chat.create was called
        mock_client_instance.chat.create.assert_called_once()
        # Get the call arguments
        _, kwargs = mock_client_instance.chat.create.call_args
        
        # Check that the 'tools' argument was passed and is a list
        self.assertIn("tools", kwargs)
        self.assertIsInstance(kwargs["tools"], list)
        
        # Check if collections_search tool is in the list of tools
        found_tool = False
        for tool in kwargs["tools"]:
            # This check is a bit brittle as it depends on the tool's __str__ or __repr__
            if "collections_search" in str(tool):
                found_tool = True
                # We could also check the collection_ids if the tool object allows
                # self.assertEqual(tool.collection_ids, ["coll_abc"])
                break
        self.assertTrue(found_tool, "collections_search tool was not found in the chat creation call.")

    def test_citation_validation_success(self):
        """
        Test that the citation validator passes with correct citations.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.citations = [
            "collections://coll_abc/files/file_xyz",
            "collections://coll_abc/files/file_123",
            "web:5"
        ]
        
        # Act & Assert
        # In the original spec, the check was for >= 2, this has been relaxed to >=1
        self.assertTrue(validate_collections_usage(mock_response, "scene_01"))

    def test_citation_validation_failure_no_citations(self):
        """
        Test that the citation validator fails when no citations are present.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.citations = []

        # Act & Assert
        self.assertFalse(validate_collections_usage(mock_response, "scene_02"))

    def test_citation_validation_failure_no_collection_citations(self):
        """
        Test that the citation validator fails when only web citations are present.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.citations = ["web:1", "web:2"]

        # Act & Assert
        self.assertFalse(validate_collections_usage(mock_response, "scene_03"))

if __name__ == '__main__':
    unittest.main()
