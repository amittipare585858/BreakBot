"""Repository and pasted-code ingestion for BreakBot."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


logger = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = [
    '.py',   # Python
    '.js',   # JavaScript
    '.ts',   # TypeScript
    '.jsx',  # React
    '.tsx',  # React TypeScript
    '.java', # Java
    '.go',   # Go
    '.rb',   # Ruby
    '.php',  # PHP
    '.cs',   # C#
    '.cpp',  # C++
    '.c',    # C
    '.rs',   # Rust
    '.swift',# Swift
    '.kt',   # Kotlin
]
SKIP_PARTS = {"node_modules", "__pycache__", ".git"}
MAX_FILE_BYTES = 100 * 1024
GITHUB_API = "https://api.github.com"
RAW_GITHUB = "https://raw.githubusercontent.com"


@dataclass(frozen=True)
class ParsedRepo:
    """Parsed GitHub repository coordinates."""

    owner: str
    repo: str


class RepoIngester:
    """Ingest code from public GitHub repositories or pasted text."""

    def ingest_github(self, repo_url: str) -> dict:
        """Fetch supported source files from a public GitHub repository."""
        parsed = self._parse_repo_url(repo_url)
        repo_name = f"{parsed.owner}/{parsed.repo}"
        logger.info("Ingesting GitHub repository %s", repo_name)

        tree_url = (
            f"{GITHUB_API}/repos/{parsed.owner}/{parsed.repo}/git/trees/main?recursive=1"
        )
        try:
            response = requests.get(tree_url, timeout=20)
            if response.status_code == 404:
                raise ValueError(f"Repository or main branch not found: {repo_name}")
            if response.status_code in {403, 429}:
                raise ValueError("GitHub API rate limit reached. Try again later.")
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ValueError(f"Could not read repository tree: {exc}") from exc

        tree = response.json().get("tree", [])
        if not tree:
            raise ValueError(f"Repository is empty or has no readable tree: {repo_name}")

        files = []
        for item in tree:
            path = item.get("path", "")
            size = int(item.get("size") or 0)
            if item.get("type") != "blob" or not self._is_supported(path):
                continue
            if size > MAX_FILE_BYTES:
                logger.info("Skipping %s because it is larger than 100KB", path)
                continue

            raw_url = f"{RAW_GITHUB}/{parsed.owner}/{parsed.repo}/main/{path}"
            try:
                raw_response = requests.get(raw_url, timeout=20)
                if raw_response.status_code == 404:
                    logger.info("Skipping missing raw file %s", path)
                    continue
                if raw_response.status_code in {403, 429}:
                    raise ValueError("GitHub raw content rate limit reached. Try again later.")
                raw_response.raise_for_status()
            except requests.RequestException as exc:
                raise ValueError(f"Could not fetch raw file {path}: {exc}") from exc

            content_bytes = raw_response.content
            if len(content_bytes) > MAX_FILE_BYTES:
                logger.info("Skipping %s because raw content is larger than 100KB", path)
                continue
            files.append({"path": path, "content": content_bytes.decode("utf-8", "replace")})

        if not files:
            raise ValueError(
                "No supported source files found. BreakBot supports Python, JavaScript, TypeScript, Java, Go, Ruby, PHP, C#, C++, C, Rust, Swift, and Kotlin."
            )

        logger.info("Ingested %s files from %s", len(files), repo_name)
        return {"repo_name": repo_name, "files": files}

    def ingest_code(self, raw_code: str, filename: str) -> dict:
        """Wrap pasted code into BreakBot's repository-like format."""
        if not raw_code.strip():
            raise ValueError("raw_code cannot be empty.")
        filename = filename.strip() or "pasted_code.py"
        logger.info("Ingesting pasted code as %s", filename)
        return {
            "repo_name": "pasted_code",
            "files": [{"path": filename, "content": raw_code}],
        }

    def _parse_repo_url(self, repo_url: str) -> ParsedRepo:
        """Parse a GitHub repository URL into owner and repository name."""
        parsed = urlparse(repo_url.strip())
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("repo_url must be a github.com URL.")

        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise ValueError("repo_url must include owner and repo name.")

        return ParsedRepo(owner=parts[0], repo=parts[1].removesuffix(".git"))

    def _is_supported(self, path: str) -> bool:
        """Return whether a repository path should be ingested."""
        parts = set(path.split("/"))
        if parts & SKIP_PARTS:
            return False
        return path.endswith(tuple(SUPPORTED_EXTENSIONS))
