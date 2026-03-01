from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harness.contracts.session import SESSION_CONTRACT_VERSION
from harness.schemas.plan import Plan
from harness.schemas.scene_build import SceneBuild
from harness.session import PipelineTrainingSession, SessionContractError


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _collections_payload() -> dict:
    return {
        "template_collection_id": "coll_templates_123",
        "project_collection_id": "coll_project_456",
        "documents": [],
    }


@patch("harness.session.Client")
def test_from_project_rejects_invalid_collections_metadata(_mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    _write_json(project_dir / ".collections_metadata.json", {"template_collection_id": "only_one_id"})

    with pytest.raises(SessionContractError):
        PipelineTrainingSession.from_project(project_dir)


@patch("harness.session.Client")
def test_from_project_rejects_invalid_session_metadata(_mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    _write_json(
        project_dir / ".xai_session.json",
        {
            "collection_ids": "not-a-list",
            "response_id": "resp_123",
            "updated_at": "2026-03-01T00:00:00Z",
        },
    )

    with pytest.raises(SessionContractError):
        PipelineTrainingSession.from_project(project_dir)


@patch("harness.session.Client")
def test_from_project_accepts_legacy_metadata_without_contract_version(_mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    _write_json(project_dir / ".collections_metadata.json", _collections_payload())

    session = PipelineTrainingSession.from_project(project_dir)

    assert session.collection_ids == ["coll_templates_123", "coll_project_456"]
    assert session.response_id is None


@patch("harness.session.Client")
def test_update_response_id_persists_session_contract(_mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    _write_json(project_dir / ".collections_metadata.json", _collections_payload())

    session = PipelineTrainingSession.from_project(project_dir)
    session.update_response_id("resp_new_456")

    saved = json.loads((project_dir / ".xai_session.json").read_text(encoding="utf-8"))
    assert saved["contract_version"] == SESSION_CONTRACT_VERSION
    assert saved["response_id"] == "resp_new_456"
    assert saved["collection_ids"] == ["coll_templates_123", "coll_project_456"]
    assert saved["updated_at"].endswith("Z")


@patch("harness.session.Client")
def test_create_chat_uses_phase_schema_when_not_provided(mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    session = PipelineTrainingSession(project_dir=project_dir, collection_ids=["coll_1"])
    session.create_chat(phase="plan")

    _, kwargs = mock_client.return_value.chat.create.call_args
    assert kwargs["response_format"] is Plan


@patch("harness.session.Client")
def test_create_chat_rejects_schema_mismatch(_mock_client, tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    session = PipelineTrainingSession(project_dir=project_dir, collection_ids=["coll_1"])
    with pytest.raises(SessionContractError):
        session.create_chat(phase="plan", response_format=SceneBuild)
