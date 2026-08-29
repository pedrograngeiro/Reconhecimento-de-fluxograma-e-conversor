from __future__ import annotations

import sys
import types
from pathlib import Path

import treinar


def test_training_project_is_resolved_from_current_directory(
    monkeypatch, tmp_path: Path
) -> None:
    data = tmp_path / "data.yaml"
    data.write_text("names: {0: process}\n", encoding="utf-8")
    captured: dict[str, object] = {}

    class FakeYOLO:
        def __init__(self, model: str) -> None:
            captured["model"] = model

        def train(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["treinar.py", "--data", str(data), "--project", "runs/flowchart"],
    )

    assert treinar.main() == 0
    assert captured["project"] == str((tmp_path / "runs/flowchart").resolve())
