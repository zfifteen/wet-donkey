from __future__ import annotations

from pathlib import Path
from typing import Union

SLOT_START_MARKER = "# SLOT_START:scene_body"
SLOT_END_MARKER = "# SLOT_END:scene_body"


class ScaffoldContractError(ValueError):
    """Raised when scaffold slot markers are missing, duplicated, or mutated."""


def _marker_positions(content: str) -> tuple[int, int]:
    if content.count(SLOT_START_MARKER) != 1 or content.count(SLOT_END_MARKER) != 1:
        raise ScaffoldContractError("scaffold must contain exactly one SLOT_START and one SLOT_END marker")

    start_index = content.find(SLOT_START_MARKER)
    end_index = content.find(SLOT_END_MARKER)

    if start_index == -1 or end_index == -1 or start_index >= end_index:
        raise ScaffoldContractError("invalid slot marker ordering")

    return start_index, end_index


def inject_scene_body(content: str, scene_body: str) -> str:
    """Inject generated scene body while preserving immutable scaffold markers."""
    if SLOT_START_MARKER in scene_body or SLOT_END_MARKER in scene_body:
        raise ScaffoldContractError("generated scene body must not contain slot markers")

    start_index, end_index = _marker_positions(content)

    return (
        content[: start_index + len(SLOT_START_MARKER)]
        + "\n"
        + scene_body
        + "\n    "
        + content[end_index:]
    )


def inject_scene_body_file(scene_file: Union[str, Path], scene_body: str) -> None:
    path = Path(scene_file)
    if not path.exists():
        raise FileNotFoundError(f"scene file not found: {path}")

    content = path.read_text(encoding="utf-8")
    new_content = inject_scene_body(content, scene_body)
    path.write_text(new_content, encoding="utf-8")
