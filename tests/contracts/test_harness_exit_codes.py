from __future__ import annotations

from harness.exit_codes import (
    EXIT_CODE_POLICIES,
    HarnessExitCode,
    get_exit_code_policy,
    is_retryable_for_phase,
)


def test_exit_code_table_contains_all_canonical_codes() -> None:
    assert set(EXIT_CODE_POLICIES.keys()) == {
        HarnessExitCode.SUCCESS,
        HarnessExitCode.INFRASTRUCTURE_ERROR,
        HarnessExitCode.VALIDATION_ERROR,
        HarnessExitCode.SCHEMA_VIOLATION,
        HarnessExitCode.POLICY_VIOLATION,
        HarnessExitCode.MANUAL_GATE_REQUIRED,
    }


def test_schema_violation_retryability_is_phase_specific() -> None:
    assert is_retryable_for_phase(HarnessExitCode.SCHEMA_VIOLATION, "plan") is True
    assert is_retryable_for_phase(HarnessExitCode.SCHEMA_VIOLATION, "build_scenes") is True
    assert is_retryable_for_phase(HarnessExitCode.SCHEMA_VIOLATION, "final_render") is False
    assert is_retryable_for_phase(HarnessExitCode.SCHEMA_VIOLATION, "assemble") is False


def test_policy_violation_is_non_retryable() -> None:
    policy = get_exit_code_policy(HarnessExitCode.POLICY_VIOLATION)

    assert policy.retryable is False
    assert policy.default_action == "immediate_block"
