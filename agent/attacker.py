"""Adversarial pytest generation for BreakBot."""

from __future__ import annotations

import logging
import os

from agent.llm_client import LLMClient
from utils.prompt_templates import ATTACK_GEN_PROMPT


logger = logging.getLogger(__name__)


class AttackGenerator:
    """Generates adversarial test cases using Gemini LLM."""

    def __init__(self):
        """Initialize the attack generator with a Gemini LLM client."""
        self.llm = LLMClient()

    def generate_attacks(self, analysis: dict, original_code: str) -> str:
        """Generate pytest attack cases from analysis."""
        weak_points = (analysis or {}).get("weak_points", [])
        attack_surfaces = (analysis or {}).get("attack_surfaces", [])

        system = (
            "You are a security testing expert. "
            "Generate only raw Python pytest test functions. "
            "No explanation, no markdown, no code fences. "
            "Just valid Python code starting with import statements."
        )
        user = (
            f"{ATTACK_GEN_PROMPT}\n\n"
            f"Weak points found:\n{weak_points}\n\n"
            f"Attack surfaces:\n{attack_surfaces}\n\n"
            f"Original code:\n{original_code}\n\n"
            "Generate 5-10 pytest functions that test edge cases. "
            "Start with: import pytest"
        )

        response = self.llm.chat(
            system_prompt=system,
            user_prompt=user,
            expect_json=False,
        )

        if not response or len(response.strip()) < 10:
            logger.warning("Attack generation returned empty, using fallback")
            response = (
                "import pytest\n\n"
                "def test_divide_by_zero():\n"
                "    with pytest.raises(ZeroDivisionError):\n"
                "        assert 1/0\n\n"
                "def test_empty_input():\n"
                "    assert '' == ''\n"
            )

        os.makedirs("temp", exist_ok=True)
        test_file = "temp/breakbot_tests.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(response)
        logger.info("Attack tests saved to %s", test_file)

        return response
