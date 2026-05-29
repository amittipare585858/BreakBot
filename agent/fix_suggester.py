import json
import logging
import re

from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)


class FixSuggester:
    """Generates fix suggestions for detected bugs."""

    def __init__(self):
        self.llm = LLMClient()

    def suggest_fix(self,
                    weak_point: str,
                    original_code: str) -> dict:
        """Generate fix for a specific weak point."""
        system = (
            "You are a senior software engineer. "
            "Provide concise, practical code fixes. "
            "Respond ONLY with JSON, no markdown."
        )
        user = (
            f"Bug: {weak_point}\n\n"
            f"Code:\n{original_code[:5000]}\n\n"
            "Respond with ONLY this JSON:\n"
            '{"issue": "one line description",'
            '"fix_code": "corrected code snippet",'
            '"explanation": "why this fixes it"}'
        )

        response = self.llm.chat(
            system_prompt=system,
            user_prompt=user,
            expect_json=True
        )

        try:
            response = re.sub(r'```json|```', '',
                            response).strip()
            return json.loads(response)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Fix suggestion JSON parsing failed: %s", e)
            return {
                "issue": weak_point,
                "fix_code": "# Review this section manually",
                "explanation": "Manual review recommended"
            }

    def suggest_all_fixes(self,
                          weak_points: list,
                          original_code: str) -> list:
        """Generate fixes for top 5 weak points."""
        fixes = []
        for wp in weak_points[:5]:
            fix = self.suggest_fix(wp, original_code)
            fix["weak_point"] = wp
            fixes.append(fix)
        return fixes