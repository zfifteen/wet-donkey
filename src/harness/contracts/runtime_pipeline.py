from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from harness.contracts.scaffold import SLOT_END_MARKER, SLOT_START_MARKER
from harness.contracts.state import load_state
from harness.schemas.narration import Narration
from harness.schemas.plan import Plan
from harness.schemas.scene_qc import SceneQC

RUNTIME_PIPELINE_CONTRACT_VERSION = "1.0.0"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_non_empty(value: str, *, field_name: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def sanitize_scene_title(title: str) -> str:
    normalized = _normalize_non_empty(title, field_name="scene_title")
    return "".join(ch if ch.isalnum() else "_" for ch in normalized.lower().replace(" ", "_"))


def class_name_for_scene(scene_id: str, scene_title: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", _normalize_non_empty(scene_title, field_name="scene_title"))
    base = "".join(token.capitalize() for token in tokens if token) or "Scene"
    if not base[0].isalpha():
        base = f"Scene{base}"

    suffix = "".join(part.capitalize() for part in scene_id.split("_"))
    return f"{base}{suffix}"


def scene_id_for_index(index: int) -> str:
    if index < 1:
        raise ValueError("scene index must be >= 1")
    return f"scene_{index:02d}"


def estimate_narration_duration_seconds(narration_text: str) -> float:
    text = _normalize_non_empty(narration_text, field_name="narration_text")
    word_count = len(text.split())
    return max(0.2, word_count * 0.4)


def _normalize_title_for_match(title: str) -> str:
    return " ".join(title.strip().lower().split())


class SceneManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    scene_index: int = Field(ge=1)
    scene_title: str
    scene_description: str
    scene_file: str
    narration_text: str
    narration_duration_seconds: float = Field(gt=0)
    visual_ideas: list[str] = Field(min_length=1)

    @field_validator("scene_id", "scene_title", "scene_description", "scene_file", "narration_text")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="scene_manifest_field")

    @field_validator("visual_ideas")
    @classmethod
    def _validate_visual_ideas(cls, value: list[str]) -> list[str]:
        return [_normalize_non_empty(item, field_name="visual_idea") for item in value]


class SceneManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = RUNTIME_PIPELINE_CONTRACT_VERSION
    generated_at: str
    scenes: list[SceneManifestEntry] = Field(min_length=1)

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise ValueError("contract_version must follow semver (x.y.z)")
        return value

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", value):
            raise ValueError("generated_at must be UTC with trailing Z")
        return value

    @model_validator(mode="after")
    def _validate_scene_order(self) -> "SceneManifest":
        expected_ids = [scene_id_for_index(index + 1) for index in range(len(self.scenes))]
        actual_ids = [scene.scene_id for scene in self.scenes]
        if actual_ids != expected_ids:
            raise ValueError("scene manifest scene_id values must be contiguous and ordered")
        return self


class SceneQCRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = RUNTIME_PIPELINE_CONTRACT_VERSION
    scene_id: str
    scene_file: str
    scene_title: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise ValueError("contract_version must follow semver (x.y.z)")
        return value

    @field_validator("scene_id", "scene_file", "scene_title")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="scene_qc_field")


def build_scene_manifest(plan: Plan, narration: Narration) -> SceneManifest:
    if len(plan.scenes) != len(narration.scenes):
        raise ValueError(
            "plan/narration scene count mismatch: "
            f"plan={len(plan.scenes)} narration={len(narration.scenes)}"
        )

    entries: list[SceneManifestEntry] = []
    for index, (plan_scene, narration_scene) in enumerate(zip(plan.scenes, narration.scenes), start=1):
        if _normalize_title_for_match(plan_scene.title) != _normalize_title_for_match(narration_scene.scene_title):
            raise ValueError(
                "plan/narration scene title mismatch at index "
                f"{index}: plan='{plan_scene.title}' narration='{narration_scene.scene_title}'"
            )

        scene_id = scene_id_for_index(index)
        safe_title = sanitize_scene_title(plan_scene.title)
        scene_file = f"scenes/{scene_id}_{safe_title}.py"

        entries.append(
            SceneManifestEntry(
                scene_id=scene_id,
                scene_index=index,
                scene_title=plan_scene.title,
                scene_description=plan_scene.description,
                scene_file=scene_file,
                narration_text=narration_scene.narration_text,
                narration_duration_seconds=estimate_narration_duration_seconds(narration_scene.narration_text),
                visual_ideas=list(plan_scene.visual_ideas),
            )
        )

    return SceneManifest(generated_at=utc_timestamp(), scenes=entries)


def load_plan_and_narration_from_state(project_dir: Path) -> tuple[Plan, Narration]:
    state_file = project_dir / "project_state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"state file not found: {state_file}")

    state = load_state(state_file)
    payload = state.model_dump(mode="json")

    if "plan" not in payload:
        raise ValueError("project_state.json is missing required 'plan' payload")
    if "narration" not in payload:
        raise ValueError("project_state.json is missing required 'narration' payload")

    plan = Plan.model_validate(payload["plan"])
    narration = Narration.model_validate(payload["narration"])
    return plan, narration


def scene_manifest_path(project_dir: Path) -> Path:
    return project_dir / "artifacts" / "scene_manifest.json"


def write_scene_manifest(project_dir: Path, manifest: SceneManifest) -> Path:
    path = scene_manifest_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def load_scene_manifest(path: Path) -> SceneManifest:
    return SceneManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _narration_script_payload(manifest: SceneManifest) -> dict[str, str]:
    return {entry.scene_id: entry.narration_text for entry in manifest.scenes}


def write_narration_script(project_dir: Path, manifest: SceneManifest) -> Path:
    script_path = project_dir / "narration_script.py"
    script_path.write_text(
        "# Auto-generated by runtime pipeline contract preparation\n"
        f"# contract_version={RUNTIME_PIPELINE_CONTRACT_VERSION}\n"
        f"# generated_at={manifest.generated_at}\n"
        "\n"
        f"SCRIPT = {json.dumps(_narration_script_payload(manifest), indent=2, ensure_ascii=True)}\n",
        encoding="utf-8",
    )
    return script_path


def build_scene_spec(entry: SceneManifestEntry) -> dict[str, Any]:
    return {
        "title": entry.scene_title,
        "description": entry.scene_description,
        "visual_ideas": entry.visual_ideas,
        "narration_duration": entry.narration_duration_seconds,
    }


def ensure_scene_scaffolds(project_dir: Path, manifest: SceneManifest) -> list[Path]:
    created: list[Path] = []

    for scene in manifest.scenes:
        scene_path = project_dir / scene.scene_file
        if scene_path.exists():
            continue

        scene_path.parent.mkdir(parents=True, exist_ok=True)
        class_name = class_name_for_scene(scene.scene_id, scene.scene_title)
        template = f"""from manim import *
from wet_donkey.scene_helpers import *

# Narration script for this scene (auto-generated)
from narration_script import SCRIPT

class {class_name}(Scene):
    def construct(self):
        with self.voiceover(text=SCRIPT[\"{scene.scene_id}\"]) as tracker:
            {SLOT_START_MARKER}
            pass
            {SLOT_END_MARKER}
"""
        scene_path.write_text(template, encoding="utf-8")
        created.append(scene_path)

    return created


def _slot_body(scene_content: str) -> str:
    if scene_content.count(SLOT_START_MARKER) != 1 or scene_content.count(SLOT_END_MARKER) != 1:
        raise ValueError("scene scaffold markers missing or duplicated")

    start = scene_content.find(SLOT_START_MARKER) + len(SLOT_START_MARKER)
    end = scene_content.find(SLOT_END_MARKER)
    if start >= end:
        raise ValueError("invalid scaffold marker order")

    return scene_content[start:end]


def _body_has_executable_content(slot_body: str) -> bool:
    filtered = []
    for line in slot_body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "pass":
            continue
        filtered.append(stripped)

    return bool(filtered)


def validate_built_scene_files(project_dir: Path, manifest: SceneManifest) -> list[str]:
    errors: list[str] = []
    for scene in manifest.scenes:
        scene_path = project_dir / scene.scene_file
        if not scene_path.exists():
            errors.append(f"missing scene file for {scene.scene_id}: {scene_path}")
            continue

        content = scene_path.read_text(encoding="utf-8")
        try:
            slot_body = _slot_body(content)
        except ValueError as exc:
            errors.append(f"invalid scaffold markers for {scene.scene_id}: {exc}")
            continue

        if not _body_has_executable_content(slot_body):
            errors.append(f"scene body is empty for {scene.scene_id}: {scene_path}")

    return errors


def scene_qc_report_path(project_dir: Path, scene: SceneManifestEntry) -> Path:
    scene_stem = Path(scene.scene_file).stem
    return project_dir / "qc" / f"{scene_stem}_qc.json"


def write_scene_qc_report(
    project_dir: Path,
    scene: SceneManifestEntry,
    qc_result: SceneQC,
    *,
    output_path: Path | None = None,
) -> Path:
    destination = output_path or scene_qc_report_path(project_dir, scene)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = SceneQCRecord(
        scene_id=scene.scene_id,
        scene_file=scene.scene_file,
        scene_title=qc_result.scene_title,
        passed=qc_result.passed,
        score=qc_result.score,
        issues=[issue.model_dump(mode="json") for issue in qc_result.issues],
    )
    destination.write_text(json.dumps(payload.model_dump(mode="json"), indent=2), encoding="utf-8")
    return destination


def validate_scene_qc_reports(project_dir: Path, manifest: SceneManifest, *, min_score: float = 0.7) -> list[str]:
    if min_score < 0.0 or min_score > 1.0:
        raise ValueError("min_score must be between 0.0 and 1.0")

    errors: list[str] = []
    for scene in manifest.scenes:
        report_path = scene_qc_report_path(project_dir, scene)
        if not report_path.exists():
            errors.append(f"missing QC report for {scene.scene_id}: {report_path}")
            continue

        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            report = SceneQCRecord.model_validate(payload)
        except Exception as exc:
            errors.append(f"invalid QC report for {scene.scene_id}: {exc}")
            continue

        if report.scene_id != scene.scene_id:
            errors.append(
                f"QC scene_id mismatch for {scene.scene_id}: report={report.scene_id} expected={scene.scene_id}"
            )

        if not report.passed:
            errors.append(f"QC failed for {scene.scene_id}: passed=false")

        if report.score < min_score:
            errors.append(
                f"QC score below threshold for {scene.scene_id}: score={report.score} threshold={min_score}"
            )

    return errors
