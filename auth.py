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
                if not new_user or not new_pass or not confirm_pass:
                    st.error("Please fill in all fields")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match")
                elif register_user(new_user, new_pass):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already taken")
