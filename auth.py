"""Simple Streamlit authentication helpers for BreakBot."""

from __future__ import annotations

import hashlib
import json
import os
import re

import streamlit as st


USERS_FILE = "users.json"


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> dict:
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    default = {
        "admin": hash_password("admin123"),
        "demo": hash_password("demo123"),
    }
    save_users(default)
    return default


def save_users(users: dict) -> None:
    """Save users to JSON file."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f)


def verify_user(username: str, password: str) -> bool:
    """Verify username and password."""
    users = load_users()
    if username in users:
        return users[username] == hash_password(password)
    return False


def register_user(username: str, password: str) -> bool:
    """Register a new user. Returns False if username taken."""
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True


def is_valid_email(email: str) -> bool:
    """Check if email format is valid - any provider."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def show_login_page():
    """Display login/register page."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp { background: #080810 !important; color: #e8e8f0 !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stDecoration"] { display: none !important; }
.st-emotion-cache-1dp5vir { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.stButton > button { background: linear-gradient(135deg, #ff3b3b, #cc0000) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 14px !important; width: 100% !important; padding: 12px !important; letter-spacing: 0.3px !important; box-shadow: 0 4px 16px rgba(255,59,59,0.3) !important; transition: all 0.2s !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(255,59,59,0.4) !important; }
.stTextInput > label { color: #555580 !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
.stTextInput > div > div > input { background: #0c0c18 !important; border: 1px solid #1a1a3a !important; border-radius: 8px !important; color: #e8e8f0 !important; font-size: 14px !important; padding: 12px !important; }
.stTextInput > div > div > input:focus { border-color: rgba(255,59,59,0.5) !important; box-shadow: 0 0 0 3px rgba(255,59,59,0.1) !important; }
.stTextInput > div > div > input::placeholder { color: #333360 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0c0c18 !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid #1a1a3a !important; gap: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #555580 !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; border: none !important; padding: 8px 20px !important; }
.stTabs [aria-selected="true"] { background: #ff3b3b !important; color: white !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

    # Login page layout
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;
            padding: 60px 0 36px;'>
            <div style='font-size:36px;
                font-weight:900;
                letter-spacing:5px;
                color:#ff3b3b;
                margin-bottom:10px;'>
                BREAKBOT
            </div>
            <div style='font-size:11px;
                color:#333360;
                text-transform:uppercase;
                letter-spacing:3px;'>
                AI Red-Team Security Agent
            </div>
        </div>

        <div style='background:#0c0c18;
            border:1px solid #1a1a3a;
            border-radius:16px;
            padding:32px 28px;
            box-shadow:0 20px 60px rgba(0,0,0,0.5);'>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_pass = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login", key="login_btn"):
                if not login_user or not login_pass:
                    st.error("Please fill all fields")
                else:
                    try:
                        from database import verify_user
                        user = verify_user(login_user.strip(), login_pass.strip())
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = user["username"]
                            st.session_state.is_admin = user.get("is_admin", False)
                            st.session_state.user_email = user.get("email", "")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    except Exception as e:
                        st.error(f"Login error: {e}")

            st.markdown("""
            <div style='margin-top:20px;
                padding-top:16px;
                border-top:1px solid #12122a;
                font-size:12px;
                color:#333360;
                text-align:center;'>
                Demo: 
                <code style='background:#12122a;
                    color:#ff6b6b;
                    padding:2px 8px;
                    border-radius:4px;'>demo</code>
                /
                <code style='background:#12122a;
                    color:#ff6b6b;
                    padding:2px 8px;
                    border-radius:4px;'>demo123</code>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            new_user = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            new_email = st.text_input("Email Address", key="reg_email", placeholder="name@example.com")
            new_pass = st.text_input("Password", type="password", key="reg_pass", placeholder="Minimum 6 characters")
            confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Repeat your password")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", key="reg_btn"):
                if not all([new_user, new_email, new_pass, confirm]):
                    st.error("Please fill all fields")
                elif not is_valid_email(new_email):
                    st.error("Please enter a valid email")
                elif len(new_pass) < 6:
                    st.error("Password min 6 characters")
                elif new_pass != confirm:
                    st.error("Passwords do not match")
                else:
                    from database import register_user
                    result = register_user(new_user, new_email, new_pass)
                    if result["success"]:
                        st.success("Account created! Please login.")
                    else:
                        st.error(result["error"])

        st.markdown("</div>", unsafe_allow_html=True)
def show_user_history():
    """Display scan history for the current user."""
    from database import get_user_history
    import streamlit as st

    history = get_user_history(st.session_state.username)
    if not history:
        st.info("No scan history yet. Run your first scan!")
        return

    for i, scan in enumerate(history):
        with st.expander(
            f"Scan {i + 1} | "
            f"{str(scan.get('scanned_at', ''))[:16]} | "
            f"Bugs Found: {scan.get('bugs_found', 0)}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Weak Points", scan.get("weak_points_found", 0))
            with col2:
                st.metric("Bugs Found", scan.get("bugs_found", 0))
            if scan.get("report_content"):
                st.markdown("**Report Preview:**")
                st.markdown(scan["report_content"][:500] + "...")


def show_admin_panel():
    """Display admin analytics and tables."""
    from database import get_all_scans, get_all_users, get_stats
    import pandas as pd
    import streamlit as st

    st.markdown("## Admin Panel")

    stats = get_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", stats["total_users"])
    with col2:
        st.metric("Total Scans", stats["total_scans"])
    with col3:
        st.metric("Total Bugs Found", stats["total_bugs"])

    st.markdown("---")
    tab1, tab2 = st.tabs(["All Users", "All Scans"])

    with tab1:
        users = get_all_users()
        if users:
            df = pd.DataFrame(users)
            df = df[["username", "email", "is_admin", "created_at"]]
            df.columns = ["Username", "Email", "Admin", "Joined"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users found")

    with tab2:
        scans = get_all_scans()
        if scans:
            df = pd.DataFrame(scans)
            df = df[["username", "weak_points_found", "bugs_found", "scanned_at"]]
            df.columns = ["User", "Weak Points", "Bugs Found", "Scanned At"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No scans found")

