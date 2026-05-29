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
* { font-family: 'Inter', sans-serif !important; }

/* Main background - WHITE */
.stApp {
    background: #ffffff !important;
    color: #1a1a2e !important;
}

/* Hide unwanted elements */
/* Hide sidebar collapse button completely */
[data-testid="stSidebarCollapseButton"] {
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
}
button[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
/* Hide ALL header buttons */
[data-testid="stHeader"] button {
    display: none !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
}
[data-testid="stSidebarNav"] { display:none !important; }
[data-testid="stSidebarNavItems"] { display:none !important; }
ul[data-testid="stSidebarNavItems"] { display:none !important; }
[data-testid="stSidebarNavSeparator"] { display:none !important; }
[data-testid="stDecoration"] { display:none !important; }
.st-emotion-cache-1dp5vir { display:none !important; }
#MainMenu { visibility:hidden; }
footer { visibility:hidden; }
[data-testid="stToolbar"] { display:none; }

/* Sidebar - Light gray */
[data-testid="stSidebar"] {
    background: #f8f8fc !important;
    border-right: 1px solid #e8e8f0 !important;
}
[data-testid="stSidebar"] > div {
    padding: 24px 16px !important;
}

/* Sidebar logo */
.bb-logo {
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 3px;
    color: #ff3b3b;
    margin-bottom: 4px;
}
.bb-tagline {
    font-size: 10px;
    color: #9999bb;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 20px;
}

/* User card */
.bb-user-card {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.bb-username {
    font-weight: 700;
    font-size: 14px;
    color: #1a1a2e;
}
.bb-email {
    font-size: 11px;
    color: #9999bb;
    margin-top: 2px;
}

/* Nav section label */
.bb-nav-label {
    font-size: 10px;
    color: #9999bb;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
    margin-bottom: 8px;
}

/* Navigation buttons */
.stButton > button {
    background: #ffffff !important;
    color: #555580 !important;
    border: 1px solid #e8e8f0 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    width: 100% !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    margin-bottom: 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
.stButton > button:hover {
    background: #fff0f0 !important;
    border-color: #ff3b3b60 !important;
    color: #ff3b3b !important;
    transform: translateX(3px) !important;
}

/* Active nav item */
.bb-nav-active {
    background: #fff0f0;
    border: 1px solid #ff3b3b60;
    border-radius: 8px;
    padding: 8px 16px;
    color: #ff3b3b;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 4px;
}

/* Primary buttons */
div[data-testid="stButton"] button[kind="primary"],
.primary-action button {
    background: linear-gradient(
        135deg, #ff3b3b, #cc0000) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(255,59,59,0.3) !important;
}
.step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    background: linear-gradient(135deg, #fff5f5, #fff0f0);
    border-left: 3px solid #ff3b3b;
    border-radius: 0 10px 10px 0;
    margin: 24px 0 16px 0;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #1a1a2e;
    box-shadow: 0 2px 8px rgba(255,59,59,0.08);
}
.step-num {
    background: #ff3b3b;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 800;
    flex-shrink: 0;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #ffffff !important;
    border: 1px solid #e8e8f0 !important;
    border-radius: 8px !important;
    color: #1a1a2e !important;
    font-size: 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #ff3b3b80 !important;
    box-shadow: 0 0 0 3px rgba(255,59,59,0.1) !important;
}

/* Code blocks */
.stCodeBlock {
    border-radius: 10px !important;
    border: 1px solid #1e1e4a !important;
}

/* Cards */
.bb-card {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Metric cards */
.bb-metric,
.metric-card {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.bb-metric-val,
.metric-val {
    font-size: 40px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
}
.bb-metric-label,
.metric-label {
    font-size: 11px;
    color: #9999bb;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 500;
}

/* Score card */
.bb-score-card {
    background: linear-gradient(135deg, #fff5f5, #fff0f0);
    border: 1px solid #ffdddd;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
}

/* Severity badges */
.bb-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    margin: 3px;
    font-family: 'Inter', sans-serif;
}

/* Report section */
.bb-report-header {
    background: linear-gradient(135deg, #ff3b3b, #cc0000);
    color: white;
    padding: 20px 24px;
    border-radius: 12px 12px 0 0;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 1px;
}
.bb-report-body {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 20px 24px;
}
.bb-report-section {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f0f0f8;
}
.bb-report-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #9999bb;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
}

/* Bug item */
.bb-bug-item {
    background: #fff5f5;
    border: 1px solid #ffdddd;
    border-left: 3px solid #ff3b3b;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
}
.bb-bug-name {
    font-size: 13px;
    font-weight: 600;
    color: #cc0000;
}
.bb-bug-error {
    font-size: 12px;
    color: #888;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}

/* Function tags */
.bb-fn-tag {
    display: inline-block;
    background: #f5f5ff;
    border: 1px solid #e0e0f0;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    color: #555580;
    font-family: 'JetBrains Mono', monospace;
    margin: 3px;
}

/* Weakness item */
.bb-weak-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #f5f5ff;
}

/* Section divider */
.bb-divider {
    border: none;
    border-top: 1px solid #f0f0f8;
    margin: 16px 0;
}

/* Radio buttons */
.stRadio label {
    color: #333355 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.stRadio > div {
    gap: 8px !important;
}
[data-testid="stRadio"] label {
    color: #333355 !important;
}
[data-testid="stRadio"] span {
    color: #333355 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f5f5ff !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #e8e8f0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #9999bb !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: #ff3b3b !important;
    color: white !important;
    font-weight: 600 !important;
}

/* Dataframe */
.stDataFrame {
    border: 1px solid #e8e8f0 !important;
    border-radius: 8px !important;
}

/* Success/error messages */
.stSuccess {
    background: #f0fff8 !important;
    border: 1px solid #00cc88 !important;
    color: #006644 !important;
}
.stError {
    background: #fff5f5 !important;
    border: 1px solid #ffaaaa !important;
    color: #cc0000 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #f8f8fc; }
::-webkit-scrollbar-thumb {
    background: #ff3b3b40;
    border-radius: 2px;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="bb-logo">BREAKBOT</div>
    <div class="bb-tagline">AI Red-Team Agent</div>
    <div class="bb-divider"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="bb-user-card">
        <div class="bb-username">
            {st.session_state.username}
        </div>
        <div class="bb-email">
            {st.session_state.user_email}
        </div>
    </div>
    <div class="bb-nav-label">Navigation</div>
    """, unsafe_allow_html=True)

    nav_items = ["Run Scan", "My History", "Dashboard"]
    if st.session_state.get("is_admin", False):
        nav_items.append("Admin Panel")

    for item in nav_items:
        if st.session_state.nav_page == item:
            st.markdown(f"""
            <div class="bb-nav-active">{item}</div>
            """, unsafe_allow_html=True)
        else:
            if st.button(item, key=f"nav_{item}"):
                st.session_state.nav_page = item
                st.rerun()

    st.markdown('<div class="bb-divider"></div>',
                unsafe_allow_html=True)

    if st.session_state.nav_page == "Run Scan":
        st.markdown("""
        <div style='font-size:10px;color:#9999bb;
            text-transform:uppercase;letter-spacing:2px;
            font-weight:600;margin:16px 0 8px 0;'>
            Input Mode
        </div>""", unsafe_allow_html=True)
        mode = st.radio(
            "Select input mode",
            ["GitHub Repo", "Paste Code"],
            index=1,
            label_visibility="visible")
    else:
        mode = "Paste Code"

    st.markdown('<div class="bb-divider"></div>',
                unsafe_allow_html=True)

    if st.button("Logout", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("""
    <div style='font-size:10px;color:#ccccdd;
        text-align:center;margin-top:20px;
        text-transform:uppercase;letter-spacing:1px;'>
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
    <div class="step-num">1</div>Input
</div>""", unsafe_allow_html=True)

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
        <div class="step-num">2</div>Analysis
    </div>""", unsafe_allow_html=True)
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
        <div class="step-num">3</div>Attack
    </div>""", unsafe_allow_html=True)
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
        <div class="step-num">4</div>Run & Report
    </div>""", unsafe_allow_html=True)
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
                     style="color:#1a1a2e">{total}</div>
                <div class="bb-metric-label">Total Tests</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="bb-metric">
                <div class="bb-metric-val"
                     style="color:#00aa66">{passed}</div>
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

            st.markdown("""
            <div class="bb-report-header">
                BUG ATTACK REPORT
            </div>
            <div class="bb-report-body">
            """, unsafe_allow_html=True)

            functions = st.session_state.analysis.get(
                "functions", [])
            if functions:
                st.markdown("""
                <div class="bb-report-section">
                    <div class="bb-report-section-title">
                        Functions Analyzed
                    </div>
                """, unsafe_allow_html=True)
                tags = "".join([
                    f'<span class="bb-fn-tag">{fn}</span>'
                    for fn in functions])
                st.markdown(tags, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            weak_points = st.session_state.analysis.get(
                "weak_points", [])
            if weak_points:
                st.markdown("""
                <div class="bb-report-section">
                    <div class="bb-report-section-title">
                        Vulnerabilities Found
                    </div>
                """, unsafe_allow_html=True)
                for wp in weak_points:
                    sev = get_severity(wp)
                    col = get_severity_color(sev)
                    st.markdown(f"""
                    <div class="bb-weak-item">
                        <span style="background:{col}20;
                            border:1px solid {col}60;
                            color:{col};border-radius:4px;
                            padding:2px 8px;font-size:10px;
                            font-weight:700;min-width:65px;
                            text-align:center;display:inline-block;">
                            {sev}
                        </span>
                        <span style="color:#444466;font-size:13px;">
                            {wp}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            failures = st.session_state.test_results.get(
                "failures", [])
            if failures:
                st.markdown("""
                <div class="bb-report-section">
                    <div class="bb-report-section-title">
                        Confirmed Bugs
                    </div>
                """, unsafe_allow_html=True)
                for i, f in enumerate(failures, 1):
                    st.markdown(f"""
                    <div class="bb-bug-item">
                        <div class="bb-bug-name">
                            Bug #{i}: {f.get('test_name','')}
                        </div>
                        <div class="bb-bug-error">
                            {f.get('error','')[:150]}
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
                    <div style='background:#ffffff;
                        border:1px solid #e8e8f0;
                        border-radius:10px;
                        padding:16px; margin:8px 0;
                        box-shadow:0 2px 8px rgba(0,0,0,0.05);'>
                        <div style='color:#ff3b3b; font-weight:700;
                            margin-bottom:8px;'>
                            Fix #{i}: {fix.get('weak_point','')[:60]}
                        </div>
                        <div style='color:#555580; font-size:13px;'>
                            Issue: {fix.get('issue','')}
                        </div>
                        <div style='color:#555580; font-size:13px;
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

