from __future__ import annotations

import re
import stat
import subprocess
import sys
from pathlib import Path

KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
TODO_LINE = (
    "# TODO: Provision a dedicated XAI_MANAGEMENT_API_KEY; currently reusing "
    "XAI_API_KEY temporarily."
)


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "bootstrap_env_from_fh.py"


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = KEY_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        raw = match.group(2).strip()
        if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
            raw = raw[1:-1]
        values[key] = raw.replace('\\"', '"').replace('\\\\', '\\')
    return values


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_script_path()), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_bootstrap_reuses_source_key_and_writes_management_todo(tmp_path) -> None:
    template_env = tmp_path / ".env.example"
    source_env = tmp_path / "fh.env"
    target_env = tmp_path / ".env"

    template_env.write_text(
        "XAI_API_KEY=\"\"\n"
        "XAI_MANAGEMENT_API_KEY=\"\"\n"
        "FH_ENABLE_TRAINING_CORPUS=\"1\"\n"
        "FH_TEMPLATE_COLLECTION_ID=\"\"\n",
        encoding="utf-8",
    )

    secret = "test-source-api-key"
    source_env.write_text(f"XAI_API_KEY=\"{secret}\"\n", encoding="utf-8")

    result = _run(
        "--target-env",
        str(target_env),
        "--template-env",
        str(template_env),
        "--source-env",
        str(source_env),
    )

    assert result.returncode == 0, result.stderr
    assert target_env.exists()

    content = target_env.read_text(encoding="utf-8")
    assert TODO_LINE in content
    values = _parse_env(target_env)

    assert values["XAI_API_KEY"] == secret
    assert values["XAI_MANAGEMENT_API_KEY"] == secret
    assert values["FH_ENABLE_TRAINING_CORPUS"] == "1"

    output = result.stdout + result.stderr
    assert secret not in output

    mode = stat.S_IMODE(target_env.stat().st_mode)
    assert mode == 0o600


def test_bootstrap_uses_template_defaults_when_source_missing(tmp_path) -> None:
    template_env = tmp_path / ".env.example"
    source_env = tmp_path / "missing.env"
    target_env = tmp_path / ".env"

    template_env.write_text(
        "XAI_API_KEY=\"PLACEHOLDER\"\n"
        "XAI_MANAGEMENT_API_KEY=\"\"\n"
        "FH_ENABLE_TRAINING_CORPUS=\"1\"\n"
        "FH_TEMPLATE_COLLECTION_ID=\"\"\n",
        encoding="utf-8",
    )

    result = _run(
        "--target-env",
        str(target_env),
        "--template-env",
        str(template_env),
        "--source-env",
        str(source_env),
    )

    assert result.returncode == 0, result.stderr
    values = _parse_env(target_env)
    assert values["XAI_API_KEY"] == "PLACEHOLDER"
    assert values["XAI_MANAGEMENT_API_KEY"] == "PLACEHOLDER"


def test_bootstrap_preserves_existing_values_unless_force(tmp_path) -> None:
    template_env = tmp_path / ".env.example"
    source_env = tmp_path / "fh.env"
    target_env = tmp_path / ".env"

    template_env.write_text(
        "XAI_API_KEY=\"\"\n"
        "XAI_MANAGEMENT_API_KEY=\"\"\n"
        "FH_ENABLE_TRAINING_CORPUS=\"1\"\n"
        "FH_TEMPLATE_COLLECTION_ID=\"\"\n",
        encoding="utf-8",
    )
    source_env.write_text("XAI_API_KEY=\"source-value\"\n", encoding="utf-8")
    target_env.write_text(
        "XAI_API_KEY=\"existing-value\"\n"
        "XAI_MANAGEMENT_API_KEY=\"existing-management\"\n"
        "FH_ENABLE_TRAINING_CORPUS=\"1\"\n"
        "FH_TEMPLATE_COLLECTION_ID=\"\"\n",
        encoding="utf-8",
    )

    preserve = _run(
        "--target-env",
        str(target_env),
        "--template-env",
        str(template_env),
        "--source-env",
        str(source_env),
    )
    assert preserve.returncode == 0

    values = _parse_env(target_env)
    assert values["XAI_API_KEY"] == "existing-value"
    assert values["XAI_MANAGEMENT_API_KEY"] == "existing-management"

    force = _run(
        "--target-env",
        str(target_env),
        "--template-env",
        str(template_env),
        "--source-env",
        str(source_env),
        "--force",
    )
    assert force.returncode == 0

    values = _parse_env(target_env)
    assert values["XAI_API_KEY"] == "source-value"
    assert values["XAI_MANAGEMENT_API_KEY"] == "source-value"
