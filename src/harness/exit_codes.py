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
    default_action: str
    retryable: bool


_SCHEMA_RETRYABLE_PHASES = {"plan", "narration", "build_scenes", "scene_qc"}


EXIT_CODE_POLICIES: dict[HarnessExitCode, ExitCodePolicy] = {
    HarnessExitCode.SUCCESS: ExitCodePolicy(
        category="success",
        default_action="advance_phase",
        retryable=False,
    ),
    HarnessExitCode.INFRASTRUCTURE_ERROR: ExitCodePolicy(
        category="infrastructure",
        default_action="retry_or_block",
        retryable=True,
    ),
    HarnessExitCode.VALIDATION_ERROR: ExitCodePolicy(
        category="semantic_contract",
        default_action="retry_with_failure_context",
        retryable=True,
    ),
    HarnessExitCode.SCHEMA_VIOLATION: ExitCodePolicy(
        category="schema",
        default_action="retry_with_schema_diagnostics",
        retryable=True,
    ),
    HarnessExitCode.POLICY_VIOLATION: ExitCodePolicy(
        category="policy",
        default_action="immediate_block",
        retryable=False,
    ),
    HarnessExitCode.MANUAL_GATE_REQUIRED: ExitCodePolicy(
        category="manual_gate",
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
            default_action=base_policy.default_action,
            retryable=phase in _SCHEMA_RETRYABLE_PHASES,
        )

    return base_policy


def is_retryable_for_phase(code: Union[int, HarnessExitCode], phase: Optional[str] = None) -> bool:
    return get_exit_code_policy(code, phase=phase).retryable
