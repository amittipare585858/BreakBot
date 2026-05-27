"""Google Gemini API wrapper for BreakBot."""

from __future__ import annotations

import logging
import os
import re

import google.generativeai as genai


logger = logging.getLogger(__name__)


class LLMClient:
    """Google Gemini API client wrapper for BreakBot."""

    def __init__(self):
        """Initialize Gemini using Streamlit secrets first, then the .env file."""
        api_key = None
        try:
            import streamlit as st

            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

        if not api_key:
            from dotenv import load_dotenv

            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in secrets or .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    def _clean_response(self, text: str) -> str:
        """Strip markdown code fences from the Gemini response."""
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```python\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        return text.strip()

    def chat(self, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        """Send a prompt to Gemini and return cleaned response text."""
        try:
            full_prompt = (
                f"SYSTEM: {system_prompt}\n\n"
                f"USER: {user_prompt}"
            )
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                ),
            )
            if not response or not response.text:
                if expect_json:
                    return '{"functions":[],"weak_points":["Empty response from API"],"attack_surfaces":[]}'
                return ""
            return self._clean_response(response.text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if expect_json:
                return (
                    '{"functions":[],"weak_points":["API error: '
                    + str(e)
                    + '"],"attack_surfaces":[]}'
                )
            return ""
