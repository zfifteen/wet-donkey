from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Union


class HarnessExitCode(IntEnum):
    SUCCESS = 0
    INFRASTRUCTURE_ERROR = 1
    VALIDATION_ERROR = 2
    SCHEMA_VIOLATION = 3
    POLICY_VIOLATION = 4
    MANUAL_GATE_REQUIRED = 5


@dataclass(frozen=True)
class ExitCodePolicy:
    category: str
    gate: str
    owner_component: str
    machine_error_code: str
    default_action: str
    retryable: bool


_SCHEMA_RETRYABLE_PHASES = {"plan", "narration", "build_scenes", "scene_qc"}
VALIDATION_GATE_ORDER: tuple[str, ...] = ("schema", "contract", "semantic", "runtime", "assembly")
_VALIDATION_GATE_INDEX = {gate: index for index, gate in enumerate(VALIDATION_GATE_ORDER)}


EXIT_CODE_POLICIES: dict[HarnessExitCode, ExitCodePolicy] = {
    HarnessExitCode.SUCCESS: ExitCodePolicy(
        category="success",
        gate="assembly",
        owner_component="orchestrator",
        machine_error_code="SUCCESS",
        default_action="advance_phase",
        retryable=False,
    ),
    HarnessExitCode.INFRASTRUCTURE_ERROR: ExitCodePolicy(
        category="infrastructure",
        gate="runtime",
        owner_component="harness",
        machine_error_code="INFRASTRUCTURE_ERROR",
        default_action="retry_or_block",
        retryable=True,
    ),
    HarnessExitCode.VALIDATION_ERROR: ExitCodePolicy(
        category="semantic_contract",
        gate="semantic",
        owner_component="parser",
        machine_error_code="VALIDATION_ERROR",
        default_action="retry_with_failure_context",
        retryable=True,
    ),
    HarnessExitCode.SCHEMA_VIOLATION: ExitCodePolicy(
        category="schema",
        gate="schema",
        owner_component="harness",
        machine_error_code="SCHEMA_VIOLATION",
        default_action="retry_with_schema_diagnostics",
        retryable=True,
    ),
    HarnessExitCode.POLICY_VIOLATION: ExitCodePolicy(
        category="policy",
        gate="contract",
        owner_component="orchestrator",
        machine_error_code="POLICY_VIOLATION",
        default_action="immediate_block",
        retryable=False,
    ),
    HarnessExitCode.MANUAL_GATE_REQUIRED: ExitCodePolicy(
        category="manual_gate",
        gate="assembly",
        owner_component="orchestrator",
        machine_error_code="MANUAL_GATE_REQUIRED",
        default_action="wait_for_human_action",
        retryable=False,
    ),
}


def get_exit_code_policy(code: Union[int, HarnessExitCode], phase: Optional[str] = None) -> ExitCodePolicy:
    enum_code = HarnessExitCode(code)
    base_policy = EXIT_CODE_POLICIES[enum_code]

    if enum_code is HarnessExitCode.SCHEMA_VIOLATION and phase is not None:
        return ExitCodePolicy(
            category=base_policy.category,
            gate=base_policy.gate,
            owner_component=base_policy.owner_component,
            machine_error_code=base_policy.machine_error_code,
            default_action=base_policy.default_action,
            retryable=phase in _SCHEMA_RETRYABLE_PHASES,
        )

    return base_policy


def is_retryable_for_phase(code: Union[int, HarnessExitCode], phase: Optional[str] = None) -> bool:
    return get_exit_code_policy(code, phase=phase).retryable


def validate_gate_sequence(gates: list[str]) -> bool:
    """
    Return True when gates are monotonic by canonical validation hierarchy order.
    """
    if not gates:
        return True

    seen = []
    for gate in gates:
        if gate not in _VALIDATION_GATE_INDEX:
            raise ValueError(f"unknown validation gate '{gate}'")
        seen.append(_VALIDATION_GATE_INDEX[gate])

    return seen == sorted(seen)
