from __future__ import annotations

import shutil
from pathlib import Path

from breakbot.config import BreakBotConfig
from breakbot.models import GeneratedTest, SourceBundle


class WorkspaceBuilder:
    def __init__(self, config: BreakBotConfig):
        self.config = config

    def materialize(self, source: SourceBundle, tests: list[GeneratedTest]) -> Path:
        root = self.config.run_root / _safe_name(source.source_name)
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)

        for file in source.files:
            target = root / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(file.content, encoding="utf-8")

        for test in tests:
            target = root / test.file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(test.content, encoding="utf-8")

        return root


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:80]
