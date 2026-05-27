from __future__ import annotations

from breakbot.models import BugAttackReport


def render_markdown_report(report: BugAttackReport) -> str:
    lines = [
        "# Bug Attack Report",
        "",
        "## Summary",
        "",
        f"- Source: `{report.summary.source_name}`",
        f"- Files analyzed: {report.summary.files_analyzed}",
        f"- Generated at: {report.summary.generated_at}",
        f"- Analysis mode: {report.summary.llm_mode}",
        f"- Findings: {len(report.findings)}",
        f"- Generated tests: {len(report.generated_tests)}",
    ]

    if report.test_run:
        lines.extend(
            [
                f"- Pytest exit code: {report.test_run.exit_code}",
                f"- Pytest passed: {report.test_run.passed}",
                f"- Duration: {report.test_run.duration_seconds}s",
            ]
        )

    lines.extend(["", "## Findings", ""])
    for index, finding in enumerate(report.findings, start=1):
        location = finding.file_path
        if finding.line_hint:
            location += f":{finding.line_hint}"
        lines.extend(
            [
                f"### {index}. {finding.title}",
                "",
                f"- Severity: `{finding.severity}`",
                f"- Location: `{location}`",
                f"- Description: {finding.description}",
                f"- Attack idea: {finding.attack_idea}",
                f"- Suggested fix: {finding.suggested_fix}",
                "",
            ]
        )

    lines.extend(["## Generated Tests", ""])
    for test in report.generated_tests:
        lines.extend(
            [
                f"### `{test.file_path}`",
                "",
                "```python",
                test.content.rstrip(),
                "```",
                "",
            ]
        )

    if report.test_run:
        lines.extend(
            [
                "## Pytest Output",
                "",
                "```text",
                report.test_run.output or "(no output)",
                "```",
                "",
            ]
        )

    return "\n".join(lines)
