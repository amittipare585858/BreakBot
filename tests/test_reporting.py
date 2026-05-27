from breakbot.models import BugAttackReport, Finding, GeneratedTest, ReportSummary


def test_markdown_report_contains_findings_and_tests():
    report = BugAttackReport(
        summary=ReportSummary(
            source_name="demo",
            files_analyzed=1,
            generated_at="2026-01-01T00:00:00+00:00",
            llm_mode="heuristic",
        ),
        findings=[
            Finding(
                title="Example bug",
                severity="medium",
                file_path="demo.py",
                line_hint=1,
                description="Desc",
                attack_idea="Attack",
                suggested_fix="Fix",
            )
        ],
        generated_tests=[
            GeneratedTest(
                name="test_demo",
                file_path="tests/test_demo.py",
                content="def test_demo():\n    assert True\n",
            )
        ],
    )

    markdown = report.to_markdown()

    assert "# Bug Attack Report" in markdown
    assert "Example bug" in markdown
    assert "tests/test_demo.py" in markdown
