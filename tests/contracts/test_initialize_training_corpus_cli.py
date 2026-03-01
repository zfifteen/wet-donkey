from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import grpc
import scripts.initialize_training_corpus as initialize_training_corpus


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "initialize_training_corpus.py"


def test_initialize_training_corpus_exits_with_policy_code_on_invalid_management_key(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["XAI_MANAGEMENT_API_KEY"] = "invalid-management-key"

    result = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--project-dir",
            str(project_dir),
            "--project-name",
            "bad-key-project",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 4
    combined = f"{result.stdout}\n{result.stderr}"
    assert (
        "Invalid XAI_MANAGEMENT_API_KEY for collections operations" in combined
        or "Collections initialization failed:" in combined
    )


class _FakeUnauthenticated(grpc.RpcError):
    def code(self):
        return grpc.StatusCode.UNAUTHENTICATED

    def details(self):
        return "Invalid bearer token. Please ensure you use a valid management key."


def test_management_host_candidates_uses_override(monkeypatch) -> None:
    monkeypatch.setenv("XAI_MANAGEMENT_API_HOST", "api.x.ai")
    assert initialize_training_corpus._management_host_candidates() == ["api.x.ai"]


def test_build_client_with_host_fallback_retries_on_legacy_host(monkeypatch) -> None:
    call_hosts: list[str] = []

    class _FakeCollections:
        def __init__(self, host: str):
            self.host = host

        def list(self, limit: int):
            _ = limit
            if self.host == "management-api.x.ai":
                raise _FakeUnauthenticated()
            return []

    class _FakeClient:
        def __init__(self, **kwargs):
            host = kwargs["management_api_host"]
            call_hosts.append(host)
            self.collections = _FakeCollections(host)

    monkeypatch.delenv("XAI_MANAGEMENT_API_HOST", raising=False)
    monkeypatch.setattr(initialize_training_corpus, "Client", _FakeClient)

    client = initialize_training_corpus._build_client_with_host_fallback(
        api_key="api-key",
        management_api_key="mgmt-key",
    )

    assert call_hosts == ["management-api.x.ai", "api.x.ai"]
    assert isinstance(client, _FakeClient)
