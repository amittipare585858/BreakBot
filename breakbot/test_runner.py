from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from breakbot.config import BreakBotConfig
from breakbot.models import TestRunResult


class PytestRunner:
    def __init__(self, config: BreakBotConfig):
        self.config = config

    def run(self, workspace: Path) -> TestRunResult:
        command = [sys.executable, "-m", "pytest", "-q", "tests"]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.config.pytest_timeout_seconds,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            output = ((exc.stdout or "") + (exc.stderr or "")).strip()
            output += f"\nBreakBot timed out after {self.config.pytest_timeout_seconds} seconds."
            exit_code = 124

        return TestRunResult(
            command=command,
            exit_code=exit_code,
            passed=exit_code == 0,
            output=output.strip(),
            duration_seconds=round(time.perf_counter() - started, 3),
        )
