#!/usr/bin/env python3.13
from __future__ import annotations

import argparse
import subprocess
import sys

CANONICAL_DOC_PREFIXES = (
    "AGENTS.md",
    "docs/implementation-plan/",
    "docs/lessons-learned/",
    "docs/tech-spec/",
)

CONTRACT_TOUCH_PREFIXES = (
    "src/harness/",
    "src/wet_donkey_voice/",
    "scripts/build_video.sh",
    "scripts/update_project_state.py",
    "scripts/validate_media_pipeline.py",
)


def _is_contract_touch(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in CONTRACT_TOUCH_PREFIXES)


def _is_canonical_doc(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in CANONICAL_DOC_PREFIXES)


def _changed_files_from_git(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_docs_gate(changed_files: list[str]) -> tuple[bool, str]:
    contract_touches = sorted({path for path in changed_files if _is_contract_touch(path)})
    if not contract_touches:
        return True, "Docs-as-gate passed: no contract-touching files changed."

    docs_touches = sorted({path for path in changed_files if _is_canonical_doc(path)})
    if docs_touches:
        return True, (
            "Docs-as-gate passed: contract-touching changes include canonical docs updates. "
            f"Contract files={contract_touches}; docs={docs_touches}"
        )

    return False, (
        "Docs-as-gate failed: contract-touching changes require canonical docs updates. "
        f"Contract files={contract_touches}; required one of prefixes={CANONICAL_DOC_PREFIXES}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when contract-touching code changes are missing canonical docs updates."
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD~1",
        help="Git base ref for change detection when --changed-file is not provided.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file path. May be provided multiple times. Overrides git diff when present.",
    )

    args = parser.parse_args()

    try:
        changed_files = args.changed_file or _changed_files_from_git(args.base_ref)
    except RuntimeError as exc:
        print(f"Docs-as-gate check failed: {exc}", file=sys.stderr)
        return 1

    ok, message = check_docs_gate(changed_files)
    output_stream = sys.stdout if ok else sys.stderr
    print(message, file=output_stream)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
