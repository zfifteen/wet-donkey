from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PhaseName = Literal[
    "init",
    "plan",
    "review",
    "narration",
    "build_scenes",
    "scene_qc",
    "precache_voiceovers",
    "final_render",
    "assemble",
    "complete",
]

PhaseStatus = Literal["active", "blocked", "complete"]

CONTRACT_VERSION = "1.0.0"

PHASE_SEQUENCE: tuple[PhaseName, ...] = (
    "init",
    "plan",
    "review",
    "narration",
    "build_scenes",
    "scene_qc",
    "precache_voiceovers",
    "final_render",
    "assemble",
    "complete",
)

DEFAULT_MAX_ATTEMPTS: dict[PhaseName, int] = {
    "init": 1,
    "plan": 2,
    "review": 1,
    "narration": 2,
    "build_scenes": 4,
    "scene_qc": 3,
    "precache_voiceovers": 2,
    "final_render": 2,
    "assemble": 2,
    "complete": 1,
}

LOOP_SIGNATURE_REPEAT_BLOCK_THRESHOLD = 2

_TRANSITIONS: dict[PhaseName, tuple[PhaseName, ...]] = {
    "init": ("plan",),
    "plan": ("review",),
    "review": ("narration",),
    "narration": ("build_scenes",),
    "build_scenes": ("scene_qc",),
    "scene_qc": ("precache_voiceovers",),
    "precache_voiceovers": ("final_render",),
    "final_render": ("assemble",),
    "assemble": ("complete",),
    "complete": (),
}


class PhaseTransitionError(ValueError):
    """Raised when a state transition violates the canonical phase graph."""


class HistoryEntry(BaseModel):
    phase: PhaseName
    timestamp: str
    actor: Optional[str] = None
    reason: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def _timestamp_must_be_utc_z(cls, value: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", value):
            raise ValueError("timestamp must be UTC with trailing Z")
        return value


class ProjectState(BaseModel):
    model_config = ConfigDict(extra="allow")

    contract_version: str = CONTRACT_VERSION
    project_name: str
    topic: str
    phase: PhaseName
    phase_status: PhaseStatus = "active"
    history: list[HistoryEntry] = Field(min_length=1)

    @field_validator("contract_version")
    @classmethod
    def _semver_contract_version(cls, value: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise ValueError("contract_version must follow semver (x.y.z)")
        return value

    @model_validator(mode="after")
    def _history_phase_alignment(self) -> "ProjectState":
        if self.history[-1].phase != self.phase:
            raise ValueError("latest history phase must match current phase")
        if self.phase == "complete" and self.phase_status != "complete":
            raise ValueError("phase_status must be complete when phase is complete")
        if self.phase != "complete" and self.phase_status == "complete":
            raise ValueError("phase_status complete is only valid when phase is complete")
        return self


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def allowed_next_phases(phase: PhaseName) -> tuple[PhaseName, ...]:
    return _TRANSITIONS[phase]


def can_transition(from_phase: PhaseName, to_phase: PhaseName) -> bool:
    return to_phase in allowed_next_phases(from_phase)


def create_initial_state(project_name: str, topic: str) -> ProjectState:
    return ProjectState(
        contract_version=CONTRACT_VERSION,
        project_name=project_name,
        topic=topic,
        phase="init",
        phase_status="active",
        history=[HistoryEntry(phase="init", timestamp=utc_timestamp(), actor="orchestrator")],
    )


def normalize_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("contract_version", CONTRACT_VERSION)

    phase = data.get("phase", "init")
    if "phase_status" not in data:
        data["phase_status"] = "complete" if phase == "complete" else "active"

    history = data.get("history")
    if not history:
        data["history"] = [{"phase": phase, "timestamp": utc_timestamp(), "actor": "orchestrator"}]

    data.setdefault("attempt_counters", {})
    data.setdefault("failure_context", {})

    return data


def load_state(state_file: Path) -> ProjectState:
    raw = json.loads(state_file.read_text())
    normalized = normalize_state_payload(raw)
    return ProjectState.model_validate(normalized)


def save_state_atomic(state_file: Path, state: ProjectState) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state.model_dump(mode="json"), indent=2)

    with NamedTemporaryFile("w", dir=state_file.parent, delete=False, encoding="utf-8") as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)

    tmp_path.replace(state_file)


def update_state_key(state: ProjectState, key: str, value: Any) -> ProjectState:
    payload = state.model_dump(mode="json")
    payload[key] = value
    normalized = normalize_state_payload(payload)
    return ProjectState.model_validate(normalized)


def transition_state(
    state: ProjectState,
    to_phase: PhaseName,
    *,
    actor: str = "orchestrator",
    reason: Optional[str] = None,
) -> ProjectState:
    if to_phase == state.phase:
        return state

    if not can_transition(state.phase, to_phase):
        raise PhaseTransitionError(f"invalid phase transition: {state.phase} -> {to_phase}")

    payload = state.model_dump(mode="json")
    payload["phase"] = to_phase
    payload["phase_status"] = "complete" if to_phase == "complete" else "active"
    payload["history"] = [
        *payload["history"],
        {
            "phase": to_phase,
            "timestamp": utc_timestamp(),
            "actor": actor,
            "reason": reason,
        },
    ]

    attempt_counters = dict(payload.get("attempt_counters", {}))
    attempt_counters.pop(to_phase, None)
    payload["attempt_counters"] = attempt_counters

    failure_context = dict(payload.get("failure_context", {}))
    if failure_context.get("phase") == to_phase:
        failure_context = {}
    payload["failure_context"] = failure_context

    normalized = normalize_state_payload(payload)
    return ProjectState.model_validate(normalized)


def get_attempt_count(state: ProjectState, phase: PhaseName) -> int:
    payload = state.model_dump(mode="json")
    counters = payload.get("attempt_counters", {})
    try:
        return int(counters.get(phase, 0))
    except (TypeError, ValueError):
        return 0


def normalize_error_signature(
    *,
    phase: PhaseName,
    gate: str,
    error_code: str,
    error_message: str,
) -> str:
    raw = "|".join(
        [
            phase.strip().lower(),
            gate.strip().lower(),
            error_code.strip().upper(),
            " ".join(error_message.strip().split()).lower(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_non_empty(value: Optional[str]) -> bool:
    return bool(value and value.strip())


def record_phase_failure(
    state: ProjectState,
    *,
    error_code: str,
    error_message: str,
    gate: str = "runtime",
    owner_component: str = "orchestrator",
    retryable: bool = True,
    error_signature: Optional[str] = None,
    attempt_delta: Optional[str] = None,
    evidence_token: Optional[str] = None,
    max_attempts_by_phase: Optional[dict[PhaseName, int]] = None,
    actor: str = "orchestrator",
    force_block: bool = False,
) -> ProjectState:
    if state.phase == "complete":
        raise PhaseTransitionError("cannot record failure in complete phase")

    phase: PhaseName = state.phase
    limits = max_attempts_by_phase or DEFAULT_MAX_ATTEMPTS
    phase_limit = limits[phase]

    payload = state.model_dump(mode="json")
    counters = dict(payload.get("attempt_counters", {}))
    attempt = int(counters.get(phase, 0)) + 1
    counters[phase] = attempt
    payload["attempt_counters"] = counters

    previous_failure = dict(payload.get("failure_context", {}))
    previous_signature = previous_failure.get("error_signature")
    signature = error_signature or normalize_error_signature(
        phase=phase,
        gate=gate,
        error_code=error_code,
        error_message=error_message,
    )

    same_signature_as_previous = bool(previous_signature) and previous_signature == signature
    has_meaningful_delta = (
        attempt == 1
        or not same_signature_as_previous
        or _is_non_empty(attempt_delta)
        or _is_non_empty(evidence_token)
    )
    blind_retry = retryable and attempt > 1 and not has_meaningful_delta
    loop_risk = (
        retryable
        and same_signature_as_previous
        and not has_meaningful_delta
        and attempt >= LOOP_SIGNATURE_REPEAT_BLOCK_THRESHOLD
    )

    blocked_reason: Optional[str] = None
    if force_block:
        blocked_reason = "FORCE_BLOCK"
    elif not retryable:
        blocked_reason = "NON_RETRYABLE_FAILURE"
    elif blind_retry:
        blocked_reason = "NO_NEW_EVIDENCE"
    elif loop_risk:
        blocked_reason = "LOOP_SIGNATURE_REPEAT"
    elif attempt >= phase_limit:
        blocked_reason = "RETRY_BUDGET_EXHAUSTED"

    blocked = blocked_reason is not None
    payload["phase_status"] = "blocked" if blocked else "active"
    payload["failure_context"] = {
        "phase": phase,
        "gate": gate,
        "owner_component": owner_component,
        "error_code": error_code,
        "error_message": error_message,
        "retryable": retryable,
        "error_signature": signature,
        "previous_error_signature": previous_signature,
        "same_signature_as_previous": same_signature_as_previous,
        "attempt_delta": attempt_delta,
        "evidence_token": evidence_token,
        "has_meaningful_delta": has_meaningful_delta,
        "blind_retry": blind_retry,
        "loop_risk": loop_risk,
        "loop_signature_repeat_threshold": LOOP_SIGNATURE_REPEAT_BLOCK_THRESHOLD,
        "blocked_reason": blocked_reason,
        "attempt": attempt,
        "max_attempts": phase_limit,
        "blocked": blocked,
        "timestamp": utc_timestamp(),
    }
    payload["history"] = [
        *payload["history"],
        {
            "phase": phase,
            "timestamp": utc_timestamp(),
            "actor": actor,
            "reason": f"failure:{gate}:{error_code}:attempt={attempt}",
        },
    ]

    normalized = normalize_state_payload(payload)
    return ProjectState.model_validate(normalized)


def clear_phase_failures(
    state: ProjectState,
    *,
    actor: str = "orchestrator",
    reason: Optional[str] = None,
) -> ProjectState:
    phase = state.phase
    payload = state.model_dump(mode="json")

    counters = dict(payload.get("attempt_counters", {}))
    counters.pop(phase, None)
    payload["attempt_counters"] = counters

    payload["failure_context"] = {}
    if payload.get("phase_status") == "blocked":
        payload["phase_status"] = "active"
        payload["history"] = [
            *payload["history"],
            {
                "phase": phase,
                "timestamp": utc_timestamp(),
                "actor": actor,
                "reason": reason or "manual_resume",
            },
        ]

    normalized = normalize_state_payload(payload)
    return ProjectState.model_validate(normalized)
