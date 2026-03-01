from __future__ import annotations

from pathlib import Path


def test_no_github_workflow_yaml_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflows_dir = repo_root / ".github" / "workflows"
    workflow_files = sorted(
        str(path.relative_to(repo_root))
        for pattern in ("*.yml", "*.yaml")
        for path in workflows_dir.glob(pattern)
    )
    assert workflow_files == [], (
        "GitHub workflow files are deferred for this version; remove workflow files: "
        f"{workflow_files}"
    )
