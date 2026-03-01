from __future__ import annotations

import json
from pathlib import Path


REQUIRED_M6_LESSONS = {"L-003", "L-006", "L-007", "L-009", "L-010"}


def _load_matrix() -> dict:
    matrix_path = Path(__file__).resolve().parent / "lessons_regression_matrix.json"
    return json.loads(matrix_path.read_text(encoding="utf-8"))


def test_lessons_regression_matrix_includes_required_m6_lessons() -> None:
    matrix = _load_matrix()
    assert REQUIRED_M6_LESSONS.issubset(matrix.keys())


def test_lessons_regression_matrix_points_to_existing_tests() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    matrix = _load_matrix()

    for lesson_id, entries in matrix.items():
        assert entries, f"{lesson_id} must include at least one test mapping"

        for entry in entries:
            path = root_dir / entry["path"]
            test_name = entry["test"]

            assert path.exists(), f"Mapped test file does not exist: {path}"
            file_text = path.read_text(encoding="utf-8")
            assert test_name in file_text, f"Mapped test name missing: {lesson_id} -> {test_name}"
