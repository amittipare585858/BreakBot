"""Gemini-powered code analysis for BreakBot."""

from __future__ import annotations

import json
import logging
import re

from agent.llm_client import LLMClient
from utils.prompt_templates import ANALYZE_PROMPT


logger = logging.getLogger(__name__)


def safe_parse_json(text: str) -> dict:
    """Safely parse JSON with multiple fallback strategies."""
    default = {
        "functions": [],
        "weak_points": ["Analysis failed - please try again"],
        "attack_surfaces": [],
    }

    if not text or len(text.strip()) < 5:
        return default

    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    except Exception:
        pass

    try:
        functions = re.findall(r'"functions"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        weak_points = re.findall(r'"weak_points"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        attack_surfaces = re.findall(r'"attack_surfaces"\s*:\s*\[(.*?)\]', text, re.DOTALL)

        def extract_list(match):
            if not match:
                return []
            items = re.findall(r'"([^"]+)"', match[0])
            return items

        result = {
            "functions": extract_list(functions),
            "weak_points": extract_list(weak_points),
            "attack_surfaces": extract_list(attack_surfaces),
        }
        if result["weak_points"]:
            return result
    except Exception:
        pass

    return default


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

        system = (
            "You are a code security expert. "
            "You MUST respond with ONLY a raw JSON object. "
            "No markdown, no code fences, no explanation. "
            "Start your response with { and end with }. "
            "Never return empty arrays - always find something."
        )

        user = (
            "Analyze this code for bugs and security issues.\n\n"
            f"{combined}\n\n"
            "Return ONLY this JSON with NO empty arrays:\n"
            "{\n"
            '  "functions": ["list every function name found"],\n'
            '  "weak_points": [\n'
            '    "ZeroDivisionError possible in divide_numbers()",\n'
            '    "SQL injection risk in process_user_input()",\n'
            '    "File handle never closed in read_file()"\n'
            "  ],\n"
            '  "attack_surfaces": [\n'
            '    "division by zero",\n'
            '    "null input",\n'
            '    "empty list",\n'
            '    "SQL injection"\n'
            "  ]\n"
            "}"
        )

        response = self.llm.chat(
            system_prompt=system,
            user_prompt=user,
            expect_json=True,
        )

        result = safe_parse_json(response)

        if not result.get("weak_points"):
            simple_user = (
                f"List all bugs in this code as JSON:\n{combined}\n\n"
                "Respond ONLY with:\n"
                '{"functions":["name1","name2"],'
                '"weak_points":["bug description 1","bug description 2"],'
                '"attack_surfaces":["attack type 1","attack type 2"]}'
            )
            response = self.llm.chat(
                system_prompt="Respond with raw JSON only. No markdown.",
                user_prompt=simple_user,
                expect_json=True,
            )
            result = safe_parse_json(response)

        return result
