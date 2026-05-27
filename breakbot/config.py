from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BreakBotConfig:
    model: str = "gemini-1.5-flash"
    max_repo_files: int = 30
    max_file_bytes: int = 60_000
    max_generated_tests: int = 8
    pytest_timeout_seconds: int = 30
    run_root: Path = Path("breakbot_runs")
    github_api_base: str = "https://api.github.com"
