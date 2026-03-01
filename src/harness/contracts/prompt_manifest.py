from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, meta
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from ..schemas import get_schema_for_phase

PROMPT_MANIFEST_CONTRACT_VERSION = "1.0.0"

PHASE_ALLOWED_TOOLS: dict[str, set[str]] = {
    "plan": {"collections_search", "code_execution", "web_search"},
    "narration": {"collections_search", "code_execution", "web_search"},
    "build_scenes": {"collections_search", "code_execution"},
    "scene_qc": {"collections_search", "code_execution"},
    "scene_repair": {"collections_search", "code_execution"},
}

PHASE_ALLOWED_ANNOTATIONS: dict[str, set[str]] = {
    "plan": set(),
    "narration": set(),
    "build_scenes": set(),
    "scene_qc": set(),
    "scene_repair": set(),
}


class PromptContractError(ValueError):
    """Raised when prompt assets violate manifest/schema contracts."""


def _validate_semver(value: str) -> str:
    if not re.match(r"^\d+\.\d+\.\d+$", value):
        raise ValueError("contract_version must follow semver (x.y.z)")
    return value


def _dedupe_and_validate(values: list[str], field_name: str) -> list[str]:
    cleaned = [value.strip() for value in values]
    if any(not value for value in cleaned):
        raise ValueError(f"{field_name} must not contain empty values")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError(f"{field_name} must be unique")
    return cleaned


class PromptManifest(BaseModel):
    contract_version: str = PROMPT_MANIFEST_CONTRACT_VERSION
    prompt_id: str
    phase: str
    schema_name: str
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    required_annotations: list[str] = Field(default_factory=list)
    output_restrictions: list[str] = Field(default_factory=list)
    output_fields: list[str] = Field(default_factory=list)

    @field_validator("contract_version")
    @classmethod
    def _semver_contract_version(cls, value: str) -> str:
        return _validate_semver(value)

    @field_validator(
        "required_variables",
        "optional_variables",
        "required_tools",
        "allowed_tools",
        "required_annotations",
        "output_restrictions",
        "output_fields",
    )
    @classmethod
    def _unique_non_empty_lists(cls, value: list[str], info) -> list[str]:
        return _dedupe_and_validate(value, info.field_name)

    @model_validator(mode="after")
    def _contract_invariants(self) -> "PromptManifest":
        required_set = set(self.required_variables)
        optional_set = set(self.optional_variables)
        if required_set & optional_set:
            overlap = sorted(required_set & optional_set)
            raise ValueError(f"required_variables and optional_variables overlap: {overlap}")

        required_tools = set(self.required_tools)
        allowed_tools = set(self.allowed_tools)
        if not required_tools.issubset(allowed_tools):
            missing = sorted(required_tools - allowed_tools)
            raise ValueError(f"required_tools must be a subset of allowed_tools: {missing}")

        return self

    @property
    def declared_variables(self) -> set[str]:
        return set(self.required_variables) | set(self.optional_variables)


def discover_template_variables(phase_dir: Path) -> set[str]:
    environment = Environment(loader=FileSystemLoader(phase_dir))
    discovered: set[str] = set()
    for template_name in ("system.md", "user.md"):
        source = environment.loader.get_source(environment, template_name)[0]
        parsed = environment.parse(source)
        discovered.update(meta.find_undeclared_variables(parsed))
    return discovered


def load_prompt_manifest(phase_dir: Path) -> PromptManifest:
    manifest_path = phase_dir / "manifest.yaml"
    if not manifest_path.exists():
        raise PromptContractError(f"prompt manifest not found: {manifest_path}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptContractError(f"invalid manifest format in {manifest_path}: {exc}") from exc

    try:
        return PromptManifest.model_validate(payload)
    except ValidationError as exc:
        raise PromptContractError(f"invalid prompt manifest contract in {manifest_path}: {exc}") from exc


def validate_manifest_template_alignment(manifest: PromptManifest, discovered_variables: set[str]) -> None:
    declared = manifest.declared_variables
    undeclared_template_vars = discovered_variables - declared
    stale_manifest_vars = declared - discovered_variables

    if undeclared_template_vars:
        missing = sorted(undeclared_template_vars)
        raise PromptContractError(
            f"manifest for phase '{manifest.phase}' is missing template variables: {missing}"
        )

    if stale_manifest_vars:
        stale = sorted(stale_manifest_vars)
        raise PromptContractError(
            f"manifest for phase '{manifest.phase}' declares unused variables: {stale}"
        )


def validate_runtime_variables(manifest: PromptManifest, provided_variables: Iterable[str]) -> None:
    provided = set(provided_variables)
    missing = set(manifest.required_variables) - provided
    if missing:
        raise PromptContractError(
            f"missing required prompt variables for phase '{manifest.phase}': {sorted(missing)}"
        )

    undeclared = provided - manifest.declared_variables
    if undeclared:
        raise PromptContractError(
            f"undeclared prompt variables for phase '{manifest.phase}': {sorted(undeclared)}"
        )


def validate_manifest_schema_alignment(manifest: PromptManifest) -> None:
    schema = get_schema_for_phase(manifest.phase)
    if manifest.schema_name != schema.__name__:
        raise PromptContractError(
            f"manifest schema mismatch for phase '{manifest.phase}': "
            f"expected '{schema.__name__}', got '{manifest.schema_name}'"
        )

    schema_fields = set(schema.model_fields.keys())
    manifest_fields = set(manifest.output_fields)
    if schema_fields != manifest_fields:
        missing = sorted(schema_fields - manifest_fields)
        extra = sorted(manifest_fields - schema_fields)
        raise PromptContractError(
            f"manifest output_fields mismatch for phase '{manifest.phase}': "
            f"missing={missing}, extra={extra}"
        )


def validate_manifest_tool_policy(manifest: PromptManifest) -> None:
    allowed_tools = PHASE_ALLOWED_TOOLS.get(manifest.phase, set())
    required_tools = set(manifest.required_tools)
    declared_allowed_tools = set(manifest.allowed_tools)

    if not required_tools.issubset(allowed_tools):
        missing = sorted(required_tools - allowed_tools)
        raise PromptContractError(
            f"manifest required_tools violate phase tool policy for '{manifest.phase}': {missing}"
        )

    if not declared_allowed_tools.issubset(allowed_tools):
        unsupported = sorted(declared_allowed_tools - allowed_tools)
        raise PromptContractError(
            f"manifest allowed_tools violate phase tool policy for '{manifest.phase}': {unsupported}"
        )

    allowed_annotations = PHASE_ALLOWED_ANNOTATIONS.get(manifest.phase, set())
    required_annotations = set(manifest.required_annotations)
    if not required_annotations.issubset(allowed_annotations):
        unsupported_annotations = sorted(required_annotations - allowed_annotations)
        raise PromptContractError(
            f"manifest required_annotations violate phase annotation policy for "
            f"'{manifest.phase}': {unsupported_annotations}"
        )
