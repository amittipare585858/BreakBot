import streamlit as st
import os
from dotenv import load_dotenv
from agent.ingester import RepoIngester
from agent.analyzer import CodeAnalyzer
from agent.attacker import AttackGenerator
from agent.runner import TestRunner
from agent.reporter import BugReporter
from agent.pdf_reporter import generate_pdf_report
from agent.scorer import get_severity, get_severity_color, calculate_score
from agent.fix_suggester import FixSuggester
from auth import show_login_page
from database import save_scan_history
from pages.dashboard import show_dashboard

load_dotenv()

# ─── SESSION STATE INIT ───────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "is_admin": False,
        "user_email": "",
        "nav_page": "Run Scan",
        "analysis": {},
        "attack_code": "",
        "test_results": {},
        "report": "",
        "fixes": [],
        "original_code": "",
        "ingested_files": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ─── LOGIN GATE ───────────────────────────────────────────
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# ─── GLOBAL CSS ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&display=swap');
* { font-family: 'Space Grotesk', sans-serif !important; }
.stApp { background: #0a0a0f; color: #ffffff; }
[data-testid="stSidebar"] {
    background: #0d0d1a;
    border-right: 1px solid #ff3b3b30;
}
.stButton > button {
    background: linear-gradient(135deg, #ff3b3b, #cc0000) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(255,59,59,0.4) !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1a1a2e !important;
    border: 1px solid #ff3b3b30 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
.step-header {
    background: linear-gradient(135deg, #1a0a0a, #2a0a0a);
    border-left: 4px solid #ff3b3b;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin: 20px 0 16px 0;
    font-size: 20px;
    font-weight: 700;
}
.metric-card {
    background: #16213e;
    border: 1px solid #ff3b3b20;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}
.metric-val {
    font-size: 42px;
    font-weight: 700;
    color: #ff3b3b;
}
.metric-label {
    font-size: 12px;
    color: #a0a0b0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.bb-badge {
    display: inline-block;
    background: #ff3b3b20;
    border: 1px solid #ff3b3b50;
    color: #ff6b6b;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    margin: 4px 2px;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb {
    background: #ff3b3b50;
    border-radius: 3px;
}
/* Hide broken sidebar collapse icon */
[data-testid="collapsedControl"] {
    display: none !important;
}
button[kind="headerNoPadding"] {
    display: none !important;
}
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
.st-emotion-cache-h4xjwg {
    display: none !important;
}
/* Hide any text rendering as icon names */
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-size:26px; font-weight:800;
        background: linear-gradient(135deg, #ff3b3b, #ff8080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px 0;'>
        BREAKBOT
    </div>
    <div style='color:#a0a0b0; font-size:12px;
                margin-bottom:10px;'>
        AI Red-Team Security Agent
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"**{st.session_state.username}**")
    st.markdown(
        f"<small style='color:#a0a0b0'>"
        f"{st.session_state.user_email}</small>",
        unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Navigation**")

    if st.button("Run Scan", key="nav_scan"):
        st.session_state.nav_page = "Run Scan"
        st.rerun()

    if st.button("My History", key="nav_history"):
        st.session_state.nav_page = "My History"
        st.rerun()

    if st.button("Dashboard", key="nav_dashboard"):
        st.session_state.nav_page = "Dashboard"
        st.rerun()

    if st.session_state.get("is_admin", False):
        if st.button("Admin Panel", key="nav_admin"):
            st.session_state.nav_page = "Admin Panel"
            st.rerun()

    st.markdown("---")

    if st.session_state.nav_page == "Run Scan":
        st.markdown("**Input Mode**")
        mode = st.radio("",
            ["GitHub Repo", "Paste Code"],
            index=1,
            label_visibility="collapsed")
    else:
        mode = "Paste Code"

    st.markdown("---")
    if st.button("Logout", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown(
        "<small style='color:#555'>Powered by "
        "Google Gemini</small>",
        unsafe_allow_html=True)

# ─── PAGE: MY HISTORY ─────────────────────────────────────
if st.session_state.nav_page == "My History":
    st.markdown(
        '<div class="step-header">My Scan History</div>',
        unsafe_allow_html=True)
    try:
        from database import get_user_history
        history = get_user_history(
            st.session_state.username)
        if not history:
            st.info(
                "No scans yet! "
                "Go to Run Scan to analyze your first repo.")
        else:
            for i, scan in enumerate(history):
                st.markdown(f"""
                <div style='background:#16213e;
                    border:1px solid #ff3b3b20;
                    border-radius:10px;
                    padding:16px; margin:8px 0;'>
                    <div style='color:#ff3b3b; font-weight:700;'>
                        Scan {i + 1} |
                        {str(scan.get('scanned_at',''))[:16]} |
                        Bugs: {scan.get('bugs_found', 0)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Weak Points",
                        scan.get('weak_points_found', 0))
                with c2:
                    st.metric("Bugs Found",
                        scan.get('bugs_found', 0))
                if scan.get("code_snippet"):
                    st.markdown("**Code Snippet:**")
                    st.code(scan["code_snippet"])
                if scan.get("report_content"):
                    st.markdown(scan["report_content"][:500])
                st.markdown("---")
    except Exception as e:
        st.error(f"Could not load history: {e}")
    st.stop()

# ─── PAGE: ADMIN PANEL ────────────────────────────────────
if st.session_state.nav_page == "Admin Panel":
    if not st.session_state.get("is_admin", False):
        st.error("Access denied")
        st.stop()
    st.markdown(
        '<div class="step-header">Admin Panel</div>',
        unsafe_allow_html=True)
    try:
        from database import get_all_users, get_all_scans, get_stats
        import pandas as pd
        stats = get_stats()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">
                    {stats['total_users']}</div>
                <div class="metric-label">Total Users</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">
                    {stats['total_scans']}</div>
                <div class="metric-label">Total Scans</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">
                    {stats['total_bugs']}</div>
                <div class="metric-label">Bugs Found</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("---")
        t1, t2 = st.tabs(["All Users", "All Scans"])
        with t1:
            users = get_all_users()
            if users:
                df = pd.DataFrame(users)[
                    ["username","email",
                     "is_admin","created_at"]]
                df.columns = ["Username","Email",
                              "Admin","Joined"]
                st.dataframe(df, use_container_width=True)
        with t2:
            scans = get_all_scans()
            if scans:
                df = pd.DataFrame(scans)[
                    ["username","weak_points_found",
                     "bugs_found","scanned_at"]]
                df.columns = ["User","Weak Points",
                              "Bugs Found","Scanned At"]
                st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Admin error: {e}")
    st.stop()

if st.session_state.nav_page == "Dashboard":
    show_dashboard(
        st.session_state.username,
        st.session_state.get("is_admin", False)
    )
    st.stop()

# ─── PAGE: RUN SCAN ───────────────────────────────────────
st.markdown(
    '<div class="step-header">Step 1: Input</div>',
    unsafe_allow_html=True)

ingested = None

if mode == "GitHub Repo":
    repo_url = st.text_input("Repository URL",
        placeholder="https://github.com/user/repo")
    if st.button("Ingest Repo", key="ingest_btn"):
        if not repo_url:
            st.error("Please enter a repo URL")
        else:
            with st.spinner("Reading repo..."):
                try:
                    ingester = RepoIngester()
                    ingested = ingester.ingest_github(repo_url)
                    st.session_state.ingested_files = \
                        ingested["files"]
                    st.session_state.original_code = \
                        "\n".join([
                            f['content']
                            for f in ingested["files"]
                        ])[:500]
                    st.session_state.analysis = {}
                    st.session_state.attack_code = ""
                    st.session_state.test_results = {}
                    st.session_state.report = ""
                    st.session_state.fixes = []
                    st.success(
                        f"Ingested "
                        f"{len(ingested['files'])} files!")
                except Exception as e:
                    st.error(f"Ingestion error: {e}")
else:
    code_input = st.text_area("Paste your code here",
        height=250,
        placeholder="def my_function():\n    pass")
    filename = st.text_input("Filename",
        value="pasted_code.py")
    if st.button("Analyze Code", key="analyze_btn"):
        if not code_input:
            st.error("Please paste some code")
        else:
            ingested = {
                "repo_name": "pasted_code",
                "files": [{
                    "path": filename,
                    "content": code_input
                }]
            }
            st.session_state.ingested_files = \
                ingested["files"]
            st.session_state.original_code = \
                code_input[:500]
            st.session_state.analysis = {}
            st.session_state.attack_code = ""
            st.session_state.test_results = {}
            st.session_state.report = ""
            st.session_state.fixes = []

# ─── STEP 2: ANALYSIS ────────────────────────────────────
if st.session_state.ingested_files:
    st.markdown(
        '<div class="step-header">Step 2: Analysis</div>',
        unsafe_allow_html=True)
    if not st.session_state.analysis:
        with st.spinner("Analyzing code..."):
            try:
                analyzer = CodeAnalyzer()
                analysis = analyzer.analyze(
                    st.session_state.ingested_files)
                st.session_state.analysis = analysis
            except Exception as e:
                st.error(f"Analysis error: {e}")
    if st.session_state.analysis:
        st.markdown("**Analysis Results:**")
        weak_points = st.session_state.analysis.get(
            "weak_points", [])
        if not weak_points:
            st.info("No weak points found")
        else:
            st.markdown(
                '<div style="background:#16213e; '
                'border:1px solid #ff3b3b20; '
                'border-radius:12px; padding:20px; '
                'margin:10px 0;">',
                unsafe_allow_html=True)
            for wp in weak_points:
                severity = get_severity(wp)
                color = get_severity_color(severity)
                st.markdown(
                    f'<span style="display:inline-block;'
                    f'background:{color}22;'
                    f'border:1px solid {color}88;'
                    f'color:{color};'
                    f'border-radius:20px;'
                    f'padding:4px 12px;'
                    f'font-size:12px;margin:4px 2px;">'
                    f'[{severity}] {wp}</span>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

# ─── STEP 3: ATTACK ───────────────────────────────────────
if st.session_state.analysis:
    st.markdown(
        '<div class="step-header">Step 3: Attack</div>',
        unsafe_allow_html=True)
    if st.button("Launch Attack", key="attack_btn"):
        with st.spinner("Generating attack cases..."):
            try:
                attacker = AttackGenerator()
                original = "\n".join([
                    f['content']
                    for f in st.session_state.ingested_files
                ])
                attack_code = attacker.generate_attacks(
                    st.session_state.analysis, original)
                st.session_state.attack_code = attack_code
            except Exception as e:
                st.error(f"Attack error: {e}")
    if st.session_state.attack_code:
        st.code(st.session_state.attack_code,
                language="python")

# ─── STEP 4: RUN & REPORT ─────────────────────────────────
if st.session_state.attack_code:
    st.markdown(
        '<div class="step-header">'
        'Step 4: Run & Report</div>',
        unsafe_allow_html=True)
    if st.button("Run Tests", key="run_btn"):
        with st.spinner("Running tests..."):
            try:
                runner = TestRunner()
                results = runner.run("temp/breakbot_tests.py")
                st.session_state.test_results = results
            except Exception as e:
                st.error(f"Runner error: {e}")
    if st.session_state.test_results:
        results = st.session_state.test_results
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{total}</div>
                <div class="metric-label">Total</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val"
                     style="color:#00ff88">{passed}</div>
                <div class="metric-label">Passed</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>""", unsafe_allow_html=True)

        weak_points = st.session_state.analysis.get(
            "weak_points", [])
        score_data = calculate_score(
            weak_points,
            st.session_state.test_results.get("failed", 0),
            st.session_state.test_results.get("total", 0)
        )
        st.markdown(f"""
        <div style='background:#16213e;
            border:2px solid {score_data["color"]};
            border-radius:12px;padding:24px;
            text-align:center;margin:16px 0;'>
            <div style='font-size:56px;font-weight:800;
                color:{score_data["color"]};'>
                {score_data["score"]}
            </div>
            <div style='font-size:16px;font-weight:600;
                color:{score_data["color"]};'>
                {score_data["label"]}
            </div>
            <div style='color:#a0a0b0;font-size:12px;
                margin-top:12px;'>
                Critical: {score_data["critical"]} |
                High: {score_data["high"]} |
                Medium: {score_data["medium"]} |
                Low: {score_data["low"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.report:
            with st.spinner("Generating report..."):
                try:
                    reporter = BugReporter()
                    report = reporter.compile_report(
                        repo_name="pasted_code",
                        analysis=st.session_state.analysis,
                        test_results=results,
                        fixes=[]
                    )
                    st.session_state.report = report

                    # SAVE TO HISTORY
                    try:
                        save_scan_history(
                            username=st.session_state.username,
                            code_snippet=st.session_state.original_code,
                            weak_points=len(
                                st.session_state.analysis.get(
                                    "weak_points", [])),
                            bugs=failed,
                            report=report if isinstance(
                                report, str) else str(report)
                        )
                        st.success("Scan saved to history!")
                    except Exception as e:
                        print(f"History save error: {e}")

                except Exception as e:
                    st.error(f"Report error: {e}")

        if st.session_state.report:
            if not st.session_state.get("fixes"):
                with st.spinner("Generating fix suggestions..."):
                    try:
                        weak_points_for_fixes = (
                            st.session_state.analysis.get(
                                "weak_points", [])
                        )
                        if not weak_points_for_fixes:
                            fixes = []
                            st.session_state["fixes"] = fixes
                        else:
                            suggester = FixSuggester()
                            original = "\n".join([
                                f['content']
                                for f in st.session_state.ingested_files
                            ])
                            fixes = suggester.suggest_all_fixes(
                                weak_points_for_fixes,
                                original
                            )
                            st.session_state["fixes"] = fixes
                    except Exception as e:
                        print(f"Fix suggestion error: {e}")
                        fixes = []
            else:
                fixes = st.session_state.get("fixes", [])

            st.markdown("**Bug Attack Report**")
            st.markdown(st.session_state.report)
            st.download_button(
                label="Download Report",
                data=st.session_state.report,
                file_name="breakbot_report.md",
                mime="text/markdown"
            )

            if fixes:
                st.markdown("### Fix Suggestions")
                for i, fix in enumerate(fixes, 1):
                    st.markdown(f"""
                    <div style='background:#16213e;
                        border:1px solid #ff3b3b30;
                        border-radius:10px;
                        padding:16px; margin:8px 0;'>
                        <div style='color:#ff3b3b; font-weight:700;
                            margin-bottom:8px;'>
                            Fix #{i}: {fix.get('weak_point','')[:60]}
                        </div>
                        <div style='color:#a0a0b0; font-size:13px;'>
                            Issue: {fix.get('issue','')}
                        </div>
                        <div style='color:#a0a0b0; font-size:13px;
                            margin-top:6px;'>
                            Why: {fix.get('explanation','')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(fix.get('fix_code',''),
                           language='python')

            try:
                pdf_path = generate_pdf_report(
                    repo_name="pasted_code",
                    analysis=st.session_state.analysis,
                    test_results=st.session_state.test_results,
                    fixes=st.session_state.get("fixes", []),
                    username=st.session_state.username
                )
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF Report",
                        data=f,
                        file_name="BreakBot_Report.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"PDF generation error: {e}")
