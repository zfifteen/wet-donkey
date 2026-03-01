from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

OBSERVABILITY_CONTRACT_VERSION = "1.0.0"
RUN_CONTEXT_FILE = ".run_context.json"
EVENTS_LOG_RELATIVE_PATH = Path("log/events.jsonl")
TRACE_BUNDLE_RELATIVE_DIR = Path("log/trace-bundles")

EventType = Literal[
    "phase_start",
    "phase_success",
    "phase_failure",
    "phase_blocked",
    "phase_transition",
    "phase_unblocked",
    "diagnostic_bundle",
]


class ContextBudgetMarker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_tokens: int | None = None
    budget_tokens: int | None = None
    compaction_applied: bool = False


class RetryContextMarker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preserved_full_context: bool = False
    meaningful_delta: bool = False


class ObservabilityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = OBSERVABILITY_CONTRACT_VERSION
    timestamp_utc: str
    run_id: str
    phase: str
    phase_attempt_id: str
    event_type: EventType
    actor: str = "orchestrator"
    component_owner: str | None = None
    gate: str | None = None
    retryable: bool | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_signature: str | None = None
    previous_error_signature: str | None = None
    attempt_delta: str | None = None
    evidence_token: str | None = None
    next_action: str | None = None
    artifact_pointers: list[str] = Field(default_factory=list)
    context_budget_marker: ContextBudgetMarker = Field(default_factory=ContextBudgetMarker)
    retry_context_marker: RetryContextMarker = Field(default_factory=RetryContextMarker)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("contract_version")
    @classmethod
    def _validate_contract_version(cls, value: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise ValueError("contract_version must follow semver (x.y.z)")
        return value

    @field_validator("timestamp_utc")
    @classmethod
    def _validate_timestamp(cls, value: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", value):
            raise ValueError("timestamp_utc must be UTC with trailing Z")
        return value

    @field_validator("run_id", "phase", "phase_attempt_id", "actor")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("value must be non-empty")
        return normalized


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_phase_attempt_id(phase: str, attempt: int) -> str:
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    normalized_phase = " ".join(phase.strip().split())
    if not normalized_phase:
        raise ValueError("phase must be non-empty")
    return f"{normalized_phase}:attempt:{attempt}"


def _run_context_path(project_dir: Path) -> Path:
    return project_dir / RUN_CONTEXT_FILE


def _events_path(project_dir: Path) -> Path:
    return project_dir / EVENTS_LOG_RELATIVE_PATH


def ensure_run_context(project_dir: Path) -> str:
    run_context_file = _run_context_path(project_dir)
    if run_context_file.exists():
        payload = json.loads(run_context_file.read_text(encoding="utf-8"))
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id.strip():
            return run_id

    run_id = f"{project_dir.name}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    run_context_file.write_text(
        json.dumps(
            {
                "contract_version": OBSERVABILITY_CONTRACT_VERSION,
                "run_id": run_id,
                "created_at": utc_timestamp(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return run_id


def append_event(project_dir: Path, event: ObservabilityEvent) -> Path:
    events_path = _events_path(project_dir)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")
    return events_path


def read_events(project_dir: Path, *, tail: int | None = None) -> list[dict[str, Any]]:
    events_path = _events_path(project_dir)
    if not events_path.exists():
        return []

    lines = events_path.read_text(encoding="utf-8").splitlines()
    if tail is not None and tail >= 0:
        lines = lines[-tail:]

    parsed: list[dict[str, Any]] = []
    for line in lines:
        if line.strip():
            parsed.append(json.loads(line))
    return parsed


def emit_phase_event(
    project_dir: Path,
    *,
    phase: str,
    event_type: EventType,
    attempt: int,
    actor: str = "orchestrator",
    metadata: dict[str, Any] | None = None,
    next_action: str | None = None,
) -> ObservabilityEvent:
    run_id = ensure_run_context(project_dir)
    event = ObservabilityEvent(
        timestamp_utc=utc_timestamp(),
        run_id=run_id,
        phase=phase,
        phase_attempt_id=build_phase_attempt_id(phase, attempt),
        event_type=event_type,
        actor=actor,
        next_action=next_action,
        metadata=metadata or {},
    )
    append_event(project_dir, event)
    return event


def recommended_next_action(blocked_reason: str | None, retryable: bool | None) -> str:
    if blocked_reason == "NO_NEW_EVIDENCE":
        return "Attach attempt_delta or evidence_token before retrying."
    if blocked_reason == "RETRY_BUDGET_EXHAUSTED":
        return "Manual decision required: retry_with_override, accept_partial, or abort."
    if blocked_reason == "NON_RETRYABLE_FAILURE" or retryable is False:
        return "Fix the contract violation directly before resuming."
    if blocked_reason == "FORCE_BLOCK":
        return "Manual intervention required due to policy gate."
    return "Review failure_context and choose explicit remediation action."


def _artifact_pointers_for_project(project_dir: Path) -> list[str]:
    candidates = (
        Path("project_state.json"),
        Path("artifacts/voice_manifest.json"),
        Path("artifacts/render_preconditions.json"),
        Path("artifacts/render_manifest.json"),
        Path("artifacts/assembly_manifest.json"),
        EVENTS_LOG_RELATIVE_PATH,
    )
    pointers: list[str] = []
    for relative in candidates:
        if (project_dir / relative).exists():
            pointers.append(str(relative))
    return pointers


def event_from_failure_context(
    project_dir: Path,
    *,
    phase: str,
    failure_context: dict[str, Any],
    actor: str,
) -> ObservabilityEvent:
    run_id = ensure_run_context(project_dir)

    attempt = int(failure_context.get("attempt", 1) or 1)
    blocked = bool(failure_context.get("blocked", False))
    blocked_reason = failure_context.get("blocked_reason")

    event_type: EventType = "phase_blocked" if blocked else "phase_failure"

    context_budget_marker = ContextBudgetMarker(
        estimated_tokens=failure_context.get("context_estimated_tokens"),
        budget_tokens=failure_context.get("context_budget_tokens"),
        compaction_applied=bool(failure_context.get("context_compaction_applied", False)),
    )
    retry_context_marker = RetryContextMarker(
        preserved_full_context=bool(failure_context.get("retry_context_preserved", False)),
        meaningful_delta=bool(failure_context.get("has_meaningful_delta", False)),
    )

    event = ObservabilityEvent(
        timestamp_utc=utc_timestamp(),
        run_id=run_id,
        phase=phase,
        phase_attempt_id=build_phase_attempt_id(phase, attempt),
        event_type=event_type,
        actor=actor,
        component_owner=failure_context.get("owner_component"),
        gate=failure_context.get("gate"),
        retryable=failure_context.get("retryable"),
        error_code=failure_context.get("error_code"),
        error_message=failure_context.get("error_message"),
        error_signature=failure_context.get("error_signature"),
        previous_error_signature=failure_context.get("previous_error_signature"),
        attempt_delta=failure_context.get("attempt_delta"),
        evidence_token=failure_context.get("evidence_token"),
        next_action=recommended_next_action(blocked_reason, failure_context.get("retryable")),
        artifact_pointers=_artifact_pointers_for_project(project_dir),
        context_budget_marker=context_budget_marker,
        retry_context_marker=retry_context_marker,
        metadata={
            "blocked": blocked,
            "blocked_reason": blocked_reason,
            "same_signature_as_previous": bool(failure_context.get("same_signature_as_previous", False)),
            "loop_risk": bool(failure_context.get("loop_risk", False)),
            "max_attempts": failure_context.get("max_attempts"),
        },
    )
    return event


def export_blocked_trace_bundle(
    project_dir: Path,
    *,
    state_payload: dict[str, Any],
    actor: str,
) -> Path:
    phase = str(state_payload.get("phase", "unknown"))
    phase_status = str(state_payload.get("phase_status", "active"))
    failure_context = dict(state_payload.get("failure_context") or {})

    if phase_status != "blocked" or not failure_context:
        raise ValueError("blocked trace bundle requires blocked phase_status and failure_context")

    run_id = ensure_run_context(project_dir)
    timestamp = utc_timestamp()
    trace_dir = project_dir / TRACE_BUNDLE_RELATIVE_DIR
    trace_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = trace_dir / f"blocked-{phase}-{timestamp.replace(':', '').replace('-', '')}.json"

    history = state_payload.get("history", [])
    retry_history = [
        entry
        for entry in history
        if isinstance(entry, dict)
        and entry.get("phase") == phase
        and isinstance(entry.get("reason"), str)
        and entry.get("reason", "").startswith("failure:")
    ]

    bundle = {
        "contract_version": OBSERVABILITY_CONTRACT_VERSION,
        "generated_at": timestamp,
        "run_id": run_id,
        "phase": phase,
        "phase_status": phase_status,
        "phase_attempt_id": build_phase_attempt_id(phase, int(failure_context.get("attempt", 1) or 1)),
        "failure_diagnostics": {
            "component_owner": failure_context.get("owner_component"),
            "gate": failure_context.get("gate"),
            "error_code": failure_context.get("error_code"),
            "error_message": failure_context.get("error_message"),
            "error_signature": failure_context.get("error_signature"),
            "previous_error_signature": failure_context.get("previous_error_signature"),
            "same_signature_as_previous": failure_context.get("same_signature_as_previous"),
            "attempt_delta": failure_context.get("attempt_delta"),
            "evidence_token": failure_context.get("evidence_token"),
            "retryable": failure_context.get("retryable"),
            "blocked_reason": failure_context.get("blocked_reason"),
            "next_action": recommended_next_action(
                failure_context.get("blocked_reason"),
                failure_context.get("retryable"),
            ),
            "retry_context_integrity_marker": {
                "preserved_full_context": bool(failure_context.get("retry_context_preserved", False)),
                "meaningful_delta": bool(failure_context.get("has_meaningful_delta", False)),
            },
            "context_budget_marker": {
                "estimated_tokens": failure_context.get("context_estimated_tokens"),
                "budget_tokens": failure_context.get("context_budget_tokens"),
                "compaction_applied": bool(failure_context.get("context_compaction_applied", False)),
            },
        },
        "retry_history_summary": retry_history,
        "artifact_pointers": _artifact_pointers_for_project(project_dir),
        "events_tail": read_events(project_dir, tail=50),
        "state_snapshot": state_payload,
    }

    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    diagnostic_event = ObservabilityEvent(
        timestamp_utc=timestamp,
        run_id=run_id,
        phase=phase,
        phase_attempt_id=bundle["phase_attempt_id"],
        event_type="diagnostic_bundle",
        actor=actor,
        next_action="Review blocked trace bundle before any override/resume action.",
        artifact_pointers=[str(bundle_path.relative_to(project_dir))],
        metadata={
            "bundle_path": str(bundle_path.relative_to(project_dir)),
            "blocked_reason": failure_context.get("blocked_reason"),
        },
    )
    append_event(project_dir, diagnostic_event)
    return bundle_path
