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
from auth import show_admin_panel, show_login_page, show_user_history


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def apply_theme() -> None:
    """Inject the BreakBot premium dark UI styles."""
    st.markdown(
        """
<style>
/* Global */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

* { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    background: #0a0a0f;
    color: #ffffff;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d0d1a;
    border-right: 1px solid #ff3b3b30;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #ff3b3b, #cc0000);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #ff5555, #ee0000);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255, 59, 59, 0.4);
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1a1a2e;
    border: 1px solid #ff3b3b30;
    border-radius: 8px;
    color: #ffffff;
    font-family: 'Space Grotesk', sans-serif;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #ff3b3b;
    box-shadow: 0 0 0 2px rgba(255, 59, 59, 0.2);
}

/* Cards */
.bb-card {
    background: #16213e;
    border: 1px solid #ff3b3b20;
    border-radius: 12px;
    padding: 24px;
    margin: 12px 0;
}

/* Step headers */
.bb-step {
    background: linear-gradient(135deg, #1a0a0a, #2a0a0a);
    border-left: 4px solid #ff3b3b;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin: 20px 0 16px 0;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* Metrics */
.bb-metric {
    background: #16213e;
    border: 1px solid #ff3b3b20;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}
.bb-metric-value {
    font-size: 42px;
    font-weight: 700;
    color: #ff3b3b;
}
.bb-metric-label {
    font-size: 13px;
    color: #a0a0b0;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Logo */
.bb-logo {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, #ff3b3b, #ff8080);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

/* Badge */
.bb-badge {
    display: inline-block;
    background: #ff3b3b20;
    border: 1px solid #ff3b3b50;
    color: #ff6b6b;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    margin: 4px;
}

/* Divider */
.bb-divider {
    border: none;
    border-top: 1px solid #ff3b3b15;
    margin: 24px 0;
}

/* Success/fail colors */
.bb-pass { color: #00ff88; }
.bb-fail { color: #ff3b3b; }

/* Code blocks */
.stCodeBlock { border-radius: 8px; }

/* Expander */
.streamlit-expanderHeader {
    background: #16213e;
    border-radius: 8px;
    color: #ffffff;
}

/* Radio buttons */
.stRadio > div { gap: 10px; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb {
    background: #ff3b3b50;
    border-radius: 3px;
}
</style>
""",
        unsafe_allow_html=True,
    )


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


def render_step(title: str) -> None:
    """Render a styled step header."""
    st.markdown(f'<div class="bb-step">{title}</div>', unsafe_allow_html=True)


def render_badges(points: list) -> None:
    """Render weak points as badge HTML."""
    for point in points:
        label = point
        if isinstance(point, dict):
            label = point.get("description") or point.get("name") or point.get("type") or str(point)
        st.markdown(f'<span class="bb-badge">{label}</span>', unsafe_allow_html=True)


def render_metrics(total: int, passed: int, failed: int) -> None:
    """Render test result metrics as custom cards."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
    <div class="bb-metric">
        <div class="bb-metric-value">{total}</div>
        <div class="bb-metric-label">Total Tests</div>
    </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
    <div class="bb-metric">
        <div class="bb-metric-value bb-pass">{passed}</div>
        <div class="bb-metric-label">Passed</div>
    </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
    <div class="bb-metric">
        <div class="bb-metric-value bb-fail">{failed}</div>
        <div class="bb-metric-label">Failed</div>
    </div>""",
            unsafe_allow_html=True,
        )


def main() -> None:
    """Run the BreakBot Streamlit UI."""
    st.set_page_config(page_title="BreakBot", page_icon="BB", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        show_login_page()
        st.stop()

    apply_theme()
    init_state()

    with st.sidebar:
        st.markdown('<div class="bb-logo">BREAK BOT</div>', unsafe_allow_html=True)
        st.markdown("**AI Red-Team Agent**")
        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)

        st.markdown(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        st.markdown("---")
        st.markdown("**Navigation**")

        if st.session_state.get("is_admin", False):
            nav_options = ["Run Scan", "My History", "Admin Panel"]
        else:
            nav_options = ["Run Scan", "My History"]

        if "nav_page" not in st.session_state:
            st.session_state.nav_page = "Run Scan"

        for option in nav_options:
            if st.button(option, key=f"nav_{option}"):
                st.session_state.nav_page = option
                st.rerun()

        st.markdown("---")

        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)
        st.markdown("**Input Mode**")
        mode = st.radio("", ["GitHub Repo", "Paste Code"], label_visibility="collapsed")

        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)
        st.markdown("Powered by Google Gemini", unsafe_allow_html=True)

    current_page = st.session_state.get("nav_page", "Run Scan")

    if current_page == "My History":
        st.markdown("## My Scan History")
        show_user_history()
        st.stop()

    if current_page == "Admin Panel" and st.session_state.get("is_admin", False):
        show_admin_panel()
        st.stop()

    _ = LLMClient
    ingester = RepoIngester()
    analyzer = CodeAnalyzer()
    attacker = AttackGenerator()
    runner = TestRunner()
    reporter = BugReporter()

    render_step("Step 1: Input")
    try:
        if mode == "GitHub Repo":
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
            raw_code = st.text_area(
                "Code",
                height=260,
                placeholder="def divide(a, b):\n    return a / b",
            )
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
        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)
        render_step("Step 2: Analysis")
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
                    render_badges(weak_points)
                else:
                    st.info("No weak points were returned.")
                st.json(st.session_state.analysis)

        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)
        render_step("Step 3: Attack")
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

        st.markdown('<hr class="bb-divider">', unsafe_allow_html=True)
        render_step("Step 4: Run & Report")
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
            results = st.session_state.test_results or {}
            render_metrics(
                results.get("total", 0),
                results.get("passed", 0),
                results.get("failed", 0),
            )

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
