"""Gemini-powered code analysis for BreakBot."""

from __future__ import annotations

import json
import logging
import re

from agent.llm_client import LLMClient
from utils.prompt_templates import ANALYZE_PROMPT


logger = logging.getLogger(__name__)


def safe_parse_json(text: str) -> dict:
    """Safely parse JSON from LLM response, handling all edge cases."""
    try:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()
        return json.loads(text)
    except Exception:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        logger.warning("JSON parsing failed, returning empty analysis")
        return {
            "functions": [],
            "weak_points": ["Could not parse analysis - try again"],
            "attack_surfaces": [],
        }


class CodeAnalyzer:
    """Analyzes code using Gemini LLM to find weak points."""

    def __init__(self):
        """Initialize the analyzer with a Gemini LLM client."""
        self.llm = LLMClient()

    def analyze(self, files: list) -> dict:
        """Analyze code files and return structured analysis."""
        combined = ""
        for f in files:
            combined += f"\n\n# FILE: {f['path']}\n{f['content']}"

        if len(combined) > 12000:
            combined = combined[:12000]
            logger.info("Code truncated to 12000 chars for analysis")

        system = (
            "You are a security and code quality expert. "
            "Analyze the provided code and respond ONLY with a valid JSON object. "
            "No explanation, no markdown, no code fences. Just raw JSON."
        )
        user = (
            f"{ANALYZE_PROMPT}\n\nCode to analyze:\n{combined}\n\n"
            "Respond ONLY with this exact JSON structure:\n"
            '{"functions": ["func1", "func2"], '
            '"weak_points": ["description1", "description2"], '
            '"attack_surfaces": ["surface1", "surface2"]}'
        )

        response = self.llm.chat(
            system_prompt=system,
            user_prompt=user,
            expect_json=True,
        )
        return safe_parse_json(response)
