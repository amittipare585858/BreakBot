from __future__ import annotations

import ast
import json
from textwrap import dedent

from agent.llm_client import LLMClient
from breakbot.config import BreakBotConfig
from breakbot.models import Finding, SourceBundle


class BreakBotLLM:
    def __init__(self, config: BreakBotConfig):
        self.config = config
        try:
            self.client: LLMClient | None = LLMClient()
        except Exception:
            self.client = None

    @property
    def mode(self) -> str:
        return "gemini" if self.client else "heuristic"

    def analyze(self, source: SourceBundle) -> list[Finding]:
        if self.client:
            try:
                findings = self._analyze_with_gemini(source)
                if findings:
                    return findings
            except Exception:
                return self._heuristic_findings(source)
        return self._heuristic_findings(source)

    def _analyze_with_gemini(self, source: SourceBundle) -> list[Finding]:
        file_blocks = "\n\n".join(
            f"### {file.path}\n```python\n{file.content[: self.config.max_file_bytes]}\n```"
            for file in source.files
        )
        prompt = dedent(
            f"""
            You are BreakBot, an AI red-team agent. Analyze this Python codebase for bugs,
            security issues, edge-case failures, and adversarial inputs.

            Return only valid JSON as an array. Each object must have:
            title, severity, file_path, line_hint, description, attack_idea, suggested_fix.

            Codebase:
            {file_blocks}
            """
        ).strip()

        text = self.client.chat(
            system_prompt="You are BreakBot, an AI red-team code analysis agent.",
            user_prompt=prompt,
        )
        data = json.loads(_extract_json(text))
        return [Finding(**item) for item in data[: self.config.max_generated_tests]]

    def _heuristic_findings(self, source: SourceBundle) -> list[Finding]:
        findings: list[Finding] = []
        for file in source.files:
            try:
                tree = ast.parse(file.content)
            except SyntaxError as exc:
                findings.append(
                    Finding(
                        title="Syntax error blocks execution",
                        severity="high",
                        file_path=file.path,
                        line_hint=exc.lineno,
                        description="The file cannot be parsed as Python, so tests and runtime behavior will fail.",
                        attack_idea="Import the module or run pytest collection to trigger the syntax failure.",
                        suggested_fix="Fix the syntax error and add a collection smoke test.",
                    )
                )
                continue

            findings.extend(self._function_findings(file.path, tree))
            findings.extend(self._call_findings(file.path, tree))

        if not findings:
            findings.append(
                Finding(
                    title="No obvious adversarial surface found",
                    severity="info",
                    file_path=source.files[0].path if source.files else "unknown",
                    line_hint=None,
                    description="Heuristic mode did not find a clear bug pattern. Gemini mode may discover deeper issues.",
                    attack_idea="Run broad property-style tests with empty, null, huge, and malformed inputs.",
                    suggested_fix="Add explicit input validation and boundary tests around public functions.",
                )
            )
        return findings[: self.config.max_generated_tests]

    def _function_findings(self, file_path: str, tree: ast.AST) -> list[Finding]:
        findings: list[Finding] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            arg_names = [arg.arg.lower() for arg in node.args.args]
            source_names = " ".join([node.name.lower(), *arg_names])

            if any(token in source_names for token in ["divide", "ratio", "percent", "rate"]):
                findings.append(
                    Finding(
                        title=f"Potential divide-by-zero edge case in {node.name}",
                        severity="medium",
                        file_path=file_path,
                        line_hint=node.lineno,
                        description="The function name or arguments imply division-like behavior that may fail on zero denominators.",
                        attack_idea=f"Call {node.name} with denominator-style inputs set to 0.",
                        suggested_fix="Validate denominator inputs and define a predictable zero-handling policy.",
                    )
                )

            if any(token in source_names for token in ["parse", "load", "json", "yaml", "csv"]):
                findings.append(
                    Finding(
                        title=f"Malformed input handling risk in {node.name}",
                        severity="medium",
                        file_path=file_path,
                        line_hint=node.lineno,
                        description="Parser-style functions are often vulnerable to empty, malformed, or deeply nested inputs.",
                        attack_idea=f"Call {node.name} with empty strings, invalid syntax, and oversized payloads.",
                        suggested_fix="Catch parser exceptions, limit input size, and return structured validation errors.",
                    )
                )

            if not any(isinstance(child, ast.Try) for child in ast.walk(node)):
                findings.append(
                    Finding(
                        title=f"No local exception boundary in {node.name}",
                        severity="low",
                        file_path=file_path,
                        line_hint=node.lineno,
                        description="The function has no local exception handling, so adversarial input may bubble raw exceptions to callers.",
                        attack_idea=f"Invoke {node.name} with None, empty containers, and wrong primitive types.",
                        suggested_fix="Add validation near the function boundary or document the expected exception contract.",
                    )
                )
        return findings

    def _call_findings(self, file_path: str, tree: ast.AST) -> list[Finding]:
        findings: list[Finding] = []
        risky_calls = {"eval", "exec", "open", "subprocess.run", "subprocess.Popen"}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _call_name(node.func)
            if call_name in risky_calls:
                findings.append(
                    Finding(
                        title=f"Risky call surface: {call_name}",
                        severity="high" if call_name in {"eval", "exec"} else "medium",
                        file_path=file_path,
                        line_hint=getattr(node, "lineno", None),
                        description=f"The code calls {call_name}, which can become dangerous with attacker-controlled input.",
                        attack_idea="Pass path traversal strings, shell metacharacters, or code-like payloads through this call path.",
                        suggested_fix="Avoid dynamic execution, constrain file paths, and pass subprocess arguments as lists.",
                    )
                )
        return findings


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("["):
        return stripped
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("LLM response did not contain a JSON array.")
    return stripped[start : end + 1]
