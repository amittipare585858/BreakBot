"""Sandboxed pytest runner for BreakBot-generated attacks."""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from pathlib import Path


logger = logging.getLogger(__name__)


class TestRunner:
    """Run pytest in a subprocess and parse concise result data."""

    def run(self, test_file_path: str) -> dict:
        """Run `pytest test_file_path --tb=short -q` with a 30 second timeout."""
        path = Path(test_file_path)
        if not path.exists():
            logger.info("Generated test file not found: %s", test_file_path)
            return {
                "total": 0,
                "passed": 0,
                "failed": 1,
                "failures": [
                    {
                        "test_name": "file_not_found",
                        "error": f"Test file not found: {test_file_path}",
                        "traceback": "",
                    }
                ],
            }

        command = [sys.executable, "-m", "pytest", str(path), "--tb=short", "-q"]
        logger.info("Running pytest command: %s", " ".join(command))
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
        except subprocess.TimeoutExpired as exc:
            output = ((exc.stdout or "") + (exc.stderr or "")).strip()
            logger.info("pytest timed out after 30 seconds")
            return {
                "total": 1,
                "passed": 0,
                "failed": 1,
                "failures": [
                    {
                        "test_name": "pytest_timeout",
                        "error": "pytest timed out after 30 seconds",
                        "traceback": output,
                    }
                ],
            }

        return self._parse_pytest_output(output)

    def _parse_pytest_output(self, output: str) -> dict:
        """Extract totals and failure details from pytest output."""
        passed = self._extract_count(output, "passed")
        failed = self._extract_count(output, "failed") + self._extract_count(output, "error")
        failures = self._extract_failures(output)

        if "SyntaxError" in output and not failures:
            failures.append(
                {
                    "test_name": "generated_test_syntax_error",
                    "error": "SyntaxError in generated tests",
                    "traceback": output[-4000:],
                }
            )
            failed = max(failed, 1)

        if not passed and not failed and "collected" in output:
            collected_match = re.search(r"collected\s+(\d+)\s+items?", output)
            failed = 0
            passed = int(collected_match.group(1)) if collected_match else 0

        total = passed + failed
        logger.info("pytest parsed result: total=%s passed=%s failed=%s", total, passed, failed)
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "failures": failures,
        }

    def _extract_count(self, output: str, label: str) -> int:
        """Extract pytest summary counts for a label such as passed or failed."""
        matches = re.findall(rf"(\d+)\s+{label}", output)
        return sum(int(value) for value in matches)

    def _extract_failures(self, output: str) -> list[dict]:
        """Extract failed test names, errors, and traceback snippets."""
        failures = []
        failed_names = re.findall(r"FAILED\s+([^\s]+)", output)
        for name in failed_names:
            pattern = re.escape(name.split("::")[-1])
            match = re.search(rf"(_+\s+{pattern}.*?)(?=\nFAILED\s+|\n=+|$)", output, re.S)
            snippet = match.group(1).strip() if match else output[-4000:]
            error_match = re.search(r"\nE\s+(.+)", snippet)
            failures.append(
                {
                    "test_name": name,
                    "error": error_match.group(1).strip() if error_match else "pytest failure",
                    "traceback": snippet[-4000:],
                }
            )

        if "ERROR" in output and not failures:
            failures.append(
                {
                    "test_name": "pytest_collection_error",
                    "error": "pytest collection or import error",
                    "traceback": output[-4000:],
                }
            )
        return failures
