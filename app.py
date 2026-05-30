"""Legacy entrypoint for the rebuilt BreakBot FastAPI application.

Run with:
    uvicorn api:app --reload
"""

from api import app

__all__ = ["app"]