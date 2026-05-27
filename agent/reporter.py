"""Markdown and JSON report generation for BreakBot."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from agent.llm_client import LLMClient
from utils.prompt_templates import FIX_SUGGEST_PROMPT


logger = logging.getLogger(__name__)
SYSTEM = "You are BreakBot, an AI bug-fix assistant. Return valid JSON when requested."


class BugReporter:
    """Compile Bug Attack Reports and generate fix suggestions."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        reports_dir: str | Path = "reports",
    ):
        """Create a reporter with an LLM client and report output directory."""
        self.llm = llm or LLMClient()
        self.reports_dir = Path(reports_dir)
        self.last_markdown_path: Path | None = None
        self.last_json_path: Path | None = None

    def compile_report(
        self,
        repo_name: str,
        analysis: dict,
        test_results: dict,
        fixes: list,
    ) -> str:
        """Build, save, and return a Markdown Bug Attack Report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_repo_name = self._safe_name(repo_name)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = self.reports_dir / f"{safe_repo_name}_{timestamp}.md"
        json_path = self.reports_dir / f"{safe_repo_name}_{timestamp}.json"

        lines = [
            "# Bug Attack Report",
            "",
            "## Repository",
            "",
            f"- Name: `{repo_name}`",
            f"- Generated: `{timestamp}`",
            "",
            "## Analysis Summary",
            "",
            f"- Functions identified: {len(analysis.get('functions', []))}",
            f"- Weak points identified: {len(analysis.get('weak_points', []))}",
            f"- Attack surfaces identified: {len(analysis.get('attack_surfaces', []))}",
            "",
            "## Functions",
            "",
            self._render_items(analysis.get("functions", [])),
            "",
            "## Weak Points",
            "",
            self._render_items(analysis.get("weak_points", [])),
            "",
            "## Attack Surfaces",
            "",
            self._render_items(analysis.get("attack_surfaces", [])),
            "",
            "## Test Results",
            "",
            f"- Total tests run: {test_results.get('total', 0)}",
            f"- Passed: {test_results.get('passed', 0)}",
            f"- Failed: {test_results.get('failed', 0)}",
            "",
            "## Failed Tests and Fix Suggestions",
            "",
        ]

        failures = test_results.get("failures", [])
        if failures:
            for index, failure in enumerate(failures):
                fix = fixes[index] if index < len(fixes) else {}
                lines.extend(
                    [
                        f"### {failure.get('test_name', 'unknown_test')}",
                        "",
                        f"- Error: `{failure.get('error', '')}`",
                        "",
                        "Traceback:",
                        "",
                        "```text",
                        failure.get("traceback", ""),
                        "```",
                        "",
                        "Fix suggestion:",
                        "",
                        f"- Original issue: {fix.get('original_issue', 'No fix generated.')}",
                        f"- Explanation: {fix.get('explanation', '')}",
                        "",
                        "```python",
                        fix.get("fix_code", ""),
                        "```",
                        "",
                    ]
                )
        else:
            lines.extend(["No failing adversarial tests were reported.", ""])

        markdown = "\n".join(lines)
        json_payload = {
            "repo_name": repo_name,
            "generated_at": timestamp,
            "analysis": analysis,
            "test_results": test_results,
            "fixes": fixes,
            "markdown_report": str(markdown_path),
        }

        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
        self.last_markdown_path = markdown_path
        self.last_json_path = json_path
        logger.info("Saved report to %s and %s", markdown_path, json_path)
        return markdown

    def generate_fixes(self, failures: list, original_code: str) -> list:
        """Generate one fix suggestion for each failed test."""
        fixes = []
        for failure in failures:
            bug_description = json.dumps(failure, indent=2)
            user_msg = FIX_SUGGEST_PROMPT.format(
                bug_description=bug_description,
                original_code=original_code,
            )
            try:
                response = self.llm.chat(
                    system_prompt=SYSTEM,
                    user_prompt=user_msg,
                    expect_json=True,
                )
                fixes.append(self._parse_fix_response(response, failure))
            except Exception as exc:
                logger.exception("Fix generation failed; using fallback fix")
                fixes.append(
                    {
                        "original_issue": failure.get("error", "Unknown failure"),
                        "fix_code": "",
                        "explanation": f"Gemini fix generation failed: {exc}",
                    }
                )
        return fixes

    def _parse_fix_response(self, response: str, failure: dict) -> dict:
        """Parse a fix JSON response with a safe fallback."""
        try:
            clean = response.strip()
            if not clean.startswith("{"):
                start = clean.find("{")
                end = clean.rfind("}")
                if start == -1 or end == -1:
                    raise ValueError("LLM fix response did not contain JSON.")
                clean = clean[start : end + 1]
            parsed = json.loads(clean)
            return {
                "original_issue": parsed.get("original_issue", ""),
                "fix_code": parsed.get("fix_code", ""),
                "explanation": parsed.get("explanation", ""),
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Could not parse fix JSON: %s", exc)
            return {
                "original_issue": failure.get("error", "Unknown failure"),
                "fix_code": "",
                "explanation": "The LLM returned an invalid fix JSON response.",
            }

    def _render_items(self, items: list) -> str:
        """Render a list of analysis items as Markdown bullets."""
        if not items:
            return "_None reported._"
        lines = []
        for item in items:
            if isinstance(item, dict):
                lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    def _safe_name(self, repo_name: str) -> str:
        """Convert a repository name into a filesystem-safe prefix."""
        return "".join(char if char.isalnum() or char in "-_" else "_" for char in repo_name)
