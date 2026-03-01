from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

SESSION_CONTRACT_VERSION = "1.0.0"


class SessionContractError(ValueError):
    """Raised when session or collection metadata violates WD contracts."""


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_contract_version(value: str) -> str:
    if not re.match(r"^\d+\.\d+\.\d+$", value):
        raise ValueError("contract_version must follow semver (x.y.z)")
    return value


def _validate_timestamp(value: str) -> str:
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", value):
        raise ValueError("updated_at must be UTC with trailing Z")
    return value


def _validate_collection_ids(values: list[str]) -> list[str]:
    cleaned = [value.strip() for value in values if value.strip()]
    if len(cleaned) != len(values):
        raise ValueError("collection_ids must not contain empty values")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("collection_ids must be unique")
    return cleaned


class SessionMetadata(BaseModel):
    contract_version: str = SESSION_CONTRACT_VERSION
    collection_ids: list[str] = Field(min_length=1)
    response_id: str | None = None
    updated_at: str = Field(default_factory=utc_timestamp)

    @field_validator("contract_version")
    @classmethod
    def _semver_contract_version(cls, value: str) -> str:
        return _validate_contract_version(value)

    @field_validator("updated_at")
    @classmethod
    def _utc_timestamp(cls, value: str) -> str:
        return _validate_timestamp(value)

    @field_validator("collection_ids")
    @classmethod
    def _non_empty_collection_ids(cls, value: list[str]) -> list[str]:
        return _validate_collection_ids(value)


class CollectionDocument(BaseModel):
    file_id: str
    name: str


class CollectionsMetadata(BaseModel):
    contract_version: str = SESSION_CONTRACT_VERSION
    template_collection_id: str
    project_collection_id: str
    documents: list[CollectionDocument] = Field(default_factory=list)
    updated_at: str = Field(default_factory=utc_timestamp)

    @field_validator("contract_version")
    @classmethod
    def _semver_contract_version(cls, value: str) -> str:
        return _validate_contract_version(value)

    @field_validator("updated_at")
    @classmethod
    def _utc_timestamp(cls, value: str) -> str:
        return _validate_timestamp(value)


def normalize_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("contract_version", SESSION_CONTRACT_VERSION)
    data.setdefault("updated_at", utc_timestamp())
    return data


def normalize_collections_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("contract_version", SESSION_CONTRACT_VERSION)
    data.setdefault("documents", [])
    data.setdefault("updated_at", utc_timestamp())
    return data


def _parse_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionContractError(f"invalid JSON in {path.name}: {exc}") from exc


def load_session_metadata(path: Path) -> SessionMetadata:
    payload = normalize_session_payload(_parse_json_file(path))
    try:
        return SessionMetadata.model_validate(payload)
    except ValidationError as exc:
        raise SessionContractError(f"invalid session metadata contract in {path.name}: {exc}") from exc


def load_collections_metadata(path: Path) -> CollectionsMetadata:
    payload = normalize_collections_payload(_parse_json_file(path))
    try:
        return CollectionsMetadata.model_validate(payload)
    except ValidationError as exc:
        raise SessionContractError(f"invalid collections metadata contract in {path.name}: {exc}") from exc


def save_session_metadata(path: Path, metadata: SessionMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(metadata.model_dump(mode="json"), indent=2)
    with NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
