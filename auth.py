"""Simple Streamlit authentication helpers for BreakBot."""

from __future__ import annotations

import hashlib
import json
import os

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


def show_login_page() -> None:
    """Display the login/register page."""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: #0a0a0f; color: #ffffff; }
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 40px;
        background: #16213e;
        border: 1px solid #ff3b3b30;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(255,59,59,0.1);
    }
    .login-logo {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, #ff3b3b, #ff8080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 8px;
    }
    .login-sub {
        text-align: center;
        color: #a0a0b0;
        font-size: 14px;
        margin-bottom: 32px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ff3b3b, #cc0000) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 12px !important;
    }
    .stTextInput > div > div > input {
        background: #0a0a0f !important;
        border: 1px solid #ff3b3b30 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0a0b0;
    }
    .stTabs [aria-selected="true"] {
        color: #ff3b3b;
        border-bottom: 2px solid #ff3b3b;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-logo">BREAKBOT</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-sub">AI Red-Team Security Agent</div>',
            unsafe_allow_html=True,
        )

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            username = st.text_input(
                "Username",
                key="login_user",
                placeholder="Enter username",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="login_pass",
                placeholder="Enter password",
            )

            if st.button("Login", key="login_btn"):
                if not username or not password:
                    st.error("Please fill in all fields")
                elif verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

            st.markdown("---")
            st.markdown(
                "Demo account: username `demo` password `demo123`",
                unsafe_allow_html=True,
            )

        with tab2:
            new_user = st.text_input(
                "Choose Username",
                key="reg_user",
                placeholder="Enter username",
            )
            new_email = st.text_input(
                "Gmail Address",
                key="reg_email",
                placeholder="yourname@gmail.com",
            )
            new_pass = st.text_input(
                "Choose Password",
                type="password",
                key="reg_pass",
                placeholder="Min 6 characters",
            )
            confirm_pass = st.text_input(
                "Confirm Password",
                type="password",
                key="reg_confirm",
                placeholder="Repeat password",
            )

            if st.button("Create Account", key="reg_btn"):
                if not new_user or not new_email or not new_pass or not confirm_pass:
                    st.error("Please fill in all fields")
                elif not new_email.lower().endswith("@gmail.com"):
                    st.error("Email must be a Gmail address")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match")
                elif register_user(new_user, new_pass):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already taken")


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
