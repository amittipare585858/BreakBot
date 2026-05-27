"""Google Gemini API wrapper for BreakBot."""

from __future__ import annotations

import json
import logging
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class LLMClient:
    """Google Gemini API client wrapper for BreakBot."""

    def __init__(self):
        """Initialize the Gemini model with GEMINI_API_KEY from the .env file."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def _clean_response(self, text: str) -> str:
        """Strip all markdown formatting from response."""
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```python\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()
        return text

    def chat(self, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        """Send a prompt to Gemini and return response text."""
        try:
            full_prompt = (
                f"SYSTEM INSTRUCTION: {system_prompt}\n\n"
                f"USER REQUEST: {user_prompt}"
            )
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                    candidate_count=1,
                ),
            )

            if not response or not response.text:
                logger.error("Empty response from Gemini")
                if expect_json:
                    return '{"functions":[],"weak_points":["Analysis failed - empty response"],"attack_surfaces":[]}'
                return ""

            cleaned = self._clean_response(response.text)
            logger.info(f"Gemini response (first 200 chars): {cleaned[:200]}")
            return cleaned

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if expect_json:
                return '{"functions":[],"weak_points":["API error occurred"],"attack_surfaces":[]}'
            return ""
