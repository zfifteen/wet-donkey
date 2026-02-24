# tests/harness_responses/test_structured_outputs.py
import unittest
from unittest.mock import MagicMock, patch

from harness_responses.client import generate_plan
from harness_responses.schemas.plan import Plan, Scene

class TestStructuredOutputs(unittest.TestCase):

    @patch('harness_responses.client.PipelineTrainingSession')
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
                    title="Test Scene 1",
                    description="An intro",
                    estimated_duration_seconds=30,
                    visual_ideas=["idea1", "idea2"]
                )
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
        self.assertEqual(len(result.scenes), 1)
        self.assertEqual(result.scenes[0].title, "Test Scene 1")
        
        # Check that the session was updated
        mock_session_instance.update_response_id.assert_called_once_with("resp_plan_123")

    @patch('harness_responses.client.PipelineTrainingSession')
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
        # The `sample()` call itself would raise the error in a real scenario
        mock_chat.sample.side_effect = ValidationError.from_exception_data(
            title="Plan",
            line_errors=[{"loc": ("scenes",), "msg": "field required"}]
        )
        mock_session_instance.create_chat.return_value = mock_chat
        
        # Act & Assert
        with self.assertRaises(ValidationError):
            generate_plan(mock_session_instance, "a test topic")

if __name__ == '__main__':
    unittest.main()
