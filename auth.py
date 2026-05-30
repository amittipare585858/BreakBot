"""Legacy auth module.

Authentication is now handled by FastAPI endpoints in api.py:
- POST /auth/login
- POST /auth/register
"""


def show_login_page():
    raise RuntimeError("Legacy UI was removed. Use index.html with api.py instead.")


def show_user_history():
    raise RuntimeError("Legacy UI was removed. Use GET /history/{username} instead.")


def show_admin_panel():
    raise RuntimeError("Legacy UI was removed. Use /admin endpoints instead.")