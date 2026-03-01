from __future__ import annotations

from harness.exit_codes import (
    EXIT_CODE_POLICIES,
    HarnessExitCode,
    get_exit_code_policy,
    is_retryable_for_phase,
    validate_gate_sequence,
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
    assert policy.gate == "contract"
    assert policy.owner_component == "orchestrator"


def test_exit_codes_include_gate_and_owner_metadata() -> None:
    schema_policy = get_exit_code_policy(HarnessExitCode.SCHEMA_VIOLATION, phase="build_scenes")
    semantic_policy = get_exit_code_policy(HarnessExitCode.VALIDATION_ERROR)
    runtime_policy = get_exit_code_policy(HarnessExitCode.INFRASTRUCTURE_ERROR)

    assert schema_policy.gate == "schema"
    assert schema_policy.owner_component == "harness"
    assert semantic_policy.gate == "semantic"
    assert semantic_policy.owner_component == "parser"
    assert runtime_policy.gate == "runtime"
    assert runtime_policy.owner_component == "harness"


def test_validation_gate_sequence_must_be_monotonic() -> None:
    assert validate_gate_sequence(["schema", "contract", "semantic", "runtime", "assembly"]) is True
    assert validate_gate_sequence(["schema", "semantic", "runtime"]) is True
    assert validate_gate_sequence(["runtime", "schema"]) is False
