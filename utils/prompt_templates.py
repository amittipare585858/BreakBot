"""Prompt templates used by BreakBot's LLM-powered pipeline."""

ANALYZE_PROMPT = """
You are BreakBot, an AI red-team code analysis agent.

Given the source code below:
1. Identify all functions, their inputs, and major logic paths.
2. Flag potential weak points, including null inputs, type mismatches,
   boundary values, auth checks, SQL/injection surfaces, and infinite loops.
3. Identify concrete attack surfaces an adversarial tester should target.

Return only valid JSON with this exact structure:
{
  "functions": [],
  "weak_points": [],
  "attack_surfaces": []
}

Source code:
{source_code}
""".strip()


ATTACK_GEN_PROMPT = """
You are BreakBot, an AI adversarial test generator.

Given the weak points JSON and original source code below, generate 10-20
adversarial test cases as Python pytest functions.

Cover null inputs, negative numbers, empty strings, overflow values, SQL
injection strings, special characters, concurrent calls, and wrong data types.

Return only raw Python code. Do not include explanations, markdown fences, or
any text outside the Python code.

Weak points JSON:
{analysis_json}

Original source code:
{original_code}
""".strip()


FIX_SUGGEST_PROMPT = """
You are BreakBot, an AI bug-fix assistant.

Given the bug description and original code snippet below:
1. Suggest a corrected version of the affected function.
2. Explain what was wrong in 1-2 sentences.

Return only valid JSON with this exact structure:
{
  "original_issue": "",
  "fix_code": "",
  "explanation": ""
}

Bug description:
{bug_description}

Original code snippet:
{original_code}
""".strip()
