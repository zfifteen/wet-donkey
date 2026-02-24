# tests/test_training_corpus_upload.py
import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from scripts.upload_scene_to_collection import upload_validated_scene

class TestTrainingCorpusUpload(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_upload_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.scene_file = self.project_dir / "scene_01_test.py"
        self.qc_file = self.project_dir / "qc_scene_01_test.md"
        self.metadata_file = self.project_dir / ".collections_metadata.json"

        # Create dummy files
        self.scene_file.write_text("from manim import * ...")
        self.qc_file.write_text("QC Report: All good.")
        
        # Create metadata file
        self.metadata = {
            "template_collection_id": "coll_templates_123",
            "project_collection_id": "coll_proj_456",
            "documents": []
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('scripts.upload_scene_to_collection.Client')
    @patch.dict(os.environ, {"XAI_MANAGEMENT_API_KEY": "fake-key"})
    def test_upload_flow(self, MockClient):
        """
        Test the main upload function to ensure it calls the client correctly.
        """
        # Arrange
        mock_client_instance = MockClient.return_value
        
        # Mock the return value of the upload_document call
        mock_scene_doc = MagicMock()
        mock_scene_doc.file_metadata.file_id = "file_scene_123"
        mock_scene_doc.name = "scene_01_test.py"
        
        mock_qc_doc = MagicMock()
        mock_qc_doc.file_metadata.file_id = "file_qc_456"
        mock_qc_doc.name = "qc_scene_01_test.md"

        mock_client_instance.collections.upload_document.side_effect = [
            mock_scene_doc, 
            mock_qc_doc
        ]

        # Act
        upload_validated_scene(str(self.project_dir), str(self.scene_file), str(self.qc_file))

        # Assert
        # 1. Check that upload_document was called twice (for scene and QC)
        self.assertEqual(mock_client_instance.collections.upload_document.call_count, 2)
        
        # 2. Check the calls
        calls = mock_client_instance.collections.upload_document.call_args_list
        
        # Call 1: Scene file
        _, scene_kwargs = calls[0]
        self.assertEqual(scene_kwargs['collection_id'], "coll_proj_456")
        self.assertEqual(scene_kwargs['name'], "scene_01_test.py")
        self.assertEqual(scene_kwargs['fields']['status'], "validated")
        
        # Call 2: QC report
        _, qc_kwargs = calls[1]
        self.assertEqual(qc_kwargs['collection_id'], "coll_proj_456")
        self.assertEqual(qc_kwargs['name'], "qc_scene_01_test.md")
        self.assertEqual(qc_kwargs['fields']['type'], "qc_report")

        # 3. Check that the metadata file was updated correctly
        with open(self.metadata_file, 'r') as f:
            updated_metadata = json.load(f)
        
        self.assertEqual(len(updated_metadata['documents']), 2)
        self.assertEqual(updated_metadata['documents'][0]['file_id'], "file_scene_123")
        self.assertEqual(updated_metadata['documents'][1]['file_id'], "file_qc_456")

if __name__ == '__main__':
    unittest.main()
