import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="BreakBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class ScanRequest(BaseModel):
    code: str
    filename: str = "pasted_code.py"
    username: str


class GithubScanRequest(BaseModel):
    repo_url: str
    username: str


class ScanPipeline:
    def __init__(self, files: list[dict[str, str]], repo_name: str, username: str):
        self.files = files
        self.repo_name = repo_name
        self.username = username
        self.code = "\n\n".join(file.get("content", "") for file in files)


def _scan_from_code(request: ScanRequest) -> ScanPipeline:
    if not request.code.strip():
        raise ValueError("Code cannot be empty.")
    filename = request.filename.strip() or "pasted_code.py"
    return ScanPipeline(
        files=[{"path": filename, "content": request.code}],
        repo_name=filename,
        username=request.username,
    )


def _serialize_error(exc: Exception) -> dict[str, Any]:
    logger.exception("BreakBot API error: %s", exc)
    return {"success": False, "error": str(exc)}


@app.post("/auth/login")
async def login(request: LoginRequest):
    try:
        from database import verify_user
        user = verify_user(request.username, request.password)
        if user:
            return {
                "success": True,
                "user": {
                    "username": user["username"],
                    "email": user.get("email", ""),
                    "is_admin": user.get("is_admin", False),
                },
            }
        return {"success": False, "error": "Invalid username or password"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/auth/register")
async def register(request: RegisterRequest):
    try:
        from database import register_user
        return register_user(request.username, request.email, request.password)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scan/analyze")
async def analyze_code(request: ScanRequest):
    try:
        from agent.analyzer import CodeAnalyzer
        scan = _scan_from_code(request)
        analysis = CodeAnalyzer().analyze(scan.files)
        return {"success": True, "analysis": analysis}
    except Exception as exc:
        return _serialize_error(exc)


@app.post("/scan/github")
async def analyze_github(request: GithubScanRequest):
    try:
        from agent.analyzer import CodeAnalyzer
        from agent.ingester import RepoIngester
        ingested = RepoIngester().ingest_github(request.repo_url)
        analysis = CodeAnalyzer().analyze(ingested["files"])
        return {
            "success": True,
            "repo_name": ingested["repo_name"],
            "files": ingested["files"],
            "analysis": analysis,
        }
    except Exception as exc:
        return _serialize_error(exc)


@app.post("/scan/attack")
async def generate_attack(request: ScanRequest):
    try:
        from agent.analyzer import CodeAnalyzer
        from agent.attacker import AttackGenerator
        scan = _scan_from_code(request)
        analysis = CodeAnalyzer().analyze(scan.files)
        attack_code = AttackGenerator().generate_attacks(analysis, scan.code)
        return {"success": True, "attack_code": attack_code, "analysis": analysis}
    except Exception as exc:
        return _serialize_error(exc)


@app.post("/scan/run")
async def run_tests(request: ScanRequest):
    try:
        from agent.analyzer import CodeAnalyzer
        from agent.attacker import AttackGenerator
        from agent.runner import TestRunner
        scan = _scan_from_code(request)
        analysis = CodeAnalyzer().analyze(scan.files)
        AttackGenerator().generate_attacks(analysis, scan.code)
        results = TestRunner().run("temp/breakbot_tests.py")
        return {"success": True, "analysis": analysis, "results": results}
    except Exception as exc:
        return _serialize_error(exc)


@app.post("/scan/report")
async def generate_report(request: ScanRequest):
    try:
        from agent.analyzer import CodeAnalyzer
        from agent.attacker import AttackGenerator
        from agent.fix_suggester import FixSuggester
        from agent.reporter import BugReporter
        from agent.runner import TestRunner
        from database import save_scan_history

        scan = _scan_from_code(request)
        analysis = CodeAnalyzer().analyze(scan.files)
        attack_code = AttackGenerator().generate_attacks(analysis, scan.code)
        results = TestRunner().run("temp/breakbot_tests.py")
        fixes = FixSuggester().suggest_all_fixes(
            analysis.get("weak_points", []), scan.code)
        report = BugReporter().compile_report(
            repo_name=scan.repo_name,
            analysis=analysis,
            test_results=results,
            fixes=fixes,
        )
        save_scan_history(
            username=scan.username,
            code_snippet=scan.code[:500],
            weak_points=len(analysis.get("weak_points", [])),
            bugs=results.get("failed", 0),
            report=report if isinstance(report, str) else str(report),
        )
        return {
            "success": True,
            "analysis": analysis,
            "attack_code": attack_code,
            "results": results,
            "fixes": fixes,
            "report": report,
        }
    except Exception as exc:
        return _serialize_error(exc)


@app.get("/history/{username}")
async def get_history(username: str):
    try:
        from database import get_user_history
        return {"success": True, "history": get_user_history(username)}
    except Exception as exc:
        return _serialize_error(exc)


@app.get("/admin/stats")
async def get_stats():
    try:
        from database import get_stats
        return get_stats()
    except Exception as exc:
        return _serialize_error(exc)


@app.get("/admin/users")
async def get_users():
    try:
        from database import get_all_users
        return {"success": True, "users": get_all_users()}
    except Exception as exc:
        return _serialize_error(exc)


@app.get("/")
async def root():
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "BreakBot API Running", "version": "2.0"}


@app.get("/health")
async def health():
    return {"message": "BreakBot API Running", "version": "2.0"}


static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")