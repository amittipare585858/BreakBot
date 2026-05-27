from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CodeFile:
    path: str
    content: str
    language: str = "python"


@dataclass
class SourceBundle:
    source_name: str
    files: list[CodeFile]


@dataclass
class Finding:
    title: str
    severity: str
    file_path: str
    line_hint: int | None
    description: str
    attack_idea: str
    suggested_fix: str


@dataclass
class GeneratedTest:
    name: str
    file_path: str
    content: str
    targets: list[str] = field(default_factory=list)


@dataclass
class TestRunResult:
    command: list[str]
    exit_code: int
    passed: bool
    output: str
    duration_seconds: float


@dataclass
class ReportSummary:
    source_name: str
    files_analyzed: int
    generated_at: str
    llm_mode: str


@dataclass
class BugAttackReport:
    summary: ReportSummary
    findings: list[Finding]
    generated_tests: list[GeneratedTest]
    test_run: TestRunResult | None = None
    workspace_path: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        from breakbot.reporting import render_markdown_report

        return render_markdown_report(self)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
