from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_prompt_schema_alignment_script_passes() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    script = root_dir / "scripts" / "check_prompt_schema_alignment.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "passed" in result.stdout.lower()
