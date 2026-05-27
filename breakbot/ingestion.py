from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from breakbot.config import BreakBotConfig
from breakbot.models import CodeFile, SourceBundle


PYTHON_SUFFIXES = {".py"}
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str


def parse_github_url(url: str) -> GitHubRepo:
    parsed = urlparse(url.strip())
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Expected a github.com repository URL.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub URL must include owner and repository name.")

    return GitHubRepo(owner=parts[0], name=parts[1].removesuffix(".git"))


class SourceIngestor:
    def __init__(self, config: BreakBotConfig):
        self.config = config

    def from_pasted_code(self, code: str) -> SourceBundle:
        if not code.strip():
            raise ValueError("Paste code before running BreakBot.")
        return SourceBundle(
            source_name="pasted-code",
            files=[CodeFile(path="pasted_code.py", content=code.strip() + "\n")],
        )

    def from_github(self, url: str) -> SourceBundle:
        repo = parse_github_url(url)
        tree_url = (
            f"{self.config.github_api_base}/repos/{repo.owner}/{repo.name}"
            "/git/trees/HEAD?recursive=1"
        )
        tree_response = requests.get(tree_url, timeout=20)
        tree_response.raise_for_status()
        tree = tree_response.json().get("tree", [])

        selected = []
        for item in tree:
            path = item.get("path", "")
            if item.get("type") != "blob":
                continue
            if not self._is_supported_path(path):
                continue
            if int(item.get("size") or 0) > self.config.max_file_bytes:
                continue
            selected.append(path)
            if len(selected) >= self.config.max_repo_files:
                break

        files = [self._fetch_file(repo, path) for path in selected]
        if not files:
            raise ValueError("No supported Python files were found in the repository.")
        return SourceBundle(source_name=f"{repo.owner}/{repo.name}", files=files)

    def _fetch_file(self, repo: GitHubRepo, path: str) -> CodeFile:
        contents_url = f"{self.config.github_api_base}/repos/{repo.owner}/{repo.name}/contents/{path}"
        response = requests.get(contents_url, timeout=20)
        response.raise_for_status()
        payload = response.json()
        encoded = re.sub(r"\s+", "", payload.get("content", ""))
        content = base64.b64decode(encoded).decode("utf-8", errors="replace")
        return CodeFile(path=path, content=content)

    def _is_supported_path(self, path: str) -> bool:
        parts = set(path.split("/"))
        if parts & SKIP_PARTS:
            return False
        return any(path.endswith(suffix) for suffix in PYTHON_SUFFIXES)
