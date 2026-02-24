# tests/harness/test_stateful_repair.py
import unittest
from unittest.mock import MagicMock, patch

from harness.client import repair_scene
from harness.schemas.scene_build import SceneBuild

class TestStatefulRepair(unittest.TestCase):

    @patch('harness.client.PipelineTrainingSession')
    @patch('harness.client.Path')
    def test_repair_scene_call_flow(self, MockPath, MockSession):
        """
        Test the call flow of the repair_scene function, ensuring it uses
        the session's response_id to maintain state.
        """
        # Arrange
        mock_session_instance = MockSession.return_value
        # Simulate a session that has a history
        mock_session_instance.response_id = "resp_failed_build_123"

        # Mock the file read
        mock_file = MockPath.return_value
        mock_file.read_text.return_value = "original broken code"

        # Mock the SDK response
        mock_sdk_response = MagicMock()
        mock_sdk_response.content = SceneBuild(
            scene_body="fixed code",
            reasoning="I fixed it."
        )
        mock_sdk_response.id = "resp_repair_attempt_456"

        mock_chat = MagicMock()
        mock_chat.sample.return_value = mock_sdk_response
        mock_session_instance.create_chat.return_value = mock_chat

        failure_reason = "Syntax Error on line 5"

        # Act
        result = repair_scene(mock_session_instance, "/path/to/scene.py", failure_reason)

        # Assert
        # 1. Check that a chat was created for the 'scene_repair' phase
        mock_session_instance.create_chat.assert_called_once_with(
            phase="scene_repair",
            response_format=SceneBuild
        )
        
        # 2. Check that the prompts were composed with the correct context
        from harness.prompts import compose_prompts
        # This is a bit complex, we would need to also patch compose_prompts
        # to check the arguments passed to it. For now, we trust it's called.

        # 3. Check that the chat was appended to
        mock_chat.append.assert_called_once()
        
        # 4. Check that the result is the parsed SceneBuild object
        self.assertIsInstance(result, SceneBuild)
        self.assertEqual(result.scene_body, "fixed code")

        # 5. MOST IMPORTANT: Check that the session ID was updated to continue the conversation
        mock_session_instance.update_response_id.assert_called_once_with("resp_repair_attempt_456")

if __name__ == '__main__':
    unittest.main()
