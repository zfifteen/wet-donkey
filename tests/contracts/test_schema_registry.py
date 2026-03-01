from __future__ import annotations

import re

import pytest

from harness.schemas import (
    PHASE_SCHEMA_REGISTRY,
    SCHEMA_REGISTRY_CONTRACT_VERSION,
    get_schema_for_phase,
)


REQUIRED_PHASES = {"plan", "narration", "build_scenes", "scene_qc", "scene_repair"}


def test_registry_contract_version_is_semver() -> None:
    assert re.match(r"^\d+\.\d+\.\d+$", SCHEMA_REGISTRY_CONTRACT_VERSION)


def test_required_phase_schemas_exist() -> None:
    assert REQUIRED_PHASES.issubset(set(PHASE_SCHEMA_REGISTRY.keys()))


def test_unknown_phase_lookup_fails() -> None:
    with pytest.raises(ValueError):
        get_schema_for_phase("unknown_phase")
