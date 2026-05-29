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

# â”€â”€â”€ SESSION STATE INIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ LOGIN GATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# â”€â”€â”€ GLOBAL CSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── BASE ── */
*, *::before, *::after {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}
.stApp {
    background: #080810 !important;
    color: #e8e8f0 !important;
}

/* ── HIDE UNWANTED ── */
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.st-emotion-cache-1dp5vir { display: none !important; }
[data-testid="stSidebarCollapseButton"] { visibility: hidden !important; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0c0c18 !important;
    border-right: 1px solid #1a1a3a !important;
}
[data-testid="stSidebar"] > div { padding: 28px 20px !important; }

/* ── LOGO ── */
.bb-logo { font-size: 20px; font-weight: 900; letter-spacing: 4px; color: #ff3b3b; margin-bottom: 4px; }
.bb-tagline { font-size: 10px; color: #333360; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 24px; }

/* ── USER CARD ── */
.bb-user-card { background: #12122a; border: 1px solid #1a1a3a; border-radius: 12px; padding: 14px 16px; margin-bottom: 24px; }
.bb-username { font-weight: 700; font-size: 14px; color: #ffffff; margin-bottom: 2px; }
.bb-email { font-size: 11px; color: #555580; }

/* ── NAV LABEL ── */
.bb-nav-label { font-size: 10px; color: #333360; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 10px; }

/* ── NAV ACTIVE ── */
.bb-nav-active { background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.3); border-radius: 8px; padding: 9px 16px; color: #ff6b6b; font-size: 13px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.3px; }

/* ── ALL BUTTONS ── */
.stButton > button { background: #12122a !important; color: #a0a0c0 !important; border: 1px solid #1a1a3a !important; border-radius: 8px !important; font-weight: 500 !important; font-size: 13px !important; padding: 9px 16px !important; width: 100% !important; transition: all 0.2s ease !important; margin-bottom: 6px !important; letter-spacing: 0.2px !important; }
.stButton > button:hover { background: rgba(255,59,59,0.1) !important; border-color: rgba(255,59,59,0.4) !important; color: #ff6b6b !important; transform: translateX(3px) !important; }

/* ── STEP HEADERS ── */
.step-header { display: flex; align-items: center; gap: 14px; padding: 16px 22px; background: linear-gradient(135deg, #120808, #1a0a0a); border-left: 3px solid #ff3b3b; border-radius: 0 12px 12px 0; margin: 28px 0 20px 0; font-size: 15px; font-weight: 700; color: #ffffff; letter-spacing: 0.3px; box-shadow: 0 4px 20px rgba(255,59,59,0.08); }
.step-num { background: #ff3b3b; color: white; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; flex-shrink: 0; }

/* ── INPUT FIELDS ── */
.stTextInput > label, .stTextArea > label { color: #555580 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea { background: #0c0c18 !important; border: 1px solid #1a1a3a !important; border-radius: 8px !important; color: #e8e8f0 !important; font-size: 14px !important; font-family: 'Inter', sans-serif !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: rgba(255,59,59,0.5) !important; box-shadow: 0 0 0 3px rgba(255,59,59,0.1) !important; }
.stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder { color: #333360 !important; }

/* ── RADIO BUTTONS ── */
.stRadio > label { color: #555580 !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
div[role="radiogroup"] label { color: #a0a0c0 !important; font-size: 13px !important; }
div[role="radiogroup"] label span { color: #a0a0c0 !important; }

/* ── METRIC CARDS ── */
.bb-metric { background: #0c0c18; border: 1px solid #1a1a3a; border-radius: 14px; padding: 24px 20px; text-align: center; transition: all 0.2s ease; }
.bb-metric:hover { border-color: rgba(255,59,59,0.3); transform: translateY(-2px); box-shadow: 0 12px 30px rgba(0,0,0,0.3); }
.bb-metric-val { font-size: 44px; font-weight: 900; line-height: 1; margin-bottom: 8px; }
.bb-metric-label { font-size: 10px; color: #333360; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; }

/* ── CARDS ── */
.bb-card { background: #0c0c18; border: 1px solid #1a1a3a; border-radius: 14px; padding: 24px; margin: 10px 0; transition: all 0.2s; }
.bb-card:hover { border-color: rgba(255,59,59,0.2); }

/* ── SEVERITY BADGES ── */
.bb-badge { display: inline-block; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 700; margin: 3px; letter-spacing: 0.5px; }

/* ── REPORT ── */
.bb-report-header { background: linear-gradient(135deg, #ff3b3b, #cc0000); color: white; padding: 22px 28px; border-radius: 14px 14px 0 0; font-size: 14px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
.bb-report-body { background: #0c0c18; border: 1px solid #1a1a3a; border-top: none; border-radius: 0 0 14px 14px; padding: 24px 28px; }
.bb-report-section { margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #12122a; }
.bb-report-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.bb-report-section-title { font-size: 10px; font-weight: 700; color: #333360; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }
.bb-fn-tag { display: inline-block; background: #12122a; border: 1px solid #1a1a3a; border-radius: 6px; padding: 4px 12px; font-size: 12px; color: #a0a0c0; font-family: 'JetBrains Mono', monospace; margin: 3px; }
.bb-weak-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid #0e0e20; }
.bb-weak-item:last-child { border-bottom: none; }
.bb-bug-item { background: rgba(255,59,59,0.05); border: 1px solid rgba(255,59,59,0.15); border-left: 3px solid #ff3b3b; border-radius: 0 10px 10px 0; padding: 12px 16px; margin: 8px 0; }
.bb-bug-name { font-size: 13px; font-weight: 700; color: #ff6b6b; margin-bottom: 4px; }
.bb-bug-error { font-size: 11px; color: #555580; font-family: 'JetBrains Mono', monospace; line-height: 1.5; }

/* ── SCORE CARD ── */
.bb-score-card { background: linear-gradient(135deg, #120808, #1a0808); border: 1px solid rgba(255,59,59,0.2); border-radius: 16px; padding: 28px; text-align: center; margin: 16px 0; }

/* ── DIVIDER ── */
.bb-divider { border: none; border-top: 1px solid #1a1a3a; margin: 20px 0; }

/* ── HISTORY CARDS ── */
.bb-history-card { background: #0c0c18; border: 1px solid #1a1a3a; border-radius: 12px; padding: 18px 22px; margin: 10px 0; transition: all 0.2s; cursor: pointer; }
.bb-history-card:hover { border-color: rgba(255,59,59,0.3); transform: translateX(4px); }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] { background: #0c0c18 !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid #1a1a3a !important; gap: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #555580 !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; border: none !important; }
.stTabs [aria-selected="true"] { background: #ff3b3b !important; color: white !important; font-weight: 700 !important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader { background: #0c0c18 !important; border: 1px solid #1a1a3a !important; border-radius: 8px !important; color: #a0a0c0 !important; }

/* ── DATAFRAME ── */
.stDataFrame { border: 1px solid #1a1a3a !important; border-radius: 10px !important; }
.stDataFrame td { color: #e8e8f0 !important; background: #0c0c18 !important; }
.stDataFrame th { color: #555580 !important; background: #12122a !important; }

/* ── CODE BLOCKS ── */
.stCodeBlock { border: 1px solid #1a1a3a !important; border-radius: 10px !important; }

/* ── SUCCESS/ERROR ── */
.stSuccess { background: rgba(0,170,102,0.1) !important; border: 1px solid rgba(0,170,102,0.3) !important; color: #00dd88 !important; border-radius: 8px !important; }
.stError { background: rgba(255,59,59,0.08) !important; border: 1px solid rgba(255,59,59,0.3) !important; color: #ff6b6b !important; border-radius: 8px !important; }
.stInfo { background: rgba(100,100,255,0.08) !important; border: 1px solid rgba(100,100,255,0.2) !important; color: #8888ff !important; border-radius: 8px !important; }
.stWarning { background: rgba(255,180,0,0.08) !important; border: 1px solid rgba(255,180,0,0.2) !important; color: #ffcc44 !important; border-radius: 8px !important; }

/* ── LINE CHART ── */
.stLineChart { border-radius: 12px !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080810; }
::-webkit-scrollbar-thumb { background: rgba(255,59,59,0.3); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,59,59,0.5); }
</style>
""", unsafe_allow_html=True)

# â”€â”€â”€ SIDEBAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with st.sidebar:
    st.markdown("""
    <div class="bb-logo">BREAKBOT</div>
    <div class="bb-tagline">
        AI Red-Team Agent
    </div>
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

    nav_items = ["Run Scan", "My History", 
                 "Dashboard"]
    if st.session_state.get("is_admin", False):
        nav_items.append("Admin Panel")

    for item in nav_items:
        if st.session_state.nav_page == item:
            st.markdown(
                f'<div class="bb-nav-active">'
                f'{item}</div>',
                unsafe_allow_html=True)
        else:
            if st.button(item, 
                         key=f"nav_{item}"):
                st.session_state.nav_page = item
                st.rerun()

    st.markdown(
        '<div class="bb-divider"></div>',
        unsafe_allow_html=True)

    if st.session_state.nav_page == "Run Scan":
        st.markdown(
            '<div class="bb-nav-label">'
            'Input Mode</div>',
            unsafe_allow_html=True)
        mode = st.radio(
            "Select input mode",
            ["GitHub Repo", "Paste Code"],
            index=1,
            label_visibility="collapsed")
    else:
        mode = "Paste Code"

    st.markdown(
        '<div class="bb-divider"></div>',
        unsafe_allow_html=True)

    if st.button("Logout", key="logout_btn"):
        for key in list(
                st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("""
    <div style='margin-top:24px;
        font-size:10px;color:#1a1a3a;
        text-align:center;
        text-transform:uppercase;
        letter-spacing:1px;'>
        Powered by Google Gemini
    </div>
    """, unsafe_allow_html=True)
# â”€â”€â”€ PAGE: MY HISTORY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if st.session_state.nav_page == "My History":
    st.markdown("""
    <div class="step-header">
        <div class="step-num">H</div>
        My Scan History
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from database import get_user_history
        history = get_user_history(
            st.session_state.username)
        
        if not history:
            st.markdown("""
            <div style='background:#ffffff;
                border:1.5px solid #ebebf5;
                border-radius:12px;
                padding:40px;
                text-align:center;
                color:#9999bb;'>
                No scans yet. 
                Run your first scan to see history!
            </div>
            """, unsafe_allow_html=True)
        else:
            # Show selected scan detail
            if "selected_scan" not in st.session_state:
                st.session_state.selected_scan = None
            
            # If a scan is selected show its detail
            if st.session_state.selected_scan is not None:
                i = st.session_state.selected_scan
                scan = history[
                    i]
                
                # Back button
                if st.button(
                    "Back to History", 
                    key="back_btn"):
                    st.session_state.selected_scan = None
                    st.rerun()
                
                st.markdown(f"""
                <div style='background:#ffffff;
                    border:1.5px solid #ebebf5;
                    border-radius:12px;
                    padding:24px;
                    margin:16px 0;
                    box-shadow:0 2px 8px 
                        rgba(0,0,0,0.06);'>
                    <div style='font-size:16px;
                        font-weight:700;
                        color:#1a1a2e;
                        margin-bottom:4px;'>
                        {scan.get('code_snippet',
                            'pasted_code')[:30]}...
                    </div>
                    <div style='font-size:11px;
                        color:#9999bb;'>
                        Scanned: 
                        {str(scan.get(
                            'scanned_at',''))[:16]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Metrics
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <div class="bb-metric">
                        <div class="bb-metric-val"
                            style="color:#ff3b3b;">
                            {scan.get(
                                'weak_points_found',0)}
                        </div>
                        <div class="bb-metric-label">
                            Weak Points
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="bb-metric">
                        <div class="bb-metric-val"
                            style="color:#ff3b3b;">
                            {scan.get('bugs_found',0)}
                        </div>
                        <div class="bb-metric-label">
                            Bugs Found
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Download options
                if scan.get("report_content"):
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download as Markdown
                        st.download_button(
                            label="Download MD Report",
                            data=scan["report_content"],
                            file_name=f"BreakBot_Scan_{i+1}_Report.md",
                            mime="text/markdown",
                            key=f"dl_md_{i}"
                        )
                    
                    with col2:
                        # Generate and download PDF
                        try:
                            from agent.pdf_reporter import (
                                generate_pdf_report)
                            
                            # Build minimal analysis 
                            # and results from history
                            hist_analysis = {
                                "functions": [],
                                "weak_points": [],
                                "attack_surfaces": []
                            }
                            hist_results = {
                                "total": 0,
                                "passed": 0,
                                "failed": scan.get(
                                    "bugs_found", 0),
                                "failures": []
                            }
                            
                            pdf_path = generate_pdf_report(
                                repo_name=f"scan_{i+1}",
                                analysis=hist_analysis,
                                test_results=hist_results,
                                fixes=[],
                                username=st.session_state.username
                            )
                            
                            with open(pdf_path, "rb") as f:
                                pdf_data = f.read()
                            
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_data,
                                file_name=f"BreakBot_Scan_{i+1}_Report.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{i}"
                            )
                        except Exception as e:
                            st.error(
                                f"PDF error: {e}")
                    
                    st.markdown("---")
                    st.markdown("**Full Report:**")
                    st.markdown(
                        scan["report_content"])
            
            else:
                # Show list of scans as cards
                st.markdown(f"""
                <div style='font-size:13px;
                    color:#9999bb;
                    margin-bottom:16px;'>
                    {len(history)} scan(s) found. 
                    Click any scan to view details.
                </div>
                """, unsafe_allow_html=True)
                
                for i, scan in enumerate(history):
                    # Get scan name from code snippet
                    snippet = scan.get(
                        'code_snippet', '')
                    scan_name = (
                        snippet[:40].strip() 
                        if snippet 
                        else f"Scan #{i+1}"
                    )
                    date = str(scan.get(
                        'scanned_at', ''))[:16]
                    bugs = scan.get('bugs_found', 0)
                    wps = scan.get(
                        'weak_points_found', 0)
                    
                    # Severity color
                    bug_color = (
                        "#ff3b3b" if bugs > 3
                        else "#cc8800" if bugs > 0
                        else "#00aa66"
                    )
                    
                    st.markdown(f"""
                    <div style='background:#ffffff;
                        border:1.5px solid #ebebf5;
                        border-radius:12px;
                        padding:16px 20px;
                        margin:8px 0;
                        box-shadow:0 2px 6px 
                            rgba(0,0,0,0.05);
                        cursor:pointer;
                        transition:all 0.2s;'>
                        <div style='display:flex;
                            justify-content:space-between;
                            align-items:center;'>
                            <div>
                                <div style='font-size:14px;
                                    font-weight:600;
                                    color:#1a1a2e;
                                    margin-bottom:4px;'>
                                    Scan #{i+1}
                                </div>
                                <div style='font-size:12px;
                                    color:#9999bb;'>
                                    {date}
                                </div>
                            </div>
                            <div style='display:flex;
                                gap:12px;
                                align-items:center;'>
                                <div style='text-align:center;'>
                                    <div style='font-size:18px;
                                        font-weight:700;
                                        color:#555580;'>
                                        {wps}
                                    </div>
                                    <div style='font-size:10px;
                                        color:#9999bb;'>
                                        Weak Points
                                    </div>
                                </div>
                                <div style='text-align:center;'>
                                    <div style='font-size:18px;
                                        font-weight:700;
                                        color:{bug_color};'>
                                        {bugs}
                                    </div>
                                    <div style='font-size:10px;
                                        color:#9999bb;'>
                                        Bugs
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(
                        f"View Details",
                        key=f"scan_btn_{i}"):
                        st.session_state.selected_scan = i
                        st.rerun()
                    
    except Exception as e:
        st.error(f"Could not load history: {e}")
    
    st.stop()
# â”€â”€â”€ PAGE: ADMIN PANEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ PAGE: RUN SCAN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ STEP 2: ANALYSIS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ STEP 3: ATTACK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ STEP 4: RUN & REPORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

