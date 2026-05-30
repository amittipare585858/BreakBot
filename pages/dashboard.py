"""Legacy dashboard module.

The dashboard is now implemented in index.html and powered by api.py.
"""


def show_dashboard(username: str, is_admin: bool = False):
    raise RuntimeError("Legacy dashboard was removed. Use index.html instead.")