# tests/harness/test_structured_outputs.py
import unittest
from unittest.mock import MagicMock, patch

from harness.client import generate_plan
from harness.schemas.plan import Plan, Scene

class TestStructuredOutputs(unittest.TestCase):

    @patch('harness.client.PipelineTrainingSession')
    def test_generate_plan_returns_pydantic_model(self, MockSession):
        """
        Test that `generate_plan` returns a valid Pydantic `Plan` object.
        """
        # Arrange
        mock_session_instance = MockSession.return_value
        
        # This is the object the xAI SDK would return after parsing the response
        mock_sdk_response = MagicMock()
        mock_sdk_response.content = Plan(
            title="Test Video",
            description="A test plan",
            target_duration_seconds=600,
            scenes=[
                Scene(
                    title=f"Test Scene {i+1}",
                    description="An intro",
                    estimated_duration_seconds=30,
                    visual_ideas=["idea1", "idea2"]
                )
                for i in range(12)
            ]
        )
        mock_sdk_response.id = "resp_plan_123"

        # Mock the chat object chain
        mock_chat = MagicMock()
        mock_chat.sample.return_value = mock_sdk_response
        mock_session_instance.create_chat.return_value = mock_chat
        
        # Act
        result = generate_plan(mock_session_instance, "a test topic")

        # Assert
        self.assertIsInstance(result, Plan)
        self.assertEqual(result.title, "Test Video")
        self.assertEqual(len(result.scenes), 12)
        self.assertEqual(result.scenes[0].title, "Test Scene 1")
        
        # Check that the session was updated
        mock_session_instance.update_response_id.assert_called_once_with("resp_plan_123")

    @patch('harness.client.PipelineTrainingSession')
    def test_pydantic_validation_error_is_handled(self, MockSession):
        """
        Test how Pydantic validation errors would be handled.
        Note: With the xAI SDK's `response_format` feature, the SDK itself
        would raise an error before our code gets the response. This test
        simulates what would happen if our code received invalid data.
        """
        # Arrange
        from pydantic import ValidationError

        mock_session_instance = MockSession.return_value
        
        # Simulate an invalid response from the LLM that the SDK fails to parse
        mock_chat = MagicMock()
        # Build a real ValidationError instance from an invalid model payload.
        try:
            Plan.model_validate({"title": "x"})
        except ValidationError as exc:
            mock_chat.sample.side_effect = exc
        mock_session_instance.create_chat.return_value = mock_chat
        
        # Act & Assert
        with self.assertRaises(ValidationError):
            generate_plan(mock_session_instance, "a test topic")

if __name__ == '__main__':
    unittest.main()
