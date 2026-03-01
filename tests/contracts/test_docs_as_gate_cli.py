from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "check_docs_as_gate.py"


def test_docs_as_gate_fails_without_docs_for_contract_changes() -> None:
    script = _script_path()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--changed-file",
            "src/harness/contracts/state.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "failed" in result.stderr.lower()


def test_docs_as_gate_passes_with_canonical_docs_update() -> None:
    script = _script_path()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--changed-file",
            "src/harness/contracts/state.py",
            "--changed-file",
            "docs/implementation-plan/README.md",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "passed" in result.stdout.lower()


def test_docs_as_gate_passes_for_non_contract_changes() -> None:
    script = _script_path()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--changed-file",
            "README.md",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "passed" in result.stdout.lower()
