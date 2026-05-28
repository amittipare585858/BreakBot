"""Supabase database helpers for BreakBot."""

from __future__ import annotations

import hashlib
import os

import streamlit as st


def get_supabase():
    """Create and return a Supabase client, or None on failure."""
    try:
        from supabase import create_client

        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except Exception:
            from dotenv import load_dotenv

            load_dotenv()
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_KEY", "")
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, email: str, password: str) -> dict:
    """Register a user in Supabase."""
    try:
        supabase = get_supabase()
        if not supabase:
            return {"success": False, "error": "Database connection failed"}
        existing = (
            supabase.table("users")
            .select("username")
            .eq("username", username)
            .execute()
        )
        if existing.data:
            return {
                "success": False,
                "error": "Username already taken. "
                         "Please choose a different username.",
            }
        existing_email = (
            supabase.table("users")
            .select("email")
            .eq("email", email)
            .execute()
        )
        if existing_email.data:
            return {
                "success": False,
                "error": "Email already registered. "
                         "Please use a different email or login.",
            }
        supabase.table("users").insert(
            {
                "username": username,
                "email": email,
                "password": hash_password(password),
                "is_admin": False,
            }
        ).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_user(username: str, password: str) -> dict:
    """Verify a username and password against Supabase."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
        result = (
            supabase.table("users")
            .select("*")
            .eq("username", username)
            .eq("password", hash_password(password))
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception:
        return None


def save_scan_history(
    username: str,
    code_snippet: str,
    weak_points: int,
    bugs: int,
    report: str,
):
    """Save a scan history entry for a user."""
    try:
        supabase = get_supabase()
        if not supabase:
            return
        supabase.table("scan_history").insert(
            {
                "username": username,
                "code_snippet": code_snippet[:500],
                "weak_points_found": weak_points,
                "bugs_found": bugs,
                "report_content": report,
            }
        ).execute()
    except Exception as e:
        print(f"Error saving history: {e}")


def get_user_history(username: str) -> list:
    """Return recent scan history for a user."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        result = (
            supabase.table("scan_history")
            .select("*")
            .eq("username", username)
            .order("scanned_at", desc=True)
            .limit(10)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_all_users() -> list:
    """Return all users for the admin panel."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        result = (
            supabase.table("users")
            .select("id,username,email,is_admin,created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_all_scans() -> list:
    """Return recent scans for the admin panel."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        result = (
            supabase.table("scan_history")
            .select("*")
            .order("scanned_at", desc=True)
            .limit(50)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_stats() -> dict:
    """Return aggregate admin stats."""
    try:
        supabase = get_supabase()
        if not supabase:
            return {"total_users": 0, "total_scans": 0, "total_bugs": 0}
        users = supabase.table("users").select("id", count="exact").execute()
        scans = supabase.table("scan_history").select("id", count="exact").execute()
        bugs = supabase.table("scan_history").select("bugs_found").execute()
        total_bugs = sum(s.get("bugs_found", 0) for s in (bugs.data or []))
        return {
            "total_users": users.count or 0,
            "total_scans": scans.count or 0,
            "total_bugs": total_bugs,
        }
    except Exception:
        return {"total_users": 0, "total_scans": 0, "total_bugs": 0}
