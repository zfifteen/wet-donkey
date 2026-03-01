"""Schema registry for harness structured outputs."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from .narration import Narration
from .plan import Plan
from .scene_build import SceneBuild
from .scene_qc import SceneQC

SCHEMA_REGISTRY_CONTRACT_VERSION = "1.0.0"

PHASE_SCHEMA_REGISTRY: dict[str, Type[BaseModel]] = {
    "plan": Plan,
    "narration": Narration,
    "build_scenes": SceneBuild,
    "scene_qc": SceneQC,
    "scene_repair": SceneBuild,
}


def get_schema_for_phase(phase: str) -> Type[BaseModel]:
    try:
        return PHASE_SCHEMA_REGISTRY[phase]
    except KeyError as exc:
        raise ValueError(f"no schema registered for phase '{phase}'") from exc
