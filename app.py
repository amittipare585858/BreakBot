"""BreakBot Streamlit application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from agent.analyzer import CodeAnalyzer
from agent.attacker import AttackGenerator
from agent.ingester import RepoIngester
from agent.llm_client import LLMClient
from agent.reporter import BugReporter
from agent.runner import TestRunner


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def init_state() -> None:
    """Initialize persistent Streamlit session state values."""
    defaults = {
        "repo_data": None,
        "analysis": None,
        "test_code": None,
        "test_file_path": str(Path("temp") / "breakbot_tests.py"),
        "test_results": None,
        "fixes": None,
        "report_markdown": None,
        "report_path": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def original_code() -> str:
    """Return concatenated code from the currently ingested repository data."""
    repo_data = st.session_state.get("repo_data") or {"files": []}
    return "\n\n".join(
        f"# FILE: {file.get('path', 'unknown')}\n{file.get('content', '')}"
        for file in repo_data.get("files", [])
    )


def severity_badge(item: object) -> str:
    """Render a colored weak-point badge based on severity."""
    if isinstance(item, dict):
        severity = str(item.get("severity", "medium")).lower()
        label = item.get("description") or item.get("name") or item.get("type") or str(item)
    else:
        severity = "medium"
        label = str(item)

    prefix = "[MED]"
    color = "#facc15"
    if severity == "high":
        prefix = "[HIGH]"
        color = "#fb7185"
    elif severity == "low":
        prefix = "[LOW]"
        color = "#4ade80"

    return (
        f"<span class='badge' style='border-color:{color}; color:{color};'>"
        f"{prefix} {label}</span>"
    )


def apply_theme() -> None:
    """Apply a compact dark visual theme to the Streamlit app."""
    st.markdown(
        """
        <style>
        .stApp {
            background: #0b1020;
            color: #e5e7eb;
        }
        [data-testid="stSidebar"] {
            background: #111827;
        }
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
        }
        .metric-card {
            border: 1px solid #263244;
            background: #111827;
            border-radius: 8px;
            padding: 1rem;
        }
        .badge {
            display: inline-block;
            border: 1px solid;
            border-radius: 999px;
            padding: 0.25rem 0.55rem;
            margin: 0.2rem 0.25rem 0.2rem 0;
            background: #0f172a;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the BreakBot Streamlit UI."""
    st.set_page_config(page_title="BreakBot", page_icon="BB", layout="wide")
    apply_theme()
    init_state()

    with st.sidebar:
        st.title("BreakBot")
        st.caption("AI Red-Team Agent")
        input_mode = st.radio("Input mode", ["GitHub Repo", "Paste Code"])
        st.caption("Powered by Google Gemini")

    _ = LLMClient
    ingester = RepoIngester()
    analyzer = CodeAnalyzer()
    attacker = AttackGenerator()
    runner = TestRunner()
    reporter = BugReporter()

    st.header("Step 1: Input")
    try:
        if input_mode == "GitHub Repo":
            repo_url = st.text_input("Repository URL", placeholder="https://github.com/user/repo")
            if st.button("Ingest Repo", type="primary"):
                with st.spinner("Ingesting repository..."):
                    st.session_state.repo_data = ingester.ingest_github(repo_url)
                    st.session_state.analysis = None
                    st.session_state.test_code = None
                    st.session_state.test_results = None
                    st.session_state.report_markdown = None
                st.success(f"Ingested {st.session_state.repo_data['repo_name']}")
        else:
            raw_code = st.text_area("Code", height=260, placeholder="def divide(a, b):\n    return a / b")
            filename = st.text_input("Filename", value="pasted_code.py")
            if st.button("Analyze Code", type="primary"):
                st.session_state.repo_data = ingester.ingest_code(raw_code, filename)
                st.session_state.analysis = None
                st.session_state.test_code = None
                st.session_state.test_results = None
                st.session_state.report_markdown = None
                st.success("Pasted code loaded")
    except Exception as exc:
        logger.exception("Input step failed")
        st.error(str(exc))

    if st.session_state.repo_data:
        st.divider()
        st.header("Step 2: Analysis")
        if st.session_state.analysis is None:
            try:
                with st.spinner("[*] Reading your code..."):
                    st.session_state.analysis = analyzer.analyze(st.session_state.repo_data["files"])
            except Exception as exc:
                logger.exception("Analysis step failed")
                st.error(str(exc))

        if st.session_state.analysis:
            with st.expander("Analysis results", expanded=True):
                weak_points = (st.session_state.analysis or {}).get("weak_points", [])
                if weak_points:
                    badges = "".join(severity_badge(item) for item in weak_points)
                    st.markdown(badges, unsafe_allow_html=True)
                else:
                    st.info("No weak points were returned.")
                st.json(st.session_state.analysis)

        st.divider()
        st.header("Step 3: Attack")
        if st.button("Launch Attack"):
            try:
                with st.spinner("[!] Generating adversarial cases..."):
                    st.session_state.test_code = attacker.generate_attacks(
                        st.session_state.analysis or {},
                        original_code(),
                    )
                    st.session_state.test_results = None
                    st.session_state.report_markdown = None
            except Exception as exc:
                logger.exception("Attack step failed")
                st.error(str(exc))

        if st.session_state.test_code:
            st.code(st.session_state.test_code, language="python")

        st.divider()
        st.header("Step 4: Run & Report")
        if st.button("Run Tests", disabled=not bool(st.session_state.test_code)):
            try:
                with st.spinner("Running attacks..."):
                    st.session_state.test_results = runner.run(st.session_state.test_file_path)
                    failures = (st.session_state.test_results or {}).get("failures", [])
                    st.session_state.fixes = reporter.generate_fixes(failures, original_code())
                    st.session_state.report_markdown = reporter.compile_report(
                        st.session_state.repo_data["repo_name"],
                        st.session_state.analysis or {},
                        st.session_state.test_results or {},
                        st.session_state.fixes,
                    )
                    st.session_state.report_path = str(reporter.last_markdown_path)
            except Exception as exc:
                logger.exception("Run/report step failed")
                st.error(str(exc))

        if st.session_state.test_results:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total", (st.session_state.test_results or {}).get("total", 0))
            col_b.metric("Passed [PASS]", (st.session_state.test_results or {}).get("passed", 0))
            col_c.metric("Failed [FAIL]", (st.session_state.test_results or {}).get("failed", 0))

        if st.session_state.report_markdown:
            st.subheader("Bug Attack Report")
            st.markdown(st.session_state.report_markdown)
            report_path = st.session_state.report_path
            if report_path and Path(report_path).exists():
                st.download_button(
                    "Download Markdown Report",
                    Path(report_path).read_text(encoding="utf-8"),
                    file_name=Path(report_path).name,
                    mime="text/markdown",
                )


if __name__ == "__main__":
    main()
