from __future__ import annotations

import pytest

from harness.contracts.scaffold import (
    SLOT_END_MARKER,
    SLOT_START_MARKER,
    ScaffoldContractError,
    inject_scene_body,
)


TEMPLATE = f"""class Demo(Scene):
    def construct(self):
        with self.voiceover(text=\"x\"):
            {SLOT_START_MARKER}
            pass
            {SLOT_END_MARKER}
"""


def test_inject_scene_body_preserves_markers() -> None:
    body = "title = Text('Hello')\nself.play(Write(title))"

    rendered = inject_scene_body(TEMPLATE, body)

    assert rendered.count(SLOT_START_MARKER) == 1
    assert rendered.count(SLOT_END_MARKER) == 1
    assert "            title = Text('Hello')" in rendered
    assert "            self.play(Write(title))" in rendered


def test_inject_scene_body_normalizes_existing_indentation() -> None:
    body = "    title = Text('Hello')\n        self.play(Write(title))"
    rendered = inject_scene_body(TEMPLATE, body)
    assert "            title = Text('Hello')" in rendered
    assert "                self.play(Write(title))" in rendered
    assert "            # SLOT_END:scene_body" in rendered


def test_inject_scene_body_requires_markers() -> None:
    with pytest.raises(ScaffoldContractError):
        inject_scene_body("class Demo(Scene):\n    pass\n", "self.play(FadeIn(Text('x')))" )


def test_inject_scene_body_rejects_marker_in_payload() -> None:
    with pytest.raises(ScaffoldContractError):
        inject_scene_body(TEMPLATE, f"bad {SLOT_START_MARKER} payload")
