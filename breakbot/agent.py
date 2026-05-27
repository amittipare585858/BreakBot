from __future__ import annotations

from breakbot.config import BreakBotConfig
from breakbot.ingestion import SourceIngestor
from breakbot.llm import BreakBotLLM
from breakbot.models import BugAttackReport, ReportSummary, utc_timestamp
from breakbot.test_generation import AdversarialTestGenerator
from breakbot.test_runner import PytestRunner
from breakbot.workspace import WorkspaceBuilder


class BreakBotAgent:
    def __init__(self, config: BreakBotConfig | None = None):
        self.config = config or BreakBotConfig()
        self.ingestor = SourceIngestor(self.config)
        self.llm = BreakBotLLM(self.config)
        self.generator = AdversarialTestGenerator(self.config)
        self.workspace_builder = WorkspaceBuilder(self.config)
        self.runner = PytestRunner(self.config)

    def attack(
        self,
        *,
        github_url: str | None = None,
        pasted_code: str | None = None,
        run_tests: bool = True,
    ) -> BugAttackReport:
        if bool(github_url) == bool(pasted_code):
            raise ValueError("Provide exactly one source: github_url or pasted_code.")

        source = (
            self.ingestor.from_github(github_url)
            if github_url
            else self.ingestor.from_pasted_code(pasted_code or "")
        )
        findings = self.llm.analyze(source)
        generated_tests = self.generator.generate(source, findings)
        workspace = self.workspace_builder.materialize(source, generated_tests)
        test_run = self.runner.run(workspace) if run_tests else None

        summary = ReportSummary(
            source_name=source.source_name,
            files_analyzed=len(source.files),
            generated_at=utc_timestamp(),
            llm_mode=self.llm.mode,
        )
        return BugAttackReport(
            summary=summary,
            findings=findings,
            generated_tests=generated_tests,
            test_run=test_run,
            workspace_path=str(workspace),
        )
