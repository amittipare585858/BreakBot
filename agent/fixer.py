"""Compatibility wrapper around BugReporter fix generation."""

from __future__ import annotations

from agent.llm_client import LLMClient
from agent.reporter import BugReporter


class FixSuggester:
    """Generate a single Gemini fix suggestion."""

    def __init__(self, llm: LLMClient | None = None):
        """Create a fix suggester."""
        self.reporter = BugReporter(llm=llm)

    def suggest_fix(self, bug_description: str, original_code: str) -> dict:
        """Return one fix dictionary for a bug description."""
        failures = [{"test_name": "manual_bug", "error": bug_description, "traceback": ""}]
        return self.reporter.generate_fixes(failures, original_code)[0]
