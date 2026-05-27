"""Google Gemini API wrapper for BreakBot."""

from __future__ import annotations

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
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096,
            ),
        )

    def _clean_response(self, text: str) -> str:
        """Strip markdown code fences from LLM response."""
        text = text.strip()
        text = re.sub(r"^```(?:json|python)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def chat(self, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        """Send a prompt to Gemini and return the response text."""
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.model.generate_content(full_prompt)
            return self._clean_response(response.text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if expect_json:
                return '{"functions": [], "weak_points": [], "attack_surfaces": []}'
            return ""
