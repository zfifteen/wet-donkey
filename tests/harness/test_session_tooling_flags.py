from __future__ import annotations

import os
from unittest.mock import patch

from harness.session import PipelineTrainingSession


def test_create_chat_includes_collections_search_when_training_corpus_enabled() -> None:
    with (
        patch("harness.session.Client") as mock_client,
        patch("harness.session.collections_search", return_value="collections_tool") as mock_collections,
        patch("harness.session.code_execution", return_value="code_tool") as mock_code,
        patch("harness.session.web_search", return_value="web_tool") as mock_web,
        patch.dict(os.environ, {"FH_ENABLE_TRAINING_CORPUS": "1"}, clear=False),
    ):
        session = PipelineTrainingSession(project_dir="/tmp/test_project", collection_ids=["coll_a", "coll_b"])
        session.create_chat("plan")

        mock_collections.assert_called_once_with(collection_ids=["coll_a", "coll_b"])
        mock_code.assert_called_once()
        mock_web.assert_called_once()

        kwargs = mock_client.return_value.chat.create.call_args.kwargs
        assert kwargs["tools"][0] == "collections_tool"


def test_create_chat_skips_collections_search_when_training_corpus_disabled() -> None:
    with (
        patch("harness.session.Client") as mock_client,
        patch("harness.session.collections_search", return_value="collections_tool") as mock_collections,
        patch("harness.session.code_execution", return_value="code_tool") as mock_code,
        patch("harness.session.web_search", return_value="web_tool") as mock_web,
        patch.dict(os.environ, {"FH_ENABLE_TRAINING_CORPUS": "0"}, clear=False),
    ):
        session = PipelineTrainingSession(project_dir="/tmp/test_project", collection_ids=["coll_a", "coll_b"])
        session.create_chat("plan")

        mock_collections.assert_not_called()
        mock_code.assert_called_once()
        mock_web.assert_called_once()

        kwargs = mock_client.return_value.chat.create.call_args.kwargs
        assert "collections_tool" not in kwargs["tools"]
