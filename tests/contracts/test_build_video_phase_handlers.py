from __future__ import annotations

from pathlib import Path


def test_runtime_phase_handlers_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts" / "build_video.sh").read_text(encoding="utf-8")

    assert "narration:handle_narration" in script
    assert "build_scenes:handle_build_scenes" in script
    assert "scene_qc:handle_scene_qc" in script

    assert "narration:handle_unimplemented" not in script
    assert "build_scenes:handle_unimplemented" not in script
    assert "scene_qc:handle_unimplemented" not in script


def test_init_handler_requires_training_corpus_and_dedicated_management_key() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts" / "build_video.sh").read_text(encoding="utf-8")

    assert 'training_corpus_enabled="${FH_ENABLE_TRAINING_CORPUS:-1}"' not in script
    assert "Training corpus initialization is disabled" not in script
    assert "write_disabled_collections_metadata" not in script
    assert "phase start after project bootstrap" in script
    assert "CURRENT_PHASE_ATTEMPT" in script
    assert "requires a dedicated XAI_MANAGEMENT_API_KEY" in script
