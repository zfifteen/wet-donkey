#!/usr/bin/env python3.13
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

_prompt_manifest_contract = importlib.import_module("harness.contracts.prompt_manifest")
PromptContractError = _prompt_manifest_contract.PromptContractError
validate_prompt_contracts = importlib.import_module("harness.prompts").validate_prompt_contracts


def main() -> int:
    try:
        validate_prompt_contracts()
    except (FileNotFoundError, PromptContractError) as exc:
        print(f"Prompt/schema alignment check failed: {exc}", file=sys.stderr)
        return 1

    print("Prompt/schema alignment check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
