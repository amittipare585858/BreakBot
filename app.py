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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Reset and base */
* {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}
.stApp {
    background: #080810 !important;
    color: #e8e8f0 !important;
}

/* Remove ALL unwanted lines and borders */
hr { display: none !important; }
.stHorizontalBlock { gap: 1rem !important; }
[data-testid="stDecoration"] {
    display: none !important;
}
.st-emotion-cache-h4xjwg {
    display: none !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
    border: none !important;
}
/* Remove green/colored lines */
.stApp > header {
    background: transparent !important;
}
[data-testid="stHeader"]::before,
[data-testid="stHeader"]::after {
    display: none !important;
}
.st-emotion-cache-1dp5vir {
    display: none !important;
}
div[data-testid="stDecoration"] {
    display: none !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0c0c18 !important;
    border-right: 1px solid #1a1a3a !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div {
    padding: 24px 16px !important;
}

/* Sidebar logo */
.bb-logo {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 3px;
    background: linear-gradient(135deg, #ff3b3b, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.bb-tagline {
    font-size: 11px;
    color: #555580;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 20px;
}

/* User info in sidebar */
.bb-user-card {
    background: #12122a;
    border: 1px solid #1e1e4a;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 20px;
}
.bb-username {
    font-weight: 600;
    font-size: 14px;
    color: #ffffff;
}
.bb-email {
    font-size: 11px;
    color: #555580;
    margin-top: 2px;
}

/* Navigation buttons */
.stButton > button {
    background: transparent !important;
    color: #a0a0c0 !important;
    border: 1px solid #1e1e4a !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    width: 100% !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    margin-bottom: 4px !important;
}
.stButton > button:hover {
    background: #ff3b3b15 !important;
    border-color: #ff3b3b50 !important;
    color: #ff6b6b !important;
    transform: translateX(4px) !important;
}

/* Primary action buttons */
.primary-btn > button {
    background: linear-gradient(135deg, #ff3b3b, #cc0000) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    letter-spacing: 0.3px !important;
}
.primary-btn > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(255,59,59,0.3) !important;
}
.step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    background: linear-gradient(135deg, #120808, #1a0a0a);
    border-left: 3px solid #ff3b3b;
    border-radius: 0 10px 10px 0;
    margin: 24px 0 16px 0;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #ffffff;
}
.step-num {
    background: #ff3b3b;
    color: white;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    flex-shrink: 0;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0e0e20 !important;
    border: 1px solid #1e1e4a !important;
    border-radius: 8px !important;
    color: #e8e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #ff3b3b80 !important;
    box-shadow: 0 0 0 2px rgba(255,59,59,0.1) !important;
}

/* Code blocks */
.stCodeBlock {
    border-radius: 10px !important;
    border: 1px solid #1e1e4a !important;
}

/* Metric cards */
.bb-metric,
.metric-card {
    background: #0e0e20;
    border: 1px solid #1e1e4a;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.2s ease;
}
.bb-metric:hover,
.metric-card:hover {
    border-color: #ff3b3b40;
    transform: translateY(-2px);
}
.bb-metric-val,
.metric-val {
    font-size: 40px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
    color: #ff3b3b;
}
.bb-metric-label,
.metric-label {
    font-size: 11px;
    color: #555580;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 500;
}

/* Score card */
.bb-score-card {
    background: linear-gradient(135deg, #0e0e20, #120820);
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    margin: 16px 0;
}

/* Severity badges */
.bb-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
    margin: 3px;
    font-family: 'Inter', sans-serif;
}

/* Report card */
.bb-report-card {
    background: #0e0e20;
    border: 1px solid #1e1e4a;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
}
.bb-report-title {
    font-size: 13px;
    font-weight: 700;
    color: #ff6b6b;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.bb-report-body {
    font-size: 13px;
    color: #a0a0c0;
    line-height: 1.6;
}

/* Section divider */
.bb-divider {
    border: none;
    border-top: 1px solid #1a1a3a;
    margin: 20px 0;
}

/* Radio buttons */
.stRadio label {
    color: #a0a0c0 !important;
    font-size: 13px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080810; }
::-webkit-scrollbar-thumb {
    background: #ff3b3b40;
    border-radius: 2px;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="bb-logo">BREAKBOT</div>
    <div class="bb-tagline">AI Red-Team Agent</div>
    <div class="bb-divider" style="border-top:1px solid #1a1a3a; margin:12px 0;"></div>
    """, unsafe_allow_html=True)

    # User card
    st.markdown(f"""
    <div class="bb-user-card">
        <div class="bb-username">
            {st.session_state.username}
        </div>
        <div class="bb-email">
            {st.session_state.user_email}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown("""
    <div style='font-size:10px; color:#333360;
        text-transform:uppercase; letter-spacing:2px;
        font-weight:600; margin-bottom:8px;'>
        Navigation
    </div>
    """, unsafe_allow_html=True)

    nav_items = ["Run Scan", "My History", "Dashboard"]
    if st.session_state.get("is_admin", False):
        nav_items.append("Admin Panel")

    for item in nav_items:
        active = st.session_state.nav_page == item
        if active:
            st.markdown(f"""
            <div style='background:#ff3b3b15;
                border:1px solid #ff3b3b40;
                border-radius:8px;
                padding:8px 16px;
                color:#ff6b6b;
                font-size:13px;
                font-weight:600;
                margin-bottom:4px;
                cursor:pointer;'>
                {item}
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(item, key=f"nav_{item}"):
                st.session_state.nav_page = item
                st.rerun()

    st.markdown("""
    <div class="bb-divider" style="border-top:1px solid #1a1a3a; margin:16px 0;"></div>
    """, unsafe_allow_html=True)

    # Input mode (only on Run Scan)
    if st.session_state.nav_page == "Run Scan":
        st.markdown("""
        <div style='font-size:10px; color:#333360;
            text-transform:uppercase; letter-spacing:2px;
            font-weight:600; margin-bottom:8px;'>
            Input Mode
        </div>
        """, unsafe_allow_html=True)
        mode = st.radio("",
            ["GitHub Repo", "Paste Code"],
            index=1,
            label_visibility="collapsed")
    else:
        mode = "Paste Code"

    st.markdown("""
    <div class="bb-divider" style="border-top:1px solid #1a1a3a; margin:16px 0;"></div>
    """, unsafe_allow_html=True)

    if st.button("Logout", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("""
    <div style='position:absolute; bottom:20px; left:16px;
        right:16px; font-size:10px; color:#2a2a50;
        text-align:center; text-transform:uppercase;
        letter-spacing:1px;'>
        Powered by Google Gemini
    </div>
    """, unsafe_allow_html=True)

# ─── PAGE: MY HISTORY ─────────────────────────────────────
if st.session_state.nav_page == "My History":
    st.markdown("""
    <div class="step-header">
        My Scan History
    </div>
    """, unsafe_allow_html=True)
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
st.markdown("""
<div class="step-header">
    <div class="step-num">1</div>
    Input
</div>
""", unsafe_allow_html=True)

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
    st.markdown("""
    <div class="step-header">
        <div class="step-num">2</div>
        Analysis
    </div>
    """, unsafe_allow_html=True)
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
    st.markdown("""
    <div class="step-header">
        <div class="step-num">3</div>
        Attack
    </div>
    """, unsafe_allow_html=True)
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
    st.markdown("""
    <div class="step-header">
        <div class="step-num">4</div>
        Run & Report
    </div>
    """, unsafe_allow_html=True)
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
            <div class="bb-metric">
                <div class="bb-metric-val"
                     style="color:#e8e8f0">{total}</div>
                <div class="bb-metric-label">Total Tests</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="bb-metric">
                <div class="bb-metric-val"
                     style="color:#00d97e">{passed}</div>
                <div class="bb-metric-label">Passed</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="bb-metric">
                <div class="bb-metric-val"
                     style="color:#ff3b3b">{failed}</div>
                <div class="bb-metric-label">Failed</div>
            </div>""", unsafe_allow_html=True)

        weak_points = st.session_state.analysis.get(
            "weak_points", [])
        score_data = calculate_score(
            weak_points,
            st.session_state.test_results.get("failed", 0),
            st.session_state.test_results.get("total", 0)
        )
        st.markdown(f"""
        <div class='bb-score-card' style='
            border:2px solid {score_data["color"]};
            box-shadow:0 18px 50px rgba(0,0,0,0.25);'>
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

            # Parse and display report beautifully
            st.markdown("""
            <div style='background:#0e0e20;
                border:1px solid #1e1e4a;
                border-radius:16px; padding:28px;
                margin:16px 0;'>
                <div style='font-size:20px; font-weight:800;
                    color:#ff3b3b; margin-bottom:4px;
                    letter-spacing:1px;'>
                    BUG ATTACK REPORT
                </div>
                <div style='font-size:12px; color:#333360;
                    margin-bottom:20px;'>
                    Generated by BreakBot AI Red-Team Agent
                </div>
            """, unsafe_allow_html=True)

            functions = st.session_state.analysis.get(
                "functions", [])
            if functions:
                st.markdown(f"""
                <div class="bb-report-card">
                    <div class="bb-report-title">
                        Functions Analyzed ({len(functions)})
                    </div>
                    <div style='display:flex; flex-wrap:wrap; gap:6px;'>
                        {"".join([
                            f'<span style="background:#12122a;'
                            f'border:1px solid #1e1e4a;'
                            f'border-radius:6px;padding:3px 10px;'
                            f'font-size:12px;color:#a0a0c0;'
                            f'font-family:JetBrains Mono,monospace;">'
                            f'{fn}</span>'
                            for fn in functions
                        ])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            weak_points = st.session_state.analysis.get(
                "weak_points", [])
            if weak_points:
                st.markdown("""
                <div class="bb-report-card">
                    <div class="bb-report-title">
                        Vulnerabilities Found
                    </div>
                """, unsafe_allow_html=True)
                for wp in weak_points:
                    severity = get_severity(wp)
                    color = get_severity_color(severity)
                    st.markdown(f"""
                    <div style='display:flex; align-items:center;
                        gap:10px; padding:8px 0;
                        border-bottom:1px solid #12122a;'>
                        <span style='background:{color}22;
                            border:1px solid {color}60;
                            color:{color};border-radius:4px;
                            padding:2px 8px;font-size:10px;
                            font-weight:700;letter-spacing:1px;
                            min-width:70px;text-align:center;'>
                            {severity}
                        </span>
                        <span style='color:#c0c0d0;font-size:13px;'>
                            {wp}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            failures = st.session_state.test_results.get(
                "failures", [])
            if failures:
                st.markdown("""
                <div class="bb-report-card"
                     style="border-color:#ff3b3b30;">
                    <div class="bb-report-title"
                         style="color:#ff3b3b;">
                        Bugs Confirmed by Testing
                    </div>
                """, unsafe_allow_html=True)
                for i, f in enumerate(failures, 1):
                    st.markdown(f"""
                    <div style='padding:10px 0;
                        border-bottom:1px solid #12122a;'>
                        <div style='font-size:13px;font-weight:600;
                            color:#ff6b6b;margin-bottom:4px;'>
                            Bug #{i}: {f.get('test_name','')}
                        </div>
                        <div style='font-size:12px;color:#666690;
                            font-family:JetBrains Mono,monospace;'>
                            {f.get('error','')[:200]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
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
